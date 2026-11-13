#!/usr/bin/env python3
"""Mutation-sensitive source-only Docker CMD ordering/grammar checks."""
import json
import unittest
from unittest.mock import patch
import cloud_mgba_cmd_order_gate as gate


def docker(*stages, shell=("sh", "-c")):
    return 'FROM ubuntu:26.04\nCMD ' + json.dumps([*shell, " && ".join(stages)]) + '\n'


class DockerCommandGuardTests(unittest.TestCase):
    def test_exact_first_gate_and_eight_stage_order(self):
        self.assertEqual(gate.EXPECTED_STAGES[0],
                         "python3 /lab/tools/cloud_mgba_pkg_gate.py")
        self.assertEqual(len(gate.EXPECTED_STAGES), 8)
        self.assertEqual(gate.validate_dockerfile(docker(*gate.EXPECTED_STAGES)),
                         gate.EXPECTED_STAGES)

    def test_all_stages_must_be_exact_and_ordered(self):
        original = gate.EXPECTED_STAGES
        for altered in (
            original[1:2] + original[:1] + original[2:],
            original[1:],
            original + ("echo hidden extra stage",),
            original[:5] + original[6:],
            ("dpkg-query -W mgba-sdl | grep 0.10.5",) + original[1:],
            ("python3 /lab/tools/cloud_mgba_pkg_gate.py || true",) + original[1:],
            ("grep -F 0.10.5 /tmp/mgba_pkg_version.txt",) + original[1:],
            original[:6] + ("python3 /lab/tools/cloud_rsp_thumb_hit_fixture.py",) + original[7:],
        ):
            with self.subTest(stages=altered):
                with self.assertRaisesRegex(ValueError, "gate-first|forbidden"):
                    gate.validate_dockerfile(docker(*altered))

    def test_never_accept_shell_separators_or_redirection_pipes(self):
        for text in (
            docker(*gate.EXPECTED_STAGES).replace(" && mgba --version",
                                                  " ; mgba --version"),
            docker(*gate.EXPECTED_STAGES).replace(" && mgba --version",
                                                  " || mgba --version"),
            docker(*gate.EXPECTED_STAGES).replace(" && mgba --version",
                                                  " | mgba --version"),
            docker(*gate.EXPECTED_STAGES).replace(" && mgba --version",
                                                  " && mgba --version;"),
        ):
            with self.subTest(text=text):
                with self.assertRaisesRegex(ValueError, "forbidden"):
                    gate.validate_dockerfile(text)

    def test_cmd_count_and_shell_form_must_be_exact(self):
        good = docker(*gate.EXPECTED_STAGES)
        for bad in (
            good + good,
            good.replace("CMD ", "RUN ", 1),
            docker(*gate.EXPECTED_STAGES, shell=("bash", "-c")),
            "FROM ubuntu:26.04\nCMD python3 /lab/tools/cloud_mgba_pkg_gate.py\n",
            "FROM ubuntu:26.04\nCMD [bad json]\n",
        ):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    gate.validate_dockerfile(bad)


if __name__ == "__main__":
    unittest.main()
