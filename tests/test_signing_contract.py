"""Signing contract: only the independent Windows artifact is signed.

These checks keep workflow order, disclosure and distribution name consistent.
They do not replace cryptographic verification on a Windows runner.
"""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SigningWorkflowTests(unittest.TestCase):
    def test_authenticode_signing_after_frozen_smoke_and_before_zip(self):
        workflow = (ROOT / ".github/workflows/windows-x64.yml").read_text(encoding="utf-8")
        sign = workflow.index("- name: Authenticode-sign ClipMint executable")
        frozen = workflow.index("- name: Frozen executable smoke test")
        package = workflow.index("- name: Zip portable alpha")
        self.assertLess(frozen, sign)
        self.assertLess(sign, package)
        self.assertIn("./tools/sign-development.ps1", workflow)
        self.assertIn("ClipMint-Development-Signer.cer", workflow)
        self.assertNotIn("upload-pfx", workflow.lower())

    def test_github_attestation_follows_final_zip_and_is_main_only(self):
        workflow = (ROOT / ".github/workflows/windows-x64.yml").read_text(encoding="utf-8")
        self.assertIn("uses: actions/attest@v4", workflow)
        self.assertIn("if: github.event_name != 'pull_request'", workflow)
        self.assertIn("id-token: write", workflow)
        self.assertIn("attestations: write", workflow)
        self.assertIn("gh attestation verify", workflow)
        self.assertLess(workflow.index("- name: Zip portable alpha"), workflow.index("- name: GitHub Sigstore-signed build provenance"))

    def test_public_artifact_is_explicitly_untrusted_development_signed(self):
        workflow = (ROOT / ".github/workflows/windows-x64.yml").read_text(encoding="utf-8")
        notice = (ROOT / "DEVELOPMENT-SIGNING.md").read_text(encoding="utf-8")
        script = (ROOT / "tools/sign-development.ps1").read_text(encoding="utf-8")
        self.assertIn("Complete-Development-Signed-Alpha.zip", workflow)
        self.assertIn("Set-AuthenticodeSignature", script)
        self.assertIn("Get-AuthenticodeSignature", script)
        self.assertIn("KeyExportPolicy NonExportable", script)
        self.assertIn("Trusted Root", notice)
        self.assertIn("NOT issued by a trusted certificate authority", notice)


if __name__ == "__main__":
    unittest.main()
