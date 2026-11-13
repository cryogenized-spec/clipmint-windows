# GitHub Actions only: create an ephemeral UNTRUSTED development code-signing
# certificate, Authenticode-sign the Windows alpha EXE, verify it on the isolated
# Windows runner, then remove all temporary trust entries and the private key.
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
$rootImported = $false
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

    # Trust the ephemeral public cert for verification ON THIS DISPOSABLE
    # BUILD RUNNER ONLY. Remove it again before publishing the artifact.
    Import-Certificate -FilePath $publicCertPath -CertStoreLocation 'Cert:\CurrentUser\Root' | Out-Null
    $rootImported = $true

    $signed = Set-AuthenticodeSignature -LiteralPath $target -Certificate $cert `
        -HashAlgorithm SHA256 -IncludeChain All
    if ($signed.Status -ne [System.Management.Automation.SignatureStatus]::Valid) {
        throw "Signature creation or local trust validation failed: $($signed.Status) / $($signed.StatusMessage)"
    }
    $check = Get-AuthenticodeSignature -LiteralPath $target
    if ($check.Status -ne [System.Management.Automation.SignatureStatus]::Valid -or
        -not $check.SignerCertificate -or
        $check.SignerCertificate.Thumbprint -ne $cert.Thumbprint) {
        throw "Authenticode signature verification failed: $($check.Status) / $($check.StatusMessage)"
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
    Write-Host "PASS: SHA-256 Authenticode signed and verified (CI-only temporary trust): $($cert.Thumbprint)"
}
finally {
    if ($cert) {
        $thumb = $cert.Thumbprint
        if ($rootImported) {
            Remove-Item -LiteralPath "Cert:\CurrentUser\Root\$thumb" -Force -ErrorAction SilentlyContinue
        }
        # Removing the private key from the ephemeral runner's cert store is
        # best-effort; GitHub-hosted runners are also discarded after each job.
        Remove-Item -LiteralPath "Cert:\CurrentUser\My\$thumb" -DeleteKey -Force -ErrorAction SilentlyContinue
    }
}
