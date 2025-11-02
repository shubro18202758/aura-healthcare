"""
Reports Router for AURA Healthcare System
Handles medical report generation, viewing, and management
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel
from io import BytesIO
import json

from app.config import get_settings
from app.database import get_database
from app.models import User, Role
from app.models.report import MedicalReport, ReportType, ReportStatus
from app.routers.auth import get_current_active_user, require_role

router = APIRouter(prefix="/api/reports", tags=["reports"])
settings = get_settings()

# Request/Response Models
class GenerateReportRequest(BaseModel):
    conversation_id: str
    report_type: ReportType = ReportType.CONSULTATION
    notes: Optional[str] = None

# Routes
async def generate_ai_medical_report(conversation_id: str, messages: List[dict], documents: List[dict], patient_info: dict) -> dict:
    """
    Generate comprehensive AI medical report
    
    Analyzes:
    - Conversation history
    - Uploaded medical documents
    - Patient information
    - Symptoms and findings
    """
    from app.services.ai_service import get_ai_service
    
    ai_service = get_ai_service()
    
    # Build comprehensive prompt
    conversation_text = "\n".join([
        f"{'Patient' if msg['sender'] == 'patient' else 'AI Assistant'}: {msg['content']}"
        for msg in messages
    ])
    
    document_summary = "\n".join([
        f"- {doc['document_type']}: {doc['file_name']} (uploaded {doc['uploaded_at']})"
        for doc in documents
    ])
    
    prompt = f"""
As a medical AI assistant, analyze the following comprehensive patient data and generate a detailed medical report.

**PATIENT INFORMATION:**
- Patient ID: {patient_info.get('patient_id', 'N/A')}
- Name: {patient_info.get('full_name', 'N/A')}
- Medical Specialty: {patient_info.get('specialty', 'General')}

**CONVERSATION HISTORY:**
{conversation_text}

**UPLOADED MEDICAL DOCUMENTS:**
{document_summary if documents else 'No documents uploaded'}

**GENERATE A COMPREHENSIVE MEDICAL REPORT WITH THE FOLLOWING SECTIONS:**

1. **CHIEF COMPLAINT & HISTORY OF PRESENT ILLNESS:**
   - Primary reason for consultation
   - Timeline of symptoms
   - Severity and progression

2. **SYMPTOMS ANALYSIS:**
   - List all reported symptoms
   - Duration and frequency
   - Associated factors

3. **MEDICAL HISTORY & DOCUMENTS:**
   - Review of uploaded test results
   - Previous diagnoses mentioned
   - Current medications (if any)

4. **CLINICAL ASSESSMENT:**
   - Key findings from conversation
   - Risk factors identified
   - Areas of concern

5. **PRELIMINARY DIAGNOSIS:**
   - Most likely conditions
   - Differential diagnoses
   - Confidence level

6. **RECOMMENDATIONS:**
   - Suggested tests or examinations
   - Lifestyle modifications
   - Follow-up requirements
   - Urgency level (routine, urgent, emergency)

7. **DOCTOR'S REVIEW NOTES:**
   - Areas requiring doctor's attention
   - Questions for follow-up
   - Document verification needed

Format the report in clear, professional medical language. Be thorough but concise.
"""
    
    try:
        ai_response = await ai_service.generate_response(prompt)
        
        return {
            "full_report": ai_response,
            "generated_by": "AI with human review required",
            "confidence": "high" if len(messages) > 10 and documents else "medium"
        }
    except Exception as e:
        return {
            "full_report": f"Error generating AI report: {str(e)}. Manual review required.",
            "generated_by": "System",
            "confidence": "low"
        }

@router.post("/generate", response_model=MedicalReport)
async def generate_report(
    request: GenerateReportRequest,
    current_user: User = Depends(require_role(Role.DOCTOR))
):
    """
    Generate comprehensive AI-powered medical report
    
    - Analyzes conversation history
    - Reviews uploaded medical documents
    - Extracts symptoms, findings, diagnosis
    - Creates structured medical report with AI assistance
    - Requires doctor review and approval
    """
    db = await get_database()
    
    # Get conversation
    conv = await db.conversations.find_one({
        "conversation_id": request.conversation_id
    })
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Get messages
    messages = await db.messages.find({
        "conversation_id": request.conversation_id
    }).sort("timestamp", 1).to_list(None)
    
    # Get uploaded medical documents
    documents = await db.medical_documents.find({
        "conversation_id": request.conversation_id,
        "is_active": True
    }).to_list(None)
    
    # Get patient information
    patient_info = await db.users.find_one({
        "user_id": conv["patient_id"]
    })
    
    # Generate AI report
    ai_report = await generate_ai_medical_report(
        request.conversation_id,
        messages,
        documents,
        patient_info or {}
    )
    
    # Create comprehensive report
    report = MedicalReport(
        report_id=f"report_{datetime.utcnow().timestamp()}",
        patient_id=conv["patient_id"],
        doctor_id=current_user.user_id,
        conversation_id=request.conversation_id,
        report_type=request.report_type,
        generated_at=datetime.utcnow(),
        status=ReportStatus.DRAFT,
        summary=ai_report["full_report"][:500] + "..." if len(ai_report["full_report"]) > 500 else ai_report["full_report"],
        findings=ai_report["full_report"],
        doctor_notes=request.notes,
        metadata={
            "total_messages": len(messages),
            "total_documents": len(documents),
            "document_types": list(set([doc["document_type"] for doc in documents])),
            "ai_confidence": ai_report["confidence"],
            "generated_by": ai_report["generated_by"]
        }
    )
    
    await db.reports.insert_one(report.dict())
    return report

@router.get("/{report_id}", response_model=MedicalReport)
async def get_report(
    report_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get medical report by ID"""
    db = await get_database()
    
    report_data = await db.reports.find_one({"report_id": report_id})
    if not report_data:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report = MedicalReport(**report_data)
    
    # Check permissions
    if current_user.role == Role.PATIENT:
        if report.patient_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Cannot access another patient's report")
    
    return report

@router.get("/", response_model=List[MedicalReport])
async def list_reports(
    patient_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user)
):
    """List medical reports"""
    db = await get_database()
    
    query = {}
    if current_user.role == Role.PATIENT:
        query["patient_id"] = current_user.user_id
    elif current_user.role == Role.DOCTOR:
        if not patient_id:
            query["doctor_id"] = current_user.user_id
        else:
            query["patient_id"] = patient_id
    elif patient_id:
        query["patient_id"] = patient_id
    
    if status:
        query["status"] = status
    
    reports_data = await db.reports.find(query).sort(
        "generated_at", -1
    ).limit(limit).to_list(None)
    
    return [MedicalReport(**r) for r in reports_data]

@router.put("/{report_id}/finalize", response_model=MedicalReport)
async def finalize_report(
    report_id: str,
    current_user: User = Depends(require_role(Role.DOCTOR))
):
    """Finalize and sign medical report"""
    db = await get_database()
    
    await db.reports.update_one(
        {"report_id": report_id, "doctor_id": current_user.user_id},
        {
            "$set": {
                "status": ReportStatus.FINALIZED,
                "finalized_at": datetime.utcnow()
            }
        }
    )
    
    report_data = await db.reports.find_one({"report_id": report_id})
    if not report_data:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return MedicalReport(**report_data)

@router.get("/{report_id}/export")
async def export_report(
    report_id: str,
    format: str = "pdf",  # pdf, docx, txt, json, html
    current_user: User = Depends(get_current_active_user)
):
    """
    Export medical report in various formats
    
    Supported formats:
    - pdf: PDF document (professional medical report)
    - docx: Microsoft Word document
    - txt: Plain text file
    - json: JSON format (structured data)
    - html: HTML document (web-friendly)
    """
    db = await get_database()
    
    report_data = await db.reports.find_one({"report_id": report_id})
    if not report_data:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report = MedicalReport(**report_data)
    
    # Check permissions
    if current_user.role == Role.PATIENT:
        if report.patient_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Cannot access another patient's report")
    
    # Get patient and doctor details
    patient_data = await db.users.find_one({"user_id": report.patient_id})
    doctor_data = await db.users.find_one({"user_id": report.doctor_id})
    
    patient_name = patient_data.get("full_name", "Unknown Patient") if patient_data else "Unknown Patient"
    doctor_name = doctor_data.get("full_name", "Unknown Doctor") if doctor_data else "Unknown Doctor"
    
    # Format filename
    safe_patient_name = patient_name.replace(" ", "_")
    timestamp = datetime.utcnow().strftime("%Y%m%d")
    filename = f"medical_report_{safe_patient_name}_{timestamp}"
    
    if format.lower() == "json":
        # JSON format - structured data
        json_data = {
            "report_id": report.report_id,
            "patient": {
                "id": report.patient_id,
                "name": patient_name
            },
            "doctor": {
                "id": report.doctor_id,
                "name": doctor_name
            },
            "generated_at": report.generated_at.isoformat(),
            "status": report.status,
            "type": report.report_type,
            "summary": report.summary,
            "findings": report.findings,
            "doctor_notes": report.doctor_notes,
            "metadata": report.metadata
        }
        
        return Response(
            content=json.dumps(json_data, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}.json"}
        )
    
    elif format.lower() == "txt":
        # Plain text format
        txt_content = f"""
AURA HEALTHCARE SYSTEM
MEDICAL REPORT

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PATIENT INFORMATION:
Name: {patient_name}
Patient ID: {report.patient_id}

DOCTOR INFORMATION:
Name: {doctor_name}
Doctor ID: {report.doctor_id}

REPORT DETAILS:
Report ID: {report.report_id}
Report Type: {report.report_type}
Generated: {report.generated_at.strftime("%B %d, %Y at %I:%M %p")}
Status: {report.status}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SUMMARY:
{report.summary}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DETAILED FINDINGS:
{report.findings}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DOCTOR'S NOTES:
{report.doctor_notes or "No additional notes"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

METADATA:
- Total Messages Analyzed: {report.metadata.get('total_messages', 'N/A')}
- Documents Reviewed: {report.metadata.get('total_documents', 'N/A')}
- AI Confidence: {report.metadata.get('ai_confidence', 'N/A')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This report was generated by AURA Healthcare System
© 2025 AURA Healthcare. All rights reserved.
"""
        
        return Response(
            content=txt_content.strip(),
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename={filename}.txt"}
        )
    
    elif format.lower() == "html":
        # HTML format - web-friendly
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Medical Report - {patient_name}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .container {{
            background: white;
            border-radius: 12px;
            padding: 40px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        .header {{
            border-bottom: 3px solid #667eea;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #667eea;
            margin: 0 0 10px 0;
            font-size: 32px;
        }}
        .header p {{
            color: #666;
            margin: 5px 0;
        }}
        .section {{
            margin: 30px 0;
        }}
        .section-title {{
            color: #667eea;
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin: 20px 0;
        }}
        .info-item {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
        }}
        .info-label {{
            font-weight: 600;
            color: #495057;
            font-size: 14px;
            margin-bottom: 5px;
        }}
        .info-value {{
            color: #212529;
            font-size: 16px;
        }}
        .content {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            white-space: pre-wrap;
            line-height: 1.8;
        }}
        .status {{
            display: inline-block;
            padding: 6px 16px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 14px;
        }}
        .status.draft {{
            background: #fff3cd;
            color: #856404;
        }}
        .status.finalized {{
            background: #d4edda;
            color: #155724;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #f0f0f0;
            text-align: center;
            color: #6c757d;
            font-size: 14px;
        }}
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            .container {{
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏥 AURA Healthcare System</h1>
            <p style="font-size: 18px; color: #667eea; font-weight: 600;">Medical Report</p>
            <p style="color: #999;">Report ID: {report.report_id}</p>
        </div>

        <div class="section">
            <div class="section-title">📋 Report Information</div>
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">Patient Name</div>
                    <div class="info-value">{patient_name}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Doctor Name</div>
                    <div class="info-value">{doctor_name}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Generated Date</div>
                    <div class="info-value">{report.generated_at.strftime("%B %d, %Y at %I:%M %p")}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Report Status</div>
                    <div class="info-value">
                        <span class="status {'finalized' if report.status == 'FINALIZED' else 'draft'}">{report.status}</span>
                    </div>
                </div>
            </div>
        </div>

        <div class="section">
            <div class="section-title">📝 Summary</div>
            <div class="content">{report.summary}</div>
        </div>

        <div class="section">
            <div class="section-title">🔍 Detailed Findings</div>
            <div class="content">{report.findings}</div>
        </div>

        {f'''
        <div class="section">
            <div class="section-title">💬 Doctor's Notes</div>
            <div class="content">{report.doctor_notes}</div>
        </div>
        ''' if report.doctor_notes else ''}

        <div class="section">
            <div class="section-title">📊 Report Metadata</div>
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">Messages Analyzed</div>
                    <div class="info-value">{report.metadata.get('total_messages', 'N/A')}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Documents Reviewed</div>
                    <div class="info-value">{report.metadata.get('total_documents', 'N/A')}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">AI Confidence</div>
                    <div class="info-value">{report.metadata.get('ai_confidence', 'N/A').upper()}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Report Type</div>
                    <div class="info-value">{report.report_type}</div>
                </div>
            </div>
        </div>

        <div class="footer">
            <p><strong>AURA Healthcare System</strong></p>
            <p>© 2025 AURA Healthcare. All rights reserved.</p>
            <p style="margin-top: 10px; font-size: 12px;">
                This report is confidential and intended solely for medical purposes.
            </p>
        </div>
    </div>
</body>
</html>
"""
        
        return Response(
            content=html_content.strip(),
            media_type="text/html",
            headers={"Content-Disposition": f"attachment; filename={filename}.html"}
        )
    
    elif format.lower() == "pdf":
        # PDF format - would need reportlab or similar library
        # For now, return HTML that can be printed to PDF
        raise HTTPException(
            status_code=501,
            detail="PDF export coming soon. Please use HTML format and print to PDF, or use TXT/JSON formats."
        )
    
    elif format.lower() == "docx":
        # DOCX format - would need python-docx library
        raise HTTPException(
            status_code=501,
            detail="DOCX export coming soon. Please use HTML or TXT formats for now."
        )
    
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: {format}. Supported formats: pdf, docx, txt, json, html"
        )

@router.post("/auto-generate/{conversation_id}")
async def auto_generate_report(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Automatically generate report when conversation reaches certain criteria
    
    Triggered when:
    - Conversation has sufficient messages (>5)
    - Medical documents are uploaded
    - No existing draft report exists
    """
    db = await get_database()
    
    # Check if report already exists
    existing = await db.reports.find_one({
        "conversation_id": conversation_id,
        "status": {"$in": ["DRAFT", "FINALIZED"]}
    })
    
    if existing:
        return {
            "message": "Report already exists",
            "report_id": existing["report_id"],
            "status": existing["status"]
        }
    
    # Get conversation
    conv = await db.conversations.find_one({"conversation_id": conversation_id})
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Count messages
    message_count = await db.messages.count_documents({"conversation_id": conversation_id})
    
    if message_count < 5:
        return {
            "message": "Not enough messages for report generation",
            "required": 5,
            "current": message_count
        }
    
    # Auto-generate report
    # Find or assign a doctor (for demo purposes, use current user if doctor, otherwise find any doctor)
    doctor_id = current_user.user_id if current_user.role == Role.DOCTOR else "system_auto_gen"
    
    # Get messages
    messages = await db.messages.find({
        "conversation_id": conversation_id
    }).sort("timestamp", 1).to_list(None)
    
    # Get documents
    documents = await db.medical_documents.find({
        "conversation_id": conversation_id,
        "is_active": True
    }).to_list(None)
    
    # Get patient info
    patient_info = await db.users.find_one({"user_id": conv["patient_id"]})
    
    # Generate AI report
    ai_report = await generate_ai_medical_report(
        conversation_id,
        messages,
        documents,
        patient_info or {}
    )
    
    # Create report
    report = MedicalReport(
        report_id=f"report_{datetime.utcnow().timestamp()}",
        patient_id=conv["patient_id"],
        doctor_id=doctor_id,
        conversation_id=conversation_id,
        report_type=ReportType.CONSULTATION,
        generated_at=datetime.utcnow(),
        status=ReportStatus.DRAFT,
        summary=ai_report["full_report"][:500] + "..." if len(ai_report["full_report"]) > 500 else ai_report["full_report"],
        findings=ai_report["full_report"],
        doctor_notes="Auto-generated report - requires doctor review",
        metadata={
            "total_messages": len(messages),
            "total_documents": len(documents),
            "document_types": list(set([doc["document_type"] for doc in documents])) if documents else [],
            "ai_confidence": ai_report["confidence"],
            "generated_by": "Auto-generation system",
            "auto_generated": True
        }
    )
    
    await db.reports.insert_one(report.dict())
    
    return {
        "message": "Report auto-generated successfully",
        "report_id": report.report_id,
        "status": report.status,
        "requires_review": True
    }


# ============================================================================
# REPORT ANALYSIS ENDPOINTS (Doctor AI Assistant)
# ============================================================================

class ReportQueryRequest(BaseModel):
    """Request model for querying a report"""
    query: str
    context: Optional[str] = None

class ReportSummaryRequest(BaseModel):
    """Request model for report summaries"""
    summary_type: str = "brief"  # brief, detailed, key_findings, urgent, differential, recommendations

class CompareReportsRequest(BaseModel):
    """Request model for comparing reports"""
    report_id_1: str
    report_id_2: str
    focus_areas: Optional[List[str]] = None

@router.post("/analyze/{report_id}")
async def analyze_report(
    report_id: str,
    request: ReportQueryRequest,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """
    AI-powered report analysis for doctors
    Allows doctors to ask questions about a specific medical report
    
    Examples:
    - "What are the main symptoms?"
    - "Are there any urgent findings?"
    - "Summarize the key points"
    - "What tests were recommended?"
    """
    from app.services.report_analysis_service import get_report_analysis_service
    
    # Only doctors can use report analysis
    if current_user.role != Role.DOCTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can analyze reports"
        )
    
    # Get the report
    report = await db.reports.find_one({"report_id": report_id})
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    # Get patient info for context
    patient = await db.users.find_one({"user_id": report["patient_id"]})
    patient_info = {
        "name": patient.get("full_name", "Unknown"),
        "email": patient.get("email", "Unknown")
    }
    
    # Prepare report data
    report_data = {
        **report,
        "patient": patient_info
    }
    
    # Analyze using AI
    analysis_service = get_report_analysis_service()
    response = await analysis_service.analyze_report(
        report_data=report_data,
        query=request.query,
        context=request.context
    )
    
    return {
        "report_id": report_id,
        "query": request.query,
        "response": response,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/summarize/{report_id}")
async def summarize_report(
    report_id: str,
    request: ReportSummaryRequest,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """
    Generate different types of summaries for a medical report
    
    Summary types:
    - brief: 3-4 sentence executive summary
    - detailed: Comprehensive summary
    - key_findings: Top findings in bullet points
    - urgent: Urgent/concerning findings only
    - differential: Differential diagnoses summary
    - recommendations: All recommendations and follow-ups
    """
    from app.services.report_analysis_service import get_report_analysis_service
    
    # Only doctors can summarize reports
    if current_user.role != Role.DOCTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can summarize reports"
        )
    
    # Get the report
    report = await db.reports.find_one({"report_id": report_id})
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    # Generate summary
    analysis_service = get_report_analysis_service()
    summary = await analysis_service.summarize_report(
        report_data=report,
        summary_type=request.summary_type
    )
    
    return {
        "report_id": report_id,
        "summary_type": request.summary_type,
        "summary": summary,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/compare")
async def compare_reports(
    request: CompareReportsRequest,
    current_user: User = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """
    Compare two medical reports and identify changes
    Useful for tracking patient progress over time
    """
    from app.services.report_analysis_service import get_report_analysis_service
    
    # Only doctors can compare reports
    if current_user.role != Role.DOCTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can compare reports"
        )
    
    # Get both reports
    report1 = await db.reports.find_one({"report_id": request.report_id_1})
    report2 = await db.reports.find_one({"report_id": request.report_id_2})
    
    if not report1 or not report2:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both reports not found"
        )
    
    # Ensure both reports are for the same patient
    if report1["patient_id"] != report2["patient_id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot compare reports from different patients"
        )
    
    # Compare reports
    analysis_service = get_report_analysis_service()
    comparison = await analysis_service.compare_reports(
        report1=report1,
        report2=report2,
        focus_areas=request.focus_areas
    )
    
    return {
        "report_id_1": request.report_id_1,
        "report_id_2": request.report_id_2,
        "comparison": comparison,
        "timestamp": datetime.utcnow().isoformat()
    }
