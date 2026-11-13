# GitHub Actions only: create an ephemeral UNTRUSTED development code-signing
# certificate, Authenticode-sign the Windows alpha EXE, verify it on the isolated
# Windows runner, then remove its ephemeral private key.
#
# This does NOT produce a Microsoft-trusted publisher identity and is NOT
# intended to bypass Windows SmartScreen. The public .cer contains NO private key.
param(
    [Parameter(Mandatory=$true)][string]$ExePath,
    [Parameter(Mandatory=$true)][string]$OutputDirectory
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

if (-not $IsWindows -and $PSVersionTable.PSEdition -eq 'Core') {
    throw 'Development Authenticode signing requires Windows'
}
$target = (Resolve-Path -LiteralPath $ExePath -ErrorAction Stop).ProviderPath
if (-not $target.EndsWith('.exe', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Only the ClipMint Windows .exe is approved for development signing'
}
if ((Split-Path $target -Leaf) -ne 'ClipMint-Windows.exe') {
    throw 'Unexpected executable name; refusing to sign'
}
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
$outDir = (Resolve-Path -LiteralPath $OutputDirectory).ProviderPath

$cert = $null
try {
    # The private key exists only in this temporary CI runner's CurrentUser store.
    # Every build uses a NEW certificate. Never upload or export a PFX.
    $cert = New-SelfSignedCertificate `
        -Type CodeSigningCert `
        -Subject 'CN=ClipMint Windows Alpha Development (UNTRUSTED)' `
        -FriendlyName 'ClipMint CI development signature only - not a verified publisher' `
        -KeyAlgorithm RSA -KeyLength 3072 -HashAlgorithm SHA256 `
        -KeyExportPolicy NonExportable `
        -NotAfter (Get-Date).AddMonths(3) `
        -CertStoreLocation 'Cert:\CurrentUser\My'
    if (-not $cert -or -not $cert.HasPrivateKey) {
        throw 'Could not generate ephemeral code-signing certificate'
    }

    $publicCertPath = Join-Path $outDir 'ClipMint-Development-Signer.cer'
    Export-Certificate -Cert $cert -FilePath $publicCertPath -Force | Out-Null

    # Never import a self-signed certificate into Trusted Root, even on a CI
    # runner: that can trigger an interactive Windows security prompt and hang
    # unattended builds. An untrusted-but-intact Authenticode signature reports
    # NotTrusted; it is not a trusted publisher identity.
    $signed = Set-AuthenticodeSignature -LiteralPath $target -Certificate $cert `
        -HashAlgorithm SHA256 -IncludeChain All
    $check = Get-AuthenticodeSignature -LiteralPath $target
    $accepted = @(
        [System.Management.Automation.SignatureStatus]::Valid,
        [System.Management.Automation.SignatureStatus]::NotTrusted
    )
    if (-not $check.SignerCertificate -or
        $check.SignerCertificate.Thumbprint -ne $cert.Thumbprint -or
        $check.Status -notin $accepted) {
        throw "Authenticode signing/verification failed: $($check.Status) / $($check.StatusMessage)"
    }

    # The metadata explicitly identifies the certificate as UNTRUSTED and
    # self-signed. It is information, NOT a substitute for GitHub attestation.
    $info = @(
        'ClipMint Windows x64 — DEVELOPMENT SELF-SIGNED Authenticode signature',
        'This certificate is NOT issued by a publicly trusted certificate authority.',
        'Windows SmartScreen may still display Unknown Publisher or other warnings.',
        'Do not install this certificate into Trusted Root to bypass Windows warnings.',
        'Each CI run uses an ephemeral signing key; signing identity is not persistent.',
        "Signed executable: ClipMint-Windows.exe",
        "Subject: $($cert.Subject)",
        "SHA-1 certificate thumbprint: $($cert.Thumbprint)",
        "Certificate expiry (UTC): $($cert.NotAfter.ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ'))",
        "Source: https://github.com/cryogenized-spec/clipmint-windows",
        'Verify build provenance separately using GitHub artifact attestations.',
        'Only the ClipMint executable is signed by this development key. Bundled',
        'FFmpeg is third-party software and retains its original attribution.'
    )
    Set-Content -LiteralPath (Join-Path $outDir 'DEVELOPMENT-SIGNATURE.txt') `
        -Value $info -Encoding UTF8
    Write-Host "PASS: SHA-256 Authenticode development signer embedded ($($check.Status); untrusted publisher): $($cert.Thumbprint)"
}
finally {
    if ($cert) {
        $thumb = $cert.Thumbprint
        # Removing the private key from the ephemeral runner's cert store is
        # best-effort; GitHub-hosted runners are also discarded after each job.
        Remove-Item -LiteralPath "Cert:\CurrentUser\My\$thumb" -DeleteKey -Force -ErrorAction SilentlyContinue
    }
}
