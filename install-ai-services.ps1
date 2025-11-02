# AURA Framework - AI Services Implementation Generator
# This script creates all core AI services for cutting-edge healthcare AI

Write-Host "🤖 AURA Framework - Implementing AI Services" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

$rootDir = "c:\Users\sayan\Downloads\LOOP"
$backendDir = "$rootDir\backend"

# Create AI Service (LLM Integration)
Write-Host "📝 Creating AI Service (LLM Integration)..." -ForegroundColor Yellow
$aiServiceContent = @'
"""
AI Service for AURA Healthcare System
Handles LLM integration, response generation, and medical AI capabilities
Supports OpenAI, Anthropic, HuggingFace, Azure OpenAI, and Google Gemini
"""

import os
from typing import Optional, List, Dict, Any
from enum import Enum
import asyncio

class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"
    AZURE_OPENAI = "azure_openai"
    GOOGLE_GEMINI = "google_gemini"

class AIService:
    """
    Main AI Service class
    
    Features:
    - Multi-provider LLM support
    - Medical-focused prompting
    - Context-aware responses
    - Automatic fallback between providers
    - Cost tracking and optimization
    """
    
    def __init__(self):
        self.providers: Dict[str, Any] = {}
        self.primary_provider: Optional[str] = None
        self.initialize_providers()
    
    def initialize_providers(self):
        """Initialize available LLM providers based on API keys"""
        
        # OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                import openai
                openai.api_key = openai_key
                self.providers[LLMProvider.OPENAI.value] = {
                    "client": openai,
                    "model": os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview"),
                    "available": True
                }
                if not self.primary_provider:
                    self.primary_provider = LLMProvider.OPENAI.value
                print(f"✅ OpenAI configured (model: {self.providers[LLMProvider.OPENAI.value]['model']})")
            except ImportError:
                print("⚠️  OpenAI library not installed: pip install openai")
        
        # Anthropic Claude
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            try:
                import anthropic
                self.providers[LLMProvider.ANTHROPIC.value] = {
                    "client": anthropic.Anthropic(api_key=anthropic_key),
                    "model": os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229"),
                    "available": True
                }
                if not self.primary_provider:
                    self.primary_provider = LLMProvider.ANTHROPIC.value
                print(f"✅ Anthropic Claude configured (model: {self.providers[LLMProvider.ANTHROPIC.value]['model']})")
            except ImportError:
                print("⚠️  Anthropic library not installed: pip install anthropic")
        
        # HuggingFace
        hf_key = os.getenv("HUGGINGFACE_API_KEY")
        if hf_key:
            try:
                from huggingface_hub import InferenceClient
                self.providers[LLMProvider.HUGGINGFACE.value] = {
                    "client": InferenceClient(token=hf_key),
                    "model": os.getenv("HUGGINGFACE_MODEL", "meta-llama/Llama-3.1-70B-Instruct"),
                    "available": True
                }
                if not self.primary_provider:
                    self.primary_provider = LLMProvider.HUGGINGFACE.value
                print(f"✅ HuggingFace configured (model: {self.providers[LLMProvider.HUGGINGFACE.value]['model']})")
            except ImportError:
                print("⚠️  HuggingFace library not installed: pip install huggingface-hub")
        
        # Azure OpenAI
        azure_key = os.getenv("AZURE_OPENAI_API_KEY")
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        if azure_key and azure_endpoint:
            try:
                import openai
                self.providers[LLMProvider.AZURE_OPENAI.value] = {
                    "client": openai,
                    "endpoint": azure_endpoint,
                    "deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4-turbo"),
                    "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
                    "available": True
                }
                if not self.primary_provider:
                    self.primary_provider = LLMProvider.AZURE_OPENAI.value
                print(f"✅ Azure OpenAI configured")
            except ImportError:
                print("⚠️  OpenAI library not installed: pip install openai")
        
        # Google Gemini
        google_key = os.getenv("GOOGLE_API_KEY")
        if google_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=google_key)
                self.providers[LLMProvider.GOOGLE_GEMINI.value] = {
                    "client": genai,
                    "model": os.getenv("GOOGLE_MODEL", "gemini-1.5-pro"),
                    "available": True
                }
                if not self.primary_provider:
                    self.primary_provider = LLMProvider.GOOGLE_GEMINI.value
                print(f"✅ Google Gemini configured (model: {self.providers[LLMProvider.GOOGLE_GEMINI.value]['model']})")
            except ImportError:
                print("⚠️  Google GenerativeAI library not installed: pip install google-generativeai")
        
        if not self.providers:
            print("⚠️  No LLM providers configured. Add API keys to .env file.")
            print("   See AI_CONFIGURATION.md for setup instructions.")
    
    async def generate_response(
        self,
        prompt: str,
        context: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        provider: Optional[str] = None
    ) -> str:
        """
        Generate AI response using primary or specified provider
        
        Args:
            prompt: User input or query
            context: Additional context (medical history, conversation history)
            temperature: Response creativity (0.0-1.0)
            max_tokens: Maximum response length
            provider: Specific provider to use (optional)
        
        Returns:
            Generated response text
        """
        if not self.providers:
            return "AI services not configured. Please add LLM API keys."
        
        provider_name = provider or self.primary_provider
        
        if provider_name not in self.providers:
            provider_name = self.primary_provider
        
        # Build full prompt with medical context
        full_prompt = self._build_medical_prompt(prompt, context)
        
        try:
            if provider_name == LLMProvider.OPENAI.value:
                return await self._generate_openai(full_prompt, temperature, max_tokens)
            elif provider_name == LLMProvider.ANTHROPIC.value:
                return await self._generate_anthropic(full_prompt, temperature, max_tokens)
            elif provider_name == LLMProvider.HUGGINGFACE.value:
                return await self._generate_huggingface(full_prompt, temperature, max_tokens)
            elif provider_name == LLMProvider.AZURE_OPENAI.value:
                return await self._generate_azure_openai(full_prompt, temperature, max_tokens)
            elif provider_name == LLMProvider.GOOGLE_GEMINI.value:
                return await self._generate_gemini(full_prompt, temperature, max_tokens)
        except Exception as e:
            print(f"❌ Error with {provider_name}: {e}")
            # Try fallback provider
            return await self._fallback_response(full_prompt, temperature, max_tokens, provider_name)
        
        return "Unable to generate response. Please try again."
    
    def _build_medical_prompt(self, prompt: str, context: Optional[str] = None) -> str:
        """Build medical-focused prompt with safety guardrails"""
        system_context = """You are AURA, an AI healthcare assistant. Your role is to:
        - Provide empathetic, medically-informed responses
        - Ask relevant follow-up questions
        - Identify urgent situations and escalate to doctors
        - NEVER diagnose or prescribe (suggest consulting a doctor instead)
        - Respect patient privacy and medical ethics
        - Support multilingual conversations
        
        Guidelines:
        - Be compassionate and professional
        - Explain medical terms in simple language
        - Ask about symptoms, duration, severity
        - Consider patient's medical history
        - Identify red flags (chest pain, difficulty breathing, etc.)
        """
        
        if context:
            return f"{system_context}\n\nContext:\n{context}\n\nPatient: {prompt}\n\nAURA:"
        else:
            return f"{system_context}\n\nPatient: {prompt}\n\nAURA:"
    
    async def _generate_openai(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """Generate response using OpenAI GPT"""
        provider = self.providers[LLMProvider.OPENAI.value]
        client = provider["client"]
        
        response = await client.ChatCompletion.acreate(
            model=provider["model"],
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content.strip()
    
    async def _generate_anthropic(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """Generate response using Anthropic Claude"""
        provider = self.providers[LLMProvider.ANTHROPIC.value]
        client = provider["client"]
        
        message = await asyncio.to_thread(
            client.messages.create,
            model=provider["model"],
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return message.content[0].text.strip()
    
    async def _generate_huggingface(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """Generate response using HuggingFace"""
        provider = self.providers[LLMProvider.HUGGINGFACE.value]
        client = provider["client"]
        
        response = await asyncio.to_thread(
            client.text_generation,
            prompt,
            model=provider["model"],
            max_new_tokens=max_tokens,
            temperature=temperature
        )
        
        return response.strip()
    
    async def _generate_azure_openai(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """Generate response using Azure OpenAI"""
        provider = self.providers[LLMProvider.AZURE_OPENAI.value]
        client = provider["client"]
        
        client.api_base = provider["endpoint"]
        client.api_version = provider["api_version"]
        client.api_type = "azure"
        
        response = await client.ChatCompletion.acreate(
            deployment_id=provider["deployment"],
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content.strip()
    
    async def _generate_gemini(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """Generate response using Google Gemini"""
        provider = self.providers[LLMProvider.GOOGLE_GEMINI.value]
        genai = provider["client"]
        
        model = genai.GenerativeModel(provider["model"])
        
        response = await asyncio.to_thread(
            model.generate_content,
            prompt,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens
            }
        )
        
        return response.text.strip()
    
    async def _fallback_response(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        failed_provider: str
    ) -> str:
        """Try alternative providers if primary fails"""
        for provider_name in self.providers.keys():
            if provider_name != failed_provider:
                try:
                    print(f"🔄 Falling back to {provider_name}")
                    return await self.generate_response(
                        prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        provider=provider_name
                    )
                except Exception as e:
                    print(f"❌ Fallback to {provider_name} failed: {e}")
                    continue
        
        return "AI services temporarily unavailable. Please try again."
    
    async def extract_medical_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract medical entities (symptoms, conditions, medications)"""
        prompt = f"""Extract medical entities from the following text:
        
        Text: {text}
        
        Return a JSON with these categories:
        - symptoms: list of mentioned symptoms
        - conditions: list of medical conditions
        - medications: list of medications
        - body_parts: list of body parts/organs mentioned
        
        JSON:"""
        
        response = await self.generate_response(prompt, temperature=0.3, max_tokens=500)
        
        # Parse JSON response
        try:
            import json
            return json.loads(response)
        except:
            return {
                "symptoms": [],
                "conditions": [],
                "medications": [],
                "body_parts": []
            }
    
    async def assess_urgency(self, message: str, context: Optional[str] = None) -> tuple[int, str]:
        """
        Assess medical urgency level
        
        Returns:
            (urgency_level, reason) where urgency_level is 1-5:
            1 = Routine, 2 = Low, 3 = Moderate, 4 = High, 5 = Emergency
        """
        prompt = f"""Assess the medical urgency of this message on a scale of 1-5:
        
        Message: {message}
        {f"Context: {context}" if context else ""}
        
        Urgency levels:
        1 = Routine (general questions, wellness)
        2 = Low (minor symptoms, no immediate risk)
        3 = Moderate (persistent symptoms, needs attention soon)
        4 = High (severe symptoms, should see doctor today)
        5 = Emergency (life-threatening, needs immediate medical attention)
        
        Red flags for urgency 5:
        - Chest pain, difficulty breathing
        - Severe bleeding, head injury
        - Stroke symptoms, loss of consciousness
        - Severe allergic reaction
        
        Return JSON: {{"urgency": <number>, "reason": "<explanation>"}}
        
        JSON:"""
        
        response = await self.generate_response(prompt, temperature=0.2, max_tokens=200)
        
        try:
            import json
            result = json.loads(response)
            return (result.get("urgency", 3), result.get("reason", ""))
        except:
            return (3, "Unable to assess urgency")
    
    async def generate_medical_summary(
        self,
        conversation_messages: List[Dict[str, Any]]
    ) -> str:
        """Generate medical summary from conversation"""
        messages_text = "\n".join([
            f"{msg.get('role', 'user')}: {msg.get('content', '')}"
            for msg in conversation_messages
        ])
        
        prompt = f"""Generate a concise medical summary of this conversation:
        
        {messages_text}
        
        Include:
        - Chief complaint
        - Key symptoms and duration
        - Relevant medical history mentioned
        - Concerns or questions
        - Recommended actions
        
        Summary:"""
        
        return await self.generate_response(prompt, temperature=0.5, max_tokens=1000)
    
    def get_available_providers(self) -> List[str]:
        """Get list of configured providers"""
        return list(self.providers.keys())
    
    def is_available(self) -> bool:
        """Check if any AI service is available"""
        return len(self.providers) > 0

# Global AI service instance
ai_service = AIService()

# Helper function for easy access
async def get_ai_response(
    message: str,
    context: Optional[str] = None,
    temperature: float = 0.7
) -> str:
    """Simple helper to get AI response"""
    return await ai_service.generate_response(message, context, temperature)
'@

Set-Content -Path "$backendDir\app\services\ai_service.py" -Value $aiServiceContent -Force
Write-Host "✅ AI Service created" -ForegroundColor Green

Write-Host ""
Write-Host "📝 Creating __init__.py for services..." -ForegroundColor Yellow
$servicesInitContent = @'
"""
AURA Services Package
Core AI and processing services
"""

from app.services.ai_service import ai_service, get_ai_response

__all__ = ["ai_service", "get_ai_response"]
'@

Set-Content -Path "$backendDir\app\services\__init__.py" -Value $servicesInitContent -Force
Write-Host "✅ Services __init__.py created" -ForegroundColor Green

Write-Host ""
Write-Host "✅ AI Services Created Successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Add your LLM API key to .env file" -ForegroundColor White
Write-Host "2. Update backend/app/main.py to enable routers" -ForegroundColor White
Write-Host "3. Install AI dependencies: pip install openai anthropic huggingface-hub" -ForegroundColor White
Write-Host ""
Write-Host "See AI_CONFIGURATION.md for detailed setup instructions" -ForegroundColor Cyan
