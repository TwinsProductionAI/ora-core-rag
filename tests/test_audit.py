import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ora_core_rag.index import ORACoreIndex


class AuditTests(unittest.TestCase):
    def test_query_writes_jsonl_audit_when_enabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            audit_log = tmp_path / "audit.jsonl"
            index = ORACoreIndex(tmp_path / "index.sqlite", audit_log=audit_log)
            index.add_document(
                {
                    "id": "audit_doc",
                    "uri": "memory://audit",
                    "kind": "text",
                    "scope": "ORA_CORE",
                    "canon_level": "CORE",
                    "title": "Audit Doc",
                    "tags": [],
                },
                "PRIMORDIA checks truth before comfort.",
            )
            packet = index.query("PRIMORDIA truth")

            self.assertEqual(packet["status"], "SUPPORTED")
            lines = audit_log.read_text(encoding="utf-8").splitlines()
            event_types = [json.loads(line)["event_type"] for line in lines]
            self.assertIn("document_indexed", event_types)
            self.assertIn("query", event_types)


if __name__ == "__main__":
    unittest.main()
