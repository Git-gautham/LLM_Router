$ErrorActionPreference = "Stop"

$projectRoot = $PSScriptRoot
$python = Join-Path $projectRoot "venv\Scripts\python.exe"
$frontendRoot = Join-Path $projectRoot "frontend"
$frontendPackage = Join-Path $frontendRoot "package.json"

if (-not (Test-Path $python)) {
    throw "The virtual environment was not found at $python. Create it before running this script."
}

if (-not (Test-Path $frontendPackage)) {
    throw "The frontend package was not found at $frontendPackage."
}

$backendCommand = @"
Set-Location '$projectRoot'
Write-Host 'Starting PRISM backend at http://127.0.0.1:8000' -ForegroundColor Cyan
& '$python' -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
"@

$frontendCommand = @"
Set-Location '$frontendRoot'
Write-Host 'Starting PRISM frontend at http://127.0.0.1:5173' -ForegroundColor Cyan
& npm.cmd run dev -- --host 127.0.0.1
"@

Start-Process powershell.exe `
    -WorkingDirectory $projectRoot `
    -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $backendCommand)

Start-Process powershell.exe `
    -WorkingDirectory $frontendRoot `
    -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $frontendCommand)

function Wait-ForPort {
    param (
        [string]$HostName,
        [int]$Port,
        [int]$TimeoutSeconds = 60
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)

    do {
        try {
            $client = [System.Net.Sockets.TcpClient]::new()
            $connection = $client.BeginConnect($HostName, $Port, $null, $null)
            if ($connection.AsyncWaitHandle.WaitOne(500)) {
                $client.EndConnect($connection)
                $client.Close()
                return $true
            }
            $client.Close()
        } catch {
            if ($client) {
                $client.Close()
            }
        }

        Start-Sleep -Milliseconds 500
    } while ((Get-Date) -lt $deadline)

    return $false
}

function Wait-ForHttp {
    param (
        [string]$Url,
        [int]$TimeoutSeconds = 60
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)

    do {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                return $true
            }
        } catch {
        }

        Start-Sleep -Milliseconds 500
    } while ((Get-Date) -lt $deadline)

    return $false
}

Write-Host "Waiting for PRISM services..." -ForegroundColor Yellow

$backendReady = Wait-ForHttp -Url "http://127.0.0.1:8000/api/health"
$frontendReady = Wait-ForHttp -Url "http://127.0.0.1:5173"

if (-not $backendReady) {
    Write-Warning "Backend did not become ready within 60 seconds. Check its terminal for errors."
}

if (-not $frontendReady) {
    Write-Warning "Frontend did not become ready within 60 seconds. Check its terminal for errors."
}

if ($backendReady -and $frontendReady) {
    Start-Process "http://127.0.0.1:5173"
    Write-Host "PRISM is running. Close the backend and frontend terminals to stop it." -ForegroundColor Green
} else {
    Write-Host "PRISM did not start completely. No browser was opened." -ForegroundColor Red
}
