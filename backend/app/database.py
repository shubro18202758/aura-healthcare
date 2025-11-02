"""
AURA Healthcare - Database Management
"""

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from redis import Redis
import asyncio
from typing import Optional
import bcrypt
from app.config import settings

# bcrypt 4.x removed __about__, so provide a shim for passlib's version probe.
if not hasattr(bcrypt, "__about__"):
    class _BcryptAbout:
        __version__ = getattr(bcrypt, "__version__", "")

    bcrypt.__about__ = _BcryptAbout()

# MongoDB Client
_mongo_client: Optional[AsyncIOMotorClient] = None
_db = None

# Redis Client
_redis_client: Optional[Redis] = None

async def get_database():
    """Get MongoDB database instance with optimized connection pooling"""
    global _mongo_client, _db
    
    if _mongo_client is None:
        _mongo_client = AsyncIOMotorClient(
            settings.MONGO_URL,
            maxPoolSize=50,  # Increased connection pool
            minPoolSize=10,
            maxIdleTimeMS=30000,
            waitQueueTimeoutMS=5000,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=20000,
            # Enable compression for better network performance (zlib only, snappy requires extra package)
            compressors='zlib',
            # Enable retryable writes
            retryWrites=True,
            retryReads=True,
            # Connection pool management
            maxConnecting=2
        )
        _db = _mongo_client[settings.DATABASE_NAME]
        print(f"✅ Connected to MongoDB: {settings.DATABASE_NAME} (Pool: 10-50)")
    
    return _db

def get_redis():
    """Get Redis client instance with optimized connection pooling"""
    global _redis_client
    
    if _redis_client is None:
        _redis_client = Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=50,  # Connection pool size
            socket_keepalive=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30
        )
        print(f"✅ Connected to Redis (Pool: 50)")
    
    return _redis_client

async def init_db():
    """Initialize database and create collections"""
    try:
        db = await get_database()
        
        # Create collections if they don't exist
        collections = await db.list_collection_names()
        
        required_collections = [
            "users",
            "doctors",
            "patients",
            "conversations",
            "messages",
            "reports",
            "medical_documents",
            "knowledge_base"
        ]
        
        for collection in required_collections:
            if collection not in collections:
                await db.create_collection(collection)
                print(f"✅ Created collection: {collection}")
        
        # Create indexes for better performance
        await create_indexes(db)
        
        # Populate sample data if in demo mode
        if settings.DEMO_MODE and settings.POPULATE_SAMPLE_DATA:
            await populate_sample_data(db)
        
        print("✅ Database initialized successfully")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise

async def create_indexes(db):
    """Create database indexes for optimized queries"""
    
    # Users collection
    await db.users.create_index("email", unique=True)
    await db.users.create_index("username", unique=True)
    
    # Doctors collection
    await db.doctors.create_index("user_id", unique=True)
    await db.doctors.create_index("specialty")
    
    # Patients collection
    await db.patients.create_index("user_id", unique=True)
    
    # Conversations collection
    await db.conversations.create_index("patient_id")
    await db.conversations.create_index("doctor_id")
    await db.conversations.create_index([("patient_id", 1), ("status", 1)])
    await db.conversations.create_index("created_at")
    
    # Messages collection
    await db.messages.create_index("conversation_id")
    await db.messages.create_index([("conversation_id", 1), ("timestamp", 1)])
    
    # Reports collection
    await db.reports.create_index("conversation_id", unique=True)
    await db.reports.create_index("patient_id")
    await db.reports.create_index("doctor_id")
    
    # Knowledge base collection
    await db.knowledge_base.create_index("doctor_id")
    await db.knowledge_base.create_index("specialty")
    await db.knowledge_base.create_index([("specialty", 1), ("is_active", 1)])
    await db.knowledge_base.create_index("entry_id", unique=True)
    
    print("✅ Database indexes created")

async def populate_sample_data(db):
    """Populate database with sample data for demo"""
    from datetime import datetime
    import bcrypt
    
    def hash_password(password: str) -> str:
        """Hash password using bcrypt directly to avoid passlib backend issues"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Sample doctor (idempotent upsert to ensure consistent schema)
    # Check if user already exists with valid hash
    existing_doctor = await db.users.find_one({"email": "doctor@aura.health"})
    if existing_doctor and existing_doctor.get("hashed_password"):
        doctor_hashed = existing_doctor.get("hashed_password")
    else:
        # Generate fresh hash using bcrypt directly
        doctor_hashed = hash_password("doctor123")

    doctor_user = {
        "user_id": "doctor_demo",
        "email": "doctor@aura.health",
        "username": "dr_smith",
        "hashed_password": doctor_hashed,
        "full_name": "Dr. Sarah Smith",
        "role": "doctor",
        "language": "en",
        "specialty": "cardiology",
        "is_active": True,
        "created_at": existing_doctor.get("created_at") if existing_doctor and existing_doctor.get("created_at") else datetime.utcnow(),
        "last_login": existing_doctor.get("last_login") if existing_doctor else None
    }
    await db.users.update_one(
        {"email": doctor_user["email"]},
        {
            "$set": doctor_user,
            "$unset": {"password": ""}
        },
        upsert=True
    )
    await db.doctors.update_one(
        {"user_id": doctor_user["user_id"]},
        {
            "$set": {
                "user_id": doctor_user["user_id"],
                "specialty": doctor_user["specialty"],
                "license_number": "MD12345",
                "years_of_experience": 10,
                "hospital": "AURA Medical Center",
                "bio": "Board-certified cardiologist specializing in preventive care",
                "created_at": datetime.utcnow()
            }
        },
        upsert=True
    )
    print("✅ Sample doctor account ready")

    # Sample patient (idempotent upsert)
    # Check if user already exists with valid hash
    existing_patient = await db.users.find_one({"email": "patient@aura.health"})
    if existing_patient and existing_patient.get("hashed_password"):
        patient_hashed = existing_patient.get("hashed_password")
    else:
        # Generate fresh hash using bcrypt directly
        patient_hashed = hash_password("patient123")

    patient_user = {
        "user_id": "patient_demo",
        "email": "patient@aura.health",
        "username": "john_doe",
        "hashed_password": patient_hashed,
        "full_name": "John Doe",
        "role": "patient",
        "language": "en",
        "is_active": True,
        "created_at": existing_patient.get("created_at") if existing_patient and existing_patient.get("created_at") else datetime.utcnow(),
        "last_login": existing_patient.get("last_login") if existing_patient else None
    }
    await db.users.update_one(
        {"email": patient_user["email"]},
        {
            "$set": patient_user,
            "$unset": {"password": ""}
        },
        upsert=True
    )
    await db.patients.update_one(
        {"user_id": patient_user["user_id"]},
        {
            "$set": {
                "user_id": patient_user["user_id"],
                "age": 45,
                "gender": "male",
                "blood_group": "O+",
                "allergies": ["penicillin"],
                "chronic_conditions": ["hypertension"],
                "emergency_contact": {
                    "name": "Jane Doe",
                    "phone": "+1234567890",
                    "relation": "spouse"
                },
                "created_at": datetime.utcnow()
            }
        },
        upsert=True
    )
    print("✅ Sample patient account ready")

async def close_database():
    """Close database connections"""
    global _mongo_client, _redis_client
    
    if _mongo_client:
        _mongo_client.close()
        print("✅ MongoDB connection closed")
    
    if _redis_client:
        _redis_client.close()
        print("✅ Redis connection closed")

# Dependency for FastAPI routes
async def get_db():
    """Dependency to get database in routes"""
    return await get_database()
