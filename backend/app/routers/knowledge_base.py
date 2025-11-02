"""
Knowledge Base Router for AURA Healthcare System
Handles specialty-specific medical knowledge management by doctors
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime
import time

from app.database import get_database
from app.models import (
    KnowledgeBaseEntry, KnowledgeBaseCreate, KnowledgeBaseUpdate,
    KnowledgeBaseResponse, User, Role
)
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/knowledge-base", tags=["knowledge-base"])


@router.post("/entries", response_model=KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge_entry(
    entry: KnowledgeBaseCreate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Create a new knowledge base entry (Doctor only)
    Doctors can add specialty-specific questions and context
    """
    # Check if user is a doctor
    if current_user.role != Role.DOCTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can create knowledge base entries"
        )
    
    # Check if doctor has a specialty
    if not current_user.specialty:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Doctor must have a specialty assigned to create knowledge base entries"
        )
    
    # Create entry
    entry_id = f"kb_{int(time.time() * 1000)}_{current_user.user_id}"
    
    kb_entry = {
        "entry_id": entry_id,
        "doctor_id": current_user.user_id,
        "doctor_name": current_user.full_name,
        "specialty": current_user.specialty,
        "topic": entry.topic,
        "questions": entry.questions,
        "context": entry.context,
        "keywords": entry.keywords,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "is_active": True
    }
    
    await db.knowledge_base.insert_one(kb_entry)
    
    return KnowledgeBaseResponse(**kb_entry)


@router.get("/entries", response_model=List[KnowledgeBaseResponse])
async def get_knowledge_entries(
    specialty: Optional[str] = None,
    is_active: Optional[bool] = True,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    Get knowledge base entries
    - Doctors can see their own entries
    - Patients can see entries for their specialty
    - Filter by specialty and active status
    """
    query = {}
    
    # Build query based on user role
    if current_user.role == Role.DOCTOR:
        # Doctors see only their own entries
        query["doctor_id"] = current_user.user_id
    elif current_user.role == Role.PATIENT:
        # Patients see entries for their specialty (if assigned)
        if current_user.specialty:
            query["specialty"] = current_user.specialty
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Patient must have a specialty assigned to view knowledge base"
            )
    
    # Apply filters
    if specialty and current_user.role == Role.DOCTOR:
        query["specialty"] = specialty
    
    if is_active is not None:
        query["is_active"] = is_active
    
    # Fetch entries
    cursor = db.knowledge_base.find(query)
    entries = await cursor.to_list(length=100)
    
    return [KnowledgeBaseResponse(**entry) for entry in entries]


@router.get("/entries/specialty/{specialty}", response_model=List[KnowledgeBaseResponse])
async def get_entries_by_specialty(
    specialty: str,
    db = Depends(get_database)
):
    """
    Get all active knowledge base entries for a specific specialty
    Used by AI system to fetch relevant context
    """
    query = {
        "specialty": specialty,
        "is_active": True
    }
    
    cursor = db.knowledge_base.find(query).sort("created_at", -1)
    entries = await cursor.to_list(length=100)
    
    return [KnowledgeBaseResponse(**entry) for entry in entries]


@router.get("/entries/{entry_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_entry(
    entry_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get a specific knowledge base entry"""
    entry = await db.knowledge_base.find_one({"entry_id": entry_id})
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base entry not found"
        )
    
    # Check access permissions
    if current_user.role == Role.DOCTOR and entry["doctor_id"] != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own knowledge base entries"
        )
    
    return KnowledgeBaseResponse(**entry)


@router.put("/entries/{entry_id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_entry(
    entry_id: str,
    update_data: KnowledgeBaseUpdate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Update a knowledge base entry (Doctor only - own entries)"""
    if current_user.role != Role.DOCTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can update knowledge base entries"
        )
    
    # Find entry
    entry = await db.knowledge_base.find_one({"entry_id": entry_id})
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base entry not found"
        )
    
    # Check ownership
    if entry["doctor_id"] != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own knowledge base entries"
        )
    
    # Prepare update
    update_dict = update_data.dict(exclude_unset=True)
    update_dict["updated_at"] = datetime.utcnow()
    
    # Update entry
    await db.knowledge_base.update_one(
        {"entry_id": entry_id},
        {"$set": update_dict}
    )
    
    # Fetch updated entry
    updated_entry = await db.knowledge_base.find_one({"entry_id": entry_id})
    
    return KnowledgeBaseResponse(**updated_entry)


@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_entry(
    entry_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_database)
):
    """Delete a knowledge base entry (Doctor only - own entries)"""
    if current_user.role != Role.DOCTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can delete knowledge base entries"
        )
    
    # Find entry
    entry = await db.knowledge_base.find_one({"entry_id": entry_id})
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base entry not found"
        )
    
    # Check ownership
    if entry["doctor_id"] != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own knowledge base entries"
        )
    
    # Soft delete (set is_active to False)
    await db.knowledge_base.update_one(
        {"entry_id": entry_id},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    
    return None


@router.get("/specialties", response_model=List[str])
async def get_available_specialties(db = Depends(get_database)):
    """Get list of specialties that have knowledge base entries"""
    specialties = await db.knowledge_base.distinct("specialty", {"is_active": True})
    return sorted(specialties)
