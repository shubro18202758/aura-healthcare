"""
AURA Healthcare - NLP Service for Medical Text Processing
"""

import re
import spacy
from typing import Dict, List, Any, Optional
from transformers import pipeline, AutoTokenizer, AutoModel
import torch
from datetime import datetime
import asyncio

class NLPService:
    """Natural Language Processing service for medical text analysis"""
    
    def __init__(self):
        self.nlp = None
        self.medical_ner = None
        self.sentiment_analyzer = None
        self.medical_qa = None
        self.entity_patterns = {}
        
    async def initialize(self):
        """Initialize NLP models and pipelines"""
        try:
            print("🔄 Initializing NLP Service...")
            
            # Load spaCy model for medical NER
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                print("⚠️ spaCy model not found, using basic tokenization")
                self.nlp = None
            
            # Initialize medical NER pipeline
            self.medical_ner = pipeline(
                "ner",
                model="d4data/biomedical-ner-all",
                tokenizer="d4data/biomedical-ner-all",
                aggregation_strategy="simple"
            )
            
            # Initialize sentiment analysis
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest"
            )
            
            # Initialize medical Q&A
            self.medical_qa = pipeline(
                "question-answering",
                model="deepset/roberta-base-squad2-covid",
                tokenizer="deepset/roberta-base-squad2-covid"
            )
            
            # Define medical entity patterns
            self._init_medical_patterns()
            
            print("✅ NLP Service initialized successfully")
            
        except Exception as e:
            print(f"❌ NLP Service initialization failed: {e}")
            # Initialize with basic functionality
            self._init_fallback_service()
    
    def _init_fallback_service(self):
        """Initialize basic NLP service without heavy models"""
        self.medical_ner = None
        self.sentiment_analyzer = None
        self.medical_qa = None
        print("🔄 Using fallback NLP service")
    
    def _init_medical_patterns(self):
        """Initialize regex patterns for medical entity recognition"""
        self.entity_patterns = {
            "symptoms": [
                r"\b(pain|ache|hurt|sore|tender|burning|throbbing|sharp|dull)\b",
                r"\b(fever|temperature|chills|sweats)\b",
                r"\b(nausea|vomiting|dizzy|dizziness|fatigue|tired|weakness)\b",
                r"\b(headache|migraine|backache|stomachache)\b",
                r"\b(cough|sneez|runny nose|congestion|shortness of breath)\b"
            ],
            "body_parts": [
                r"\b(head|neck|shoulder|arm|elbow|wrist|hand|finger|thumb)\b",
                r"\b(chest|back|spine|stomach|abdomen|hip|leg|knee|ankle|foot|toe)\b",
                r"\b(heart|lung|liver|kidney|brain|eye|ear|nose|throat|mouth)\b"
            ],
            "medications": [
                r"\b(aspirin|ibuprofen|tylenol|acetaminophen|advil|motrin)\b",
                r"\b(antibiotic|penicillin|amoxicillin|prescription|medication|pills|tablets)\b",
                r"\b(insulin|metformin|lisinopril|atorvastatin|omeprazole)\b"
            ],
            "severity": [
                r"\b(mild|moderate|severe|intense|unbearable|excruciating)\b",
                r"\b(slight|little|bit|very|extremely|really|quite)\b",
                r"\b([1-9]|10)\s*(?:out\s*of\s*10|/10)\b"  # Pain scale
            ],
            "duration": [
                r"\b(\d+)\s*(minute|hour|day|week|month|year)s?\b",
                r"\b(since|for|about|approximately|around)\s*(\d+)\s*(minute|hour|day|week|month|year)s?\b",
                r"\b(yesterday|today|last\s*night|this\s*morning|few\s*days)\b"
            ],
            "frequency": [
                r"\b(always|never|sometimes|often|rarely|occasionally)\b",
                r"\b(once|twice|three\s*times|several\s*times)\s*(a\s*)?(day|week|month)\b",
                r"\b(constant|intermittent|periodic|sporadic)\b"
            ]
        }
    
    async def extract_medical_entities(self, text: str) -> Dict[str, List[Dict]]:
        """Extract medical entities from text"""
        entities = {
            "symptoms": [],
            "body_parts": [],
            "medications": [],
            "severity": [],
            "duration": [],
            "frequency": [],
            "conditions": []
        }
        
        try:
            # Use transformer-based NER if available
            if self.medical_ner:
                ner_results = await asyncio.to_thread(self.medical_ner, text)
                for entity in ner_results:
                    entity_type = self._map_entity_type(entity['entity_group'])
                    if entity_type in entities:
                        entities[entity_type].append({
                            "text": entity['word'],
                            "confidence": entity['score'],
                            "start": entity['start'],
                            "end": entity['end']
                        })
            
            # Fallback to regex patterns
            text_lower = text.lower()
            for entity_type, patterns in self.entity_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, text_lower, re.IGNORECASE)
                    for match in matches:
                        entities[entity_type].append({
                            "text": match.group(),
                            "confidence": 0.7,  # Lower confidence for regex
                            "start": match.start(),
                            "end": match.end()
                        })
            
            # Remove duplicates
            for entity_type in entities:
                entities[entity_type] = self._remove_duplicate_entities(entities[entity_type])
            
            return entities
            
        except Exception as e:
            print(f"❌ Entity extraction failed: {e}")
            return entities
    
    def _map_entity_type(self, ner_label: str) -> str:
        """Map NER labels to our entity types"""
        mapping = {
            "DISEASE": "conditions",
            "SYMPTOM": "symptoms",
            "MEDICATION": "medications",
            "BODY_PART": "body_parts",
            "PROCEDURE": "procedures",
            "TEST": "tests"
        }
        return mapping.get(ner_label, "other")
    
    def _remove_duplicate_entities(self, entities: List[Dict]) -> List[Dict]:
        """Remove duplicate entities based on text similarity"""
        if not entities:
            return entities
        
        unique_entities = []
        seen_texts = set()
        
        for entity in entities:
            text_key = entity["text"].lower().strip()
            if text_key not in seen_texts:
                seen_texts.add(text_key)
                unique_entities.append(entity)
        
        return unique_entities
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze emotional sentiment of patient text"""
        try:
            if self.sentiment_analyzer:
                result = await asyncio.to_thread(self.sentiment_analyzer, text)
                return {
                    "label": result[0]["label"],
                    "confidence": result[0]["score"],
                    "emotional_state": self._interpret_medical_sentiment(result[0])
                }
            else:
                # Simple keyword-based sentiment for fallback
                return self._simple_sentiment_analysis(text)
                
        except Exception as e:
            print(f"❌ Sentiment analysis failed: {e}")
            return {"label": "NEUTRAL", "confidence": 0.5, "emotional_state": "uncertain"}
    
    def _interpret_medical_sentiment(self, sentiment_result: Dict) -> str:
        """Interpret sentiment in medical context"""
        label = sentiment_result["label"].upper()
        confidence = sentiment_result["score"]
        
        if label == "NEGATIVE" and confidence > 0.7:
            return "distressed"
        elif label == "NEGATIVE" and confidence > 0.5:
            return "concerned"
        elif label == "POSITIVE" and confidence > 0.7:
            return "optimistic"
        elif label == "POSITIVE" and confidence > 0.5:
            return "hopeful"
        else:
            return "neutral"
    
    def _simple_sentiment_analysis(self, text: str) -> Dict[str, Any]:
        """Simple keyword-based sentiment analysis"""
        positive_words = ["better", "good", "fine", "okay", "improving", "relief"]
        negative_words = ["worse", "bad", "terrible", "awful", "pain", "hurt", "sick"]
        
        text_lower = text.lower()
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if neg_count > pos_count:
            return {"label": "NEGATIVE", "confidence": 0.6, "emotional_state": "concerned"}
        elif pos_count > neg_count:
            return {"label": "POSITIVE", "confidence": 0.6, "emotional_state": "hopeful"}
        else:
            return {"label": "NEUTRAL", "confidence": 0.5, "emotional_state": "neutral"}
    
    async def process_medical_document(self, content: str, document_type: str) -> Dict[str, Any]:
        """Process uploaded medical documents"""
        try:
            # Extract medical entities
            entities = await self.extract_medical_entities(content)
            
            # Generate summary based on document type
            summary = await self._generate_document_summary(content, document_type, entities)
            
            # Extract key dates and values
            dates = self._extract_dates(content)
            values = self._extract_medical_values(content)
            
            return {
                "document_type": document_type,
                "entities": entities,
                "summary": summary,
                "key_dates": dates,
                "medical_values": values,
                "processed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Document processing failed: {e}")
            return {
                "document_type": document_type,
                "error": str(e),
                "raw_content": content[:500] + "..." if len(content) > 500 else content
            }
    
    async def _generate_document_summary(self, content: str, doc_type: str, entities: Dict) -> str:
        """Generate summary of medical document"""
        # Count significant entities
        total_entities = sum(len(v) for v in entities.values())
        
        if doc_type.lower() in ["lab", "laboratory", "blood test"]:
            return f"Laboratory report containing {total_entities} medical entities including test results and values."
        elif doc_type.lower() in ["radiology", "imaging", "x-ray", "mri", "ct"]:
            return f"Imaging report with {total_entities} findings and observations."
        elif doc_type.lower() in ["prescription", "medication"]:
            med_count = len(entities.get("medications", []))
            return f"Prescription document listing {med_count} medications with dosage information."
        else:
            return f"Medical document containing {total_entities} relevant medical entities and information."
    
    def _extract_dates(self, text: str) -> List[Dict[str, str]]:
        """Extract dates from medical documents"""
        date_patterns = [
            r"\b(\d{1,2}/\d{1,2}/\d{4})\b",  # MM/DD/YYYY
            r"\b(\d{1,2}-\d{1,2}-\d{4})\b",  # MM-DD-YYYY
            r"\b(\d{4}-\d{1,2}-\d{1,2})\b",  # YYYY-MM-DD
            r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b"
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                dates.append({
                    "date": match.group(),
                    "position": match.start()
                })
        
        return dates
    
    def _extract_medical_values(self, text: str) -> List[Dict[str, str]]:
        """Extract medical values and measurements"""
        value_patterns = [
            r"\b(\d+\.?\d*)\s*(mg|mcg|g|kg|ml|l|units?|iu)\b",  # Dosages
            r"\b(\d+\.?\d*)\s*(mmhg|bpm|celsius|fahrenheit|%)\b",  # Vital signs
            r"\b(\d+\.?\d*)\s*[-/]\s*(\d+\.?\d*)\b",  # Ratios like blood pressure
            r"\b(\d+\.?\d*)\s*(normal|high|low|elevated|decreased)\b"  # Values with qualifiers
        ]
        
        values = []
        for pattern in value_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                values.append({
                    "value": match.group(),
                    "position": match.start(),
                    "type": "measurement"
                })
        
        return values
    
    async def optimize_question_empathy(self, question: str, specialty: str, patient_context: Dict = None) -> str:
        """Optimize a medical question for empathy and clarity"""
        try:
            # Simple empathy optimization rules
            optimized = question
            
            # Make questions more conversational
            if question.startswith("Do you have"):
                optimized = question.replace("Do you have", "Are you experiencing")
            
            # Add empathetic prefixes for pain-related questions
            pain_keywords = ["pain", "hurt", "ache", "discomfort"]
            if any(keyword in question.lower() for keyword in pain_keywords):
                optimized = f"I understand this might be difficult to discuss. {optimized}"
            
            # Add clarifying context for medical terms
            medical_terms = {
                "dyspnea": "difficulty breathing",
                "myalgia": "muscle pain",
                "cephalgia": "headache",
                "nausea": "feeling sick to your stomach"
            }
            
            for term, explanation in medical_terms.items():
                if term in optimized.lower():
                    optimized = optimized.replace(term, f"{term} ({explanation})")
            
            # Add gentle endings
            if not optimized.endswith("?"):
                optimized += "?"
            
            return optimized
            
        except Exception as e:
            print(f"❌ Question optimization failed: {e}")
            return question
    
    async def detect_urgency(self, text: str, entities: Dict) -> Dict[str, Any]:
        """Detect urgency level in patient responses"""
        urgency_keywords = {
            "high": ["emergency", "urgent", "severe", "unbearable", "chest pain", "difficulty breathing", "blood", "faint"],
            "medium": ["moderate", "worried", "concerned", "getting worse", "several days"],
            "low": ["mild", "slight", "occasional", "manageable"]
        }
        
        text_lower = text.lower()
        urgency_level = "low"
        score = 0
        
        for level, keywords in urgency_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    if level == "high":
                        score += 3
                        urgency_level = "high"
                    elif level == "medium":
                        score += 2
                        if urgency_level != "high":
                            urgency_level = "medium"
                    else:
                        score += 1
        
        # Check for severity indicators in entities
        severity_entities = entities.get("severity", [])
        for entity in severity_entities:
            if any(word in entity["text"].lower() for word in ["severe", "intense", "unbearable"]):
                score += 2
                urgency_level = "high" if score >= 4 else "medium"
        
        return {
            "level": urgency_level,
            "score": score,
            "reasons": [f"Detected {urgency_level} urgency indicators in text"],
            "requires_immediate_attention": score >= 5
        }