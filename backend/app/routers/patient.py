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

@router.get("/profile")
async def get_patient_profile_api(current_user: User = Depends(get_current_active_user)):
    """Get patient profile with full details"""
    db = await get_database()
    profile_data = await db.patient_profiles.find_one({"patient_id": current_user.user_id})
    
    if not profile_data:
        return {
            "patient_id": current_user.user_id,
            "full_name": current_user.email,
            "email": current_user.email,
            "role": current_user.role
        }
    
    # Convert ObjectId to string
    if profile_data.get("_id"):
        profile_data["_id"] = str(profile_data["_id"])
    
    return profile_data

@router.get("/conversations")
async def get_patient_conversations_api(current_user: User = Depends(get_current_active_user)):
    """Get all conversations for current patient"""
    db = await get_database()
    
    conversations = await db.conversations.find({
        "patient_id": current_user.user_id
    }).sort("updated_at", -1).to_list(None)
    
    # Convert ObjectId to string
    for conv in conversations:
        if conv.get("_id"):
            conv["_id"] = str(conv["_id"])
    
    return conversations

@router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: User = Depends(get_current_active_user)):
    """Get real-time dashboard statistics for patient"""
    db = await get_database()
    
    # Debug: Log all conversations for this patient
    all_convs = await db.conversations.find({"patient_id": current_user.user_id}).to_list(None)
    print(f"DEBUG: Found {len(all_convs)} conversations for patient {current_user.user_id}")
    for conv in all_convs:
        print(f"  - {conv.get('conversation_id')}: status={conv.get('status')}, created={conv.get('created_at')}")
    
    # Get conversation statistics
    total_conversations = await db.conversations.count_documents({
        "patient_id": current_user.user_id
    })
    
    active_conversations = await db.conversations.count_documents({
        "patient_id": current_user.user_id,
        "status": "active"
    })
    
    # Get message statistics
    total_messages = await db.messages.count_documents({
        "conversation_id": {"$regex": f"^conv_.*_{current_user.user_id}$"}
    })
    
    # Calculate health score based on multiple factors
    health_score = await calculate_health_score(db, current_user.user_id)
    
    # Get recent activity
    recent_conversations = await db.conversations.find({
        "patient_id": current_user.user_id
    }).sort("updated_at", -1).limit(5).to_list(None)
    
    return {
        "total_consultations": total_conversations,
        "active_sessions": active_conversations,
        "total_messages": total_messages,
        "health_score": health_score,
        "recent_activity": len(recent_conversations),
        "last_consultation": recent_conversations[0].get("updated_at") if recent_conversations else None
    }

async def calculate_health_score(db, patient_id: str) -> int:
    """Calculate dynamic health score based on patient data"""
    # Get patient profile
    profile = await db.patient_profiles.find_one({"patient_id": patient_id})
    
    # Check if this is a brand new user (no profile yet)
    total_conversations = await db.conversations.count_documents({"patient_id": patient_id})
    
    if not profile and total_conversations == 0:
        # Brand new user with no data - return neutral baseline at 50%
        return 50
    
    score = 100  # Start with perfect score for existing users
    
    # Factor 1: Recent consultation activity (healthy engagement)
    conversations = await db.conversations.count_documents({
        "patient_id": patient_id,
        "created_at": {"$gte": datetime.utcnow().replace(day=1)}  # This month
    })
    
    if conversations == 0 and total_conversations > 0:
        score -= 10  # Reduce score if no consultations this month (but user has history)
    elif conversations > 0:
        score += min(5, conversations)  # Bonus for regular checkups
    
    # Factor 2: Medical history conditions
    if profile and profile.get("medical_history"):
        medical_history = profile["medical_history"]
        chronic_conditions = medical_history.get("chronic_conditions", [])
        
        if len(chronic_conditions) > 0:
            score -= len(chronic_conditions) * 3  # Each condition reduces score
        
        # Allergies don't reduce score much as they're manageable
        allergies = medical_history.get("allergies", [])
        if len(allergies) > 3:
            score -= 2
    
    # Factor 3: Vital signs (if available)
    recent_vitals = await db.vital_signs.find({
        "patient_id": patient_id
    }).sort("recorded_at", -1).limit(1).to_list(1)
    
    if recent_vitals:
        vital = recent_vitals[0]
        
        # Check blood pressure (ideal: 120/80)
        if vital.get("blood_pressure_systolic"):
            systolic = vital["blood_pressure_systolic"]
            if systolic > 140 or systolic < 90:
                score -= 10
            elif systolic > 130 or systolic < 100:
                score -= 5
        
        # Check heart rate (ideal: 60-100)
        if vital.get("heart_rate"):
            hr = vital["heart_rate"]
            if hr > 100 or hr < 60:
                score -= 8
        
        # Check oxygen saturation (should be > 95%)
        if vital.get("oxygen_saturation"):
            o2 = vital["oxygen_saturation"]
            if o2 < 95:
                score -= 15
            elif o2 < 98:
                score -= 5
    
    # Factor 4: Response time (patients who respond quickly are more engaged)
    messages = await db.messages.find({
        "sender_id": patient_id
    }).sort("timestamp", -1).limit(10).to_list(10)
    
    if len(messages) > 5:
        score += 5  # Bonus for active engagement
    
    # Ensure score is within valid range
    return max(0, min(100, score))
