# file: aws_console_rpa_playwright.py
import os
import time
import json
from datetime import datetime
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Create evidence folder
EVIDENCE_FOLDER = "evidence"
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

log_step("Starting AWS Console RPA", "info", f"Email: {EMAIL[:3]}***")

# Run
try:
    with sync_playwright() as p:
        # Launch a headed browser so user can do MFA on phone
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        log_step("Browser launched", "success")

        # Step 1: Open console
        log_step("Navigating to AWS Console", "info")
        page.goto(AWS_CONSOLE)
        page.wait_for_load_state('networkidle')
        take_screenshot(page, "01_aws_console_home", "AWS Console homepage")
        time.sleep(2)

        # Step 2: Click sign in flow (selectors may change; adjust if needed)
        log_step("Looking for sign-in options", "info")
        try:
            # If the console shows a "Sign in" link
            if page.locator("text=Sign in").count():
                page.click("text=Sign in")
                log_step("Clicked Sign in button", "success")
                time.sleep(2)
        except Exception as e:
            log_step("Sign in button click", "failed", str(e))

        # Click "Sign in using root user email" if that button exists (or choose IAM user path)
        try:
            if page.locator("text=Sign in using root user email").count():
                page.click("text=Sign in using root user email")
                log_step("Selected root user sign in", "success")
                time.sleep(2)
        except Exception as e:
            log_step("Root user selection", "info", "Root user option not found, continuing...")

        # Fill email
        log_step("Entering email", "info")
        try:
            page.fill("input[type='email'], input#resolving_input, input[name='username'], input[name='email']", EMAIL)
            page.keyboard.press("Enter")
            log_step("Email entered successfully", "success")
            time.sleep(2)
        except Exception as e:
            log_step("Email entry", "failed", str(e))
            raise

        # Fill password - different pages may have different selectors
        log_step("Entering password", "info")
        try:
            page.fill("input[type='password'], input#password", PASSWORD)
            page.keyboard.press("Enter")
            log_step("Password entered successfully", "success")
            time.sleep(2)
        except Exception as e:
            log_step("Password entry", "failed", str(e))
            raise

        print("\n" + "="*60)
        print("If MFA is required, please complete MFA on your device now.")
        print("Waiting up to 10 minutes for authentication...")
        print("="*60 + "\n")
        
        log_step("Waiting for MFA completion", "info")
        try:
            # Wait until console home loads; longer timeout to allow manual MFA
            page.wait_for_url("**/console/**", timeout=600000)  # 10 minutes max
            log_step("Successfully authenticated", "success")
        except Exception as e:
            log_step("Authentication timeout", "failed", str(e))
            raise

        # Navigate to EC2
        log_step("Navigating to EC2 Console", "info")
        try:
            page.goto(AWS_EC2_URL)
            page.wait_for_load_state('networkidle')
            time.sleep(3)  # wait for EC2 page to render
            log_step("EC2 Console loaded", "success")
            
            # Take screenshot of EC2 dashboard
            take_screenshot(page, "07_ec2_dashboard", "EC2 Console dashboard")
            
            # Navigate to EC2 Instances specifically
            log_step("Navigating to EC2 Instances", "info")
            try:
                # Wait for the left sidebar to be visible
                page.wait_for_selector("nav, [role='navigation'], .awsui-side-navigation", timeout=10000)
                time.sleep(2)
                
                # Click on Instances in the left sidebar - try multiple selectors
                instances_selectors = [
                    # Target the left sidebar instances link specifically
                    "nav a[href*='Instances'], [role='navigation'] a[href*='Instances']",
                    "a[href*='#Instances']",
                    ".awsui-side-navigation a[href*='Instances']",
                    # Text-based selectors for the sidebar
                    "nav >> text=Instances",
                    "[role='navigation'] >> text=Instances",
                    # More specific selectors
                    "a[data-testid*='instances']",
                    "a[href*='/ec2/v2/home'][href*='Instances']",
                    # Fallback text selector
                    "text=Instances"
                ]
                
                clicked = False
                for selector in instances_selectors:
                    try:
                        elements = page.locator(selector)
                        if elements.count() > 0:
                            # If multiple elements, try to find the one in the sidebar
                            for i in range(elements.count()):
                                element = elements.nth(i)
                                # Check if this element is likely in the sidebar (left side of screen)
                                box = element.bounding_box()
                                if box and box['x'] < 400:  # Left side of screen
                                    element.click()
                                    clicked = True
                                    log_step("Clicked Instances link in sidebar", "success", f"Using selector: {selector}")
                                    break
                            if clicked:
                                break
                            # If no sidebar element found, click the first one
                            elements.first.click()
                            clicked = True
                            log_step("Clicked Instances link", "success", f"Using selector: {selector}")
                            break
                    except Exception as e:
                        log_step("Selector attempt", "info", f"Failed selector {selector}: {str(e)}")
                        continue
                
                if not clicked:
                    log_step("All selectors failed, trying direct URL navigation", "info")
                    # Try direct URL navigation to instances
                    instances_url = "https://console.aws.amazon.com/ec2/v2/home#Instances:"
                    page.goto(instances_url)
                    log_step("Navigated directly to instances URL", "info")
                
                # Wait for the instances page to load
                page.wait_for_load_state('networkidle')
                time.sleep(3)
                
                # Additional wait for instances table to appear
                try:
                    page.wait_for_selector("table, [role='table'], .instances-table, [data-testid*='table']", timeout=15000)
                    log_step("Instances table detected", "success.")
                except:
                    log_step("Instances table wait timeout", "info", "Continuing anyway...")
                
                time.sleep(2)  # Additional wait for full rendering
                
                # Take screenshot of instances page - full page first
                take_screenshot(page, "08_ec2_instances_full", "EC2 Instances page (full page)", full_page=True)
                
                # Take a viewport screenshot for better visibility of current content
                take_screenshot(page, "09_ec2_instances_viewport", "EC2 Instances page (viewport)", full_page=False)
                
                # Try to take a more focused screenshot of just the instances table/content area
                try:
                    # Look for the instances table/container with improved selectors
                    table_selectors = [
                        # AWS Console specific selectors
                        "[data-testid*='instances-table']",
                        "[data-testid*='table']",
                        ".awsui-table",
                        ".instances-table",
                        "[role='table']",
                        ".ec2-instances-table",
                        "#instances",
                        # Content area selectors
                        "[data-testid*='content']",
                        ".awsui-app-layout-content",
                        "main",
                        "[role='main']"
                    ]
                    
                    table_found = False
                    for selector in table_selectors:
                        try:
                            elements = page.locator(selector)
                            if elements.count() > 0:
                                # Take screenshot of the element
                                element = elements.first
                                table_screenshot_path = os.path.join(EVIDENCE_FOLDER, f"{timestamp}_10_ec2_instances_table.png")
                                element.screenshot(path=table_screenshot_path)
                                evidence_log["screenshots"].append({
                                    "name": "10_ec2_instances_table",
                                    "path": table_screenshot_path,
                                    "timestamp": datetime.now().isoformat(),
                                    "description": f"EC2 Instances table/content area (selector: {selector})"
                                })
                                log_step("EC2 instances table screenshot taken", "success", f"Using selector: {selector}")
                                print(f"Table screenshot saved: {table_screenshot_path}")
                                table_found = True
                                break
                        except Exception as e:
                            log_step("Table selector attempt", "info", f"Failed selector {selector}: {str(e)}")
                            continue
                    
                    if not table_found:
                        log_step("EC2 instances table not found", "info", "All table selectors failed")
                        
                except Exception as e:
                    log_step("Focused instances screenshot", "failed", str(e))
                
                # Additional check - try to scroll and capture if there are instances
                try:
                    # Check if there are any instances visible
                    instance_rows = page.locator("tr, .instance-row, [data-testid*='instance']").count()
                    if instance_rows > 0:
                        log_step("EC2 instances detected", "success", f"Found {instance_rows} instance elements")
                        
                        # Scroll to make sure all instances are visible
                        page.keyboard.press("Home")  # Go to top
                        time.sleep(1)
                        
                        # Take another screenshot after scrolling
                        take_screenshot(page, "11_ec2_instances_scrolled", "EC2 Instances after scroll to top")
                    else:
                        log_step("No EC2 instances found", "info", "No instances visible on the page")
                        
                except Exception as e:
                    log_step("Instance detection", "info", f"Could not detect instances: {str(e)}")
                
                log_step("EC2 Instances page loaded", "success")
                
            except Exception as e:
                log_step("EC2 instances navigation", "failed", str(e))
                
        except Exception as e:
            log_step("EC2 navigation", "failed", str(e))
            take_screenshot(page, "07_ec2_failed", "Failed to load EC2 console")

        # Final evidence collection
        evidence_log["end_time"] = datetime.now().isoformat()
        evidence_log["status"] = "completed"
        
        # Save evidence log
        log_file = os.path.join(EVIDENCE_FOLDER, f"{timestamp}_evidence_log.json")
        with open(log_file, 'w') as f:
            json.dump(evidence_log, f, indent=2)
        print(f"\nEvidence log saved: {log_file}")
        
        print(f"\n" + "="*60)
        print("AWS RPA COMPLETED SUCCESSFULLY")
        print(f"Evidence folder: {EVIDENCE_FOLDER}")
        print(f"Screenshots taken: {len(evidence_log['screenshots'])}")
        print(f"Session ID: {timestamp}")
        print("="*60)

        # Keep browser open for manual inspection
        input("\nPress Enter to close the browser...")
        browser.close()
        
except Exception as e:
    log_step("Critical error", "failed", str(e))
    evidence_log["end_time"] = datetime.now().isoformat()
    evidence_log["status"] = "failed"
    evidence_log["error"] = str(e)
    
    # Save evidence log even on failure
    log_file = os.path.join(EVIDENCE_FOLDER, f"{timestamp}_evidence_log.json")
    with open(log_file, 'w') as f:
        json.dump(evidence_log, f, indent=2)
    
    print(f"\nERROR: {e}")
    print(f"Evidence log saved: {log_file}")
    raise
