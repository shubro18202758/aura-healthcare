"""
MCP Server - Core Model Context Protocol Server
Orchestrates multiple context providers for intelligent AI responses
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from .providers.patient_history_provider import PatientHistoryProvider
from .providers.service_classification_provider import ServiceClassificationProvider
from .providers.knowledge_base_provider import KnowledgeBaseProvider
from .providers.medical_intelligence_provider import MedicalIntelligenceProvider


class MCPServer:
    """
    Central MCP Server coordinating all context providers
    
    Features:
    - Real-time context aggregation
    - Priority-based context selection
    - Caching for performance
    - Context relevance scoring
    """
    
    def __init__(self):
        self.providers = {}
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        self.initialized = False
        
    async def initialize(self):
        """Initialize all context providers"""
        if self.initialized:
            return
            
        print("🔧 Initializing MCP Server...")
        
        # Initialize providers
        self.providers = {
            "patient_history": PatientHistoryProvider(),
            "service_classification": ServiceClassificationProvider(),
            "knowledge_base": KnowledgeBaseProvider(),
            "medical_intelligence": MedicalIntelligenceProvider()
        }
        
        # Initialize each provider
        for name, provider in self.providers.items():
            try:
                await provider.initialize()
                print(f"✅ {name} provider initialized")
            except Exception as e:
                print(f"⚠️  {name} provider initialization failed: {e}")
        
        self.initialized = True
        print("✅ MCP Server Ready!")
    
    async def get_context(
        self,
        user_id: str,
        message: str,
        conversation_id: Optional[str] = None,
        context_types: Optional[List[str]] = None,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        Get comprehensive context for AI response
        
        Args:
            user_id: Patient or doctor ID
            message: Current message/query
            conversation_id: Current conversation ID
            context_types: Specific context types to fetch (None = all)
            max_tokens: Maximum context tokens
            
        Returns:
            Aggregated context with relevance scores
        """
        if not self.initialized:
            await self.initialize()
        
        # Check cache
        cache_key = f"{user_id}:{conversation_id}:{message[:50]}"
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            if (datetime.now() - cache_entry["timestamp"]).seconds < self.cache_ttl:
                return cache_entry["context"]
        
        # Determine which providers to use
        providers_to_use = context_types or list(self.providers.keys())
        
        # Gather context from all providers in parallel
        context_tasks = []
        for provider_name in providers_to_use:
            if provider_name in self.providers:
                provider = self.providers[provider_name]
                context_tasks.append(
                    provider.get_context(user_id, message, conversation_id)
                )
        
        # Wait for all context providers
        contexts = await asyncio.gather(*context_tasks, return_exceptions=True)
        
        # Aggregate context
        aggregated_context = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "conversation_id": conversation_id,
            "contexts": {},
            "total_relevance": 0,
            "context_summary": ""
        }
        
        for i, provider_name in enumerate(providers_to_use):
            if provider_name in self.providers and i < len(contexts):
                context_data = contexts[i]
                if not isinstance(context_data, Exception):
                    aggregated_context["contexts"][provider_name] = context_data
                    aggregated_context["total_relevance"] += context_data.get("relevance_score", 0)
        
        # Generate context summary
        aggregated_context["context_summary"] = self._generate_context_summary(
            aggregated_context["contexts"],
            max_tokens
        )
        
        # Cache result
        self.cache[cache_key] = {
            "timestamp": datetime.now(),
            "context": aggregated_context
        }
        
        return aggregated_context
    
    def _generate_context_summary(self, contexts: Dict[str, Any], max_tokens: int) -> str:
        """Generate a concise summary of all context for AI injection"""
        summary_parts = []
        
        # Patient History
        if "patient_history" in contexts:
            hist = contexts["patient_history"]
            if hist.get("previous_conversations"):
                summary_parts.append(
                    f"Patient History: {len(hist['previous_conversations'])} previous conversations. "
                    f"Recent symptoms: {', '.join(hist.get('recent_symptoms', [])[:3])}"
                )
        
        # Service Classification
        if "service_classification" in contexts:
            svc = contexts["service_classification"]
            if svc.get("predicted_service_type"):
                summary_parts.append(
                    f"Likely Service: {svc['predicted_service_type']} "
                    f"(confidence: {svc.get('confidence', 0):.1%})"
                )
        
        # Knowledge Base
        if "knowledge_base" in contexts:
            kb = contexts["knowledge_base"]
            if kb.get("relevant_knowledge"):
                summary_parts.append(
                    f"Relevant Medical Knowledge: {len(kb['relevant_knowledge'])} entries from "
                    f"{kb.get('specialty', 'general')} specialty"
                )
        
        # Medical Intelligence
        if "medical_intelligence" in contexts:
            mi = contexts["medical_intelligence"]
            if mi.get("similar_cases"):
                summary_parts.append(
                    f"Similar Cases: {mi['similar_cases']} patients with similar symptoms. "
                    f"Common treatments: {', '.join(mi.get('common_treatments', [])[:2])}"
                )
        
        return " | ".join(summary_parts)
    
    async def classify_interaction(
        self,
        user_id: str,
        message: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Classify interaction type using MCP context
        
        Returns:
            Service type, sub-service, confidence, recommendations
        """
        if not self.initialized:
            await self.initialize()
        
        # Get classification from service provider
        if "service_classification" in self.providers:
            provider = self.providers["service_classification"]
            classification = await provider.classify_interaction(
                user_id, message, conversation_id
            )
            return classification
        
        return {"error": "Service classification provider not available"}
    
    async def get_patient_insights(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive patient insights"""
        if not self.initialized:
            await self.initialize()
        
        insights = {}
        
        # Patient history insights
        if "patient_history" in self.providers:
            provider = self.providers["patient_history"]
            insights["history"] = await provider.get_patient_summary(user_id)
        
        # Medical intelligence insights
        if "medical_intelligence" in self.providers:
            provider = self.providers["medical_intelligence"]
            insights["patterns"] = await provider.analyze_patient_patterns(user_id)
        
        return insights
    
    async def shutdown(self):
        """Cleanup and shutdown"""
        print("🔌 Shutting down MCP Server...")
        for provider in self.providers.values():
            if hasattr(provider, "shutdown"):
                await provider.shutdown()
        print("✅ MCP Server shutdown complete")


# Global MCP server instance
mcp_server = MCPServer()


async def get_mcp_context(
    user_id: str,
    message: str,
    conversation_id: Optional[str] = None,
    context_types: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Helper function to get MCP context"""
    return await mcp_server.get_context(user_id, message, conversation_id, context_types)
