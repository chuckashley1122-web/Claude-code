<#
.SYNOPSIS
    Read-only host check before installing Odysseus.

.DESCRIPTION
    Verifies Git, Docker Desktop, Docker Compose, WSL2, disk, RAM, CPU, GPU, and
    every port the Compose stack publishes. Installs nothing, downloads nothing,
    and changes nothing on disk. Exits 1 if any blocking check fails.

.EXAMPLE
    .\preflight.ps1
    .\preflight.ps1 -InstallPath D:\AI-Workspaces\odysseus
#>
[CmdletBinding()]
param(
    [string]$InstallPath = (Join-Path 'C:\AI-Workspaces' 'odysseus'),
    [int]$MinFreeGB = 20
)

. "$PSScriptRoot\common.ps1"

$blocking = 0
$advisory = 0

Write-Host 'Odysseus preflight - read only, nothing will be changed.' -ForegroundColor Cyan

# ---------------------------------------------------------------- tooling ----
Write-Head 'Tooling'

if (Test-CommandExists 'git') {
    Write-Pass "git: $((Invoke-Native -Command 'git' -Arguments @('--version')).Output)"
} else {
    Write-Fail 'git not found. Install Git for Windows: https://git-scm.com/download/win'
    $blocking++
}

if (Test-CommandExists 'docker') {
    Write-Pass "docker: $((Invoke-Native -Command 'docker' -Arguments @('--version')).Output)"
} else {
    Write-Fail 'docker not found. Install Docker Desktop: https://www.docker.com/products/docker-desktop/'
    $blocking++
}

if (Test-DockerRunning) {
    $srv = (Invoke-Native -Command 'docker' -Arguments @('info', '--format', '{{.ServerVersion}}')).Output
    Write-Pass "Docker daemon reachable (engine $srv)"
} else {
    Write-Fail 'Docker daemon is not reachable. Start Docker Desktop and wait for the whale icon to settle.'
    $blocking++
}

$compose = Invoke-Native -Command 'docker' -Arguments @('compose', 'version')
if ($compose.Success) {
    Write-Pass "docker compose: $($compose.Output.Split([Environment]::NewLine)[0])"
} else {
    Write-Fail 'docker compose (v2) not available. Update Docker Desktop.'
    $blocking++
}

# ------------------------------------------------------------------- wsl2 ----
Write-Head 'WSL2 backend'

if (Test-CommandExists 'wsl') {
    $wsl = Invoke-Native -Command 'wsl' -Arguments @('--status')
    # wsl.exe emits UTF-16; strip nulls so -match behaves.
    $wslText = ($wsl.Output -replace "`0", '')
    if ($wsl.Success) {
        if ($wslText -match '2') { Write-Pass 'WSL is installed and reporting version 2' }
        else { Write-Warn 'WSL present but default version unclear. Docker Desktop must use the WSL2 backend.'; $advisory++ }
    } else {
        Write-Warn 'wsl --status failed. Confirm the WSL2 backend in Docker Desktop > Settings > General.'
        $advisory++
    }
} else {
    Write-Warn 'wsl.exe not found. If Docker Desktop runs on Hyper-V instead, the install still works but differs from the guide.'
    $advisory++
}

# --------------------------------------------------------------- hardware ----
Write-Head 'Hardware'

try {
    $cs  = Get-CimInstance Win32_ComputerSystem
    $cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
    $ramGB = [math]::Round($cs.TotalPhysicalMemory / 1GB, 1)
    Write-Info "CPU: $($cpu.Name.Trim()) ($($cpu.NumberOfCores) cores / $($cpu.NumberOfLogicalProcessors) threads)"
    Write-Info "RAM: $ramGB GB"
    if ($ramGB -lt 8)       { Write-Fail 'Under 8 GB RAM. Docker plus the stack will struggle.'; $blocking++ }
    elseif ($ramGB -lt 16)  { Write-Warn 'Under 16 GB RAM. Cloud models only - do not plan on local inference.'; $advisory++ }
    else                    { Write-Pass 'RAM is sufficient for the stack' }
} catch {
    Write-Warn "Could not read CPU/RAM: $($_.Exception.Message)"
    $advisory++
}

try {
    $gpus = Get-CimInstance Win32_VideoController
    foreach ($g in $gpus) {
        $vramGB = if ($g.AdapterRAM -gt 0) { [math]::Round($g.AdapterRAM / 1GB, 1) } else { 0 }
        Write-Info "GPU: $($g.Name) (reported VRAM ~$vramGB GB)"
    }
    Write-Info 'Local model serving needs real VRAM. Start with a cloud model regardless.'
} catch {
    Write-Warn 'Could not enumerate GPUs.'
    $advisory++
}

# ------------------------------------------------------------------- disk ----
Write-Head 'Disk'

# Split-Path -Qualifier throws on a path with no drive letter — a UNC path
# (\\server\share\...) or a relative one. With $ErrorActionPreference = 'Stop'
# that killed the whole preflight mid-run instead of degrading to a warning,
# so the qualifier lookup lives inside the try as well.
try {
    $driveLetter = (Split-Path -Qualifier $InstallPath -ErrorAction Stop).TrimEnd(':')
    $drive  = Get-PSDrive -Name $driveLetter -ErrorAction Stop
    $freeGB = [math]::Round($drive.Free / 1GB, 1)
    Write-Info "$driveLetter`: has $freeGB GB free"
    if ($freeGB -lt $MinFreeGB) {
        Write-Fail "Under $MinFreeGB GB free. Images, containers, logs, and the model cache need room."
        $blocking++
    } else {
        Write-Pass "At least $MinFreeGB GB free"
    }
} catch {
    Write-Warn "Could not measure free space on '$InstallPath' - $($_.Exception.Message)"
    Write-Info "Check by hand that at least $MinFreeGB GB is free before installing."
    $advisory++
}

# ------------------------------------------------------------ install path ----
Write-Head 'Install path'

if (Test-Path $InstallPath) {
    $items = @(Get-ChildItem -Force $InstallPath)
    if ($items.Count -eq 0) {
        Write-Pass "$InstallPath exists and is empty"
    } elseif (Test-Path (Join-Path $InstallPath '.git')) {
        Write-Warn "$InstallPath already holds a Git checkout. install.ps1 will refuse to overwrite it."
        $advisory++
    } else {
        Write-Fail "$InstallPath exists and is not empty. Choose another path or clear it deliberately."
        $blocking++
    }
} else {
    Write-Pass "$InstallPath does not exist yet - install.ps1 will create it"
}

if ($InstallPath -match 'OneDrive|Dropbox|Google Drive|iCloud') {
    Write-Fail 'Install path is inside a cloud-sync folder. Syncing a live SQLite database corrupts it. Pick a local path.'
    $blocking++
}

# ------------------------------------------------------------------ ports ----
Write-Head 'Ports published by the Compose stack'

foreach ($p in $script:OdysseusPorts) {
    $free = Test-PortFree -Port $p.Port
    if ($null -eq $free) {
        Write-Warn "$($p.Port) ($($p.Service)) - could not determine whether it is free on this host"
        $advisory++
    } elseif ($free) {
        Write-Pass "$($p.Port) free ($($p.Service) - $($p.Note))"
    } elseif ($p.Port -eq 7000) {
        Write-Warn '7000 is in use. Set APP_PORT=7001 - install.ps1 -AppPort 7001 does this for you.'
        $advisory++
    } else {
        Write-Fail "$($p.Port) is in use and $($p.Service) has no configurable alternative in the default compose file. Free it before installing."
        $blocking++
    }
}

# ---------------------------------------------------------------- summary ----
Write-Head 'Summary'

if ($blocking -eq 0 -and $advisory -eq 0) {
    Write-Host '  Ready to install. Next: .\install.ps1 -WhatIf' -ForegroundColor Green
    exit 0
} elseif ($blocking -eq 0) {
    Write-Host "  $advisory advisory item(s), 0 blocking. Read them, then: .\install.ps1 -WhatIf" -ForegroundColor Yellow
    exit 0
} else {
    Write-Host "  $blocking blocking item(s) and $advisory advisory item(s)." -ForegroundColor Red
    Write-Stop 'Resolve the blocking items above before installing. This script installed nothing.'
    exit 1
}
