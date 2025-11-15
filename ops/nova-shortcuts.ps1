# Nova Semantic Mirror — Ops Shortcuts (PowerShell)
# Usage:
#   . .\ops\nova-shortcuts.ps1
#   nova-go            # run compact probe + auto-decoder
#   nova-heartbeat     # publish a heartbeat in the same shell
#   nova-pulse         # smart: run nova-go, if active=0 -> heartbeat -> recheck
#
# To auto-load: Add ". C:\code\nova-civilizational-architecture\ops\nova-shortcuts.ps1" to your $PROFILE
# Edit repo path below if your clone is elsewhere.

$env:NOVA_REPO = if ($env:NOVA_REPO) { $env:NOVA_REPO } else { "C:\code\nova-civilizational-architecture" }

function Find-NovaRepo {
    $candidates = @(
        $env:NOVA_REPO,
        $PWD.Path,
        "C:\code\nova-civilizational-architecture"
    )

    foreach ($path in $candidates) {
        if ((Test-Path $path) -and (Test-Path "$path\scripts\semantic_mirror_dashboard.py")) {
            return $path
        }
    }

    Write-Error "nova: repo not found; set NOVA_REPO to the repo path"
    return $null
}

function Decode-NovaCompact {
    param([string]$InputText)

    # Simple key=value parser
    $pairs = @{}
    [regex]::Matches($InputText, '(\w+)=([^\s]+)') | ForEach-Object {
        $pairs[$_.Groups[1].Value] = $_.Groups[2].Value
    }

    $status = if ($pairs.ContainsKey('status')) { $pairs['status'] } else { 'unknown' }
    $hit = [double]($pairs['hit'] -replace '%', '' -replace ',', '.' | Where-Object { $_ -ne '' } | Select-Object -First 1) / 100
    $deny = [double]($pairs['deny'] -replace '%', '' -replace ',', '.' | Where-Object { $_ -ne '' } | Select-Object -First 1) / 100
    $rl = [double]($pairs['rl'] -replace '%', '' -replace ',', '.' | Where-Object { $_ -ne '' } | Select-Object -First 1) / 100
    $reads = [int]($pairs['reads'] | Where-Object { $_ -ne '' } | Select-Object -First 1)
    $active = [int]($pairs['active'] | Where-Object { $_ -ne '' } | Select-Object -First 1)

    $go = ($hit -ge 0.85) -and ($deny -le 0.05) -and ($rl -le 0.005) -and ($active -gt 0)
    $decision = if ($go) { "GO" } else { "NO-GO" }

    Write-Host "$decision | status=$status hit=$($hit.ToString('F3')) deny=$($deny.ToString('F3')) rl=$($rl.ToString('F3')) reads=$reads active=$active"

    if ($active -eq 0) {
        Write-Host "hint: process-scope empty - publish heartbeat in same shell"
    } elseif ($deny -gt 0.10) {
        Write-Host "hint: ACL drift or key typo - review rules/TTL"
    } elseif ($rl -gt 0.005) {
        Write-Host "hint: bursty requester - reduce QPM / widen interval"
    }
}

function nova-go {
    $repoPath = Find-NovaRepo
    if (-not $repoPath) { return }

    Push-Location $repoPath
    try {
        $env:PYTHONPATH = "."
        if (-not $env:NOVA_SEMANTIC_MIRROR_ENABLED) { $env:NOVA_SEMANTIC_MIRROR_ENABLED = "true" }
        if (-not $env:NOVA_SEMANTIC_MIRROR_SHADOW) { $env:NOVA_SEMANTIC_MIRROR_SHADOW = "true" }

        $output = python scripts\semantic_mirror_dashboard.py --compact --once 2>$null
        if ($output) {
            $output | Decode-NovaCompact
        }
    } finally {
        Pop-Location
    }
}

function nova-heartbeat {
    $repoPath = Find-NovaRepo
    if (-not $repoPath) { return }

    Push-Location $repoPath
    try {
        $env:PYTHONPATH = "."
        python -c "from orchestrator.semantic_mirror import publish; publish('slot07.heartbeat', {'tick':1}, 'slot07_production_controls', ttl=120.0); print('heartbeat')"
    } finally {
        Pop-Location
    }
}

function nova-pulse {
    $first = nova-go
    if ($first -match 'active=0') {
        nova-heartbeat
        nova-go
    }
}
