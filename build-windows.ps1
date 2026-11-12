# Build from Windows PowerShell on a Windows x64 machine. No installers or auto-updaters.
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not [Environment]::Is64BitOperatingSystem) { throw 'Windows x64 is required' }
py -3.12 -m venv .venv
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
& $python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'pip update failed' }
& $python -m pip install -r requirements-windows.txt
if ($LASTEXITCODE -ne 0) { throw 'Install dependencies failed' }
& $python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Tests failed' }
$env:QT_QPA_PLATFORM = 'offscreen'
& $python main.py --self-test
if ($LASTEXITCODE -ne 0) { throw 'Qt self-test failed' }
Remove-Item Env:QT_QPA_PLATFORM
& $python tools\make_icon.py
if ($LASTEXITCODE -ne 0) { throw 'Icon build failed' }
& $python -m PyInstaller --noconfirm --clean --onedir --windowed --name ClipMint-Windows `
  --icon 'assets\ClipMint.ico' --add-data 'assets;assets' main.py
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller build failed' }
$env:QT_QPA_PLATFORM = 'offscreen'
& '.\dist\ClipMint-Windows\ClipMint-Windows.exe' --self-test
if ($LASTEXITCODE -ne 0) { throw 'Frozen executable self-test failed' }
Remove-Item Env:QT_QPA_PLATFORM
New-Item -ItemType Directory -Force artifacts | Out-Null
$zip = 'artifacts\ClipMint-Windows-x64-alpha.zip'
if (Test-Path $zip) { Remove-Item $zip }
Compress-Archive -Path 'dist\ClipMint-Windows\*' -DestinationPath $zip
Get-FileHash -Algorithm SHA256 $zip | Format-Table
Write-Host "Portable Windows build ready: $zip"
