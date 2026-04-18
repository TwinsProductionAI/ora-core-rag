import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ora_core_rag.registry import RAGRegistry, RegistryError


ROUTE = {
    "route_id": "GLK[TENANT:K7F3:PROD:v1]",
    "tenant_id": "K7F3",
    "environment": "prod",
    "isolation": "strict",
    "allowed_rags": ["K7F3_RAG_DOCS", "K7F3_RAG_SUPPORT"],
    "allowed_agents": ["K7F3_AGENT_SUPPORT"],
}

REGISTRY = {
    "version": "1.1.0",
    "entries": [
        {"id": "ORA_CORE_RAG", "type": "rag", "scope": "ORA_CORE", "can_answer_final": False},
        {"id": "K7F3_RAG_DOCS", "type": "rag", "scope": "TENANT", "tenant_id": "K7F3", "can_answer_final": False},
        {"id": "K7F3_RAG_SUPPORT", "type": "rag", "scope": "TENANT", "tenant_id": "K7F3", "can_answer_final": False},
        {"id": "K7F3_AGENT_SUPPORT", "type": "agent", "scope": "TENANT", "tenant_id": "K7F3", "can_answer_final": False},
        {"id": "ABCD_RAG_DOCS", "type": "rag", "scope": "TENANT", "tenant_id": "ABCD", "can_answer_final": False},
    ],
}


class RegistryPlanningTests(unittest.TestCase):
    def test_default_route_selects_allowed_resources(self):
        plan = RAGRegistry(REGISTRY).plan(route_manifest=ROUTE)
        selected_ids = [entry["id"] for entry in plan["selected"]]
        self.assertEqual(selected_ids, ["K7F3_RAG_DOCS", "K7F3_RAG_SUPPORT", "K7F3_AGENT_SUPPORT"])
        self.assertEqual(plan["policy"]["cross_tenant_access"], "DENY")
        self.assertFalse(plan["policy"]["can_answer_final"])

    def test_cross_tenant_resource_is_denied(self):
        plan = RAGRegistry(REGISTRY).plan(route_manifest=ROUTE, requested_ids=["ABCD_RAG_DOCS"])
        self.assertEqual(plan["selected"], [])
        self.assertEqual(plan["denied"][0]["decision"]["reason"], "blocked_cross_tenant_access")

    def test_neroflux_caps_rag_fanout(self):
        plan = RAGRegistry(REGISTRY).plan(
            route_manifest=ROUTE,
            requested_ids=["K7F3_RAG_DOCS", "K7F3_RAG_SUPPORT"],
            neroflux_signal={"client_sensitivity": 0.9},
        )
        selected_ids = [entry["id"] for entry in plan["selected"]]
        denied_reasons = [item["decision"]["reason"] for item in plan["denied"]]
        self.assertEqual(selected_ids, ["K7F3_RAG_DOCS"])
        self.assertIn("blocked_by_neroflux_fanout_cap", denied_reasons)

    def test_registry_rejects_final_answering_resource(self):
        bad_registry = {"entries": [{"id": "BAD_RAG", "type": "rag", "scope": "ORA_CORE", "can_answer_final": True}]}
        with self.assertRaises(RegistryError):
            RAGRegistry(bad_registry)


if __name__ == "__main__":
    unittest.main()
