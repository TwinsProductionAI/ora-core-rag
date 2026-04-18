import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ora_core_rag.route_gate import ClientRouteGate, RouteGateError


class ClientRouteGateTests(unittest.TestCase):
    def setUp(self):
        self.gate = ClientRouteGate()
        self.route = {
            "route_id": "GLK[TENANT:K7F3:PROD:v1]",
            "tenant_id": "K7F3",
            "environment": "prod",
            "isolation": "strict",
            "allowed_rags": ["K7F3_RAG_DOCS"],
            "allowed_agents": ["K7F3_AGENT_SUPPORT"],
        }

    def test_validates_glk_route(self):
        validated = self.gate.validate_manifest(self.route)
        self.assertEqual(validated["tenant_id"], "K7F3")
        self.assertIn("manifest_hash", validated)

    def test_requires_route_for_client_access(self):
        with self.assertRaises(RouteGateError):
            self.gate.authorize(None, resource_type="rag", resource_id="K7F3_RAG_DOCS")

    def test_allows_authorized_tenant_rag(self):
        decision = self.gate.authorize(self.route, resource_type="rag", resource_id="K7F3_RAG_DOCS")
        self.assertTrue(decision["allowed"])
        self.assertEqual(decision["reason"], "allowed")

    def test_denies_cross_tenant_rag(self):
        decision = self.gate.authorize(self.route, resource_type="rag", resource_id="ABCD_RAG_DOCS")
        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["reason"], "blocked_cross_tenant_access")

    def test_denies_unlisted_agent(self):
        decision = self.gate.authorize(self.route, resource_type="agent", resource_id="K7F3_AGENT_BILLING")
        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["reason"], "resource_not_allowed_for_route")


if __name__ == "__main__":
    unittest.main()
