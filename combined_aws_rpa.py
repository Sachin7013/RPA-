"""
EC2 Evidence Collection RPA Script
===================================
This script automates AWS EC2 Instances evidence collection:
1. Navigates to AWS sign-in page
2. Enters email and password
3. Waits for MFA completion (30 seconds)
4. Navigates to EC2 Instances dashboard
5. Captures screenshots of dashboard and instances table
6. Returns evidence to frontend

Folders: "evidence" with subfolders "ec2_dashboard" and "ec2_instances"
"""

import os
import time
import json
from datetime import datetime
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

# Load environment variables (set 'email' and 'password' in .env file)
load_dotenv()

# ============================================================================
# FOLDER CONFIGURATION - EC2 Evidence Only
# ============================================================================
BASE_EC2_FOLDER = "evidence"
EC2_DASHBOARD_FOLDER = os.path.join(BASE_EC2_FOLDER, "ec2_dashboard")
EC2_INSTANCES_FOLDER = os.path.join(BASE_EC2_FOLDER, "ec2_instances")

# Create folders if they don't exist
folders_to_create = [BASE_EC2_FOLDER, EC2_DASHBOARD_FOLDER, EC2_INSTANCES_FOLDER]
for folder in folders_to_create:
    os.makedirs(folder, exist_ok=True)
    print(f"✅ Folder ready: {folder}")

# ============================================================================
# AWS URLs AND CREDENTIALS
# ============================================================================
AWS_CONSOLE = "https://console.aws.amazon.com/"
AWS_EC2_URL = "https://console.aws.amazon.com/ec2/v2/home"

# Get credentials from environment variables
EMAIL = os.getenv("email")
PASSWORD = os.getenv("password")

# ============================================================================
# SESSION AND LOGGING
# ============================================================================
# Timestamp for filenames and session ID
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Evidence log - tracks all steps and collected screenshots
evidence_log = {
    "session_id": timestamp,
    "start_time": datetime.now().isoformat(),
    "end_time": None,
    "status": "in_progress",
    "steps": [],
    "screenshots": [],
    "ec2_data": {"instances": []},
    "error": None
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def log_step(step_name, status="success", details=None):
    """
    Log a step in the evidence collection process.
    
    Args:
        step_name (str): Name of the step
        status (str): Status - 'info', 'success', 'failed'
        details (str): Additional details
    """
    entry = {
        "step": step_name,
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "details": details
    }
    evidence_log["steps"].append(entry)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {step_name}: {status}")
    if details:
        print(f"   Details: {details}")

def take_screenshot(page, name, description="", full_page=False, folder_type="ec2_general"):
    """
    Take a screenshot and save to the appropriate folder.
    
    Args:
        page: Playwright page object
        name (str): Screenshot filename
        description (str): Description of the screenshot
        full_page (bool): Whether to capture full page
        folder_type (str): Target folder type
    """
    # Map folder_type to target folder
    folder_map = {
        "ec2_dashboard": EC2_DASHBOARD_FOLDER,
        "ec2_instances": EC2_INSTANCES_FOLDER,
        "ec2_general": BASE_EC2_FOLDER
    }
    target_folder = folder_map.get(folder_type, BASE_EC2_FOLDER)
    screenshot_path = os.path.join(target_folder, f"{timestamp}_{name}.png")
    try:
        page.screenshot(path=screenshot_path, full_page=full_page)
        evidence_log["screenshots"].append({
            "name": name,
            "path": screenshot_path,
            "timestamp": datetime.now().isoformat(),
            "description": description,
            "folder_type": folder_type
        })
        print(f"Screenshot saved: {screenshot_path}")
        return screenshot_path
    except Exception as e:
        log_step(f"Screenshot {name}", "failed", str(e))
        return None

def take_element_screenshot(page, selector, name, description="", folder_type="ec2_general"):
    """
    Take a screenshot of a specific page element.
    
    Args:
        page: Playwright page object
        selector (str): CSS selector for the element
        name (str): Screenshot filename
        description (str): Description of the screenshot
        folder_type (str): Target folder type
    """
    folder_map = {
        "ec2_dashboard": EC2_DASHBOARD_FOLDER,
        "ec2_instances": EC2_INSTANCES_FOLDER,
        "ec2_general": BASE_EC2_FOLDER
    }
    target_folder = folder_map.get(folder_type, BASE_EC2_FOLDER)
    screenshot_path = os.path.join(target_folder, f"{timestamp}_{name}.png")
    try:
        element = page.locator(selector).first
        if element.count() > 0:
            element.screenshot(path=screenshot_path)
            evidence_log["screenshots"].append({
                "name": name,
                "path": screenshot_path,
                "timestamp": datetime.now().isoformat(),
                "description": description,
                "folder_type": folder_type,
                "element_selector": selector
            })
            print(f"Element screenshot saved: {screenshot_path}")
            return screenshot_path
        else:
            log_step(f"Element not found: {selector}", "info")
            return None
    except Exception as e:
        log_step(f"Element screenshot {name}", "failed", str(e))
        return None

def navigate_to_ec2_instances(page):
    """
    Navigate to EC2 Instances page.
    Simple direct URL navigation.
    """
    log_step("Navigating to EC2 Instances", "info")
    try:
        # Direct URL navigation (simplest method)
        instances_url = "https://console.aws.amazon.com/ec2/v2/home#Instances:"
        page.goto(instances_url)
        page.wait_for_load_state('networkidle')
        time.sleep(3)
        
        log_step("Navigated to EC2 Instances", "success")
        return True
        
    except Exception as e:
        log_step("EC2 instances navigation", "failed", str(e))
        return False

def take_ec2_screenshots(page, name_prefix, folder_type):
    """
    Take screenshots of EC2 page.
    Simple function to capture full page and viewport.
    """
    log_step(f"Taking screenshots for {name_prefix}", "info")
    try:
        # Wait for page to load
        time.sleep(2)
        
        # Take full page screenshot
        take_screenshot(page, f"{name_prefix}_full", f"{name_prefix} full page", 
                       full_page=True, folder_type=folder_type)
        
        # Take viewport screenshot
        take_screenshot(page, f"{name_prefix}_viewport", f"{name_prefix} viewport", 
                       full_page=False, folder_type=folder_type)
        
        log_step(f"Screenshots captured for {name_prefix}", "success")
        return True
    except Exception as e:
        log_step(f"Screenshot capture for {name_prefix}", "failed", str(e))
        return False

def run_aws_collection():
    """
    Main function to collect AWS EC2 evidence.
    
    Process:
    1. Validate credentials
    2. Launch browser
    3. Navigate to AWS Console and sign in
    4. Wait for MFA completion (30 seconds)
    5. Navigate to EC2 Instances
    6. Capture screenshots
    7. Save evidence log
    """
    # ================================================================
    # VALIDATE CREDENTIALS
    # ================================================================
    if not EMAIL or not PASSWORD:
        print("❌ ERROR: Email or password missing in .env file")
        exit(1)

    print(f"\n{'='*60}")
    print(f"🎯 STARTING AWS EC2 EVIDENCE COLLECTION")
    print(f"{'='*60}")
    print(f"📧 Email: {EMAIL[:3]}***")
    print(f"🕒 Session: {timestamp}")
    print(f"{'='*60}\n")
    
    log_step("Starting AWS Evidence Collection", "info", f"Email: {EMAIL[:3]}***")

    try:
        with sync_playwright() as p:
            # ================================================================
            # STEP 1: LAUNCH BROWSER
            # ================================================================
            log_step("Launching browser", "info")
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(viewport={'width': 1920, 'height': 1080})
            page = context.new_page()
            log_step("Browser launched", "success")

            # ================================================================
            # STEP 2: NAVIGATE TO AWS CONSOLE
            # ================================================================
            log_step("Navigating to AWS Console", "info")
            page.goto(AWS_CONSOLE)
            try:
                page.wait_for_load_state('networkidle', timeout=60000)
            except Exception as e:
                log_step("Page load wait", "info", f"Network idle timeout, continuing anyway: {str(e)}")
                page.wait_for_load_state('domcontentloaded', timeout=10000)
            take_screenshot(page, "01_console_home", "AWS Console home", folder_type="ec2_general")
            time.sleep(2)

            # ================================================================
            # STEP 3: SIGN IN TO AWS
            # ================================================================
            log_step("Looking for sign-in options", "info")
            try:
                # If the console shows a "Sign in" link
                if page.locator("text=Sign in").count():
                    page.click("text=Sign in")
                    log_step("Clicked Sign in button", "success")
                    time.sleep(2)
            except Exception as e:
                log_step("Sign in button click", "failed", str(e))

            # Click "Sign in using root user email" if that button exists
            try:
                if page.locator("text=Sign in using root user email").count():
                    page.click("text=Sign in using root user email")
                    log_step("Selected root user sign in", "success")
                    time.sleep(2)
            except Exception as e:
                log_step("Root user selection", "info", "Root user option not found, continuing...")

            # Fill email with enhanced selectors
            log_step("Entering email", "info")
            try:
                page.fill("input[type='email'], input#resolving_input, input[name='username'], input[name='email']", EMAIL)
                page.keyboard.press("Enter")
                log_step("Email entered successfully", "success")
                time.sleep(2)
            except Exception as e:
                log_step("Email entry", "failed", str(e))
                raise

            # Fill password with enhanced selectors
            log_step("Entering password", "info")
            try:
                page.fill("input[type='password'], input#password", PASSWORD)
                page.keyboard.press("Enter")
                log_step("Password entered successfully", "success")
                time.sleep(2)
            except Exception as e:
                log_step("Password entry", "failed", str(e))
                raise

            # Enhanced MFA and authentication waiting
            print("\n" + "="*50)
            print("If MFA is required, please complete MFA on your device now.")
            print("Waiting up to 30 seconds for authentication...")
            print("="*50 + "\n")
            
            log_step("Waiting for MFA completion", "info")
            try:
                # Wait until console home loads with enhanced detection
                max_wait_time = 30  # 30 seconds timeout
                start_time = time.time()
                authenticated = False
                
                while not authenticated and (time.time() - start_time) < max_wait_time:
                    current_url = page.url
                    log_step("Current URL check", "info", f"URL: {current_url[:100]}...")
                    
                    # Check if we're in the console (various possible indicators)
                    if any(pattern in current_url.lower() for pattern in [
                        "console.aws.amazon.com",
                        "/console/",
                        "/home",
                        "eu-north-1",  # Region indicator suggests we're in console
                        "us-east-1",
                        "us-west-2"
                    ]) and "signin" not in current_url.lower():
                        authenticated = True
                        log_step("Successfully authenticated", "success", f"Detected console URL: {current_url[:100]}...")
                        break
                    
                    # Also check for console-specific elements on the page
                    try:
                        console_elements = [
                            "[data-testid*='console']",
                            ".awsui-app-layout",
                            "nav[role='navigation']",
                            "[aria-label*='AWS']",
                            ".aws-nav",
                            "text=Console Home"
                        ]
                        
                        for selector in console_elements:
                            if page.locator(selector).count() > 0:
                                authenticated = True
                                log_step("Successfully authenticated", "success", f"Detected console element: {selector}")
                                break
                        
                        if authenticated:
                            break
                            
                    except:
                        pass
                    
                    time.sleep(1)  # Check every 1 second for faster detection
                
                if not authenticated:
                    print("\n⚠️ Authentication timeout reached!")
                    print("If you're already logged in to AWS Console, the script will continue...")
                    print("Otherwise, please complete authentication manually and press Enter to continue.")
                    
                    # Check one more time if we're actually authenticated
                    current_url = page.url
                    if any(pattern in current_url.lower() for pattern in [
                        "console.aws.amazon.com",
                        "/console/",
                        "/home"
                    ]) and "signin" not in current_url.lower():
                        log_step("Authentication detected after timeout", "success")
                        authenticated = True
                    else:
                        log_step("Proceeding without automatic authentication detection", "info")
                        # Continue anyway - user might be logged in
                
            except Exception as e:
                log_step("Authentication process", "info", f"Continuing despite error: {str(e)}")
                # Don't raise - continue with the script

            # ================================================================
            # STEP 4: COLLECT EC2 EVIDENCE
            # ================================================================
            log_step("Starting EC2 collection", "info")
            print(f"\n{'='*60}")
            print(f"🚀 STARTING EC2 EVIDENCE COLLECTION")
            print(f"{'='*60}\n")
            
            try:
                page.goto(AWS_EC2_URL)
                page.wait_for_load_state('networkidle')
                time.sleep(3)  # Wait for EC2 page to render
                log_step("EC2 Console loaded", "success")
                
                # Take screenshot of EC2 dashboard
                take_screenshot(page, "02_ec2_dashboard", "EC2 Console dashboard", folder_type="ec2_dashboard")
                
                # Navigate to EC2 Instances page
                log_step("Navigating to EC2 Instances", "info")
                if navigate_to_ec2_instances(page):
                    # Take EC2 Instances screenshots
                    take_ec2_screenshots(page, "ec2_instances", "ec2_instances")
                else:
                    log_step("EC2 instances navigation failed", "failed")
                    
            except Exception as e:
                log_step("EC2 navigation", "failed", str(e))
                take_screenshot(page, "02_ec2_failed", "Failed to load EC2 console", folder_type="ec2_dashboard")

            # ================================================================
            # FINALIZE - Save Evidence Log
            # ================================================================
            evidence_log["end_time"] = datetime.now().isoformat()
            evidence_log["status"] = "completed"
            log_file = os.path.join(BASE_EC2_FOLDER, f"{timestamp}_combined_evidence_log.json")
            with open(log_file, 'w') as f:
                json.dump(evidence_log, f, indent=2)
            print(f"\n✅ Evidence log saved: {log_file}")
            print(f"\n{'='*60}")
            print(f"🎉 EC2 EVIDENCE COLLECTION COMPLETE 🎉")
            print(f"{'='*60}")
            print(f"📁 Evidence Folder: {BASE_EC2_FOLDER}")
            print(f"📸 Total Screenshots: {len(evidence_log['screenshots'])}")
            print(f"🔖 Session ID: {timestamp}")
            print(f"{'='*60}\n")
            time.sleep(2)
            
            log_step("Closing browser", "info")
            browser.close()
            log_step("Collection completed successfully", "success")

    except Exception as e:
        log_step("Critical error", "failed", str(e))
        evidence_log["end_time"] = datetime.now().isoformat()
        evidence_log["status"] = "failed"
        evidence_log["error"] = str(e)
        log_file = os.path.join(BASE_EC2_FOLDER, f"{timestamp}_combined_evidence_log.json")
        with open(log_file, 'w') as f:
            json.dump(evidence_log, f, indent=2)
        print(f"\nERROR: {e}")
        print(f"Log saved: {log_file}")
        raise

# Allow script to be called directly or imported
if __name__ == "__main__":
    run_aws_collection()