import os
import time
import json
from datetime import datetime
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Create evidence folder
EVIDENCE_FOLDER = "s3_evidence"
if not os.path.exists(EVIDENCE_FOLDER):
    os.makedirs(EVIDENCE_FOLDER)
    print(f"Created evidence folder: {EVIDENCE_FOLDER}")

# CONFIG - change these
AWS_CONSOLE = "https://console.aws.amazon.com/"
AWS_EC2_URL = "https://console.aws.amazon.com/ec2/v2/home"
EMAIL = os.getenv("email")        # set in env: AWS_RPA_EMAIL
PASSWORD = os.getenv("password")  # set in env securely before running

# Evidence collection setup
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
evidence_log = {
    "session_id": timestamp,
    "start_time": datetime.now().isoformat(),
    "steps": [],
    "screenshots": []
}

def log_step(step_name, status="success", details=None):
    """Log a step in the evidence collection"""
    evidence_log["steps"].append({
        "step": step_name,
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "details": details
    })
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {step_name}: {status}")

def take_screenshot(page, name, description="", full_page=False):
    """Take screenshot and save to evidence folder"""
    screenshot_path = os.path.join(EVIDENCE_FOLDER, f"{timestamp}_{name}.png")
    try:
        page.screenshot(path=screenshot_path, full_page=full_page)
        evidence_log["screenshots"].append({
            "name": name,
            "path": screenshot_path,
            "timestamp": datetime.now().isoformat(),
            "description": description
        })
        print(f"Screenshot saved: {screenshot_path}")
        return screenshot_path
    except Exception as e:
        log_step(f"Screenshot {name}", "failed", str(e))
        return None

# Validate credentials
if not EMAIL or not PASSWORD:
    print("ERROR: Email or password not found in environment variables")
    print("Please check your .env file contains 'email' and 'password'")
    exit(1)