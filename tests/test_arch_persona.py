import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ora_core_rag.arch_persona import ArchPersonaError, build_arch_persona_activation


ROUTE = {
    "route_id": "GLK[TENANT:K7F3:PROD:v1]",
    "tenant_id": "K7F3",
    "environment": "prod",
    "isolation": "strict",
    "allowed_rags": ["K7F3_RAG_DOCS"],
    "allowed_agents": ["K7F3_AGENT_SUPPORT"],
}


class ArchPersonaActivationTests(unittest.TestCase):
    def test_prefill_creates_all_foundation_groups(self):
        packet = build_arch_persona_activation({}, route_manifest=ROUTE)
        self.assertEqual(packet["arch_plus"]["code_pos"], "M10")
        self.assertEqual(packet["arch_plus"]["variant_id"], "M10_ARCH_PLUS_V3")
        self.assertEqual(
            set(packet["profile"]),
            {"context_identity", "goal_why", "tone_emo", "limits_risk", "personae_start", "arc_plus_plus"},
        )
        self.assertEqual(packet["status"], "READY_WITH_UNSURE")
        self.assertGreater(packet["source_summary"]["INCERTAIN"], 0)

    def test_user_answers_are_marked_user_provided(self):
        packet = build_arch_persona_activation(
            {
                "context_identity": {"role": "Founder", "identity": "ORA Core", "cognitive_posture": "systems"},
                "personae_start": {"personae": ["Architecte", "Juge"]},
                "arc_plus_plus": {"arcs": ["RAG", "Governance"]},
            },
            route_manifest=ROUTE,
        )
        self.assertEqual(packet["profile"]["context_identity"]["role"]["source"], "USER_PROVIDED")
        self.assertEqual(packet["profile"]["personae_start"]["personae"]["value"], ["Architecte", "Juge"])
        self.assertEqual(packet["profile"]["arc_plus_plus"]["arcs"]["value"], ["RAG", "Governance"])

    def test_rejects_more_than_four_personae(self):
        with self.assertRaises(ArchPersonaError):
            build_arch_persona_activation(
                {"personae_start": {"personae": ["A", "B", "C", "D", "E"]}},
                route_manifest=ROUTE,
            )

    def test_rejects_more_than_four_arcs(self):
        with self.assertRaises(ArchPersonaError):
            build_arch_persona_activation(
                {"arc_plus_plus": {"arcs": ["A", "B", "C", "D", "E"]}},
                route_manifest=ROUTE,
            )

    def test_policy_keeps_client_payload_out_of_core(self):
        packet = build_arch_persona_activation({}, route_manifest=ROUTE)
        self.assertEqual(packet["policy"]["write_client_payload_to_core"], "DENY")
        self.assertTrue(packet["policy"]["tenant_scoped_profile_store_required"])
        self.assertFalse(packet["policy"]["can_answer_final"])


if __name__ == "__main__":
    unittest.main()
