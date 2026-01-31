# JARZ Rental Valuation - Start Script
# Runs both backend and frontend servers

Write-Host "Starting JARZ Rental Valuation..." -ForegroundColor Cyan
Write-Host ""

# Activate Python virtual environment
Write-Host "Activating Python environment..." -ForegroundColor Yellow
& "$PSScriptRoot\.venv\Scripts\Activate.ps1"

# Start backend in a new PowerShell window
Write-Host "Starting backend server (port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; & '$PSScriptRoot\.venv\Scripts\Activate.ps1'; python -m uvicorn app.main:app --reload --port 8000"

# Wait a moment for backend to initialize
Start-Sleep -Seconds 2

# Start frontend in a new PowerShell window
Write-Host "Starting frontend server (port 3000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; npm run dev"

Write-Host ""
Write-Host "✓ Backend running on http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "✓ Frontend running on http://localhost:3000" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C in each window to stop the servers" -ForegroundColor Cyan
Write-Host "Opening app in browser..." -ForegroundColor Cyan

# Wait for frontend to start, then open browser
Start-Sleep -Seconds 5
Start-Process "http://localhost:3000"