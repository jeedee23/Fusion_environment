#!/usr/bin/env python3
"""Read-only discovery of the active Autodesk Fusion PhotoBooth.xml.

This is intentionally the first, find-only stage of the project.  It:

* finds FusionLauncher.exe for every deployment in the local webdeploy store;
* maps a running Fusion application process (including Fusion360.exe) to a
  deployment when its executable path is available, and reads its Windows
  version properties; and
* reports every eligible PhotoBooth.xml candidate without changing any file.

It does not edit XML, create backups, install anything, or start/stop Fusion.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence


REPORT_SCHEMA_VERSION = 1
FUSION_APPLICATION_PROCESS_NAMES = frozenset({"fusion.exe", "fusion360.exe"})
FUSION_PROCESS_NAMES = FUSION_APPLICATION_PROCESS_NAMES | {"fusionlauncher.exe"}


@dataclass(frozen=True)
class ProcessInfo:
    """Read-only information about a relevant Windows process."""

    process_id: int
    name: str
    executable_path: Optional[Path]
    file_version: Optional[str] = None
    product_version: Optional[str] = None
    product_name: Optional[str] = None
    version_error: Optional[str] = None


@dataclass(frozen=True)
class WindowsVersionInfo:
    """Version metadata read from a Windows executable's file properties."""

    file_version: Optional[str]
    product_version: Optional[str]
    product_name: Optional[str]
    version_error: Optional[str] = None


@dataclass(frozen=True)
class FusionInstallation:
    """One Fusion deployment identified by its FusionLauncher.exe."""

    channel: str
    deployment_root: Path
    launcher_path: Path


@dataclass(frozen=True)
class PhotoBoothCandidate:
    """One non-Inventor PhotoBooth.xml resource under a Fusion deployment."""

    channel: str
    deployment_root: Path
    launcher_path: Path
    xml_path: Path
    classification: str
    reason: str
    fusion_process_ids: tuple[int, ...]
    launcher_process_ids: tuple[int, ...]
    fusion_versions: tuple[str, ...]
    sha256: str


@dataclass(frozen=True)
class DiscoveryResult:
    """Complete, read-only discovery evidence."""

    installations: tuple[FusionInstallation, ...]
    candidates: tuple[PhotoBoothCandidate, ...]
    processes: tuple[ProcessInfo, ...]
    process_query_error: Optional[str]
    rejected_paths: tuple[str, ...]
    manual_fusion_executable: Optional[ProcessInfo] = None


def utc_now() -> str:
    """Return an unambiguous report timestamp."""

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def local_app_data() -> Path:
    """Return LocalAppData without hard-coding the current Windows account."""

    configured = os.environ.get("LOCALAPPDATA")
    if configured:
        return Path(configured)
    return Path.home() / "AppData" / "Local"


def webdeploy_root() -> Path:
    """Return the bounded Autodesk Fusion deployment root to inspect."""

    return local_app_data() / "Autodesk" / "webdeploy"


def is_windows() -> bool:
    """Return whether the current runtime is Windows."""

    return platform.system().casefold() == "windows"


def sha256_file(path: Path) -> str:
    """Hash a candidate so a future report can establish whether it changed."""

    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def is_path_within(path: Path, container: Path) -> bool:
    """Return whether a canonical path stays inside a canonical container."""

    try:
        path.resolve(strict=False).relative_to(container.resolve(strict=False))
    except ValueError:
        return False
    return True


def is_inventor_path(path: Path) -> bool:
    """Exclude Inventor and Inventor Interoperability lookalikes."""

    return any("inventor" in part.casefold() for part in path.parts)


def is_photobooth_resource(path: Path) -> bool:
    """Recognise the Fusion Environments\\PhotoBooth resource location."""

    if path.name.casefold() != "photobooth.xml" or is_inventor_path(path):
        return False
    parts = [part.casefold() for part in path.parts]
    return any(
        parts[index : index + 2] == ["environments", "photobooth"]
        for index in range(max(0, len(parts) - 1))
    )


def read_windows_version_info(path: Path) -> WindowsVersionInfo:
    """Read Windows file properties for one validated executable path."""

    if not is_windows():
        raise ValueError("Windows executable version properties are unavailable on this system.")
    escaped_path = str(path).replace("'", "''")
    command = (
        "$ErrorActionPreference='Stop'; "
        f"$version = (Get-Item -LiteralPath '{escaped_path}' -ErrorAction Stop).VersionInfo; "
        "[PSCustomObject]@{ "
        "FileVersion = $version.FileVersion; "
        "ProductVersion = $version.ProductVersion; "
        "ProductName = $version.ProductName "
        "} | ConvertTo-Json -Compress"
    )
    try:
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
            check=True,
            capture_output=True,
            text=True,
            timeout=8,
        )
        record = json.loads(completed.stdout)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read Windows version properties: {exc}") from exc
    if not isinstance(record, dict):
        raise ValueError("Windows returned invalid executable version properties.")
    return WindowsVersionInfo(
        file_version=record.get("FileVersion")
        if isinstance(record.get("FileVersion"), str)
        else None,
        product_version=record.get("ProductVersion")
        if isinstance(record.get("ProductVersion"), str)
        else None,
        product_name=record.get("ProductName")
        if isinstance(record.get("ProductName"), str)
        else None,
    )


def get_running_fusion_processes() -> tuple[tuple[ProcessInfo, ...], Optional[str]]:
    """Read relevant process paths through PowerShell without modifying processes.

    Permission restrictions and unavailable CIM services are reported as unknown
    process state, never as evidence that Fusion is closed.
    """

    if not is_windows():
        return (), "Windows process discovery is unavailable on this operating system."
    command = (
        "$ErrorActionPreference='Stop'; "
        "Get-CimInstance Win32_Process | "
        "Where-Object { $_.Name -in @('Fusion.exe','Fusion360.exe','FusionLauncher.exe') } | "
        "ForEach-Object { "
        "$version = $null; $versionError = $null; "
        "if ($_.ExecutablePath) { "
        "try { $version = (Get-Item -LiteralPath $_.ExecutablePath -ErrorAction Stop).VersionInfo } "
        "catch { $versionError = $_.Exception.Message } "
        "} "
        "[PSCustomObject]@{ "
        "ProcessId = $_.ProcessId; Name = $_.Name; ExecutablePath = $_.ExecutablePath; "
        "FileVersion = if ($version) { $version.FileVersion } else { $null }; "
        "ProductVersion = if ($version) { $version.ProductVersion } else { $null }; "
        "ProductName = if ($version) { $version.ProductName } else { $null }; "
        "VersionError = $versionError "
        "} "
        "} | ConvertTo-Json -Compress"
    )
    try:
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
            check=True,
            capture_output=True,
            text=True,
            timeout=8,
        )
        output = completed.stdout.strip()
        if not output:
            return (), None
        raw_records = json.loads(output)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        return (), f"Could not query Fusion processes: {exc}"

    records = raw_records if isinstance(raw_records, list) else [raw_records]
    processes: list[ProcessInfo] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        name = record.get("Name")
        if not isinstance(name, str) or name.casefold() not in FUSION_PROCESS_NAMES:
            continue
        try:
            process_id = int(record.get("ProcessId"))
        except (TypeError, ValueError):
            continue
        executable = record.get("ExecutablePath")
        executable_path = Path(executable) if isinstance(executable, str) and executable else None
        processes.append(
            ProcessInfo(
                process_id=process_id,
                name=name,
                executable_path=executable_path,
                file_version=record.get("FileVersion")
                if isinstance(record.get("FileVersion"), str)
                else None,
                product_version=record.get("ProductVersion")
                if isinstance(record.get("ProductVersion"), str)
                else None,
                product_name=record.get("ProductName")
                if isinstance(record.get("ProductName"), str)
                else None,
                version_error=record.get("VersionError")
                if isinstance(record.get("VersionError"), str)
                else None,
            )
        )
    return tuple(processes), None


def find_fusion_installations(root: Optional[Path] = None) -> tuple[FusionInstallation, ...]:
    """Find FusionLauncher.exe across production and pre-production deployments.

    The search is bounded to Autodesk's local webdeploy directory.  It does not
    recursively scan drives or infer a version from directory timestamps.
    """

    root = root if root is not None else webdeploy_root()
    installations: dict[Path, FusionInstallation] = {}
    for channel in ("production", "pre-production"):
        channel_root = root / channel
        if not channel_root.is_dir():
            continue
        try:
            launchers = channel_root.rglob("FusionLauncher.exe")
            for launcher in launchers:
                if not launcher.is_file() or is_inventor_path(launcher):
                    continue
                relative = launcher.relative_to(channel_root)
                if not relative.parts:
                    continue
                deployment_root = (channel_root / relative.parts[0]).resolve(strict=False)
                existing = installations.get(deployment_root)
                resolved_launcher = launcher.resolve(strict=False)
                if existing is None or len(resolved_launcher.parts) < len(existing.launcher_path.parts):
                    installations[deployment_root] = FusionInstallation(
                        channel=channel,
                        deployment_root=deployment_root,
                        launcher_path=resolved_launcher,
                    )
        except OSError:
            continue
    return tuple(
        sorted(
            installations.values(),
            key=lambda installation: (installation.channel, str(installation.deployment_root)),
        )
    )


def process_ids_for_installation(
    installation: FusionInstallation, processes: Iterable[ProcessInfo]
) -> tuple[tuple[int, ...], tuple[int, ...], tuple[str, ...]]:
    """Associate known executable paths with exactly one deployment root."""

    fusion: list[int] = []
    launcher: list[int] = []
    versions: list[str] = []
    for process in processes:
        if process.executable_path is None:
            continue
        if not is_path_within(process.executable_path, installation.deployment_root):
            continue
        if process.name.casefold() in FUSION_APPLICATION_PROCESS_NAMES:
            fusion.append(process.process_id)
            version = process.product_version or process.file_version
            if version:
                versions.append(version)
        elif process.name.casefold() == "fusionlauncher.exe":
            launcher.append(process.process_id)
    return tuple(sorted(fusion)), tuple(sorted(launcher)), tuple(sorted(set(versions)))


def candidate_classification(
    fusion_process_ids: tuple[int, ...],
    launcher_process_ids: tuple[int, ...],
    fusion_versions: tuple[str, ...],
) -> tuple[str, str]:
    """Classify target confidence without treating a filename as proof of activity."""

    if fusion_process_ids:
        version_description = (
            f" Windows version {', '.join(fusion_versions)}."
            if fusion_versions
            else " Windows version could not be read."
        )
        return (
            "active",
            "The deployment contains a running Fusion application process "
            f"(PID {', '.join(str(process_id) for process_id in fusion_process_ids)})."
            + version_description,
        )
    if launcher_process_ids:
        return (
            "launcher-running",
            "FusionLauncher.exe is running here, but no Fusion.exe process was proven.",
        )
    return (
        "not-proven-active",
        "No running Fusion.exe process with an executable path was tied to this deployment.",
    )


def find_photobooth_candidates(
    installations: Iterable[FusionInstallation], processes: Iterable[ProcessInfo]
) -> tuple[tuple[PhotoBoothCandidate, ...], tuple[str, ...]]:
    """Find eligible PhotoBooth XML resources and retain rejected-path evidence."""

    candidates: list[PhotoBoothCandidate] = []
    rejected: list[str] = []
    seen: set[Path] = set()
    process_records = tuple(processes)
    for installation in installations:
        fusion_ids, launcher_ids, fusion_versions = process_ids_for_installation(
            installation, process_records
        )
        classification, reason = candidate_classification(
            fusion_ids, launcher_ids, fusion_versions
        )
        try:
            paths = installation.deployment_root.rglob("PhotoBooth.xml")
        except OSError as exc:
            rejected.append(
                f"{installation.deployment_root}: cannot search for PhotoBooth.xml ({exc})"
            )
            continue
        try:
            for path in paths:
                try:
                    resolved = path.resolve(strict=True)
                except OSError as exc:
                    rejected.append(f"{path}: cannot resolve candidate ({exc})")
                    continue
                if resolved in seen:
                    continue
                if not is_path_within(resolved, installation.deployment_root):
                    rejected.append(
                        f"{path}: skipped because canonical path escapes the deployment root"
                    )
                    continue
                if not is_photobooth_resource(resolved):
                    rejected.append(
                        f"{resolved}: skipped because it is not a Fusion Environments\\PhotoBooth resource"
                    )
                    continue
                try:
                    digest = sha256_file(resolved)
                except OSError as exc:
                    rejected.append(f"{resolved}: cannot hash candidate ({exc})")
                    continue
                seen.add(resolved)
                candidates.append(
                    PhotoBoothCandidate(
                        channel=installation.channel,
                        deployment_root=installation.deployment_root,
                        launcher_path=installation.launcher_path,
                        xml_path=resolved,
                        classification=classification,
                        reason=reason,
                        fusion_process_ids=fusion_ids,
                        launcher_process_ids=launcher_ids,
                        fusion_versions=fusion_versions,
                        sha256=digest,
                    )
                )
        except OSError as exc:
            rejected.append(
                f"{installation.deployment_root}: search interrupted ({exc})"
            )
    candidates.sort(
        key=lambda candidate: (
            candidate.classification != "active",
            candidate.classification != "launcher-running",
            candidate.channel,
            str(candidate.xml_path),
        )
    )
    return tuple(candidates), tuple(rejected)


def discover(root: Optional[Path] = None) -> DiscoveryResult:
    """Run the complete read-only discovery operation."""

    installations = find_fusion_installations(root)
    processes, process_query_error = get_running_fusion_processes()
    candidates, rejected_paths = find_photobooth_candidates(installations, processes)
    return DiscoveryResult(
        installations=installations,
        candidates=candidates,
        processes=processes,
        process_query_error=process_query_error,
        rejected_paths=rejected_paths,
    )


def manually_identify_fusion(
    pasted_path: str, root: Optional[Path] = None
) -> DiscoveryResult:
    """Identify a Fusion deployment from an exact user-pasted Fusion360.exe path."""

    cleaned = pasted_path.strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] == '"':
        cleaned = cleaned[1:-1]
    if not cleaned:
        raise ValueError("Paste the full path to Fusion360.exe.")

    executable = Path(cleaned).expanduser()
    if executable.name.casefold() != "fusion360.exe":
        raise ValueError("The pasted path must name Fusion360.exe exactly.")
    try:
        executable = executable.resolve(strict=True)
    except OSError as exc:
        raise ValueError(f"The pasted Fusion360.exe path does not exist: {exc}") from exc
    if not executable.is_file():
        raise ValueError("The pasted Fusion360.exe path is not a file.")

    deployment_store = (root if root is not None else webdeploy_root()).resolve(
        strict=False
    )
    try:
        relative = executable.relative_to(deployment_store)
    except ValueError as exc:
        raise ValueError(
            "Fusion360.exe is outside the bounded Autodesk webdeploy deployment store."
        ) from exc
    if len(relative.parts) != 3 or relative.parts[0].casefold() not in {
        "production",
        "pre-production",
    }:
        raise ValueError(
            "Fusion360.exe must be directly inside a production or pre-production "
            "webdeploy deployment directory."
        )

    channel = relative.parts[0]
    deployment_root = deployment_store / relative.parts[0] / relative.parts[1]
    expected_path = deployment_root / "Fusion360.exe"
    if executable != expected_path.resolve(strict=False):
        raise ValueError(
            "Fusion360.exe is not in the expected root of its deployment directory."
        )
    version = read_windows_version_info(executable)
    manual_process = ProcessInfo(
        process_id=0,
        name="Fusion360.exe",
        executable_path=executable,
        file_version=version.file_version,
        product_version=version.product_version,
        product_name=version.product_name,
        version_error=version.version_error,
    )
    launcher = deployment_root / "FusionLauncher.exe"
    installation = FusionInstallation(
        channel=channel,
        deployment_root=deployment_root,
        launcher_path=launcher,
    )
    candidates, rejected_paths = find_photobooth_candidates((installation,), ())
    primary_version = version.product_version or version.file_version
    version_description = (
        f" Product Version {version.product_version}; File Version {version.file_version}."
        if version.product_version
        and version.file_version
        and version.product_version != version.file_version
        else f" Version {primary_version}."
        if primary_version
        else " Windows version properties did not provide a version."
    )
    manual_candidates = tuple(
        replace(
            candidate,
            classification="manual-active-build",
            reason=(
                "The user supplied the direct Fusion360.exe path for this deployment."
                + version_description
            ),
            fusion_versions=(primary_version,) if primary_version else (),
        )
        for candidate in candidates
    )
    return DiscoveryResult(
        installations=(installation,),
        candidates=manual_candidates,
        processes=(),
        process_query_error=None,
        rejected_paths=rejected_paths,
        manual_fusion_executable=manual_process,
    )


def prompt_for_manual_fusion_discovery(
    root: Optional[Path] = None,
) -> tuple[Optional[DiscoveryResult], Optional[str]]:
    """Ask for a user-verified Fusion360.exe path only when needed."""

    try:
        import tkinter as tk
        from tkinter import messagebox, simpledialog
    except ImportError:
        return None, "Tk is unavailable, so the Task Manager fallback cannot be shown."
    try:
        dialog = tk.Tk()
        dialog.withdraw()
        dialog.attributes("-topmost", True)
        wants_to_locate = messagebox.askyesno(
            "Active Fusion 360 not identified",
            (
                "I don't have an active Fusion 360 identified. Do you want to locate "
                "it through Task Manager?"
            ),
            parent=dialog,
        )
        if not wants_to_locate:
            return None, None
        while True:
            pasted_path = simpledialog.askstring(
                "Paste Fusion360.exe path",
                (
                    "In Task Manager, find Fusion360.exe, open Details, choose Open "
                    "file location, copy the full Fusion360.exe path, and paste it here:"
                ),
                parent=dialog,
            )
            if pasted_path is None:
                return None, None
            try:
                return manually_identify_fusion(pasted_path, root), None
            except ValueError as exc:
                retry = messagebox.askretrycancel(
                    "Cannot identify Fusion 360",
                    f"{exc}\n\nRetry with another Fusion360.exe path?",
                    parent=dialog,
                )
                if not retry:
                    return None, None
    except tk.TclError as exc:
        return None, f"The Task Manager fallback could not open its dialog: {exc}"
    finally:
        try:
            dialog.destroy()
        except (UnboundLocalError, tk.TclError):
            pass


def serialise_path(value: Any) -> Any:
    """Convert dataclass dictionaries containing paths into JSON primitives."""

    if isinstance(value, Path):
        return str(value)
    if isinstance(value, tuple):
        return [serialise_path(item) for item in value]
    if isinstance(value, list):
        return [serialise_path(item) for item in value]
    if isinstance(value, dict):
        return {key: serialise_path(item) for key, item in value.items()}
    return value


def report_payload(result: DiscoveryResult) -> dict[str, Any]:
    """Produce a stable diagnostic report without exposing a guessed target."""

    active = [
        candidate for candidate in result.candidates if candidate.classification == "active"
    ]
    manual = [
        candidate
        for candidate in result.candidates
        if candidate.classification == "manual-active-build"
    ]
    if len(active) == 1:
        target_state = "one-active-candidate"
    elif len(active) > 1:
        target_state = "multiple-active-candidates"
    elif len(manual) == 1:
        target_state = "one-manually-identified-candidate"
    elif len(manual) > 1:
        target_state = "manual-build-has-multiple-photobooth-candidates"
    elif result.process_query_error:
        target_state = "active-target-unknown-process-query-unavailable"
    else:
        target_state = "active-target-not-proven"
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at": utc_now(),
        "read_only": True,
        "target_state": target_state,
        "installations": [serialise_path(asdict(item)) for item in result.installations],
        "processes": [serialise_path(asdict(item)) for item in result.processes],
        "process_query_error": result.process_query_error,
        "manual_fusion_executable": (
            serialise_path(asdict(result.manual_fusion_executable))
            if result.manual_fusion_executable
            else None
        ),
        "candidates": [serialise_path(asdict(item)) for item in result.candidates],
        "rejected_paths": list(result.rejected_paths),
    }


def format_human_report(payload: dict[str, Any]) -> str:
    """Format the same evidence for direct PowerShell use."""

    lines = [
        "Fusion PhotoBooth discovery (read only)",
        f"Target state: {payload['target_state']}",
        f"Installations: {len(payload['installations'])}",
        f"Eligible PhotoBooth candidates: {len(payload['candidates'])}",
    ]
    if payload["process_query_error"]:
        lines.append(f"Process state: {payload['process_query_error']}")
    manual = payload["manual_fusion_executable"]
    if manual:
        primary_version = manual["product_version"] or manual["file_version"] or "unavailable"
        lines.append(
            f"Manually identified Fusion360.exe: {manual['executable_path']} "
            f"(Product Version: {primary_version})"
        )
        if (
            manual["product_version"]
            and manual["file_version"]
            and manual["product_version"] != manual["file_version"]
        ):
            lines.append(f"File Version: {manual['file_version']}")
    for index, candidate in enumerate(payload["candidates"], start=1):
        lines.extend(
            (
                "",
                f"{index}. {candidate['classification']}: {candidate['xml_path']}",
                f"   Channel: {candidate['channel']}",
                f"   Reason: {candidate['reason']}",
                f"   SHA-256: {candidate['sha256']}",
            )
        )
    if not payload["candidates"]:
        lines.append(
            "No eligible candidate was found. No file was selected or changed."
        )
    if payload["rejected_paths"]:
        lines.append(f"Rejected paths: {len(payload['rejected_paths'])}")
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run discovery and print either an auditable JSON or a concise text report."""

    parser = argparse.ArgumentParser(
        description="Read-only discovery of the active Fusion PhotoBooth.xml."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print the complete report as JSON instead of a human-readable summary",
    )
    parser.add_argument(
        "--webdeploy-root",
        type=Path,
        help=(
            "inspect this webdeploy root instead of "
            "%%LOCALAPPDATA%%\\Autodesk\\webdeploy; still read-only"
        ),
    )
    arguments = parser.parse_args(argv)
    result = discover(arguments.webdeploy_root)
    payload = report_payload(result)
    if (
        not arguments.json
        and payload["target_state"] != "one-active-candidate"
    ):
        manual_result, prompt_error = prompt_for_manual_fusion_discovery(
            arguments.webdeploy_root
        )
        if manual_result is not None:
            result = manual_result
            payload = report_payload(result)
        elif prompt_error:
            payload["manual_prompt_error"] = prompt_error
    if arguments.json:
        print(json.dumps(payload, indent=2))
    else:
        print(format_human_report(payload))
        if payload.get("manual_prompt_error"):
            print(f"Task Manager fallback: {payload['manual_prompt_error']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
