Param(
  [string]$Path = "docs/maturity.yaml",
  [switch]$DiffMain
)

$py = ".\.venv\Scripts\python"
if (-not (Test-Path $py)) { $py = "python" }

$cmd = "$py tools\maturity_check.py $Path --format json"
if ($DiffMain) { $cmd += " --diff-against origin/main" }

mkdir build -Force | Out-Null
Invoke-Expression $cmd | Tee-Object -FilePath "build\maturity.json"