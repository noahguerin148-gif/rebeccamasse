# ============================================================================
#  Construit le site et l'ouvre dans le navigateur (aperçu local).
#  Clic droit > « Exécuter avec PowerShell », ou :
#      powershell -ExecutionPolicy Bypass -File .\apercu.ps1
# ============================================================================
# Pas de 'Stop' ici : dans Windows PowerShell 5, les messages d'erreur d'un
# programme externe (Python) arrêteraient le script. On vérifie $LASTEXITCODE.
$ErrorActionPreference = 'Continue'
Set-Location $PSScriptRoot

function Terminer($code) {
    Read-Host "Appuyez sur Entrée pour fermer"
    exit $code
}

# Trouver un vrai Python (et pas le raccourci du Microsoft Store)
$python = $null
foreach ($nom in 'python', 'py') {
    $commande = Get-Command $nom -ErrorAction SilentlyContinue
    if ($commande) {
        & $commande.Source -c "import sys" 2>$null
        if ($LASTEXITCODE -eq 0) { $python = $commande.Source; break }
    }
}
if (-not $python) {
    Write-Host "Python est introuvable. Installez-le avec :  winget install Python.Python.3.12" -ForegroundColor Yellow
    Write-Host "puis fermez et rouvrez PowerShell."
    Terminer 1
}

# Installer Pillow au besoin (une seule fois)
& $python -c "import PIL" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installation de Pillow (une seule fois)..."
    & $python -m pip install --quiet --disable-pip-version-check -r outils\requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "L'installation de Pillow a échoué. Essayez :  $python -m pip install Pillow" -ForegroundColor Yellow
        Terminer 1
    }
}

# Construire le site
& $python outils\construire.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "La construction a échoué (voir le message ci-dessus)." -ForegroundColor Yellow
    Terminer 1
}

Start-Process (Join-Path $PSScriptRoot "_site\index.html")
