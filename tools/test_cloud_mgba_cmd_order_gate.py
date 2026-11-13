#!/usr/bin/env python3
"""Mutation-sensitive source-only Docker CMD ordering/grammar checks."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import cloud_mgba_cmd_order_gate as gate


def docker(*stages, shell=("sh", "-c")):
    prefix = gate.EXPECTED_DOCKERFILE.rsplit("\nCMD ", 1)[0]
    command = json.dumps([*shell, " && ".join(stages)], separators=(",", ":"))
    return prefix + "\nCMD " + command + "\n"


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
                with self.assertRaisesRegex(ValueError, "Dockerfile mismatch at line"):
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
                with self.assertRaisesRegex(ValueError, "Dockerfile mismatch at line"):
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


    def test_reject_real_docker_effective_instruction_overrides(self):
        real = gate.EXPECTED_DOCKERFILE
        attacks = (
            real + 'cmd ["sh","-c","echo pwn"]\n',
            real + 'CMD ["sh","-c","echo pwn"]\n',
            real + 'ENTRYPOINT ["sh","-c","echo pwn"]\n',
            real + 'entrypoint ["sh","-c","echo pwn"]\n',
            real + ' CMD ["sh","-c","echo pwn"]\n',
            real + "FROM ubuntu:26.04\n",
            real + "HEALTHCHECK CMD true\n",
            real + "RUN apt-get install -y curl\n",
            real.replace("USER 65534:65534\n", "USER root\n"),
            real.replace("COPY tools /lab/tools\n", "COPY . /lab\n"),
            real + "# innocuous-looking Dockerfile comment\n",
            real + "\n",
            real.replace("CMD [", "cmd ["),
        )
        for attack in attacks:
            with self.subTest(variant=attack[-95:]):
                with self.assertRaisesRegex(ValueError,
                                            r"Dockerfile mismatch at line \d+"):
                    gate.validate_dockerfile(attack)

    def test_first_differing_line_is_reported(self):
        wrong_user = gate.EXPECTED_DOCKERFILE.replace(
            "USER 65534:65534\n", "USER root\n"
        )
        with self.assertRaisesRegex(ValueError, r"line 9\b"):
            gate.validate_dockerfile(wrong_user)
        with self.assertRaisesRegex(ValueError, r"line 11\b"):
            gate.validate_dockerfile(gate.EXPECTED_DOCKERFILE + "RUN whoami\n")

    def test_real_repository_dockerfile_and_workflow_placement(self):
        # Hosted runner executes this against the working tree BEFORE docker
        # build. The image only carries /lab/tools, so skip there; the actual
        # copied Dockerfile is still validated pre-build by the workflow.
        root = Path(__file__).resolve().parents[1]
        source = root / "docker" / "cloud-mgba-netns.Dockerfile"
        workflow = root / ".github" / "workflows" / "cloud-mgba-netns-fixture.yml"
        if not source.is_file() or not workflow.is_file():
            self.skipTest("repository Dockerfile/workflow checked by host prebuild")
        self.assertEqual(gate.validate_dockerfile(source.read_text(encoding="utf-8")),
                         gate.EXPECTED_STAGES)
        script = workflow.read_text(encoding="utf-8")
        copy = "cp docker/cloud-mgba-netns.Dockerfile /tmp/sg-netns-build/Dockerfile"
        check = "python3 tools/cloud_mgba_cmd_order_gate.py /tmp/sg-netns-build/Dockerfile"
        build = "docker build -t soulgold-public-netns:lab /tmp/sg-netns-build"
        host_tests = "python3 -m unittest discover -s tools -p test_cloud_mgba_cmd_order_gate.py -v"
        self.assertEqual(script.count(check), 1)
        self.assertEqual(script.count(build), 1)
        self.assertTrue(0 <= script.index(host_tests) < script.index(copy) <
                        script.index(check) < script.index(build))
        build_region = script[script.rfind("      - name: Build isolated"):
                              script.index("      - name: Verify Docker network=none")]
        self.assertIn("          set -eu\n", build_region)

    def test_main_rejects_wrong_argv_and_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "Dockerfile"
            path.write_text(gate.EXPECTED_DOCKERFILE, encoding="utf-8")
            link = root / "Dockerfile-symlink"
            link.symlink_to(path)
            with patch.object(gate.sys, "argv", ["gate"]), \
                 self.assertRaisesRegex(ValueError, "exactly one"):
                gate.main()
            with patch.object(gate.sys, "argv", ["gate", str(path), "extra"]), \
                 self.assertRaisesRegex(ValueError, "exactly one"):
                gate.main()
            with patch.object(gate.sys, "argv", ["gate", str(link)]), \
                 self.assertRaisesRegex(ValueError, "nonsymlink"):
                gate.main()
            with patch.object(gate.sys, "argv", ["gate", str(path)]), \
                 patch("builtins.print") as printed:
                gate.main()
            self.assertIn("stages=8", printed.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
