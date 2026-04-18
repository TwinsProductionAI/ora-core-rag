import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ora_core_rag.index import ORACoreIndex
from ora_core_rag.orchestrator import ORAOrchestratorConnector


class OrchestratorConnectorTests(unittest.TestCase):
    def test_returns_orchestrator_packet_with_supported_retrieval(self):
        with tempfile.TemporaryDirectory() as tmp:
            index = ORACoreIndex(Path(tmp) / "index.sqlite")
            index.add_document(
                {
                    "id": "orch_doc",
                    "uri": "memory://orch",
                    "kind": "text",
                    "scope": "ORA_CORE",
                    "canon_level": "CORE",
                    "title": "Orch Doc",
                    "tags": [],
                },
                "ORCHESTRATEUR_LLM decides which module to consult and when verification runs.",
            )
            connector = ORAOrchestratorConnector(index)
            packet = connector.route({
                "request_id": "REQ-1",
                "query": "ORCHESTRATEUR_LLM verification",
                "risk_level": "MID",
            })

            self.assertEqual(packet["primary_module"], "ORA_CORE_RAG")
            self.assertEqual(packet["retrieval"]["status"], "SUPPORTED")
            self.assertEqual(packet["verify_status"], "RECOMMENDED")
            self.assertIn("GPV2", packet["authority_path"])

    def test_marks_verification_unavailable_without_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            index = ORACoreIndex(Path(tmp) / "index.sqlite")
            connector = ORAOrchestratorConnector(index)
            packet = connector.route({"query": "unknown canon item", "source_required": True})
            self.assertEqual(packet["retrieval"]["status"], "UNSURE")
            self.assertEqual(packet["verify_status"], "UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
