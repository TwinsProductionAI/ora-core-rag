import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ora_core_rag.governor import RAGGovernor


class RAGGovernorTests(unittest.TestCase):
    def _write_governor_fixture(self, tmp_path: Path) -> Path:
        examples = tmp_path / "examples"
        examples.mkdir()
        source = examples / "source.md"
        source.write_text("# ORA\n\nORCHESTRATEUR_LLM routes modules. PRIMORDIA verifies truth.", encoding="utf-8")
        sources = examples / "sources.json"
        sources.write_text(json.dumps({
            "version": "1.0.0",
            "sources": [
                {
                    "id": "local_ora",
                    "uri": "source.md",
                    "kind": "markdown",
                    "scope": "ORA_CORE",
                    "canon_level": "CORE",
                    "title": "Local ORA",
                    "tags": ["test"],
                }
            ],
        }), encoding="utf-8")
        route = examples / "route.json"
        route.write_text(json.dumps({
            "route_id": "GLK[TENANT:K7F3:PROD:v1]",
            "tenant_id": "K7F3",
            "environment": "prod",
            "isolation": "strict",
            "allowed_rags": ["K7F3_RAG_DOCS"],
            "allowed_agents": [],
        }), encoding="utf-8")
        registry = examples / "registry.json"
        registry.write_text(json.dumps({
            "version": "1.0.0",
            "entries": [
                {"id": "K7F3_RAG_DOCS", "type": "rag", "scope": "TENANT", "tenant_id": "K7F3", "can_answer_final": False}
            ],
        }), encoding="utf-8")
        config = examples / "governor.json"
        config.write_text(json.dumps({
            "version": "0.4.0",
            "profile": "test-governor",
            "paths": {"db": "data/index/test.sqlite", "audit_log": "data/audit/test.jsonl"},
            "sources_manifest": "examples/sources.json",
            "route_manifest": "examples/route.json",
            "rag_registry": "examples/registry.json",
            "defaults": {
                "query": "ORCHESTRATEUR_LLM PRIMORDIA",
                "top_k": 5,
                "risk_level": "MID",
                "freshness_need": "LOW",
                "source_required": True,
                "neroflux_signal": {"client_sensitivity": 0.2},
            },
        }), encoding="utf-8")
        return config

    def test_status_reports_ready_environment(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = self._write_governor_fixture(Path(tmp))
            status = RAGGovernor.from_path(config).status()
            self.assertTrue(status["ready"])
            self.assertTrue(status["environment"]["sqlite_fts5"])
            self.assertEqual(status["route"]["tenant_id"], "K7F3")

    def test_bootstrap_ingests_and_run_returns_governed_packet(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = self._write_governor_fixture(Path(tmp))
            governor = RAGGovernor.from_path(config)
            bootstrap = governor.bootstrap(ingest=True)
            self.assertEqual(bootstrap["status"], "BOOTSTRAPPED")
            self.assertEqual(len(bootstrap["ingested"]), 1)

            result = governor.run()
            self.assertEqual(result["retrieval_packet"]["retrieval"]["status"], "SUPPORTED")
            self.assertEqual(result["client_plan"]["selected"][0]["id"], "K7F3_RAG_DOCS")


if __name__ == "__main__":
    unittest.main()
