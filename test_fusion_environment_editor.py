"""Focused tests for read-only Fusion PhotoBooth discovery."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import fusion_environment_editor as finder


PHOTOBOOTH_XML = b'<?xml version="1.0"?><PhotoBooth version="3.0"/>'


class FindOnlyTests(unittest.TestCase):
    def create_deployment(self, root: Path, channel: str, name: str) -> Path:
        deployment = root / channel / name
        (deployment / "FusionLauncher.exe").parent.mkdir(parents=True)
        (deployment / "FusionLauncher.exe").write_bytes(b"launcher")
        photo = (
            deployment
            / "Neutron"
            / "Server"
            / "Scene"
            / "Resources"
            / "Environments"
            / "PhotoBooth"
            / "PhotoBooth.xml"
        )
        photo.parent.mkdir(parents=True)
        photo.write_bytes(PHOTOBOOTH_XML)
        return deployment

    def test_finds_each_channel_and_active_process_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "webdeploy"
            active_deployment = self.create_deployment(root, "pre-production", "active")
            self.create_deployment(root, "production", "other")
            processes = (
                finder.ProcessInfo(
                    process_id=42,
                    name="Fusion360.exe",
                    executable_path=active_deployment / "Fusion360.exe",
                    file_version="2705.1.11",
                    product_version="2705.1.11",
                    product_name="Fusion360",
                ),
            )
            with patch.object(
                finder, "get_running_fusion_processes", return_value=(processes, None)
            ):
                result = finder.discover(root)

        self.assertEqual(len(result.installations), 2)
        self.assertEqual(len(result.candidates), 2)
        active = [
            candidate
            for candidate in result.candidates
            if candidate.classification == "active"
        ]
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0].fusion_process_ids, (42,))
        self.assertEqual(active[0].fusion_versions, ("2705.1.11",))
        self.assertIn("Windows version 2705.1.11", active[0].reason)
        self.assertTrue(active[0].xml_path.name == "PhotoBooth.xml")

    def test_excludes_inventor_lookalikes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "webdeploy"
            deployment = self.create_deployment(root, "production", "fusion")
            inventor = (
                deployment
                / "Inventor"
                / "Environments"
                / "PhotoBooth"
                / "PhotoBooth.xml"
            )
            inventor.parent.mkdir(parents=True)
            inventor.write_bytes(PHOTOBOOTH_XML)
            with patch.object(
                finder, "get_running_fusion_processes", return_value=((), None)
            ):
                result = finder.discover(root)

        self.assertEqual(len(result.candidates), 1)
        self.assertIn("not a Fusion", "\n".join(result.rejected_paths))

    def test_reports_unknown_instead_of_guessing_when_not_running(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "webdeploy"
            self.create_deployment(root, "production", "first")
            self.create_deployment(root, "pre-production", "second")
            with patch.object(
                finder, "get_running_fusion_processes", return_value=((), None)
            ):
                payload = finder.report_payload(finder.discover(root))

        self.assertEqual(payload["target_state"], "active-target-not-proven")
        self.assertEqual(len(payload["candidates"]), 2)
        self.assertTrue(payload["read_only"])

    def test_process_query_failure_is_not_closed_proof(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "webdeploy"
            self.create_deployment(root, "production", "one")
            with patch.object(
                finder,
                "get_running_fusion_processes",
                return_value=((), "CIM permission denied"),
            ):
                payload = finder.report_payload(finder.discover(root))

        self.assertEqual(
            payload["target_state"], "active-target-unknown-process-query-unavailable"
        )
        self.assertEqual(payload["process_query_error"], "CIM permission denied")

    def test_discovery_never_changes_candidate_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "webdeploy"
            deployment = self.create_deployment(root, "production", "one")
            photo = (
                deployment
                / "Neutron"
                / "Server"
                / "Scene"
                / "Resources"
                / "Environments"
                / "PhotoBooth"
                / "PhotoBooth.xml"
            )
            before = photo.read_bytes()
            with patch.object(
                finder, "get_running_fusion_processes", return_value=((), None)
            ):
                finder.discover(root)
            after = photo.read_bytes()

        self.assertEqual(after, before)

    def test_manual_fusion360_path_identifies_its_deployment_and_version(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "webdeploy"
            deployment = self.create_deployment(root, "pre-production", "active")
            fusion = deployment / "Fusion360.exe"
            fusion.write_bytes(b"fusion")
            with patch.object(
                finder,
                "read_windows_version_info",
                return_value=finder.WindowsVersionInfo(
                    file_version="2705.1.11",
                    product_version="2705.1.11",
                    product_name="Fusion360",
                ),
            ):
                result = finder.manually_identify_fusion(f'"{fusion}"', root)

        payload = finder.report_payload(result)
        self.assertEqual(payload["target_state"], "one-manually-identified-candidate")
        self.assertEqual(result.candidates[0].classification, "manual-active-build")
        self.assertEqual(result.candidates[0].fusion_versions, ("2705.1.11",))
        self.assertEqual(
            result.manual_fusion_executable.product_version,
            "2705.1.11",
        )

    def test_manual_path_requires_exact_fusion360_executable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "webdeploy"
            deployment = self.create_deployment(root, "production", "active")
            incorrect = deployment / "not-fusion.exe"
            incorrect.write_bytes(b"not fusion")
            with self.assertRaisesRegex(ValueError, "Fusion360.exe exactly"):
                finder.manually_identify_fusion(str(incorrect), root)


if __name__ == "__main__":
    unittest.main()
