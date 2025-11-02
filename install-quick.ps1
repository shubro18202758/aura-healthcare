# AURA Healthcare - Simple Installation Script
# This installs only the essential dependencies for quick demo

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "   AURA Healthcare - Quick Install" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Installing essential dependencies..." -ForegroundColor Yellow
Write-Host "(This will take 1-2 minutes)`n" -ForegroundColor Gray

# Essential packages for basic API functionality
$packages = @(
    "fastapi",
    "uvicorn[standard]",
    "motor",
    "pymongo",
    "redis",
    "pydantic",
    "pydantic-settings",
    "python-dotenv",
    "python-multipart",
    "websockets"
)

foreach ($package in $packages) {
    Write-Host "Installing $package..." -ForegroundColor Gray
    pip install $package --quiet
}

Write-Host "`n✅ Essential dependencies installed!`n" -ForegroundColor Green

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Installation Complete!" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Run: " -NoNewline -ForegroundColor White
Write-Host "cd backend; python -m app.main" -ForegroundColor Cyan
Write-Host "2. Open: " -NoNewline -ForegroundColor White
Write-Host "http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
