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

@router.get("/me/stats")
async def get_doctor_stats(
    current_user: User = Depends(require_role(Role.DOCTOR))
):
    """Get real-time statistics for doctor dashboard"""
    db = await get_database()
    
    # Count unique patients from conversations
    conversations = await db.conversations.find({
        "doctor_id": current_user.user_id
    }).to_list(None)
    
    unique_patients = len(set([conv["patient_id"] for conv in conversations]))
    
    # Count active consultations (status: active or pending)
    active_consultations = await db.conversations.count_documents({
        "doctor_id": current_user.user_id,
        "status": {"$in": ["active", "pending"]}
    })
    
    # Count reports generated
    reports_generated = await db.reports.count_documents({
        "doctor_id": current_user.user_id
    })
    
    # Calculate satisfaction rate (based on completed conversations with ratings)
    completed_conversations = await db.conversations.find({
        "doctor_id": current_user.user_id,
        "status": "completed",
        "rating": {"$exists": True}
    }).to_list(None)
    
    if completed_conversations:
        avg_rating = sum([conv.get("rating", 0) for conv in completed_conversations]) / len(completed_conversations)
        satisfaction_rate = int((avg_rating / 5) * 100)
    else:
        satisfaction_rate = 100  # Default when no ratings yet
    
    return {
        "total_patients": unique_patients,
        "active_consultations": active_consultations,
        "reports_generated": reports_generated,
        "satisfaction_rate": satisfaction_rate
    }
