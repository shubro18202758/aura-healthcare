"""
Patient Activity Tracking Service
Tracks all patient activities and sessions for doctor access
"""

from datetime import datetime, timedelta
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.activity import (
    PatientActivity, 
    PatientSession, 
    ActivityType, 
    SessionStatus,
    PatientActivitySummary,
    PatientSessionSummary,
    DoctorDashboardStats
)
from app.database import get_database

class ActivityTracker:
    """Service for tracking patient activities and sessions"""
    
    def __init__(self):
        self.db: Optional[AsyncIOMotorDatabase] = None
    
    async def _ensure_db(self):
        """Ensure database connection"""
        if self.db is None:
            self.db = await get_database()
    
    async def start_session(
        self, 
        patient_id: str, 
        patient_name: str, 
        patient_email: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> str:
        """
        Start a new patient session when they log in
        Returns session_id
        """
        await self._ensure_db()
        
        # End any existing active sessions for this patient
        await self.db.patient_sessions.update_many(
            {"patient_id": patient_id, "status": SessionStatus.ACTIVE},
            {"$set": {
                "status": SessionStatus.EXPIRED,
                "logout_time": datetime.utcnow()
            }}
        )
        
        # Create new session
        session = PatientSession(
            patient_id=patient_id,
            patient_name=patient_name,
            patient_email=patient_email,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        await self.db.patient_sessions.insert_one(session.dict())
        
        # Log login activity
        await self.log_activity(
            patient_id=patient_id,
            patient_name=patient_name,
            activity_type=ActivityType.LOGIN,
            description=f"{patient_name} logged into the system",
            session_id=session.session_id
        )
        
        print(f"📊 Session started for patient {patient_name} (ID: {patient_id})")
        return session.session_id
    
    async def end_session(self, session_id: str) -> None:
        """
        End a patient session when they log out
        """
        await self._ensure_db()
        
        # Get session
        session_data = await self.db.patient_sessions.find_one({"session_id": session_id})
        if not session_data:
            return
        
        session = PatientSession(**session_data)
        logout_time = datetime.utcnow()
        duration_seconds = int((logout_time - session.login_time).total_seconds())
        
        # Update session
        await self.db.patient_sessions.update_one(
            {"session_id": session_id},
            {"$set": {
                "status": SessionStatus.ENDED,
                "logout_time": logout_time,
                "duration_seconds": duration_seconds
            }}
        )
        
        # Log logout activity
        await self.log_activity(
            patient_id=session.patient_id,
            patient_name=session.patient_name,
            activity_type=ActivityType.LOGOUT,
            description=f"{session.patient_name} logged out (session duration: {duration_seconds//60} minutes)",
            session_id=session_id
        )
        
        print(f"📊 Session ended for patient {session.patient_name} (Duration: {duration_seconds//60} min)")
    
    async def log_activity(
        self,
        patient_id: str,
        patient_name: str,
        activity_type: ActivityType,
        description: str,
        session_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> None:
        """
        Log a patient activity
        """
        await self._ensure_db()
        
        activity = PatientActivity(
            patient_id=patient_id,
            patient_name=patient_name,
            activity_type=activity_type,
            description=description,
            session_id=session_id,
            metadata=metadata
        )
        
        await self.db.patient_activities.insert_one(activity.dict())
        
        # Update session activity counters if session exists
        if session_id:
            update_fields = {
                "last_activity": datetime.utcnow(),
                "total_activities": 1
            }
            
            # Increment specific counters
            if activity_type == ActivityType.CHAT_MESSAGE:
                update_fields["chat_messages_sent"] = 1
            elif activity_type == ActivityType.DOCUMENT_UPLOAD:
                update_fields["documents_uploaded"] = 1
            elif activity_type == ActivityType.REPORT_VIEW:
                update_fields["reports_viewed"] = 1
            
            await self.db.patient_sessions.update_one(
                {"session_id": session_id},
                {"$inc": update_fields}
            )
    
    async def get_active_session(self, patient_id: str) -> Optional[str]:
        """
        Get active session ID for a patient
        """
        await self._ensure_db()
        
        session_data = await self.db.patient_sessions.find_one({
            "patient_id": patient_id,
            "status": SessionStatus.ACTIVE
        })
        
        if session_data:
            return session_data["session_id"]
        return None
    
    async def get_patient_summary(self, patient_id: str) -> Optional[PatientActivitySummary]:
        """
        Get complete activity summary for a patient (DOCTOR ONLY)
        """
        await self._ensure_db()
        
        # Get patient info
        from app.models import User
        user_data = await self.db.users.find_one({"user_id": patient_id})
        if not user_data:
            return None
        
        user = User(**user_data)
        
        # Get all sessions
        sessions_cursor = self.db.patient_sessions.find(
            {"patient_id": patient_id}
        ).sort("login_time", -1)
        sessions = await sessions_cursor.to_list(length=None)
        
        # Get all activities
        activities_cursor = self.db.patient_activities.find(
            {"patient_id": patient_id}
        ).sort("timestamp", -1)
        activities = await activities_cursor.to_list(length=None)
        
        # Calculate stats
        total_time_minutes = sum(
            s.get("duration_seconds", 0) // 60 
            for s in sessions if s.get("duration_seconds")
        )
        
        chat_messages = len([a for a in activities if a["activity_type"] == ActivityType.CHAT_MESSAGE])
        documents_uploaded = len([a for a in activities if a["activity_type"] == ActivityType.DOCUMENT_UPLOAD])
        reports_viewed = len([a for a in activities if a["activity_type"] == ActivityType.REPORT_VIEW])
        profile_updates = len([a for a in activities if a["activity_type"] == ActivityType.PROFILE_UPDATE])
        
        # Check if currently active
        active_session = next((s for s in sessions if s["status"] == SessionStatus.ACTIVE), None)
        
        # Recent sessions (last 10)
        recent_sessions = [
            PatientSessionSummary(
                session_id=s["session_id"],
                patient_id=s["patient_id"],
                patient_name=s["patient_name"],
                login_time=s["login_time"],
                logout_time=s.get("logout_time"),
                duration_minutes=s.get("duration_seconds", 0) // 60 if s.get("duration_seconds") else None,
                status=s["status"],
                activities_count=s.get("total_activities", 0),
                last_activity_type=None
            )
            for s in sessions[:10]
        ]
        
        # Recent activities (last 20)
        recent_activities = [
            PatientActivity(**a)
            for a in activities[:20]
        ]
        
        return PatientActivitySummary(
            patient_id=patient_id,
            patient_name=user.full_name,
            patient_email=user.email,
            total_sessions=len(sessions),
            total_activities=len(activities),
            total_time_minutes=total_time_minutes,
            first_seen=sessions[-1]["login_time"] if sessions else None,
            last_seen=sessions[0]["last_activity"] if sessions else None,
            is_currently_active=active_session is not None,
            current_session_id=active_session["session_id"] if active_session else None,
            chat_messages=chat_messages,
            documents_uploaded=documents_uploaded,
            reports_viewed=reports_viewed,
            profile_updates=profile_updates,
            recent_sessions=recent_sessions,
            recent_activities=recent_activities
        )
    
    async def get_all_patients_summary(self) -> List[PatientActivitySummary]:
        """
        Get activity summary for all patients (DOCTOR DASHBOARD)
        """
        await self._ensure_db()
        
        # Get all patients
        from app.models import User, Role
        users_cursor = self.db.users.find({"role": Role.PATIENT})
        users = await users_cursor.to_list(length=None)
        
        summaries = []
        for user_data in users:
            summary = await self.get_patient_summary(user_data["user_id"])
            if summary:
                summaries.append(summary)
        
        # Sort by last activity (most recent first)
        summaries.sort(key=lambda x: x.last_seen or datetime.min, reverse=True)
        
        return summaries
    
    async def get_dashboard_stats(self) -> DoctorDashboardStats:
        """
        Get overall statistics for doctor dashboard
        """
        await self._ensure_db()
        
        # Get total patients
        from app.models import Role
        total_patients = await self.db.users.count_documents({"role": Role.PATIENT})
        
        # Get active patients now
        active_patients_now = await self.db.patient_sessions.count_documents({
            "status": SessionStatus.ACTIVE
        })
        
        # Get today's sessions
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        total_sessions_today = await self.db.patient_sessions.count_documents({
            "login_time": {"$gte": today_start}
        })
        
        # Get today's activities
        total_activities_today = await self.db.patient_activities.count_documents({
            "timestamp": {"$gte": today_start}
        })
        
        # Get recently active patients (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(hours=24)
        recent_sessions = await self.db.patient_sessions.find({
            "last_activity": {"$gte": yesterday}
        }).to_list(length=100)
        
        patient_ids = list(set(s["patient_id"] for s in recent_sessions))
        recently_active_patients = []
        
        for patient_id in patient_ids[:10]:  # Top 10 most active
            summary = await self.get_patient_summary(patient_id)
            if summary:
                recently_active_patients.append(summary)
        
        return DoctorDashboardStats(
            total_patients=total_patients,
            active_patients_now=active_patients_now,
            total_sessions_today=total_sessions_today,
            total_activities_today=total_activities_today,
            recently_active_patients=recently_active_patients
        )

# Global activity tracker instance
_activity_tracker: Optional[ActivityTracker] = None

async def get_activity_tracker() -> ActivityTracker:
    """Get or create activity tracker instance"""
    global _activity_tracker
    if _activity_tracker is None:
        _activity_tracker = ActivityTracker()
    return _activity_tracker
