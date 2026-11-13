# ClipMint Windows — development signing and GitHub build provenance

The GitHub Actions Windows x64 alpha pipeline creates two DIFFERENT forms of
integrity evidence. These do not establish a publicly verified publisher.

## 1. Windows Authenticode signature — UNTRUSTED development certificate

The pipeline uses Windows `New-SelfSignedCertificate -Type CodeSigningCert`
to generate a **new, ephemeral, non-exportable RSA 3072-bit signing key**
for each build. It signs **only ClipMint-Windows.exe** using SHA-256
Authenticode through `Set-AuthenticodeSignature`.

For verification, the Windows CI runner temporarily trusts its OWN certificate,
checks the executable signature, then removes that temporary trust and the
signing key. No private keys, PFX or passwords are placed in the repository,
GitHub artifact, or build log. The ZIP contains the **public**
`ClipMint-Development-Signer.cer` and `DEVELOPMENT-SIGNATURE.txt`.

**CRITICAL: This certificate is NOT issued by a trusted certificate authority.**
It cannot make Windows automatically recognise the ClipMint publisher,
prevent Microsoft Defender/SmartScreen warnings, establish software
reputation, or vouch for safe program behaviour. Do **not** import it into
Trusted Root on your personal computer to bypass warnings. The certificate
changes on every CI build, so its thumbprint is build-specific.

You can inspect the executable on Windows without trusting the certificate:

```powershell
Get-AuthenticodeSignature .\ClipMint-Windows.exe |
    Format-List Status,StatusMessage,SignerCertificate
```

Compare the public certificate thumbprint inside the archive:

```powershell
$cert = [System.Security.Cryptography.X509Certificates.X509Certificate2]::new(
    (Resolve-Path .\ClipMint-Development-Signer.cer).Path)
$cert.Thumbprint
```

The signature's `SignerCertificate.Thumbprint` must match.
Because the certificate is untrusted, Windows may report `NotTrusted`,
`UnknownError` or `Unknown Publisher`; that does not establish trust.
A mismatch or `HashMismatch` indicates the binary should not be used.

## 2. GitHub artifact attestation — signed provenance for the complete ZIP

On `main` builds, `actions/attest@v4` uses GitHub's OIDC token and Sigstore
to cryptographically attest the final portable ZIP's SHA-256, repository,
workflow and build identity. GitHub CLI can verify it:

```powershell
gh attestation verify .\ClipMint-Windows-x64-Complete-Development-Signed-Alpha.zip -R cryogenized-spec/clipmint-windows
```

The artifact attestation is tied to the exact ZIP bytes. If you repack or
rename files inside it, the attestation won't verify the changed content.
GitHub attestation provides **build provenance**, not Microsoft-trusted
Authenticode publisher verification or an independent security audit.

## Packaging policy

The single download is a ZIP containing the Windows EXE, bundled Python/Qt
runtime, bundled FFmpeg, the public development certificate and notice, the
project AGPL license and FFmpeg GPLv3 notices. You need no separate downloads
to run ClipMint or record video. The EXE is not a single-file executable:
extract the ZIP fully and keep its components together.

This developer alpha still requires physical Windows desktop testing,
redistribution compliance review and a recognised code-signing certificate
before it can be described as a verified-publisher public release.
The Linux Mint ClipMint repository and signing pipelines remain untouched.
