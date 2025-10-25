from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
from typing import List, Dict, Optional
import subprocess
import os
from datetime import datetime
import time
import json
import zipfile
import io

router = APIRouter()

class AWSCredentials(BaseModel):
    email: str
    password: str

# ============================================================================
# SIMPLE JOB STATE
# ============================================================================
current_job = {
    "is_running": False,
    "progress": 0,
    "status": "Ready",
    "message": "Waiting to start",
    "error": None,
    "job_id": None,
    "screenshots": []
}

def get_ec2_screenshots() -> List[str]:
    """
    Get all EC2 screenshots from evidence folder.
    Returns list of screenshot URLs.
    """
    folder_path = Path("evidence")
    if not folder_path.exists():
        return []
    
    screenshots = []
    for png_file in folder_path.rglob("*.png"):
        # Convert to URL path
        relative_path = png_file.relative_to(Path("."))
        url_path = "/" + str(relative_path).replace("\\", "/")
        screenshots.append(url_path)
    
    # Sort by modification time (newest first)
    screenshots.sort(key=lambda x: Path(x[1:]).stat().st_mtime, reverse=True)
    return screenshots

def run_ec2_rpa(email: str, password: str):
    """
    Simple function to run EC2 RPA script.
    Just runs the script and updates job status.
    """
    global current_job
    
    try:
        # Initialize job
        job_id = f"aws-{int(time.time())}"
        current_job["is_running"] = True
        current_job["progress"] = 10
        current_job["status"] = "Starting"
        current_job["message"] = "Starting EC2 collection..."
        current_job["job_id"] = job_id
        current_job["error"] = None
        
        # Set environment variables
        env = os.environ.copy()
        env['email'] = email
        env['password'] = password
        
        # Update progress
        current_job["progress"] = 30
        current_job["status"] = "Running"
        current_job["message"] = "Running RPA script..."
        
        # Run the script
        result = subprocess.run(
            ["python", "combined_aws_rpa.py"],
            env=env,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
            cwd=os.getcwd()
        )
        
        # Check result
        if result.returncode == 0:
            # Success - get screenshots
            screenshots = get_ec2_screenshots()
            current_job["screenshots"] = screenshots
            current_job["progress"] = 100
            current_job["status"] = "Complete"
            current_job["message"] = f"Collection complete! Found {len(screenshots)} screenshots"
        else:
            raise Exception(f"Script failed: {result.stderr[:200]}")
            
    except Exception as e:
        # Handle any errors
        current_job["is_running"] = False
        current_job["progress"] = 0
        current_job["status"] = "Failed"
        current_job["message"] = f"Error: {str(e)}"
        current_job["error"] = str(e)
    
    finally:
        current_job["is_running"] = False

# ============================================================================
# API ENDPOINTS - Simple and Clear
# ============================================================================
@router.post("/awsrpa/start-collection")
async def start_collection(request: Request, background_tasks: BackgroundTasks):
    """Start EC2 collection - Simple endpoint."""
    global current_job
    
    # Check if already running
    if current_job["is_running"]:
        raise HTTPException(status_code=400, detail="Already running")
    
    # Get credentials
    data = await request.json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")
    
    # Create job ID
    job_id = f"aws-{int(time.time())}"
    current_job["job_id"] = job_id
    
    # Run in background
    background_tasks.add_task(run_ec2_rpa, email, password)
    
    return {"success": True, "jobId": job_id}

@router.get("/awsrpa/status/{job_id}")
async def get_status(job_id: str):
    """Get collection status - Simple endpoint."""
    return {
        "jobId": job_id,
        "progress": current_job["progress"],
        "status": current_job["status"],
        "message": current_job["message"],
        "error": current_job["error"],
        "isRunning": current_job["is_running"],
        "isComplete": current_job["progress"] == 100
    }

@router.get("/awsrpa/screenshots/{job_id}")
async def get_screenshots(job_id: str):
    """Get all EC2 screenshots - Simple endpoint."""
    screenshots = get_ec2_screenshots()
    return {
        "jobId": job_id,
        "screenshots": screenshots,
        "count": len(screenshots)
    }

@router.get("/health")
async def health_check():
    """Simple health check."""
    return {
        "status": "healthy",
        "message": "API is running",
        "jobRunning": current_job["is_running"],
        "progress": current_job["progress"]
    }