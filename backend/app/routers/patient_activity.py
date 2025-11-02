"""
Patient Activity Router - DOCTOR ONLY ACCESS
Provides doctors with comprehensive view of patient activities, sessions, and history
PATIENTS CANNOT ACCESS THIS DATA
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime, timedelta

from app.models import User, Role
from app.models.activity import (
    PatientActivitySummary,
    DoctorDashboardStats,
    PatientActivity,
    PatientSession
)
from app.routers.auth import require_role
from app.services.activity_tracker import get_activity_tracker
from app.database import get_database

router = APIRouter(
    prefix="/api/doctor/patient-activity",
    tags=["doctor-patient-activity"],
    dependencies=[Depends(require_role(Role.DOCTOR))]  # DOCTOR ONLY - Patients blocked
)

@router.get("/dashboard", response_model=DoctorDashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(require_role(Role.DOCTOR))
):
    """
    Get overall dashboard statistics
    
    **DOCTOR ONLY** - Shows:
    - Total patients registered
    - Currently active patients
    - Today's sessions and activities
    - Recently active patients
    """
    tracker = await get_activity_tracker()
    stats = await tracker.get_dashboard_stats()
    
    print(f"📊 Doctor {current_user.full_name} accessed dashboard stats")
    return stats

@router.get("/patients", response_model=List[PatientActivitySummary])
async def get_all_patients_activity(
    current_user: User = Depends(require_role(Role.DOCTOR))
):
    """
    Get activity summary for ALL patients
    
    **DOCTOR ONLY** - Returns comprehensive list of all patients with:
    - Total sessions and activities
    - Time spent in app
    - Recent activities
    - Current online status
    """
    tracker = await get_activity_tracker()
    summaries = await tracker.get_all_patients_summary()
    
    print(f"📊 Doctor {current_user.full_name} accessed all patients' activity")
    return summaries

@router.get("/patient/{patient_id}", response_model=PatientActivitySummary)
async def get_patient_activity(
    patient_id: str,
    current_user: User = Depends(require_role(Role.DOCTOR))
):
    """
    Get detailed activity summary for a specific patient
    
    **DOCTOR ONLY** - Shows:
    - All login/logout sessions with timestamps
    - Complete activity history
    - Documents uploaded
    - Reports viewed
    - Chat messages count
    - Time spent in app
    """
    tracker = await get_activity_tracker()
    summary = await tracker.get_patient_summary(patient_id)
    
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID {patient_id} not found"
        )
    
    print(f"📊 Doctor {current_user.full_name} accessed activity for patient {summary.patient_name}")
    return summary

@router.get("/patient/{patient_id}/sessions", response_model=List[PatientSession])
async def get_patient_sessions(
    patient_id: str,
    limit: int = 50,
    current_user: User = Depends(require_role(Role.DOCTOR))
):
    """
    Get detailed session history for a patient
    
    **DOCTOR ONLY** - Shows all login/logout sessions with:
    - Login and logout times
    - Session duration
    - IP address and user agent
    - Activity counts during session
    """
    db = await get_database()
    
    sessions_cursor = db.patient_sessions.find(
        {"patient_id": patient_id}
    ).sort("login_time", -1).limit(limit)
    
    sessions_data = await sessions_cursor.to_list(length=limit)
    sessions = [PatientSession(**s) for s in sessions_data]
    
    print(f"📊 Doctor {current_user.full_name} accessed sessions for patient {patient_id}")
    return sessions

@router.get("/patient/{patient_id}/activities", response_model=List[PatientActivity])
async def get_patient_activities(
    patient_id: str,
    activity_type: Optional[str] = None,
    days: int = 30,
    limit: int = 100,
    current_user: User = Depends(require_role(Role.DOCTOR))
):
    """
    Get detailed activity log for a patient
    
    **DOCTOR ONLY** - Shows all activities with:
    - Activity type (login, chat, document upload, etc.)
    - Timestamp
    - Description
    - Associated session
    
    Parameters:
    - activity_type: Filter by type (login, chat_message, document_upload, etc.)
    - days: Number of days to look back (default: 30)
    - limit: Max activities to return (default: 100)
    """
    db = await get_database()
    
    # Build query
    query = {"patient_id": patient_id}
    
    if activity_type:
        query["activity_type"] = activity_type
    
    if days:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query["timestamp"] = {"$gte": cutoff_date}
    
    activities_cursor = db.patient_activities.find(query).sort("timestamp", -1).limit(limit)
    activities_data = await activities_cursor.to_list(length=limit)
    activities = [PatientActivity(**a) for a in activities_data]
    
    print(f"📊 Doctor {current_user.full_name} accessed {len(activities)} activities for patient {patient_id}")
    return activities

@router.get("/active-patients", response_model=List[PatientActivitySummary])
async def get_active_patients(
    current_user: User = Depends(require_role(Role.DOCTOR))
):
    """
    Get list of currently active patients (online now)
    
    **DOCTOR ONLY** - Shows patients who are currently logged in
    """
    db = await get_database()
    
    # Get active sessions
    active_sessions = await db.patient_sessions.find({
        "status": "active"
    }).to_list(length=100)
    
    # Get summaries for active patients
    tracker = await get_activity_tracker()
    active_summaries = []
    
    for session in active_sessions:
        summary = await tracker.get_patient_summary(session["patient_id"])
        if summary:
            active_summaries.append(summary)
    
    print(f"📊 Doctor {current_user.full_name} accessed list of {len(active_summaries)} active patients")
    return active_summaries

@router.get("/patient/{patient_id}/medical-data")
async def get_patient_complete_data(
    patient_id: str,
    current_user: User = Depends(require_role(Role.DOCTOR))
):
    """
    Get COMPLETE patient data including:
    - Profile and medical history
    - Activity summary
    - Chat history
    - Uploaded documents
    - Reports and diagnoses
    - Session history
    
    **DOCTOR ONLY** - Complete patient overview for medical consultation
    """
    db = await get_database()
    tracker = await get_activity_tracker()
    
    # Get patient profile
    patient_profile = await db.patient_profiles.find_one({"patient_id": patient_id})
    
    # Get activity summary
    activity_summary = await tracker.get_patient_summary(patient_id)
    
    # Get chat history (last 50 messages)
    chat_history = await db.chat_messages.find({
        "user_id": patient_id
    }).sort("timestamp", -1).limit(50).to_list(length=50)
    
    # Get uploaded documents
    documents = await db.medical_documents.find({
        "patient_id": patient_id
    }).sort("uploaded_at", -1).to_list(length=100)
    
    # Get medical reports
    reports = await db.reports.find({
        "patient_id": patient_id
    }).sort("created_at", -1).to_list(length=100)
    
    # Get vital signs history
    vitals = await db.vital_signs.find({
        "patient_id": patient_id
    }).sort("recorded_at", -1).limit(20).to_list(length=20)
    
    print(f"📊 Doctor {current_user.full_name} accessed COMPLETE data for patient {patient_id}")
    
    return {
        "patient_id": patient_id,
        "profile": patient_profile,
        "activity_summary": activity_summary.dict() if activity_summary else None,
        "chat_history": chat_history,
        "documents": documents,
        "reports": reports,
        "vital_signs": vitals,
        "retrieved_at": datetime.utcnow()
    }

@router.get("/statistics/timeline")
async def get_activity_timeline(
    days: int = 7,
    current_user: User = Depends(require_role(Role.DOCTOR))
):
    """
    Get activity timeline statistics
    
    **DOCTOR ONLY** - Shows:
    - Daily login counts
    - Daily activity counts
    - Peak usage times
    - Patient engagement trends
    """
    db = await get_database()
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Get sessions by day
    sessions = await db.patient_sessions.find({
        "login_time": {"$gte": cutoff_date}
    }).to_list(length=10000)
    
    # Get activities by day
    activities = await db.patient_activities.find({
        "timestamp": {"$gte": cutoff_date}
    }).to_list(length=10000)
    
    # Group by date
    from collections import defaultdict
    sessions_by_date = defaultdict(int)
    activities_by_date = defaultdict(int)
    
    for session in sessions:
        date_key = session["login_time"].strftime("%Y-%m-%d")
        sessions_by_date[date_key] += 1
    
    for activity in activities:
        date_key = activity["timestamp"].strftime("%Y-%m-%d")
        activities_by_date[date_key] += 1
    
    # Build timeline
    timeline = []
    current_date = cutoff_date.date()
    end_date = datetime.utcnow().date()
    
    while current_date <= end_date:
        date_key = current_date.strftime("%Y-%m-%d")
        timeline.append({
            "date": date_key,
            "sessions": sessions_by_date.get(date_key, 0),
            "activities": activities_by_date.get(date_key, 0)
        })
        current_date += timedelta(days=1)
    
    print(f"📊 Doctor {current_user.full_name} accessed activity timeline")
    
    return {
        "timeline": timeline,
        "total_sessions": len(sessions),
        "total_activities": len(activities),
        "period_days": days
    }
