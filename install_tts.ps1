# Install TTS Dependencies for AURA Healthcare

Write-Host "🎙️ Installing Text-to-Speech Dependencies..." -ForegroundColor Cyan
Write-Host ""

# Navigate to backend directory
Set-Location -Path "backend"

# Install TTS packages
Write-Host "📦 Installing pyttsx3 (offline TTS engine)..." -ForegroundColor Yellow
pip install pyttsx3

Write-Host ""
Write-Host "📦 Installing gTTS (Google Text-to-Speech)..." -ForegroundColor Yellow
pip install gtts

Write-Host ""
Write-Host "✅ TTS dependencies installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "🎯 Next steps:" -ForegroundColor Cyan
Write-Host "  1. Start backend: python -m uvicorn app.main:app --reload" -ForegroundColor White
Write-Host "  2. Start frontend: cd aura-ui && npm run dev" -ForegroundColor White
Write-Host "  3. Test voice system in chat interface" -ForegroundColor White
Write-Host ""
Write-Host "📚 See TTS_IMPLEMENTATION_GUIDE.md for full documentation" -ForegroundColor Cyan
