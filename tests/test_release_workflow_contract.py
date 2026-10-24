"""Static guardrails for the CI/release contract.

These tests are intentionally dependency-free: they stop accidental edits from
reintroducing unconditional releases or removing the compile/package gates.
GitHub Actions itself still validates and executes the YAML workflows.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"


def _read_workflow(name: str) -> str:
    return (WORKFLOWS / name).read_text(encoding="utf-8")


def test_versioned_release_waits_for_test_firmware_and_windows_jobs():
    workflow = _read_workflow("create-release.yml")

    assert 'tags:' in workflow and '"v*"' in workflow
    assert "uses: ./.github/workflows/tests.yml" in workflow
    assert "uses: ./.github/workflows/firmware-build.yml" in workflow
    assert "uses: ./.github/workflows/windows-package.yml" in workflow
    assert "needs:" in workflow
    assert "- tests" in workflow
    assert "- firmware" in workflow
    assert "- windows-package" in workflow
    assert "gh release create" in workflow
    assert "v2.6.0" not in workflow


def test_release_workflow_uploads_windows_firmware_and_checksums():
    workflow = _read_workflow("create-release.yml")

    assert "actions/download-artifact@v4" in workflow
    assert "DSIS-v3-windows-" in workflow
    assert "DSIS-firmware-" in workflow
    assert "release-assets/windows/DSIS-v3-windows.zip" in workflow
    assert "release-assets/firmware/*.bin" in workflow
    assert "release-assets/SHA256SUMS.txt" in workflow
    assert "sha256sum" in workflow


def test_reusable_build_workflows_produce_release_artifacts():
    firmware = _read_workflow("firmware-build.yml")
    windows = _read_workflow("windows-package.yml")

    assert "workflow_call: {}" in firmware
    assert "--output-dir build/firmware" in firmware
    assert "DSIS-firmware-" in firmware
    assert "actions/upload-artifact@v4" in firmware
    assert "workflow_call: {}" in windows
    assert "Compress-Archive" in windows
    assert "DSIS-v3-windows-" in windows
    assert "actions/upload-artifact@v4" in windows
