# JARZ-AI - Start Script
# Runs both backend and frontend servers

Write-Host "Starting JARZ-AI..." -ForegroundColor Cyan
Write-Host ""

# Free ports 8000 and 3000 before starting
Write-Host "Checking and freeing ports 8000 and 3000..." -ForegroundColor Yellow

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

Stop-ProcessesOnPort -Port 8000
Stop-ProcessesOnPort -Port 3000
Start-Sleep -Seconds 1

# Activate Python virtual environment (if exists)
Write-Host "Activating Python environment..." -ForegroundColor Yellow
$venvCandidates = @(
    "$PSScriptRoot\.venv\Scripts\Activate.ps1",
    "$PSScriptRoot\backend\venv\Scripts\Activate.ps1",
    "$PSScriptRoot\backend\.venv\Scripts\Activate.ps1"
)
$activated = $false
foreach ($path in $venvCandidates) {
    if (Test-Path $path) {
        & $path
        $activated = $true
        Write-Host "Activated venv at $path" -ForegroundColor Green
        break
    }
}
if (-not $activated) {
    Write-Host "No Python virtual environment found. Tried:" -ForegroundColor Red
    $venvCandidates | ForEach-Object { Write-Host " - $_" -ForegroundColor Red }
}

# Start backend in a new PowerShell window
Write-Host "Starting backend server (port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; if (Test-Path '$PSScriptRoot\.venv\Scripts\Activate.ps1') { & '$PSScriptRoot\.venv\Scripts\Activate.ps1' } elseif (Test-Path '$PSScriptRoot\backend\venv\Scripts\Activate.ps1') { & '$PSScriptRoot\backend\venv\Scripts\Activate.ps1' } elseif (Test-Path '$PSScriptRoot\backend\.venv\Scripts\Activate.ps1') { & '$PSScriptRoot\backend\.venv\Scripts\Activate.ps1' }; python -m uvicorn app.main:app --reload --port 8000"

# Wait a moment for backend to initialize
Start-Sleep -Seconds 2

# Start frontend in a new PowerShell window
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
Write-Host "✓ Backend running on http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "✓ Frontend running on http://localhost:3000" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C in each window to stop the servers" -ForegroundColor Cyan
Write-Host "Opening app in browser..." -ForegroundColor Cyan

# Wait for frontend to start, then open browser
Start-Sleep -Seconds 5
Start-Process "http://localhost:3000"