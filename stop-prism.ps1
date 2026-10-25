$ErrorActionPreference = "Stop"

$projectRoot = [System.IO.Path]::GetFullPath($PSScriptRoot)
$processes = @(Get-CimInstance Win32_Process)
$targets = @{}

function Add-ProcessTree {
    param ([int]$ProcessId)

    if ($ProcessId -le 0 -or $targets.ContainsKey($ProcessId)) {
        return
    }

    $process = $processes | Where-Object { $_.ProcessId -eq $ProcessId } | Select-Object -First 1
    if (-not $process) {
        return
    }

    $targets[$ProcessId] = $process

    $children = $processes | Where-Object { $_.ParentProcessId -eq $ProcessId }
    foreach ($child in $children) {
        Add-ProcessTree -ProcessId ([int]$child.ProcessId)
    }
}

$candidates = $processes | Where-Object {
    $commandLine = $_.CommandLine
    $commandLine -and (
        $commandLine -match "backend\.main:app" -or
        $commandLine -match "npm(\.cmd)?\s+run\s+dev" -or
        $commandLine -match "vite.*--host\s+localhost"
    )
}

foreach ($candidate in $candidates) {
    Add-ProcessTree -ProcessId ([int]$candidate.ProcessId)

    $parentId = [int]$candidate.ParentProcessId
    while ($parentId -gt 0) {
        $parent = $processes | Where-Object { $_.ProcessId -eq $parentId } | Select-Object -First 1
        if (-not $parent) {
            break
        }

        $parentCommand = [string]$parent.CommandLine
        if ($parent.Name -notmatch "^powershell(.exe)?$|^pwsh(.exe)?$" -or
            $parentCommand -notmatch [regex]::Escape($projectRoot)) {
            break
        }

        Add-ProcessTree -ProcessId $parentId
        $parentId = [int]$parent.ParentProcessId
    }
}

if ($targets.Count -eq 0) {
    Write-Host "No PRISM processes were found." -ForegroundColor Yellow
    exit 0
}

$processIds = @($targets.Keys | Sort-Object -Descending)
foreach ($processId in $processIds) {
    try {
        Stop-Process -Id $processId -Force -ErrorAction Stop
        Write-Host "Stopped process $processId ($($targets[$processId].Name))." -ForegroundColor Green
    } catch [System.ArgumentException] {
        Write-Host "Process $processId already stopped." -ForegroundColor DarkGray
    } catch {
        Write-Warning "Could not stop process $processId`: $($_.Exception.Message)"
    }
}

Write-Host "PRISM backend, frontend, and their launcher terminals have been stopped." -ForegroundColor Green
