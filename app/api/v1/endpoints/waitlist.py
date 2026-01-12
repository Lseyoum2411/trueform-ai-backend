from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from datetime import datetime
import json
import os
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class WaitlistEntry(BaseModel):
    email: EmailStr
    name: str
    sport: str

class WaitlistCheckResponse(BaseModel):
    approved: bool
    on_waitlist: bool

class ApproveRequest(BaseModel):
    email: EmailStr

# Simple file-based storage (use database in production)
WAITLIST_DIR = "data"
WAITLIST_FILE = os.path.join(WAITLIST_DIR, "waitlist.json")

def ensure_waitlist_file():
    """Ensure waitlist file exists"""
    os.makedirs(WAITLIST_DIR, exist_ok=True)
    if not os.path.exists(WAITLIST_FILE):
        with open(WAITLIST_FILE, 'w') as f:
            json.dump([], f)

def load_waitlist() -> List[Dict]:
    """Load waitlist from file"""
    ensure_waitlist_file()
    try:
        with open(WAITLIST_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_waitlist(waitlist: List[Dict]):
    """Save waitlist to file"""
    ensure_waitlist_file()
    with open(WAITLIST_FILE, 'w') as f:
        json.dump(waitlist, f, indent=2)

@router.post("/waitlist/join")
async def join_waitlist(entry: WaitlistEntry):
    """Add user to waitlist"""
    
    waitlist = load_waitlist()
    
    # Check if email already exists
    if any(item['email'] == entry.email for item in waitlist):
        raise HTTPException(status_code=400, detail="Email already on waitlist")
    
    # Add new entry
    waitlist.append({
        "email": entry.email,
        "name": entry.name,
        "sport": entry.sport,
        "joined_at": datetime.now().isoformat(),
        "approved": False
    })
    
    # Save waitlist
    save_waitlist(waitlist)
    
    logger.info(f"New waitlist entry: {entry.email} ({entry.sport})")
    
    return {"message": "Successfully joined waitlist"}

@router.get("/waitlist/check/{email}")
async def check_waitlist_status(email: str) -> WaitlistCheckResponse:
    """Check if user is approved"""
    waitlist = load_waitlist()
    
    user = next((item for item in waitlist if item['email'] == email), None)
    
    if not user:
        return WaitlistCheckResponse(approved=False, on_waitlist=False)
    
    return WaitlistCheckResponse(
        approved=user.get("approved", False),
        on_waitlist=True
    )

@router.get("/waitlist/list")
async def list_waitlist():
    """List all waitlist entries (admin only - add auth in production)"""
    waitlist = load_waitlist()
    return waitlist

@router.post("/waitlist/approve")
async def approve_user(request: ApproveRequest):
    """Approve a user (admin only - add auth in production)"""
    waitlist = load_waitlist()
    
    user_index = next((i for i, item in enumerate(waitlist) if item['email'] == request.email), None)
    
    if user_index is None:
        raise HTTPException(status_code=404, detail="User not found on waitlist")
    
    waitlist[user_index]["approved"] = True
    waitlist[user_index]["approved_at"] = datetime.now().isoformat()
    
    save_waitlist(waitlist)
    
    logger.info(f"Approved user: {request.email}")
    
    return {"message": "User approved successfully"}



