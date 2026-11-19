import tempfile
import unittest
from pathlib import Path
from task_3.tools.vector_index import chunks_from_directory, ROOT


class ChunkTests(unittest.TestCase):
    def test_real_corpus_offsets_and_ids(self):
        chunks = chunks_from_directory(ROOT / 'task_2' / 'artifacts' / 'knowledge_base')
        self.assertGreaterEqual(len({c['source'] for c in chunks}), 30)
        self.assertEqual(len(chunks), len({c['id'] for c in chunks}))
        self.assertEqual(chunks, chunks_from_directory(ROOT / 'task_2' / 'artifacts' / 'knowledge_base'))
        for c in chunks:
            source = (ROOT / c['source']).read_text(encoding='utf-8')
            self.assertEqual(source[c['start_char']:c['end_char']], c['text'])
            self.assertLessEqual(c['words'], 250)
            self.assertGreater(c['words'], 0)
            self.assertEqual(c['start_line'], source.count('\n', 0, c['start_char']) + 1)

    def test_repeated_text_and_unicode(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            text = '== Раздел ==\n\n' + ('Пример текста. ' * 900)
            (path / 'example.md').write_text(text, encoding='utf-8')
            chunks = chunks_from_directory(path)
            self.assertGreater(len(chunks), 1)
            for c in chunks:
                self.assertEqual(text[c['start_char']:c['end_char']], c['text'])
            self.assertEqual(sorted(c['start_char'] for c in chunks), [c['start_char'] for c in chunks])

    def test_empty_corpus(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                chunks_from_directory(Path(tmp))


class StorageTests(unittest.TestCase):
    def test_disk_roundtrip_and_cosine_ranking(self):
        from qdrant_client import models
        from task_3.tools.vector_index import client_at, COLLECTION, DIMENSION
        import uuid
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'qdrant'
            x, y = [1.0] + [0.0] * (DIMENSION-1), [0.0, 1.0] + [0.0] * (DIMENSION-2)
            with client_at(path) as client:
                client.create_collection(COLLECTION, vectors_config=models.VectorParams(size=DIMENSION, distance=models.Distance.COSINE))
                client.upsert(COLLECTION, points=[models.PointStruct(id=str(uuid.uuid4()), vector=v, payload={'text': t}) for v,t in [(x,'first'),(y,'second')]])
            with client_at(path) as client:
                hits = client.query_points(COLLECTION, query=x, limit=2).points
                self.assertEqual(hits[0].payload['text'], 'first')
                self.assertAlmostEqual(hits[0].score, 1.0)
                self.assertEqual(client.count(COLLECTION, exact=True).count, 2)


if __name__ == '__main__':
    unittest.main()
