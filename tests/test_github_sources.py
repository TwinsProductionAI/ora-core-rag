import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ora_core_rag.github_sources import sources_from_tree


class GitHubSourceDiscoveryTests(unittest.TestCase):
    def test_sources_from_tree_filters_supported_files(self):
        sources = sources_from_tree(
            repo="TwinsProductionAI/ora-core-rag",
            ref="main",
            tree_items=[
                {"path": "README.md", "type": "blob"},
                {"path": "src/ora_core_rag/index.py", "type": "blob"},
                {"path": "image.png", "type": "blob"},
                {"path": "docs", "type": "tree"},
            ],
            tags=["test"],
        )

        self.assertEqual(len(sources), 2)
        self.assertEqual(sources[0]["scope"], "ORA_CORE")
        self.assertIn("github", sources[0]["tags"])
        self.assertIn("TwinsProductionAI_ora-core-rag", sources[0]["tags"])
        self.assertTrue(sources[0]["uri"].startswith("https://raw.githubusercontent.com/"))


if __name__ == "__main__":
    unittest.main()
