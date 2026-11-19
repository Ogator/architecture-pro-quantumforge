"""Add a new document to existing vector index.

Idempotent: adding the same document twice replaces existing chunks in Qdrant
(same deterministic IDs) and skips appending to chunks.jsonl / vectors.npy.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'task_3' / 'tools'))

from vector_index import chunks_from_directory, load_model, client_at, COLLECTION, MODEL, DIMENSION


def _stable_chunk_ids(chunks: list[dict], real_path: str) -> list[dict]:
    """
    Re-derive chunk IDs using the real file path instead of the temp path.

    vector_index.py sets id = uuid5(path:sha256:start:end).
    When we chunkify inside a temp dir the path is the temp path,
    so each run produces different IDs.  Here we recompute with the
    stable path the caller intends, making repeated adds idempotent.
    """
    for chunk in chunks:
        digest = chunk['source_sha256']
        start  = chunk['start_char']
        end    = chunk['end_char']
        chunk['id']     = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{real_path}:{digest}:{start}:{end}"))
        chunk['source'] = real_path
    return chunks


def _already_indexed(index_path: Path, real_path: str) -> bool:
    """Return True if any chunk from this file is present in chunks.jsonl."""
    jsonl = index_path / 'chunks.jsonl'
    if not jsonl.exists():
        return False
    with jsonl.open(encoding='utf-8') as f:
        for line in f:
            try:
                if json.loads(line).get('source') == real_path:
                    return True
            except json.JSONDecodeError:
                pass
    return False


def add_document_to_index(doc_path: Path, index_path: Path):
    """
    Add a single document to existing vector index.

    Safe to run multiple times with the same file: Qdrant upsert replaces
    existing points (same IDs), and chunks.jsonl / vectors.npy are only
    appended when the document is new.
    """
    import shutil
    import tempfile

    import numpy as np
    from qdrant_client import models

    # Validate index
    manifest_path = index_path / 'manifest.json'
    if not manifest_path.exists():
        raise ValueError(f"Index manifest not found: {manifest_path}")
    manifest = json.loads(manifest_path.read_text())
    if manifest['model'] != MODEL or manifest['dimension'] != DIMENSION:
        raise ValueError('Incompatible embedding model')

    # Determine stable source path (relative to ROOT when possible)
    try:
        real_path = doc_path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        real_path = str(doc_path.resolve())

    already_exists = _already_indexed(index_path, real_path)
    if already_exists:
        print(f"⚠ Document already indexed: {real_path}")
        print("  Qdrant points will be replaced (upsert), "
              "chunks.jsonl / vectors.npy will NOT be re-appended.")

    print(f"Adding document: {doc_path}")

    # Chunkify in temp dir so chunks_from_directory sees exactly one file
    with tempfile.TemporaryDirectory() as tmp:
        shutil.copy(doc_path, Path(tmp) / doc_path.name)
        print("Creating chunks...")
        chunks = chunks_from_directory(Path(tmp))

    # Re-derive IDs with the stable (real) path → idempotent upsert
    chunks = _stable_chunk_ids(chunks, real_path)
    print(f"Created {len(chunks)} chunks (source: {real_path})")

    # Embeddings
    print("Loading embedding model...")
    model = load_model(manifest.get('revision'))
    print("Creating embeddings...")
    vectors = model.encode(
        [c['text'] for c in chunks],
        batch_size=8,
        normalize_embeddings=True,
        show_progress_bar=True
    )
    if vectors.shape != (len(chunks), DIMENSION) or not __import__('numpy').isfinite(vectors).all():
        raise ValueError(f"Invalid embeddings shape: {vectors.shape}")

    # Upsert into Qdrant (replaces existing points with same IDs)
    print("Upserting into Qdrant...")
    with client_at(index_path / 'qdrant') as client:
        before = client.count(COLLECTION, exact=True).count
        for offset in range(0, len(chunks), 64):
            client.upsert(
                COLLECTION,
                points=[
                    models.PointStruct(id=c['id'], vector=v.tolist(), payload=c)
                    for c, v in zip(chunks[offset:offset+64], vectors[offset:offset+64])
                ],
                wait=True
            )
        after = client.count(COLLECTION, exact=True).count

    if already_exists:
        print(f"Qdrant: replaced {len(chunks)} existing points (total unchanged: {after})")
    else:
        print(f"Qdrant: added {after - before} new points (total: {after})")

    # Append to flat files only if document is new
    if not already_exists:
        print("Appending to chunks.jsonl...")
        with (index_path / 'chunks.jsonl').open('a', encoding='utf-8') as f:
            for chunk in chunks:
                f.write(json.dumps(chunk, ensure_ascii=False) + '\n')

        print("Appending to vectors.npy...")
        existing = np.load(index_path / 'vectors.npy')
        np.save(index_path / 'vectors.npy',
                np.vstack([existing, vectors]), allow_pickle=False)

        # Update manifest counts
        manifest['chunks'] += len(chunks)
        manifest['documents'] = len({
            json.loads(line)['source']
            for line in (index_path / 'chunks.jsonl').read_text().splitlines()
            if line.strip()
        })
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')

    print("\n✓ Done!")
    print(f"  Document : {real_path}")
    print(f"  Chunks   : {len(chunks)}")
    if not already_exists:
        print(f"  Total docs   : {manifest['documents']}")
        print(f"  Total chunks : {manifest['chunks']}")
    else:
        print("  (chunks.jsonl / vectors.npy unchanged — document was already indexed)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('document', type=Path, help='Path to .md file to add')
    parser.add_argument(
        '--index', type=Path,
        default=ROOT / 'task_3' / 'artifacts' / 'index',
        help='Path to existing index'
    )
    args = parser.parse_args()

    if not args.document.exists():
        parser.error(f"Document not found: {args.document}")
    if args.document.suffix != '.md':
        parser.error("Document must be a .md file")
    if not args.index.exists():
        parser.error(f"Index not found: {args.index}")

    try:
        add_document_to_index(args.document, args.index)
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
