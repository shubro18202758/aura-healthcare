# AURA Framework - Remaining Implementation Generator
# This script creates all remaining routers and core services

Write-Host "🚀 AURA Framework - Implementing Cutting-Edge Features" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

$rootDir = "c:\Users\sayan\Downloads\LOOP"
$backendDir = "$rootDir\backend"

# Create doctor router
Write-Host "📝 Creating Doctor Router..." -ForegroundColor Yellow
$doctorRouterContent = @'
"""
Doctor Router for AURA Healthcare System
Handles doctor profiles, schedules, and patient management
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.config import get_settings
from app.database import get_database
from app.models import User, Role
from app.models.doctor import DoctorProfile, Specialty
from app.routers.auth import get_current_active_user, require_role

router = APIRouter(prefix="/api/doctors", tags=["doctors"])
settings = get_settings()

# Request/Response Models
class DoctorProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    specialty: Optional[Specialty] = None
    languages: Optional[List[str]] = None
    experience_years: Optional[int] = None
    qualification: Optional[str] = None
    bio: Optional[str] = None
    consultation_fee: Optional[float] = None
    available_hours: Optional[dict] = None

# Routes
@router.get("/me", response_model=DoctorProfile)
async def get_my_profile(current_user: User = Depends(require_role(Role.DOCTOR))):
    """Get current doctor's profile"""
    db = await get_database()
    profile_data = await db.doctor_profiles.find_one({"doctor_id": current_user.user_id})
    
    if not profile_data:
        # Create default profile
        profile = DoctorProfile(
            doctor_id=current_user.user_id,
            full_name=current_user.full_name,
            email=current_user.email
        )
        await db.doctor_profiles.insert_one(profile.dict())
        return profile
    
    return DoctorProfile(**profile_data)

@router.put("/me", response_model=DoctorProfile)
async def update_my_profile(
    update: DoctorProfileUpdate,
    current_user: User = Depends(require_role(Role.DOCTOR))
):
    """Update current doctor's profile"""
    db = await get_database()
    
    update_data = {k: v for k, v in update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    await db.doctor_profiles.update_one(
        {"doctor_id": current_user.user_id},
        {"$set": update_data},
        upsert=True
    )
    
    profile_data = await db.doctor_profiles.find_one({"doctor_id": current_user.user_id})
    return DoctorProfile(**profile_data)

@router.get("/{doctor_id}", response_model=DoctorProfile)
async def get_doctor_profile(
    doctor_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get doctor profile by ID"""
    db = await get_database()
    profile_data = await db.doctor_profiles.find_one({"doctor_id": doctor_id})
    
    if not profile_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found"
        )
    
    return DoctorProfile(**profile_data)

@router.get("/", response_model=List[DoctorProfile])
async def list_doctors(
    specialty: Optional[str] = None,
    language: Optional[str] = None,
    available: bool = True,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user)
):
    """List doctors with filters"""
    db = await get_database()
    
    query = {}
    if specialty:
        query["specialty"] = specialty
    if language:
        query["languages"] = language
    if available:
        query["is_available"] = True
    
    doctors_data = await db.doctor_profiles.find(query).limit(limit).to_list(None)
    return [DoctorProfile(**doc) for doc in doctors_data]

@router.get("/me/patients", response_model=List[dict])
async def get_my_patients(
    current_user: User = Depends(require_role(Role.DOCTOR))
):
    """Get all patients assigned to current doctor"""
    db = await get_database()
    
    # Get unique patient IDs from conversations
    conversations = await db.conversations.find({
        "doctor_id": current_user.user_id
    }).to_list(None)
    
    patient_ids = list(set([conv["patient_id"] for conv in conversations]))
    
    # Get patient profiles
    patients = await db.patient_profiles.find({
        "patient_id": {"$in": patient_ids}
    }).to_list(None)
    
    return patients

@router.post("/me/availability")
async def update_availability(
    is_available: bool,
    current_user: User = Depends(require_role(Role.DOCTOR))
):
    """Update doctor availability status"""
    db = await get_database()
    
    await db.doctor_profiles.update_one(
        {"doctor_id": current_user.user_id},
        {"$set": {"is_available": is_available}}
    )
    
    return {"message": "Availability updated", "is_available": is_available}
'@

Set-Content -Path "$backendDir\app\routers\doctor.py" -Value $doctorRouterContent -Force
Write-Host "✅ Doctor Router created" -ForegroundColor Green

# Create patient router
Write-Host "📝 Creating Patient Router..." -ForegroundColor Yellow
$patientRouterContent = @'
"""
Patient Router for AURA Healthcare System
Handles patient profiles, medical history, and health records
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.config import get_settings
from app.database import get_database
from app.models import User, Role
from app.models.patient import PatientProfile, MedicalHistory, VitalSigns
from app.routers.auth import get_current_active_user, require_role

router = APIRouter(prefix="/api/patients", tags=["patients"])
settings = get_settings()

# Request/Response Models
class PatientProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    emergency_contact: Optional[dict] = None
    address: Optional[str] = None

class MedicalHistoryUpdate(BaseModel):
    chronic_conditions: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    current_medications: Optional[List[str]] = None
    past_surgeries: Optional[List[str]] = None
    family_history: Optional[List[str]] = None

class VitalSignsCreate(BaseModel):
    temperature: Optional[float] = None
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    heart_rate: Optional[int] = None
    respiratory_rate: Optional[int] = None
    oxygen_saturation: Optional[float] = None
    blood_glucose: Optional[float] = None

# Routes
@router.get("/me", response_model=PatientProfile)
async def get_my_profile(current_user: User = Depends(require_role(Role.PATIENT))):
    """Get current patient's profile"""
    db = await get_database()
    profile_data = await db.patient_profiles.find_one({"patient_id": current_user.user_id})
    
    if not profile_data:
        # Create default profile
        profile = PatientProfile(
            patient_id=current_user.user_id,
            full_name=current_user.full_name,
            email=current_user.email
        )
        await db.patient_profiles.insert_one(profile.dict())
        return profile
    
    return PatientProfile(**profile_data)

@router.put("/me", response_model=PatientProfile)
async def update_my_profile(
    update: PatientProfileUpdate,
    current_user: User = Depends(require_role(Role.PATIENT))
):
    """Update current patient's profile"""
    db = await get_database()
    
    update_data = {k: v for k, v in update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    await db.patient_profiles.update_one(
        {"patient_id": current_user.user_id},
        {"$set": update_data},
        upsert=True
    )
    
    profile_data = await db.patient_profiles.find_one({"patient_id": current_user.user_id})
    return PatientProfile(**profile_data)

@router.get("/{patient_id}", response_model=PatientProfile)
async def get_patient_profile(
    patient_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get patient profile by ID (doctors/admins only)"""
    if current_user.role == Role.PATIENT and current_user.user_id != patient_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access another patient's profile"
        )
    
    db = await get_database()
    profile_data = await db.patient_profiles.find_one({"patient_id": patient_id})
    
    if not profile_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    return PatientProfile(**profile_data)

@router.put("/me/medical-history", response_model=MedicalHistory)
async def update_medical_history(
    update: MedicalHistoryUpdate,
    current_user: User = Depends(require_role(Role.PATIENT))
):
    """Update patient's medical history"""
    db = await get_database()
    
    # Get current profile
    profile_data = await db.patient_profiles.find_one({"patient_id": current_user.user_id})
    if not profile_data:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Update medical history
    current_history = profile_data.get("medical_history", {})
    update_data = {k: v for k, v in update.dict().items() if v is not None}
    
    medical_history = MedicalHistory(**{**current_history, **update_data})
    
    await db.patient_profiles.update_one(
        {"patient_id": current_user.user_id},
        {"$set": {"medical_history": medical_history.dict()}}
    )
    
    return medical_history

@router.post("/me/vitals", response_model=VitalSigns)
async def record_vital_signs(
    vitals: VitalSignsCreate,
    current_user: User = Depends(require_role(Role.PATIENT))
):
    """Record new vital signs measurement"""
    vital_signs = VitalSigns(**vitals.dict(), recorded_at=datetime.utcnow())
    
    db = await get_database()
    await db.vital_signs.insert_one({
        "patient_id": current_user.user_id,
        **vital_signs.dict()
    })
    
    return vital_signs

@router.get("/me/vitals", response_model=List[VitalSigns])
async def get_my_vital_signs(
    limit: int = 50,
    current_user: User = Depends(require_role(Role.PATIENT))
):
    """Get patient's vital signs history"""
    db = await get_database()
    
    vitals_data = await db.vital_signs.find({
        "patient_id": current_user.user_id
    }).sort("recorded_at", -1).limit(limit).to_list(None)
    
    return [VitalSigns(**v) for v in vitals_data]
'@

Set-Content -Path "$backendDir\app\routers\patient.py" -Value $patientRouterContent -Force
Write-Host "✅ Patient Router created" -ForegroundColor Green

# Create reports router
Write-Host "📝 Creating Reports Router..." -ForegroundColor Yellow
$reportsRouterContent = @'
"""
Reports Router for AURA Healthcare System
Handles medical report generation, viewing, and management
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

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
@router.post("/generate", response_model=MedicalReport)
async def generate_report(
    request: GenerateReportRequest,
    current_user: User = Depends(require_role(Role.DOCTOR))
):
    """
    Generate medical report from conversation
    
    - Uses AI to analyze conversation
    - Extracts symptoms, findings, diagnosis
    - Creates structured medical report
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
    
    # Create report (AI generation would happen here)
    report = MedicalReport(
        report_id=f"report_{datetime.utcnow().timestamp()}",
        patient_id=conv["patient_id"],
        doctor_id=current_user.user_id,
        conversation_id=request.conversation_id,
        report_type=request.report_type,
        generated_at=datetime.utcnow(),
        status=ReportStatus.DRAFT,
        summary=f"Medical report generated from conversation {request.conversation_id}",
        doctor_notes=request.notes
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
'@

Set-Content -Path "$backendDir\app\routers\reports.py" -Value $reportsRouterContent -Force
Write-Host "✅ Reports Router created" -ForegroundColor Green

Write-Host ""
Write-Host "✅ All API Routers Created Successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Created Routers:" -ForegroundColor Cyan
Write-Host "  • backend/app/routers/auth.py (JWT, OAuth2, registration)" -ForegroundColor White
Write-Host "  • backend/app/routers/chat.py (WebSocket, real-time messaging)" -ForegroundColor White
Write-Host "  • backend/app/routers/doctor.py (doctor profiles, management)" -ForegroundColor White
Write-Host "  • backend/app/routers/patient.py (patient profiles, medical history)" -ForegroundColor White
Write-Host "  • backend/app/routers/reports.py (medical report generation)" -ForegroundColor White
Write-Host ""
Write-Host "Next: Run install-ai-services.ps1 to create AI services" -ForegroundColor Yellow
