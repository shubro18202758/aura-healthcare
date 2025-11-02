# 🚀 Quick Start - Token & Activity Tracking System

## ✅ System is Now Active!

The backend has automatically reloaded with the new features:
- ✅ JWT Token Authentication
- ✅ Patient Session Tracking  
- ✅ Patient Activity Logging
- ✅ Doctor Dashboard API

---

## 📝 Test the System in 5 Steps

### **Step 1: Register a Patient**

Open your browser or use this curl command:

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "patient1@test.com",
    "password": "patient123",
    "full_name": "John Doe",
    "role": "patient"
  }'
```

**Save the response:**
- `access_token` - Patient's token
- `user.user_id` - Patient's ID (e.g., `patient_a1b2c3d4`)

### **Step 2: Register a Doctor**

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "doctor1@test.com",
    "password": "doctor123",
    "full_name": "Dr. Sarah Smith",
    "role": "doctor",
    "specialty": "General Medicine"
  }'
```

**Save the response:**
- `access_token` - Doctor's token

### **Step 3: Patient Activity (Send Chat Message)**

Use the patient's token:

```bash
# First create a conversation
curl -X POST http://localhost:8000/api/chat/conversations \
  -H "Authorization: Bearer PATIENT_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Health Checkup"
  }'

# Save the conversation_id from response

# Then send a message
curl -X POST http://localhost:8000/api/chat/CONVERSATION_ID/message \
  -H "Authorization: Bearer PATIENT_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I have been feeling dizzy lately",
    "language": "en"
  }'
```

**This automatically logs:**
- Session started (on login)
- Chat message activity
- Updates session counters

### **Step 4: Doctor Views Dashboard**

Use the doctor's token:

```bash
curl http://localhost:8000/api/doctor/patient-activity/dashboard \
  -H "Authorization: Bearer DOCTOR_TOKEN_HERE"
```

**You'll see:**
- Total patients: 1
- Active patients now: 1 (if patient still logged in)
- Total sessions today: 1
- Total activities today: 2 (login + chat)

### **Step 5: Doctor Views Patient Activity**

Replace `PATIENT_ID` with the patient's user_id from Step 1:

```bash
curl http://localhost:8000/api/doctor/patient-activity/patient/PATIENT_ID \
  -H "Authorization: Bearer DOCTOR_TOKEN_HERE"
```

**You'll see complete patient data:**
```json
{
  "patient_id": "patient_a1b2c3d4",
  "patient_name": "John Doe",
  "patient_email": "patient1@test.com",
  "total_sessions": 1,
  "total_activities": 2,
  "total_time_minutes": 5,
  "first_seen": "2025-11-02T...",
  "last_seen": "2025-11-02T...",
  "is_currently_active": true,
  "chat_messages": 1,
  "documents_uploaded": 0,
  "reports_viewed": 0,
  "recent_sessions": [...],
  "recent_activities": [
    {
      "activity_type": "chat_message",
      "description": "Sent chat message: I have been feeling dizzy...",
      "timestamp": "..."
    },
    {
      "activity_type": "login",
      "description": "John Doe logged into the system",
      "timestamp": "..."
    }
  ]
}
```

---

## 🎨 Frontend Integration

### **Login Component**

```javascript
// Login patient
async function loginPatient(email, password) {
  const response = await fetch('http://localhost:8000/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  
  const data = await response.json();
  
  // Store token and user info
  localStorage.setItem('authToken', data.access_token);
  localStorage.setItem('userId', data.user.user_id);
  localStorage.setItem('userRole', data.user.role);
  localStorage.setItem('userName', data.user.full_name);
  
  console.log(`✅ Logged in as ${data.user.full_name}`);
  console.log(`🆔 User ID: ${data.user.user_id}`); // This is the patient's database ID
  console.log(`⏱️  Session tracking started automatically`);
  
  return data;
}
```

### **Logout Component**

```javascript
// Logout patient
async function logoutPatient() {
  const token = localStorage.getItem('authToken');
  
  await fetch('http://localhost:8000/api/auth/logout', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` }
  });
  
  console.log(`✅ Logged out`);
  console.log(`⏱️  Session ended - duration recorded`);
  
  // Clear storage
  localStorage.clear();
}
```

### **API Request Helper**

```javascript
// Make authenticated API calls
async function apiRequest(endpoint, options = {}) {
  const token = localStorage.getItem('authToken');
  
  const response = await fetch(`http://localhost:8000${endpoint}`, {
    ...options,
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      ...options.headers
    }
  });
  
  if (response.status === 401) {
    // Token expired - redirect to login
    console.error('Token expired - please login again');
    localStorage.clear();
    window.location.href = '/login';
  }
  
  return response.json();
}
```

### **Doctor Dashboard Component**

```javascript
// Doctor views patient activity
async function loadDoctorDashboard() {
  // Get overall stats
  const stats = await apiRequest('/api/doctor/patient-activity/dashboard');
  
  console.log(`📊 Dashboard Stats:`);
  console.log(`  Total Patients: ${stats.total_patients}`);
  console.log(`  Active Now: ${stats.active_patients_now}`);
  console.log(`  Sessions Today: ${stats.total_sessions_today}`);
  console.log(`  Activities Today: ${stats.total_activities_today}`);
  
  // Get all patients
  const patients = await apiRequest('/api/doctor/patient-activity/patients');
  
  patients.forEach(patient => {
    console.log(`\n👤 ${patient.patient_name}`);
    console.log(`  Email: ${patient.patient_email}`);
    console.log(`  Status: ${patient.is_currently_active ? '🟢 Online' : '⚪ Offline'}`);
    console.log(`  Total Sessions: ${patient.total_sessions}`);
    console.log(`  Total Time: ${patient.total_time_minutes} min`);
    console.log(`  Chat Messages: ${patient.chat_messages}`);
    console.log(`  Documents: ${patient.documents_uploaded}`);
  });
}
```

---

## 🔍 API Endpoints Summary

### **Authentication (Anyone)**
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login (JWT token + session start)
- `POST /api/auth/logout` - Logout (session end)
- `GET /api/auth/me` - Get current user info

### **Patient Activity (Doctor ONLY)**
- `GET /api/doctor/patient-activity/dashboard` - Dashboard stats
- `GET /api/doctor/patient-activity/patients` - All patients summary
- `GET /api/doctor/patient-activity/patient/{id}` - Specific patient
- `GET /api/doctor/patient-activity/patient/{id}/sessions` - Session history
- `GET /api/doctor/patient-activity/patient/{id}/activities` - Activity log
- `GET /api/doctor/patient-activity/active-patients` - Currently online
- `GET /api/doctor/patient-activity/patient/{id}/medical-data` - Complete data
- `GET /api/doctor/patient-activity/statistics/timeline` - Timeline stats

---

## 🎯 What Happens Automatically

### **When Patient Logs In:**
1. ✅ Password validated
2. ✅ JWT token generated with `user_id`
3. ✅ Session record created in MongoDB
4. ✅ LOGIN activity logged
5. ✅ Token returned to frontend

### **When Patient Sends Chat:**
1. ✅ Token validated → user_id extracted
2. ✅ Chat message saved
3. ✅ CHAT_MESSAGE activity logged
4. ✅ Session counters updated (chat_messages_sent++)
5. ✅ AI response generated with TTS audio

### **When Patient Logs Out:**
1. ✅ Token validated → user_id extracted
2. ✅ Session ended → logout time recorded
3. ✅ Duration calculated
4. ✅ LOGOUT activity logged
5. ✅ Frontend clears token

### **When Doctor Views Dashboard:**
1. ✅ Doctor token validated
2. ✅ Role checked (must be DOCTOR)
3. ✅ All patient data aggregated
4. ✅ Statistics calculated
5. ✅ Data returned (invisible to patients)

---

## 📦 MongoDB Collections Created

Your MongoDB now has these collections:

1. **users** - User accounts (patients, doctors)
2. **patient_sessions** - Login/logout tracking *(doctor only)*
3. **patient_activities** - Action logs *(doctor only)*
4. **patient_profiles** - Medical profiles
5. **conversations** - Chat conversations
6. **messages** - Chat messages
7. **user_preferences** - User settings (inc. TTS)

---

## 🎉 Success!

Your AURA system now has:

✅ **JWT Token Authentication** - Secure login with user_id embedded  
✅ **Session Tracking** - Login/logout times, duration  
✅ **Activity Logging** - Every patient action tracked  
✅ **Doctor Dashboard** - Complete visibility  
✅ **Patient Privacy** - Tracking invisible to patients  

**The system is running on http://localhost:8000**

**API Docs: http://localhost:8000/docs**

Happy testing! 🏥✨
