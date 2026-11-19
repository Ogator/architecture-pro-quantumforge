"""Dense retrieval for the masked corpus; no LLM or original-term map is used."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import re
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODEL = "BAAI/bge-m3"
COLLECTION = "quantumforge"
DIMENSION = 1024


def chunks_from_directory(directory: Path) -> list[dict]:
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    # Prefer paragraph and sentence boundaries; cap chunks by word count.
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=250, chunk_overlap=35, length_function=lambda s: len(s.split()),
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = []
    for source in sorted(directory.glob("*.md")):
        text = source.read_text(encoding="utf-8")
        if not text.strip():
            continue
        title = text.splitlines()[0][:160]
        previous_start = previous_end = 0
        for ordinal, body in enumerate(splitter.split_text(text)):
            # Search from the last overlap region, avoiding matches in earlier sections.
            start = text.find(body, previous_start if ordinal == 0 else max(previous_start + 1, previous_end - len(body)))
            if start < 0:
                raise ValueError(f"Cannot locate chunk {ordinal}: {source}")
            end = start + len(body)
            headings = list(re.finditer(r"(?m)^(?:=+\s*(.*?)\s*=+|#{1,6}\s+(.+))$", text[:start]))
            section = next((g for g in headings[-1].groups() if g), "Introduction") if headings else "Introduction"
            try:
                path = source.resolve().relative_to(ROOT).as_posix()
            except ValueError:
                path = str(source.resolve())
            digest = hashlib.sha256(text.encode()).hexdigest()
            chunk_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{path}:{digest}:{start}:{end}"))
            chunks.append(dict(id=chunk_id, source=path, title=title, section=section,
                               ordinal=ordinal, start_char=start, end_char=end,
                               start_line=text.count("\n", 0, start) + 1,
                               end_line=text.count("\n", 0, end - 1) + 1,
                               source_sha256=digest, text=body, words=len(body.split())))
            previous_start, previous_end = start, end
    if not chunks:
        raise ValueError(f"No nonempty Markdown documents in {directory}")
    return chunks


def load_model(revision=None):
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(MODEL, revision=revision, device="cpu")


@contextmanager
def client_at(path: Path):
    from qdrant_client import QdrantClient
    client = QdrantClient(path=str(path))
    try:
        yield client
    finally:
        client.close()


def build(args):
    from qdrant_client import models
    import numpy as np

    if args.output.exists():
        raise ValueError(f"Output already exists: {args.output}; choose a new --output")
    started = time.perf_counter()
    chunks = chunks_from_directory(args.source)
    model = load_model(args.revision)
    embedding_started = time.perf_counter()
    vectors = model.encode([c['text'] for c in chunks], batch_size=args.batch_size,
                           normalize_embeddings=True, show_progress_bar=True)
    embedding_seconds = time.perf_counter() - embedding_started
    if vectors.shape != (len(chunks), DIMENSION) or not np.isfinite(vectors).all():
        raise ValueError(f"Invalid embeddings: {vectors.shape}")
    args.output.mkdir(parents=True)
    with client_at(args.output / 'qdrant') as client:
        client.create_collection(COLLECTION, vectors_config=models.VectorParams(size=DIMENSION, distance=models.Distance.COSINE))
        for offset in range(0, len(chunks), 64):
            client.upsert(COLLECTION, points=[models.PointStruct(id=c['id'], vector=v.tolist(), payload=c)
                          for c, v in zip(chunks[offset:offset+64], vectors[offset:offset+64])], wait=True)
        assert client.count(COLLECTION, exact=True).count == len(chunks)
    with (args.output / 'chunks.jsonl').open('w', encoding='utf-8') as stream:
        for chunk in chunks:
            stream.write(json.dumps(chunk, ensure_ascii=False) + '\n')
    # Portable, non-pickle export, independent of Qdrant's local storage format.
    np.save(args.output / 'vectors.npy', vectors, allow_pickle=False)
    manifest = dict(model=MODEL, revision=args.revision, dimension=DIMENSION, distance='Cosine',
                    documents=len({c['source'] for c in chunks}), chunks=len(chunks),
                    chunk_words=250, overlap_words=35, embedding_seconds=embedding_seconds,
                    total_seconds=time.perf_counter()-started)
    (args.output / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps(manifest, indent=2))


def retrieve(client, model, query, top_k):
    vector = model.encode(query, normalize_embeddings=True).tolist()
    return [dict(score=p.score, **p.payload) for p in client.query_points(
        COLLECTION, query=vector, limit=top_k, with_payload=True).points]


CASES = [
    ("Какая раса с Droganth ценит честь и боевые традиции?", "klingon.md"),
    ("How does the slipstream core enable faster than light travel?", "warp_drive.md"),
    ("What is the Sanctity Edict and does it forbid interference with developing civilizations?", "prime_directive.md"),
]


def search(args):
    manifest = json.loads((args.index / 'manifest.json').read_text())
    if manifest['model'] != MODEL or manifest['dimension'] != DIMENSION:
        raise ValueError('Incompatible embedding model')
    if not (args.index / 'qdrant').is_dir():
        raise ValueError('Qdrant storage is missing')
    model = load_model(manifest['revision'])
    with client_at(args.index / 'qdrant') as client:
        if args.evaluate:
            results = []
            for query, expected in CASES:
                hits = retrieve(client, model, query, args.top_k)
                results.append(dict(query=query, expected_source=expected,
                                    passed=any(h['source'].endswith('/' + expected) for h in hits), hits=hits))
            report = dict(top_k=args.top_k, passed=sum(r['passed'] for r in results), total=len(results), cases=results)
            (args.index / 'search_examples.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
            print(json.dumps({k:v for k,v in report.items() if k != 'cases'}, indent=2))
            if report['passed'] != report['total']:
                raise SystemExit(1)
        else:
            print(json.dumps(retrieve(client, model, args.query, args.top_k), ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    b = sub.add_parser('build')
    b.add_argument('--source', type=Path, default=ROOT / 'task_2' / 'artifacts' / 'knowledge_base')
    b.add_argument('--output', type=Path, default=ROOT / 'task_3' / 'artifacts' / 'index')
    b.add_argument('--revision', required=True, help='Hugging Face model commit SHA')
    b.add_argument('--batch-size', type=int, default=8)
    s = sub.add_parser('search')
    s.add_argument('query', nargs='?', default='')
    s.add_argument('--index', type=Path, default=ROOT / 'task_3' / 'artifacts' / 'index')
    s.add_argument('--top-k', type=int, default=3)
    s.add_argument('--evaluate', action='store_true')
    args = parser.parse_args()
    if args.command == 'search' and (args.top_k < 1 or not (args.query.strip() or args.evaluate)):
        parser.error('Provide a nonempty query or --evaluate; --top-k must be positive')
    if args.command == 'build' and args.batch_size < 1:
        parser.error('--batch-size must be positive')
    (build if args.command == 'build' else search)(args)


if __name__ == '__main__':
    main()
