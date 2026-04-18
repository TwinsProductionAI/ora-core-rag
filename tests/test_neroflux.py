import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ora_core_rag.neroflux import NerofluxFanoutRegulator


class NerofluxFanoutTests(unittest.TestCase):
    def test_balanced_signal_allows_three_rags(self):
        result = NerofluxFanoutRegulator().regulate({"retrieval_pressure": 0.2, "agent_count": 1})
        self.assertEqual(result["pace"], "balanced")
        self.assertEqual(result["max_rag_fanout"], 3)
        self.assertIn("maintain_balanced_circulation", result["actions"])

    def test_sensitive_signal_caps_fanout_and_requires_checks(self):
        result = NerofluxFanoutRegulator().regulate({
            "client_sensitivity": 0.9,
            "permission_risk": 0.72,
            "injection_risk": 0.61,
            "agent_count": 4,
        })
        self.assertEqual(result["pace"], "slow")
        self.assertEqual(result["max_rag_fanout"], 1)
        self.assertEqual(result["top_k_per_rag"], 3)
        self.assertTrue(result["require_hnerons"])
        self.assertIn("require_access_check", result["actions"])
        self.assertIn("require_prompt_injection_scan", result["actions"])

    def test_conflict_requires_hnerons_and_review_when_high(self):
        result = NerofluxFanoutRegulator().regulate({"source_conflict": 0.85})
        self.assertTrue(result["require_hnerons"])
        self.assertTrue(result["require_human_review"])
        self.assertIn("route_to_human_review", result["actions"])


if __name__ == "__main__":
    unittest.main()
