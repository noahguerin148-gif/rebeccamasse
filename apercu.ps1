# ============================================================================
#  Construit le site et l'ouvre dans le navigateur (aperçu local).
#  Clic droit > « Exécuter avec PowerShell », ou :
#      powershell -ExecutionPolicy Bypass -File .\apercu.ps1
# ============================================================================
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

$python = (Get-Command python -ErrorAction SilentlyContinue)
if (-not $python) { $python = (Get-Command py -ErrorAction SilentlyContinue) }
if (-not $python) {
    Write-Host "Python est introuvable. Installez-le avec :  winget install Python.Python.3.12" -ForegroundColor Yellow
    Read-Host "Appuyez sur Entrée pour fermer"; exit 1
}

& $python.Source -c "import PIL" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installation de Pillow (une seule fois)..."
    & $python.Source -m pip install --quiet -r outils\requirements.txt
}

& $python.Source outils\construire.py
if ($LASTEXITCODE -ne 0) { Read-Host "Appuyez sur Entrée pour fermer"; exit 1 }

Start-Process (Join-Path $PSScriptRoot "_site\index.html")
