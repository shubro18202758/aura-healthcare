"""
Report Analysis Service for Doctor Queries
Uses dedicated Google Gemini API (loop2) for analyzing and summarizing medical reports
"""

import os
import google.generativeai as genai
from typing import Dict, List, Optional
from app.config import get_settings

settings = get_settings()

class ReportAnalysisService:
    """Service for AI-powered report analysis and queries"""
    
    def __init__(self):
        """Initialize the report analysis service with dedicated API key"""
        api_key = os.getenv("GOOGLE_REPORTS_API_KEY") or settings.GOOGLE_REPORTS_API_KEY
        model_name = os.getenv("GOOGLE_REPORTS_MODEL") or settings.GOOGLE_REPORTS_MODEL
        
        if not api_key:
            raise ValueError("GOOGLE_REPORTS_API_KEY not configured")
        
        # Configure Gemini with dedicated API key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.model_name = model_name
        print(f"✅ Report Analysis Service initialized (model: {model_name})")
    
    async def analyze_report(
        self,
        report_data: Dict,
        query: str,
        context: Optional[str] = None
    ) -> str:
        """
        Analyze a medical report and answer doctor's query
        
        Args:
            report_data: The complete medical report data
            query: Doctor's question about the report
            context: Additional context (e.g., patient history)
        
        Returns:
            AI-generated response to the query
        """
        
        # Build comprehensive context
        report_context = f"""
**MEDICAL REPORT ANALYSIS**

**Report ID:** {report_data.get('report_id', 'N/A')}
**Status:** {report_data.get('status', 'N/A')}
**Generated:** {report_data.get('generated_at', 'N/A')}
**Report Type:** {report_data.get('report_type', 'N/A')}

**PATIENT INFORMATION:**
- Patient ID: {report_data.get('patient_id', 'N/A')}
- Name: {report_data.get('patient', {}).get('name', 'N/A')}

**REPORT SUMMARY:**
{report_data.get('summary', 'No summary available')}

**DETAILED FINDINGS:**
{report_data.get('detailed_findings', 'No detailed findings available')}

**DOCTOR'S NOTES:**
{report_data.get('doctor_notes', 'No doctor notes available')}

**METADATA:**
- Messages Analyzed: {report_data.get('metadata', {}).get('messages_count', 0)}
- Documents Reviewed: {report_data.get('metadata', {}).get('documents_count', 0)}
- AI Confidence: {report_data.get('metadata', {}).get('confidence_score', 'N/A')}
- Generation Method: {report_data.get('metadata', {}).get('generated_by', 'N/A')}
"""
        
        if context:
            report_context += f"\n\n**ADDITIONAL CONTEXT:**\n{context}"
        
        # Build the prompt for AI
        prompt = f"""
You are a medical AI assistant helping a doctor analyze a patient's medical report.

{report_context}

**DOCTOR'S QUERY:**
{query}

**INSTRUCTIONS:**
1. Provide a concise, professional response to the doctor's query
2. Reference specific sections of the report when relevant
3. If asking about symptoms, findings, or diagnoses, extract the exact information
4. If the report doesn't contain the requested information, clearly state that
5. Use medical terminology appropriately
6. Be precise and factual - this is for clinical decision-making
7. If asked to summarize, focus on key clinical points
8. Highlight any urgent or concerning findings

**RESPONSE:**
"""
        
        try:
            # Generate response using Gemini
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Error in report analysis: {str(e)}")
            return f"I apologize, but I encountered an error analyzing the report: {str(e)}"
    
    async def summarize_report(
        self,
        report_data: Dict,
        summary_type: str = "brief"
    ) -> str:
        """
        Generate different types of summaries for a medical report
        
        Args:
            report_data: The complete medical report data
            summary_type: Type of summary (brief, detailed, key_findings, urgent)
        
        Returns:
            Formatted summary
        """
        
        summary_prompts = {
            "brief": "Provide a 3-4 sentence executive summary highlighting the most critical information.",
            "detailed": "Provide a comprehensive summary covering all major sections of the report.",
            "key_findings": "List the top 5-7 key clinical findings in bullet points.",
            "urgent": "Identify any urgent or concerning findings that require immediate attention. If none, state that clearly.",
            "differential": "Summarize the differential diagnoses and their likelihood based on the findings.",
            "recommendations": "Summarize all recommendations, tests suggested, and follow-up requirements."
        }
        
        prompt_instruction = summary_prompts.get(
            summary_type,
            "Provide a general summary of the report."
        )
        
        report_context = f"""
**MEDICAL REPORT**

**Summary:** {report_data.get('summary', 'N/A')}

**Detailed Findings:** {report_data.get('detailed_findings', 'N/A')}

**Doctor's Notes:** {report_data.get('doctor_notes', 'N/A')}

**Metadata:**
- Messages: {report_data.get('metadata', {}).get('messages_count', 0)}
- Documents: {report_data.get('metadata', {}).get('documents_count', 0)}
- Confidence: {report_data.get('metadata', {}).get('confidence_score', 'N/A')}
"""
        
        prompt = f"""
You are a medical AI assistant summarizing a patient's medical report for a doctor.

{report_context}

**TASK:** {prompt_instruction}

**FORMAT:** Use clear, professional medical language with appropriate structure.

**SUMMARY:**
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Error generating summary: {str(e)}")
            return f"Error generating summary: {str(e)}"
    
    async def compare_reports(
        self,
        report1: Dict,
        report2: Dict,
        focus_areas: Optional[List[str]] = None
    ) -> str:
        """
        Compare two medical reports and highlight changes/differences
        
        Args:
            report1: First report (typically older)
            report2: Second report (typically newer)
            focus_areas: Specific areas to focus on (e.g., ['symptoms', 'medications'])
        
        Returns:
            Comparison analysis
        """
        
        focus_instruction = ""
        if focus_areas:
            focus_instruction = f"\nFocus particularly on: {', '.join(focus_areas)}"
        
        prompt = f"""
You are a medical AI assistant helping a doctor compare two medical reports for the same patient.

**REPORT 1 (Earlier):**
Generated: {report1.get('generated_at', 'N/A')}
Summary: {report1.get('summary', 'N/A')}
Findings: {report1.get('detailed_findings', 'N/A')}

**REPORT 2 (Later):**
Generated: {report2.get('generated_at', 'N/A')}
Summary: {report2.get('summary', 'N/A')}
Findings: {report2.get('detailed_findings', 'N/A')}

**TASK:** Compare these reports and identify:
1. Changes in symptoms or conditions
2. Progression or improvement
3. New findings or concerns
4. Changes in recommendations
{focus_instruction}

**COMPARISON:**
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Error comparing reports: {str(e)}")
            return f"Error comparing reports: {str(e)}"

# Singleton instance
_report_analysis_service = None

def get_report_analysis_service() -> ReportAnalysisService:
    """Get or create the report analysis service singleton"""
    global _report_analysis_service
    if _report_analysis_service is None:
        _report_analysis_service = ReportAnalysisService()
    return _report_analysis_service
