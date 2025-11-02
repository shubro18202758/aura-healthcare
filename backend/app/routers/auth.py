"""
Authentication Router for AURA Healthcare System
Handles user registration, login, token management, and role-based access control
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
import secrets

from app.config import get_settings
from app.database import get_database
from app.models import User, Role, Token

# Router setup
router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Security setup - use bcrypt directly to avoid passlib backend issues
import bcrypt
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")
settings = get_settings()

# Request/Response Models
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: Role
    phone: Optional[str] = None
    language: str = "en"
    specialty: Optional[str] = None  # Medical specialty for doctors/patients

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: User

class PasswordReset(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

# Helper functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash using bcrypt directly"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    """Hash password using bcrypt directly"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Validate token and return current user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    db = await get_database()
    user_data = await db.users.find_one({"user_id": user_id})
    
    if user_data is None:
        raise credentials_exception
    
    return User(**user_data)

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Ensure user is active"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def require_role(required_role: Role):
    """Dependency to require specific role"""
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role != required_role and current_user.role != Role.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role.value}"
            )
        return current_user
    return role_checker

# Routes
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    """
    Register new user account
    
    - Creates new user with hashed password
    - Returns access token for immediate login
    - Validates email uniqueness
    """
    db = await get_database()
    
    # Check if email already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate specialty for doctors
    if user_data.role == Role.DOCTOR and not user_data.specialty:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Doctors must specify their medical specialty"
        )
    
    # Create user
    user = User(
        user_id=f"{user_data.role.value}_{secrets.token_hex(8)}",
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        phone=user_data.phone,
        language=user_data.language,
        specialty=user_data.specialty,
        created_at=datetime.utcnow(),
        last_login=datetime.utcnow()
    )
    
    # Insert into database
    await db.users.insert_one(user.dict())
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.user_id, "role": user.role.value}
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user
    )

@router.post("/token", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login with session tracking
    
    - Authenticates user with email/password
    - Returns JWT access token
    - Starts patient session tracking for activity monitoring
    """
    db = await get_database()
    
    # Find user by email
    user_data = await db.users.find_one({"email": form_data.username})
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = User(**user_data)
    
    # Verify password
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    # Update last login
    await db.users.update_one(
        {"user_id": user.user_id},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    # Start session tracking for patients
    if user.role == Role.PATIENT:
        from app.services.activity_tracker import get_activity_tracker
        tracker = await get_activity_tracker()
        session_id = await tracker.start_session(
            patient_id=user.user_id,
            patient_name=user.full_name,
            patient_email=user.email
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.user_id, "role": user.role.value}
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user
    )

@router.post("/login", response_model=TokenResponse)
async def login_json(login_data: UserLogin):
    """
    JSON login endpoint (alternative to OAuth2 form)
    
    - Accepts JSON with email and password
    - Returns JWT access token
    """
    db = await get_database()
    
    # Find user by email
    user_data = await db.users.find_one({"email": login_data.email})
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    user = User(**user_data)
    
    # Verify password
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    # Update last login
    await db.users.update_one(
        {"user_id": user.user_id},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    # Start session tracking for patients
    if user.role == Role.PATIENT:
        from app.services.activity_tracker import get_activity_tracker
        tracker = await get_activity_tracker()
        session_id = await tracker.start_session(
            patient_id=user.user_id,
            patient_name=user.full_name,
            patient_email=user.email
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.user_id, "role": user.role.value}
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user
    )

@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """
    Get current user information
    
    - Requires valid access token
    - Returns full user profile
    """
    return current_user

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(current_user: User = Depends(get_current_active_user)):
    """
    Refresh access token
    
    - Extends token expiration
    - Returns new access token
    """
    # Create new access token
    access_token = create_access_token(
        data={"sub": current_user.user_id, "role": current_user.role.value}
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=current_user
    )

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_active_user)):
    """
    Logout user with session tracking
    
    - Ends patient session (records logout time and duration)
    - Invalidates token (client should discard)
    - Returns success message
    """
    # End session tracking for patients
    if current_user.role == Role.PATIENT:
        from app.services.activity_tracker import get_activity_tracker
        tracker = await get_activity_tracker()
        session_id = await tracker.get_active_session(current_user.user_id)
        if session_id:
            await tracker.end_session(session_id)
    
    # In production, add token to blacklist in Redis
    return {"message": "Successfully logged out", "user_id": current_user.user_id}

@router.post("/password-reset")
async def request_password_reset(reset_data: PasswordReset):
    """
    Request password reset
    
    - Sends reset token to email
    - Token expires in 1 hour
    """
    db = await get_database()
    
    # Find user by email
    user_data = await db.users.find_one({"email": reset_data.email})
    if not user_data:
        # Don't reveal if email exists
        return {"message": "If email exists, reset instructions have been sent"}
    
    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=1)
    
    # Store reset token in database
    await db.password_resets.insert_one({
        "email": reset_data.email,
        "token": reset_token,
        "expires_at": expires_at,
        "used": False
    })
    
    # TODO: Send email with reset link
    # For demo, return token
    return {
        "message": "Password reset instructions sent to email",
        "reset_token": reset_token  # Remove in production!
    }

@router.post("/password-reset/confirm")
async def confirm_password_reset(reset_data: PasswordResetConfirm):
    """
    Confirm password reset with token
    
    - Validates reset token
    - Updates password
    """
    db = await get_database()
    
    # Find valid reset token
    reset_record = await db.password_resets.find_one({
        "token": reset_data.token,
        "used": False,
        "expires_at": {"$gt": datetime.utcnow()}
    })
    
    if not reset_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Update password
    new_hashed_password = get_password_hash(reset_data.new_password)
    await db.users.update_one(
        {"email": reset_record["email"]},
        {"$set": {"hashed_password": new_hashed_password}}
    )
    
    # Mark token as used
    await db.password_resets.update_one(
        {"token": reset_data.token},
        {"$set": {"used": True}}
    )
    
    return {"message": "Password successfully reset"}

@router.get("/verify")
async def verify_token(current_user: User = Depends(get_current_active_user)):
    """
    Verify if token is valid
    
    - Returns user info if token is valid
    - Used for client-side session validation
    """
    return {
        "valid": True,
        "user_id": current_user.user_id,
        "role": current_user.role,
        "email": current_user.email
    }
