import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ranking_agent import install_skill


class InstallSkillTests(unittest.TestCase):
    def test_installs_bundled_skill_into_target_project(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_path = Path(temporary_directory) / "project"
            original_argv = sys.argv
            try:
                sys.argv = [
                    "product-search-install-skill",
                    "--project",
                    str(project_path),
                ]
                install_skill.main()
            finally:
                sys.argv = original_argv

            skill_path = project_path / ".codex" / "skills" / "product-search-results"
            self.assertTrue((skill_path / "SKILL.md").is_file())
            self.assertTrue((skill_path / "agents" / "openai.yaml").is_file())
