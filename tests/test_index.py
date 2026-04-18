import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ora_core_rag.index import IndexError, ORACoreIndex


class ORACoreIndexTests(unittest.TestCase):
    def test_ingests_and_retrieves_core_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source_file = tmp_path / "ora.md"
            source_file.write_text(
                "# ORA\n\nM03 PRIMORDIA is the truth tribunal.\n\nM20 GL is the truth layer.",
                encoding="utf-8",
            )
            manifest = tmp_path / "sources.json"
            manifest.write_text(
                json.dumps({
                    "version": "1.0.0",
                    "sources": [
                        {
                            "id": "test_ora",
                            "uri": "ora.md",
                            "kind": "markdown",
                            "scope": "ORA_CORE",
                            "canon_level": "CORE",
                            "title": "Test ORA",
                            "tags": ["test"],
                        }
                    ],
                }),
                encoding="utf-8",
            )

            index = ORACoreIndex(tmp_path / "index.sqlite")
            ingest = index.ingest_manifest(manifest)
            self.assertEqual(ingest[0]["chunk_count"], 1)

            packet = index.query("PRIMORDIA truth tribunal")
            self.assertEqual(packet["status"], "SUPPORTED")
            self.assertEqual(packet["results"][0]["source_id"], "test_ora")

    def test_unknown_query_returns_unsure(self):
        with tempfile.TemporaryDirectory() as tmp:
            index = ORACoreIndex(Path(tmp) / "index.sqlite")
            packet = index.query("this token does not exist")
            self.assertEqual(packet["status"], "UNSURE")
            self.assertEqual(packet["results"], [])

    def test_refuses_client_scope_in_core_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            index = ORACoreIndex(Path(tmp) / "index.sqlite")
            with self.assertRaises(IndexError):
                index.add_document(
                    {
                        "id": "client_doc",
                        "uri": "memory://client",
                        "kind": "text",
                        "scope": "TENANT",
                        "canon_level": "CORE",
                        "title": "Client Doc",
                        "tags": [],
                    },
                    "client payload must not enter ORA core",
                )


if __name__ == "__main__":
    unittest.main()
