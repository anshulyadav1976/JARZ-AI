# JARZ-AI - Start Script
# Installs deps (if needed) and runs both backend + frontend servers.
#
# Usage:
#   .\run.ps1
#   .\run.ps1 -BackendPort 8000 -FrontendPort 3000
#   .\run.ps1 -SkipInstall
#   .\run.ps1 -NoBrowser

param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 3000,
    [switch]$SkipInstall,
    [switch]$NoBrowser
)

Write-Host "Starting JARZ-AI..." -ForegroundColor Cyan
Write-Host ""

# Free ports before starting
Write-Host "Checking and freeing ports $BackendPort and $FrontendPort..." -ForegroundColor Yellow

function Stop-ProcessesOnPort {
    param([Parameter(Mandatory=$true)][int]$Port)

    Write-Host "Scanning for processes using port $Port..." -ForegroundColor Yellow

    $pids = @()
    # Prefer Get-NetTCPConnection if available
    if (Get-Command Get-NetTCPConnection -ErrorAction SilentlyContinue) {
        try {
            $conns = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
            if ($conns) {
                $pids = $conns | Select-Object -ExpandProperty OwningProcess | Where-Object { $_ -gt 0 } | Sort-Object -Unique
            }
        } catch {
            # Ignore and fallback
        }
    }

    # Fallback: parse netstat output
    if (-not $pids -or $pids.Count -eq 0) {
        try {
            $net = netstat -ano | Select-String ":$Port\s"
            $pids = $net | ForEach-Object {
                $line = ($_ -replace "\s+", " ").ToString().Trim()
                $parts = $line.Split(" ")
                $parts[$parts.Length - 1]
            } | Where-Object { $_ -match '^[1-9][0-9]*$' } | Sort-Object -Unique
        } catch {
            # netstat may fail; continue silently
        }
    }

    if (-not $pids -or $pids.Count -eq 0) {
        Write-Host "No processes found on port $Port." -ForegroundColor Green
        return
    }

    foreach ($procId in $pids) {
        try {
            $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
            if ($proc) {
                Write-Host "Stopping PID $procId ($($proc.ProcessName)) on port $Port..." -ForegroundColor Yellow
                Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
            }
        } catch {
            Write-Host "Could not stop PID $procId on port $Port (permission or already stopped)." -ForegroundColor Red
        }
    }
}

Stop-ProcessesOnPort -Port $BackendPort
Stop-ProcessesOnPort -Port $FrontendPort
Start-Sleep -Seconds 1

# -----------------------------------------------------------------------------
# Backend setup (venv + pip install)
# -----------------------------------------------------------------------------
$backendDir = Join-Path $PSScriptRoot "backend"
$backendReq = Join-Path $backendDir "requirements.txt"
$backendEnvExample = Join-Path $backendDir ".env.example"
$backendEnv = Join-Path $backendDir ".env"
$venvDir = Join-Path $backendDir "venv"
$activatePath = Join-Path $venvDir "Scripts\Activate.ps1"

if (-not (Test-Path $backendDir)) {
    Write-Host "Backend directory not found: $backendDir" -ForegroundColor Red
    exit 1
}

if (-not $SkipInstall) {
    # Create backend/.env if missing (keeps placeholders; user should edit API keys)
    if ((Test-Path $backendEnvExample) -and (-not (Test-Path $backendEnv))) {
        Copy-Item $backendEnvExample $backendEnv -Force
        Write-Host "Created backend/.env from backend/.env.example (edit keys inside)." -ForegroundColor Yellow
    }

    # Create venv if missing
    if (-not (Test-Path $activatePath)) {
        Write-Host "Creating Python venv in backend/venv..." -ForegroundColor Yellow
        Push-Location $backendDir
        python -m venv venv
        Pop-Location
    }

    # Activate venv in this shell for installs
    if (Test-Path $activatePath) {
        Write-Host "Activating Python venv..." -ForegroundColor Yellow
        & $activatePath
        Write-Host "Installing backend Python dependencies..." -ForegroundColor Yellow
        Push-Location $backendDir
        pip install -r $backendReq
        Pop-Location
    } else {
        Write-Host "Could not find venv activate script: $activatePath" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "SkipInstall set: skipping backend dependency installation." -ForegroundColor Yellow
}

# -----------------------------------------------------------------------------
# Frontend setup (npm install)
# -----------------------------------------------------------------------------
$frontendDir = Join-Path $PSScriptRoot "frontend"
$frontendEnvExample = Join-Path $frontendDir ".env.example"
$frontendEnvLocal = Join-Path $frontendDir ".env.local"
$nodeModules = Join-Path $frontendDir "node_modules"

if (-not (Test-Path $frontendDir)) {
    Write-Host "Frontend directory not found: $frontendDir" -ForegroundColor Red
    exit 1
}

if (-not $SkipInstall) {
    # Create frontend/.env.local if missing
    if ((Test-Path $frontendEnvExample) -and (-not (Test-Path $frontendEnvLocal))) {
        Copy-Item $frontendEnvExample $frontendEnvLocal -Force
        # Ensure it points to our backend port (best-effort).
        (Get-Content $frontendEnvLocal) `
            -replace '^NEXT_PUBLIC_API_URL=.*$', "NEXT_PUBLIC_API_URL=http://localhost:$BackendPort" `
            | Set-Content $frontendEnvLocal
        Write-Host "Created frontend/.env.local from frontend/.env.example." -ForegroundColor Yellow
    }

    if (-not (Test-Path $nodeModules)) {
        Write-Host "Installing frontend dependencies (npm install)..." -ForegroundColor Yellow
        Push-Location $frontendDir
        npm install
        Pop-Location
    } else {
        Write-Host "Frontend node_modules already present (skipping npm install)." -ForegroundColor Green
    }
} else {
    Write-Host "SkipInstall set: skipping frontend dependency installation." -ForegroundColor Yellow
}

# Start backend in a new PowerShell window
Write-Host "Starting backend server (port $BackendPort)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$backendDir'; if (Test-Path '$activatePath') { & '$activatePath' }; python -m uvicorn app.main:app --reload --port $BackendPort"

# Wait a moment for backend to initialize
Start-Sleep -Seconds 2

# Start frontend in a new PowerShell window
Write-Host "Starting frontend server (port $FrontendPort)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$frontendDir'; `$env:PORT=$FrontendPort; npm run dev"
Write-Host "Starting frontend server (port 3000)..." -ForegroundColor Yellow
Write-Host "Clearing Next.js cache..." -ForegroundColor Yellow
try {
    if (Test-Path "$PSScriptRoot\frontend\.next") {
        Remove-Item -Recurse -Force "$PSScriptRoot\frontend\.next" -ErrorAction SilentlyContinue
    }
} catch {}

# Prefer explicit port to avoid auto-switch
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; npx next dev -p 3000"

Write-Host 
Write-Host "✓ Backend running on http://127.0.0.1:$BackendPort" -ForegroundColor Green
Write-Host "✓ Frontend running on http://localhost:$FrontendPort" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C in each window to stop the servers" -ForegroundColor Cyan

# Wait for frontend to start, then open browser
if (-not $NoBrowser) {
    Write-Host "Opening app in browser..." -ForegroundColor Cyan
    Start-Sleep -Seconds 5
    Start-Process "http://localhost:$FrontendPort"
} else {
    Write-Host "NoBrowser set: not opening a browser automatically." -ForegroundColor Yellow
}