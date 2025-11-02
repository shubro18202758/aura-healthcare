"""
Medical Documents Router for AURA Healthcare System
Handles document uploads, storage, and retrieval for medical records
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from pydantic import BaseModel
import secrets
import os
import json
from pathlib import Path

from app.config import get_settings
from app.database import get_database
from app.models import User, Role
from app.routers.auth import get_current_active_user

router = APIRouter(prefix="/api/medical-documents", tags=["medical-documents"])
settings = get_settings()

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads/medical_documents")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Allowed file types
ALLOWED_EXTENSIONS = {
    'pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx', 
    'txt', 'csv', 'xlsx', 'dicom'
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

class MedicalDocument(BaseModel):
    document_id: str
    patient_id: str
    conversation_id: Optional[str] = None
    document_type: str  # lab_report, prescription, xray, mri, ct_scan, other
    file_name: str
    file_path: str
    file_size: int
    mime_type: str
    description: Optional[str] = None
    uploaded_at: datetime
    uploaded_by: str  # user_id who uploaded
    tags: List[str] = []
    is_active: bool = True

class DocumentUploadResponse(BaseModel):
    document_id: str
    file_name: str
    message: str

def get_file_extension(filename: str) -> str:
    """Extract file extension"""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

def is_allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return get_file_extension(filename) in ALLOWED_EXTENSIONS

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_medical_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    conversation_id: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # Comma-separated tags
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload medical document (lab reports, prescriptions, x-rays, etc.)
    
    - Patients can upload their own documents
    - Doctors can upload documents for patients
    - Files are stored securely with unique IDs
    - Supports various medical document formats
    """
    
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    if not is_allowed_file(file.filename):
        raise HTTPException(
            status_code=400, 
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Read file content
    file_content = await file.read()
    file_size = len(file_content)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024)}MB"
        )
    
    # Generate unique document ID and filename
    document_id = f"doc_{secrets.token_hex(16)}"
    file_extension = get_file_extension(file.filename)
    stored_filename = f"{document_id}.{file_extension}"
    file_path = UPLOAD_DIR / stored_filename
    
    # Save file
    with open(file_path, 'wb') as f:
        f.write(file_content)
    
    # Parse tags
    tag_list = [tag.strip() for tag in tags.split(',')] if tags else []
    
    # Determine patient_id
    patient_id = current_user.user_id if current_user.role == Role.PATIENT else None
    if current_user.role == Role.DOCTOR and not patient_id:
        # For doctors, patient_id should be provided via conversation_id
        if conversation_id:
            db = await get_database()
            conv = await db.conversations.find_one({"conversation_id": conversation_id})
            if conv:
                patient_id = conv.get("patient_id")
    
    if not patient_id:
        raise HTTPException(
            status_code=400,
            detail="Could not determine patient ID"
        )
    
    # Create document record
    document = MedicalDocument(
        document_id=document_id,
        patient_id=patient_id,
        conversation_id=conversation_id,
        document_type=document_type,
        file_name=file.filename,
        file_path=str(file_path),
        file_size=file_size,
        mime_type=file.content_type or 'application/octet-stream',
        description=description,
        uploaded_at=datetime.utcnow(),
        uploaded_by=current_user.user_id,
        tags=tag_list
    )
    
    # Save to database
    db = await get_database()
    await db.medical_documents.insert_one(document.dict())
    
    return DocumentUploadResponse(
        document_id=document_id,
        file_name=file.filename,
        message="Document uploaded successfully"
    )

@router.get("/", response_model=List[MedicalDocument])
async def list_medical_documents(
    conversation_id: Optional[str] = None,
    document_type: Optional[str] = None,
    patient_id: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user)
):
    """
    List medical documents
    
    - Patients see only their documents
    - Doctors see documents for their patients
    """
    db = await get_database()
    
    query = {"is_active": True}
    
    # Apply role-based filtering
    if current_user.role == Role.PATIENT:
        query["patient_id"] = current_user.user_id
    elif current_user.role == Role.DOCTOR:
        if patient_id:
            query["patient_id"] = patient_id
        # For doctors, we might want to show all documents they have access to
    
    if conversation_id:
        query["conversation_id"] = conversation_id
    
    if document_type:
        query["document_type"] = document_type
    
    documents_data = await db.medical_documents.find(query).sort(
        "uploaded_at", -1
    ).limit(limit).to_list(None)
    
    return [MedicalDocument(**doc) for doc in documents_data]

@router.get("/{document_id}", response_model=MedicalDocument)
async def get_document_details(
    document_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get document metadata"""
    db = await get_database()
    
    doc_data = await db.medical_documents.find_one({
        "document_id": document_id,
        "is_active": True
    })
    
    if not doc_data:
        raise HTTPException(status_code=404, detail="Document not found")
    
    document = MedicalDocument(**doc_data)
    
    # Check permissions
    if current_user.role == Role.PATIENT:
        if document.patient_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    return document

@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Soft delete document"""
    db = await get_database()
    
    doc_data = await db.medical_documents.find_one({
        "document_id": document_id,
        "is_active": True
    })
    
    if not doc_data:
        raise HTTPException(status_code=404, detail="Document not found")
    
    document = MedicalDocument(**doc_data)
    
    # Check permissions
    if current_user.role == Role.PATIENT:
        if document.patient_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Access denied")
    elif current_user.role == Role.DOCTOR:
        if document.uploaded_by != current_user.user_id:
            raise HTTPException(status_code=403, detail="Can only delete documents you uploaded")
    
    # Soft delete
    await db.medical_documents.update_one(
        {"document_id": document_id},
        {"$set": {"is_active": False}}
    )
    
    return {"message": "Document deleted successfully"}

@router.get("/conversation/{conversation_id}/summary")
async def get_conversation_documents_summary(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get summary of all documents in a conversation"""
    db = await get_database()
    
    documents = await db.medical_documents.find({
        "conversation_id": conversation_id,
        "is_active": True
    }).to_list(None)
    
    summary = {
        "total_documents": len(documents),
        "by_type": {},
        "total_size_mb": sum(doc["file_size"] for doc in documents) / (1024 * 1024),
        "documents": [
            {
                "document_id": doc["document_id"],
                "file_name": doc["file_name"],
                "document_type": doc["document_type"],
                "uploaded_at": doc["uploaded_at"]
            }
            for doc in documents
        ]
    }
    
    # Count by type
    for doc in documents:
        doc_type = doc["document_type"]
        summary["by_type"][doc_type] = summary["by_type"].get(doc_type, 0) + 1
    
    return summary
