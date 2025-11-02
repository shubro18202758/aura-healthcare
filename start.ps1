# AURA Healthcare Framework - Quick Start Script for Windows
# This script sets up and runs the development environment

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   AURA Healthcare Framework Setup" -ForegroundColor Cyan
Write-Host "   Loop x IIT-B Hackathon 2025" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python installation
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found! Please install Python 3.9+" -ForegroundColor Red
    exit 1
}

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✅ Created .env file" -ForegroundColor Green
    Write-Host "⚠️  Please edit .env with your API keys if needed" -ForegroundColor Yellow
}

# Install Python dependencies
Write-Host "`nInstalling Python dependencies..." -ForegroundColor Yellow
Write-Host "(This may take a few minutes on first run)" -ForegroundColor Gray

try {
    pip install -r requirements.txt --quiet
    Write-Host "✅ Dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Some dependencies may have failed. Continuing..." -ForegroundColor Yellow
}

# Create necessary directories
Write-Host "`nCreating directories..." -ForegroundColor Yellow
$directories = @(
    "data\uploads",
    "data\medical_knowledge",
    "data\vector_db",
    "logs",
    "models"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}
Write-Host "✅ Directories created" -ForegroundColor Green

# Check Docker (optional)
Write-Host "`nChecking Docker (optional)..." -ForegroundColor Yellow
try {
    docker --version | Out-Null
    Write-Host "✅ Docker found - You can run 'docker-compose up -d' for databases" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Docker not found - Will use mock/demo mode" -ForegroundColor Yellow
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "   Setup Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "🚀 Starting AURA Healthcare Backend..." -ForegroundColor Green
Write-Host ""
Write-Host "📍 API will be available at:" -ForegroundColor White
Write-Host "   http://localhost:8000" -ForegroundColor Cyan
Write-Host ""
Write-Host "📍 Interactive API Docs:" -ForegroundColor White
Write-Host "   http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "📍 Demo Accounts:" -ForegroundColor White
Write-Host "   Doctor: doctor@aura.health / doctor123" -ForegroundColor Gray
Write-Host "   Patient: patient@aura.health / patient123" -ForegroundColor Gray
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the backend server
Set-Location backend
python -m app.main
