# PowerShell | build.ps1 | Windows 11, Python 3.14 + PyInstaller
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
python scripts/build_icon.py
if ($LASTEXITCODE -ne 0) { throw 'Icon build failed.' }
python scripts/build_flags.py
if ($LASTEXITCODE -ne 0) { throw 'Flag build failed.' }
python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Tester misslyckades.' }
python -m PyInstaller --noconfirm --clean --onefile --windowed --icon 'assets/reroller_icon.ico' --add-data 'reroller/data;reroller/data' --add-data 'assets;assets' --name PoE2Reroller main.py
if ($LASTEXITCODE -ne 0) { throw 'Paketeringen misslyckades.' }
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'README.md') -Destination (Join-Path $PSScriptRoot 'dist/STARTGUIDE.md')
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'VERIFICATION.md') -Destination (Join-Path $PSScriptRoot 'dist/VERIFICATION.md')
Write-Output (Join-Path $PSScriptRoot 'dist/PoE2Reroller.exe')
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'reroller/data/manifest.json') -Destination (Join-Path $PSScriptRoot 'dist/CATALOG-MANIFEST.json')
