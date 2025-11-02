# 🔐 Token-Based Authentication & Patient Activity Tracking System

## Overview

AURA now has a complete **JWT token-based authentication system** with comprehensive **patient activity tracking** that allows doctors to monitor all patient interactions while keeping this data **invisible to patients**.

---

## 🎯 Key Features

### 1. **JWT Token Authentication**
- ✅ **Secure login/logout** with bcrypt password hashing
- ✅ **Token-based sessions** with expiration (configurable)
- ✅ **Role-based access control** (Patient, Doctor, Admin)
- ✅ **Automatic token validation** on every API request
- ✅ **User ID embedded in token** for database lookups

### 2. **Patient Session Tracking**
- ✅ **Login/Logout timestamps** - Exact time when patient enters/exits
- ✅ **Session duration** - Total time spent in the app
- ✅ **Session status** - Active, Ended, or Expired
- ✅ **IP address & User agent** - Device and location info
- ✅ **Activity counters** - Messages sent, documents uploaded, reports viewed

### 3. **Patient Activity Logging**
- ✅ **Every action tracked**: Login, Logout, Chat messages, Document uploads, Report views, Profile updates
- ✅ **Detailed descriptions** - What the patient did
- ✅ **Timestamps** - When it happened
- ✅ **Session linkage** - Which session the activity occurred in
- ✅ **Metadata** - Additional context (e.g., document name, chat length)

### 4. **Doctor-Only Access**
- ✅ **Patients cannot see tracking data** - Completely hidden from patient views
- ✅ **Doctors can access ALL patient data** - Complete history and activity
- ✅ **Dashboard statistics** - Overview of all patients
- ✅ **Individual patient reports** - Detailed activity summaries
- ✅ **Real-time monitoring** - See who's currently active

---

## 🔑 How Token System Works

### **Patient Login Flow**

1. **Patient enters email & password** → Frontend sends to `/api/auth/login` or `/api/auth/token`
2. **Backend validates credentials** → Checks password hash in MongoDB
3. **Backend generates JWT token** → Contains `user_id`, `role`, `expiration`
4. **Backend starts session tracking** → Creates `PatientSession` with login time
5. **Backend logs LOGIN activity** → Records in `patient_activities` collection
6. **Frontend receives token** → Stores in localStorage/sessionStorage
7. **All subsequent requests include token** → Sent in `Authorization: Bearer <token>` header

### **Patient Logout Flow**

1. **Patient clicks logout** → Frontend calls `/api/auth/logout`
2. **Backend ends session** → Updates logout time, calculates duration
3. **Backend logs LOGOUT activity** → Records in `patient_activities` collection
4. **Frontend discards token** → Removes from storage

### **Token Validation on Every Request**

```
Frontend Request → Authorization: Bearer eyJhbGc...
                ↓
        Backend extracts token
                ↓
        Decodes JWT payload
                ↓
        Extracts user_id from token
                ↓
        Looks up user in MongoDB
                ↓
        Validates user.is_active
                ↓
        Returns User object to endpoint
```

---

## 📊 MongoDB Collections

### **users** Collection
Stores user accounts (patients, doctors, admins)
```json
{
  "user_id": "patient_a1b2c3d4",
  "email": "john.doe@example.com",
  "hashed_password": "$2b$12$...",
  "full_name": "John Doe",
  "role": "patient",
  "is_active": true,
  "created_at": "2025-11-02T10:00:00",
  "last_login": "2025-11-02T15:30:00"
}
```

### **patient_sessions** Collection (DOCTOR ONLY ACCESS)
Tracks every time a patient logs in/out
```json
{
  "session_id": "sess_1730557200.123",
  "patient_id": "patient_a1b2c3d4",
  "patient_name": "John Doe",
  "patient_email": "john.doe@example.com",
  "login_time": "2025-11-02T15:30:00",
  "logout_time": "2025-11-02T16:45:00",
  "last_activity": "2025-11-02T16:45:00",
  "status": "ended",
  "duration_seconds": 4500,
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "total_activities": 15,
  "chat_messages_sent": 8,
  "documents_uploaded": 2,
  "reports_viewed": 5
}
```

### **patient_activities** Collection (DOCTOR ONLY ACCESS)
Logs every action a patient takes
```json
{
  "activity_id": "act_1730557300.456",
  "patient_id": "patient_a1b2c3d4",
  "patient_name": "John Doe",
  "activity_type": "chat_message",
  "description": "Sent chat message: I have been feeling dizzy...",
  "timestamp": "2025-11-02T15:35:00",
  "session_id": "sess_1730557200.123",
  "metadata": {
    "conversation_id": "conv_xyz789",
    "message_length": 120
  }
}
```

---

## 🩺 Doctor Access Endpoints

All these endpoints require **Doctor role** - patients are **blocked** from accessing.

### **1. Dashboard Statistics**
```http
GET /api/doctor/patient-activity/dashboard
Authorization: Bearer <doctor_token>
```

**Response:**
```json
{
  "total_patients": 150,
  "active_patients_now": 12,
  "total_sessions_today": 45,
  "total_activities_today": 320,
  "recently_active_patients": [
    {
      "patient_id": "patient_a1b2c3d4",
      "patient_name": "John Doe",
      "is_currently_active": true,
      "last_seen": "2025-11-02T16:45:00",
      "total_sessions": 23,
      "total_activities": 156,
      "chat_messages": 89
    }
  ]
}
```

### **2. All Patients Activity**
```http
GET /api/doctor/patient-activity/patients
Authorization: Bearer <doctor_token>
```

Returns complete list of all patients with activity summaries.

### **3. Specific Patient Activity**
```http
GET /api/doctor/patient-activity/patient/{patient_id}
Authorization: Bearer <doctor_token>
```

**Response:**
```json
{
  "patient_id": "patient_a1b2c3d4",
  "patient_name": "John Doe",
  "patient_email": "john.doe@example.com",
  "total_sessions": 23,
  "total_activities": 156,
  "total_time_minutes": 1450,
  "first_seen": "2025-10-15T09:00:00",
  "last_seen": "2025-11-02T16:45:00",
  "is_currently_active": false,
  "chat_messages": 89,
  "documents_uploaded": 12,
  "reports_viewed": 34,
  "profile_updates": 3,
  "recent_sessions": [...],
  "recent_activities": [...]
}
```

### **4. Patient Session History**
```http
GET /api/doctor/patient-activity/patient/{patient_id}/sessions?limit=50
Authorization: Bearer <doctor_token>
```

Shows all login/logout sessions with timestamps and durations.

### **5. Patient Activity Log**
```http
GET /api/doctor/patient-activity/patient/{patient_id}/activities?activity_type=chat_message&days=30&limit=100
Authorization: Bearer <doctor_token>
```

Shows detailed log of all patient actions.

### **6. Currently Active Patients**
```http
GET /api/doctor/patient-activity/active-patients
Authorization: Bearer <doctor_token>
```

Shows patients who are **online right now**.

### **7. Complete Patient Data**
```http
GET /api/doctor/patient-activity/patient/{patient_id}/medical-data
Authorization: Bearer <doctor_token>
```

**Response includes:**
- Profile & medical history
- Activity summary
- Chat history (last 50 messages)
- Uploaded documents
- Medical reports
- Vital signs history

### **8. Activity Timeline**
```http
GET /api/doctor/patient-activity/statistics/timeline?days=7
Authorization: Bearer <doctor_token>
```

Shows daily activity trends over past N days.

---

## 🚫 Privacy & Security

### **What Patients CAN See:**
- ✅ Their own profile and medical data
- ✅ Their own chat history
- ✅ Their own documents and reports

### **What Patients CANNOT See:**
- ❌ Their session tracking data (login/logout times)
- ❌ Their activity logs
- ❌ Other patients' data
- ❌ Doctor dashboard statistics

### **What Doctors CAN See:**
- ✅ **EVERYTHING** - All patient data
- ✅ All patient sessions and activities
- ✅ Real-time active patients
- ✅ Complete medical history
- ✅ Chat history, documents, reports
- ✅ Dashboard statistics

### **Role-Based Access Control**

```python
@router.get("/patient-activity/dashboard")
async def get_dashboard_stats(
    current_user: User = Depends(require_role(Role.DOCTOR))  # ← Only doctors allowed
):
    ...
```

If a patient tries to access: **403 Forbidden** error.

---

## 📝 Activity Types Tracked

| Activity Type | Description | Logged When |
|--------------|-------------|-------------|
| `LOGIN` | Patient logs into system | Auth endpoint |
| `LOGOUT` | Patient logs out | Auth endpoint |
| `CHAT_MESSAGE` | Patient sends chat message | Chat endpoint |
| `DOCUMENT_UPLOAD` | Patient uploads document | Documents endpoint |
| `REPORT_VIEW` | Patient views medical report | Reports endpoint |
| `PROFILE_UPDATE` | Patient updates profile | Patient endpoint |
| `APPOINTMENT_REQUEST` | Patient requests appointment | Appointments endpoint |
| `VITAL_SIGNS_RECORD` | Patient records vitals | Patient endpoint |
| `MEDICATION_LOG` | Patient logs medication | Medications endpoint |

---

## 🔧 Implementation Example

### **Patient Login (Frontend)**
```javascript
async function login(email, password) {
  const response = await fetch('http://localhost:8000/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  
  const data = await response.json();
  
  // Store token
  localStorage.setItem('token', data.access_token);
  localStorage.setItem('user', JSON.stringify(data.user));
  
  console.log(`Logged in as: ${data.user.full_name}`);
  console.log(`User ID: ${data.user.user_id}`); // This is the patient's unique ID
  console.log(`Role: ${data.user.role}`);
}
```

### **Patient Logout (Frontend)**
```javascript
async function logout() {
  const token = localStorage.getItem('token');
  
  await fetch('http://localhost:8000/api/auth/logout', {
    method: 'POST',
    headers: { 
      'Authorization': `Bearer ${token}`
    }
  });
  
  // Clear token
  localStorage.removeItem('token');
  localStorage.removeItem('user');
}
```

### **Doctor Viewing Patient Activity (Frontend)**
```javascript
async function viewPatientActivity(patientId) {
  const token = localStorage.getItem('token'); // Doctor's token
  
  const response = await fetch(
    `http://localhost:8000/api/doctor/patient-activity/patient/${patientId}`,
    {
      headers: { 
        'Authorization': `Bearer ${token}`
      }
    }
  );
  
  const activity = await response.json();
  
  console.log(`Patient: ${activity.patient_name}`);
  console.log(`Total Sessions: ${activity.total_sessions}`);
  console.log(`Total Time: ${activity.total_time_minutes} minutes`);
  console.log(`Chat Messages: ${activity.chat_messages}`);
  console.log(`Documents: ${activity.documents_uploaded}`);
  console.log(`Currently Active: ${activity.is_currently_active}`);
}
```

---

## 🎯 Use Cases

### **For Doctors:**

1. **View all active patients now**
   - See who's currently using the app
   - Prioritize responses to active users

2. **Track patient engagement**
   - See how often patients use the app
   - Identify disengaged patients who need follow-up

3. **Review patient history before consultation**
   - See when patient first visited
   - Check recent activity and concerns
   - Review chat history for context

4. **Monitor app usage trends**
   - Peak usage times
   - Average session durations
   - Most active features

5. **Complete patient profile**
   - Medical history
   - Activity patterns
   - Chat conversations
   - Uploaded documents
   - Reports and diagnoses

---

## 🚀 Testing the System

### **1. Register a Patient**
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "patient@test.com",
    "password": "test123",
    "full_name": "Test Patient",
    "role": "patient"
  }'
```

**Response includes:**
- `access_token` - JWT token for authentication
- `user` - User object with `user_id` (this is the patient's ID)

### **2. Register a Doctor**
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "doctor@test.com",
    "password": "doc123",
    "full_name": "Dr. Smith",
    "role": "doctor",
    "specialty": "General Medicine"
  }'
```

### **3. Patient Sends Chat Message**
```bash
curl -X POST http://localhost:8000/api/chat/conv_123/message \
  -H "Authorization: Bearer <patient_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I have a headache",
    "language": "en"
  }'
```

**This automatically logs**:
- Activity type: `CHAT_MESSAGE`
- Description: "Sent chat message: I have a headache..."
- Timestamp
- Session ID

### **4. Doctor Views Patient Activity**
```bash
curl http://localhost:8000/api/doctor/patient-activity/patient/patient_a1b2c3d4 \
  -H "Authorization: Bearer <doctor_token>"
```

### **5. Doctor Views Dashboard**
```bash
curl http://localhost:8000/api/doctor/patient-activity/dashboard \
  -H "Authorization: Bearer <doctor_token>"
```

---

## 🎉 Summary

✅ **Token System Implemented** - JWT authentication with user_id embedded  
✅ **Session Tracking Active** - Login/logout times, duration, device info  
✅ **Activity Logging Active** - Every patient action tracked  
✅ **Doctor Access Enabled** - Complete patient visibility  
✅ **Patient Privacy Protected** - Tracking data hidden from patients  
✅ **Database Integration Complete** - MongoDB collections created  
✅ **API Endpoints Ready** - 8 doctor-only endpoints  

**Your AURA system now has enterprise-grade patient tracking!** 🏥✨
