"""
Context Engine - Intelligent context aggregation and relevance scoring
"""

from typing import Dict, List, Any, Optional
import re
from datetime import datetime


class ContextEngine:
    """
    Advanced context processing engine
    
    Features:
    - Context relevance scoring
    - Token optimization
    - Priority-based context selection
    - Context summarization
    """
    
    @staticmethod
    def score_relevance(context: Dict[str, Any], query: str) -> float:
        """
        Score context relevance to query
        
        Returns: 0.0 to 1.0 relevance score
        """
        if not context or not query:
            return 0.0
        
        score = 0.0
        query_lower = query.lower()
        
        # Check content fields
        content_fields = ["content", "text", "description", "symptoms", "diagnosis"]
        for field in content_fields:
            if field in context:
                field_value = str(context[field]).lower()
                # Keyword matching
                common_words = set(query_lower.split()) & set(field_value.split())
                score += len(common_words) * 0.1
        
        # Recency boost
        if "timestamp" in context:
            try:
                ts = datetime.fromisoformat(context["timestamp"])
                age_hours = (datetime.now() - ts).total_seconds() / 3600
                if age_hours < 24:
                    score += 0.3
                elif age_hours < 168:  # 1 week
                    score += 0.1
            except:
                pass
        
        # Confidence boost
        if "confidence" in context:
            score += context["confidence"] * 0.2
        
        return min(score, 1.0)
    
    @staticmethod
    def optimize_context(
        contexts: List[Dict[str, Any]],
        max_tokens: int = 2000
    ) -> List[Dict[str, Any]]:
        """
        Select and optimize context to fit token budget
        
        Prioritizes:
        - Higher relevance scores
        - More recent context
        - Critical information (diagnoses, allergies, etc.)
        """
        # Sort by relevance score
        sorted_contexts = sorted(
            contexts,
            key=lambda x: x.get("relevance_score", 0),
            reverse=True
        )
        
        # Estimate tokens (rough: 1 token ~= 4 chars)
        selected = []
        token_count = 0
        
        for context in sorted_contexts:
            context_str = str(context)
            estimated_tokens = len(context_str) // 4
            
            if token_count + estimated_tokens <= max_tokens:
                selected.append(context)
                token_count += estimated_tokens
            else:
                break
        
        return selected
    
    @staticmethod
    def extract_medical_entities(text: str) -> Dict[str, List[str]]:
        """Extract medical entities from text"""
        entities = {
            "symptoms": [],
            "medications": [],
            "conditions": [],
            "body_parts": [],
            "time_references": []
        }
        
        text_lower = text.lower()
        
        # Common symptom patterns
        symptom_patterns = [
            r'\b(pain|ache|fever|cough|nausea|vomiting|dizziness|fatigue|headache)\b',
            r'\b(swelling|rash|itching|bleeding|burning|numbness)\b'
        ]
        for pattern in symptom_patterns:
            matches = re.findall(pattern, text_lower)
            entities["symptoms"].extend(matches)
        
        # Time references
        time_patterns = [
            r'\b(\d+)\s*(day|week|month|year)s?\s*ago\b',
            r'\b(today|yesterday|last\s+\w+|this\s+\w+)\b'
        ]
        for pattern in time_patterns:
            matches = re.findall(pattern, text_lower)
            entities["time_references"].extend([" ".join(m) if isinstance(m, tuple) else m for m in matches])
        
        # Body parts
        body_parts = [
            "head", "chest", "stomach", "abdomen", "back", "leg", "arm", 
            "hand", "foot", "eye", "ear", "throat", "heart", "lung"
        ]
        for part in body_parts:
            if part in text_lower:
                entities["body_parts"].append(part)
        
        # Remove duplicates
        for key in entities:
            entities[key] = list(set(entities[key]))
        
        return entities
    
    @staticmethod
    def summarize_conversation_history(
        conversations: List[Dict[str, Any]],
        max_length: int = 500
    ) -> str:
        """Create concise summary of conversation history"""
        if not conversations:
            return "No previous conversations"
        
        summary_parts = []
        
        # Get recent conversations (last 5)
        recent = conversations[-5:] if len(conversations) > 5 else conversations
        
        for conv in recent:
            if "created_at" in conv:
                date = conv["created_at"][:10] if isinstance(conv["created_at"], str) else str(conv["created_at"])[:10]
            else:
                date = "Unknown date"
            
            topic = conv.get("topic", "General consultation")
            summary_parts.append(f"{date}: {topic}")
        
        summary = " | ".join(summary_parts)
        
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."
        
        return summary
    
    @staticmethod
    def merge_contexts(contexts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge multiple contexts into one"""
        merged = {
            "sources": [],
            "combined_score": 0.0,
            "entities": {
                "symptoms": set(),
                "medications": set(),
                "conditions": set()
            }
        }
        
        for context in contexts:
            merged["sources"].append(context.get("source", "unknown"))
            merged["combined_score"] += context.get("relevance_score", 0)
            
            # Merge entities
            if "entities" in context:
                for entity_type, values in context["entities"].items():
                    if entity_type in merged["entities"]:
                        if isinstance(values, list):
                            merged["entities"][entity_type].update(values)
                        else:
                            merged["entities"][entity_type].add(values)
        
        # Convert sets to lists
        for key in merged["entities"]:
            merged["entities"][key] = list(merged["entities"][key])
        
        # Average score
        if contexts:
            merged["combined_score"] /= len(contexts)
        
        return merged
