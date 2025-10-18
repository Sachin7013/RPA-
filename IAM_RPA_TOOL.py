# file: aws_iam_rpa_playwright.py
import os
import time
import json
from datetime import datetime
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Create evidence folder
EVIDENCE_FOLDER = "iam_evidence"
if not os.path.exists(EVIDENCE_FOLDER):
    os.makedirs(EVIDENCE_FOLDER)
    print(f"Created evidence folder: {EVIDENCE_FOLDER}")

# CONFIG - change these
AWS_CONSOLE = "https://console.aws.amazon.com/"
AWS_IAM_URL = "https://console.aws.amazon.com/iam/home"
EMAIL = os.getenv("email")        # set in env: AWS_RPA_EMAIL
PASSWORD = os.getenv("password")  # set in env securely before running

# Evidence collection setup
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
evidence_log = {
    "session_id": timestamp,
    "start_time": datetime.now().isoformat(),
    "steps": [],
    "screenshots": [],
    "iam_data": {
        "users": [],
        "groups": [],
        "roles": []
    }
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

def take_element_screenshot(page, selector, name, description=""):
    """Take screenshot of a specific element"""
    screenshot_path = os.path.join(EVIDENCE_FOLDER, f"{timestamp}_{name}.png")
    try:
        element = page.locator(selector).first
        if element.count() > 0:
            element.screenshot(path=screenshot_path)
            evidence_log["screenshots"].append({
                "name": name,
                "path": screenshot_path,
                "timestamp": datetime.now().isoformat(),
                "description": description
            })
            log_step(f"Element screenshot taken: {name}", "success", f"Selector: {selector}")
            print(f"Element screenshot saved: {screenshot_path}")
            return screenshot_path
        else:
            log_step(f"Element not found for screenshot: {name}", "failed", f"Selector: {selector}")
            return None
    except Exception as e:
        log_step(f"Element screenshot {name}", "failed", str(e))
        return None

def navigate_to_iam_section(page, section_name, url_fragment):
    """Navigate to a specific IAM section (Users, Groups, or Roles)"""
    log_step(f"Navigating to IAM {section_name}", "info")
    try:
        # Try multiple navigation methods
        navigation_methods = [
            # Method 1: Click sidebar link
            lambda: page.click(f"nav a[href*='{url_fragment}'], [role='navigation'] a[href*='{url_fragment}']"),
            # Method 2: Click text link in sidebar
            lambda: page.click(f"nav >> text={section_name}"),
            # Method 3: Direct URL navigation
            lambda: page.goto(f"https://console.aws.amazon.com/iam/home#{url_fragment}")
        ]
        
        success = False
        for i, method in enumerate(navigation_methods):
            try:
                method()
                page.wait_for_load_state('networkidle')
                time.sleep(2)
                success = True
                log_step(f"Successfully navigated to IAM {section_name}", "success", f"Method {i+1}")
                break
            except Exception as e:
                log_step(f"Navigation method {i+1} failed", "info", str(e))
                continue
        
        if not success:
            raise Exception(f"All navigation methods failed for {section_name}")
            
        return True
    except Exception as e:
        log_step(f"IAM {section_name} navigation", "failed", str(e))
        return False

def collect_iam_users(page):
    """Collect IAM Users data and screenshots"""
    log_step("Starting IAM Users collection", "info")
    
    if not navigate_to_iam_section(page, "Users", "users"):
        return False
    
    try:
        # Wait for users page to load
        page.wait_for_selector("table, [role='table'], .users-table, [data-testid*='table']", timeout=15000)
        time.sleep(3)
        
        # Take full page screenshot of users
        take_screenshot(page, "iam_users_full", "IAM Users page (full page)", full_page=True)
        
        # Take viewport screenshot
        take_screenshot(page, "iam_users_viewport", "IAM Users page (viewport)", full_page=False)
        
        # Try to capture the users table specifically
        table_selectors = [
            "[data-testid*='users-table']",
            "[data-testid*='table']",
            ".awsui-table",
            ".users-table",
            "[role='table']",
            "table",
            "[data-testid*='content']",
            ".awsui-app-layout-content"
        ]
        
        for selector in table_selectors:
            if take_element_screenshot(page, selector, "iam_users_table", f"IAM Users table (selector: {selector})"):
                break
        
        # Try to collect user names for evidence log
        try:
            user_elements = page.locator("tr td:first-child, .user-name, [data-testid*='user-name']")
            user_count = user_elements.count()
            if user_count > 0:
                users_data = []
                for i in range(min(user_count, 50)):  # Limit to 50 users
                    try:
                        user_text = user_elements.nth(i).text_content()
                        if user_text and user_text.strip():
                            users_data.append(user_text.strip())
                    except:
                        continue
                
                evidence_log["iam_data"]["users"] = users_data
                log_step("IAM Users data collected", "success", f"Found {len(users_data)} users")
            else:
                log_step("No IAM users found", "info")
        except Exception as e:
            log_step("IAM users data extraction", "failed", str(e))
        
        log_step("IAM Users collection completed", "success")
        return True
        
    except Exception as e:
        log_step("IAM Users collection", "failed", str(e))
        return False

def collect_iam_groups(page):
    """Collect IAM Groups data and screenshots"""
    log_step("Starting IAM Groups collection", "info")
    
    if not navigate_to_iam_section(page, "Groups", "groups"):
        return False
    
    try:
        # Wait for groups page to load
        page.wait_for_selector("table, [role='table'], .groups-table, [data-testid*='table']", timeout=15000)
        time.sleep(3)
        
        # Take full page screenshot of groups
        take_screenshot(page, "iam_groups_full", "IAM Groups page (full page)", full_page=True)
        
        # Take viewport screenshot
        take_screenshot(page, "iam_groups_viewport", "IAM Groups page (viewport)", full_page=False)
        
        # Try to capture the groups table specifically
        table_selectors = [
            "[data-testid*='groups-table']",
            "[data-testid*='table']",
            ".awsui-table",
            ".groups-table",
            "[role='table']",
            "table",
            "[data-testid*='content']",
            ".awsui-app-layout-content"
        ]
        
        for selector in table_selectors:
            if take_element_screenshot(page, selector, "iam_groups_table", f"IAM Groups table (selector: {selector})"):
                break
        
        # Try to collect group names for evidence log
        try:
            group_elements = page.locator("tr td:first-child, .group-name, [data-testid*='group-name']")
            group_count = group_elements.count()
            if group_count > 0:
                groups_data = []
                for i in range(min(group_count, 50)):  # Limit to 50 groups
                    try:
                        group_text = group_elements.nth(i).text_content()
                        if group_text and group_text.strip():
                            groups_data.append(group_text.strip())
                    except:
                        continue
                
                evidence_log["iam_data"]["groups"] = groups_data
                log_step("IAM Groups data collected", "success", f"Found {len(groups_data)} groups")
            else:
                log_step("No IAM groups found", "info")
        except Exception as e:
            log_step("IAM groups data extraction", "failed", str(e))
        
        log_step("IAM Groups collection completed", "success")
        return True
        
    except Exception as e:
        log_step("IAM Groups collection", "failed", str(e))
        return False

def collect_iam_roles(page):
    """Collect IAM Roles data and screenshots"""
    log_step("Starting IAM Roles collection", "info")
    
    if not navigate_to_iam_section(page, "Roles", "roles"):
        return False
    
    try:
        # Wait for roles page to load
        page.wait_for_selector("table, [role='table'], .roles-table, [data-testid*='table']", timeout=15000)
        time.sleep(3)
        
        # Take full page screenshot of roles
        take_screenshot(page, "iam_roles_full", "IAM Roles page (full page)", full_page=True)
        
        # Take viewport screenshot
        take_screenshot(page, "iam_roles_viewport", "IAM Roles page (viewport)", full_page=False)
        
        # Try to capture the roles table specifically
        table_selectors = [
            "[data-testid*='roles-table']",
            "[data-testid*='table']",
            ".awsui-table",
            ".roles-table",
            "[role='table']",
            "table",
            "[data-testid*='content']",
            ".awsui-app-layout-content"
        ]
        
        for selector in table_selectors:
            if take_element_screenshot(page, selector, "iam_roles_table", f"IAM Roles table (selector: {selector})"):
                break
        
        # Try to collect role names for evidence log
        try:
            role_elements = page.locator("tr td:first-child, .role-name, [data-testid*='role-name']")
            role_count = role_elements.count()
            if role_count > 0:
                roles_data = []
                for i in range(min(role_count, 50)):  # Limit to 50 roles
                    try:
                        role_text = role_elements.nth(i).text_content()
                        if role_text and role_text.strip():
                            roles_data.append(role_text.strip())
                    except:
                        continue
                
                evidence_log["iam_data"]["roles"] = roles_data
                log_step("IAM Roles data collected", "success", f"Found {len(roles_data)} roles")
            else:
                log_step("No IAM roles found", "info")
        except Exception as e:
            log_step("IAM roles data extraction", "failed", str(e))
        
        log_step("IAM Roles collection completed", "success")
        return True
        
    except Exception as e:
        log_step("IAM Roles collection", "failed", str(e))
        return False

# Validate credentials
if not EMAIL or not PASSWORD:
    print("ERROR: Email or password not found in environment variables")
    print("Please check your .env file contains 'email' and 'password'")
    exit(1)

log_step("Starting AWS IAM Console RPA", "info", f"Email: {EMAIL[:3]}***")

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

        # Navigate to IAM
        log_step("Navigating to IAM Console", "info")
        try:
            page.goto(AWS_IAM_URL)
            page.wait_for_load_state('networkidle')
            time.sleep(3)  # wait for IAM page to render
            log_step("IAM Console loaded", "success")
            
            # Take screenshot of IAM dashboard
            take_screenshot(page, "02_iam_dashboard", "IAM Console dashboard")
            
            # Collect IAM Users
            log_step("Starting IAM data collection", "info")
            users_success = collect_iam_users(page)
            
            # Collect IAM Groups
            groups_success = collect_iam_groups(page)
            
            # Collect IAM Roles
            roles_success = collect_iam_roles(page)
            
            # Summary of collection results
            collection_results = {
                "users": users_success,
                "groups": groups_success,
                "roles": roles_success
            }
            
            successful_collections = sum(collection_results.values())
            log_step("IAM data collection completed", "success", 
                    f"Successfully collected {successful_collections}/3 IAM sections")
            
            if successful_collections == 3:
                log_step("All IAM sections collected successfully", "success")
            elif successful_collections > 0:
                log_step("Partial IAM collection completed", "info", 
                        f"Failed sections: {[k for k, v in collection_results.items() if not v]}")
            else:
                log_step("IAM collection failed", "failed", "No sections were successfully collected")
                
        except Exception as e:
            log_step("IAM navigation", "failed", str(e))
            take_screenshot(page, "02_iam_failed", "Failed to load IAM console")

        # Final evidence collection
        evidence_log["end_time"] = datetime.now().isoformat()
        evidence_log["status"] = "completed"
        
        # Save evidence log
        log_file = os.path.join(EVIDENCE_FOLDER, f"{timestamp}_iam_evidence_log.json")
        with open(log_file, 'w') as f:
            json.dump(evidence_log, f, indent=2)
        print(f"\nIAM Evidence log saved: {log_file}")
        
        print(f"\n" + "="*60)
        print("AWS IAM RPA COMPLETED SUCCESSFULLY")
        print(f"Evidence folder: {EVIDENCE_FOLDER}")
        print(f"Screenshots taken: {len(evidence_log['screenshots'])}")
        print(f"IAM Users found: {len(evidence_log['iam_data']['users'])}")
        print(f"IAM Groups found: {len(evidence_log['iam_data']['groups'])}")
        print(f"IAM Roles found: {len(evidence_log['iam_data']['roles'])}")
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
    log_file = os.path.join(EVIDENCE_FOLDER, f"{timestamp}_iam_evidence_log.json")
    with open(log_file, 'w') as f:
        json.dump(evidence_log, f, indent=2)
    
    print(f"\nERROR: {e}")
    print(f"IAM Evidence log saved: {log_file}")
    raise