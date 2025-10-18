# ==============================================
# File: aws_ec2_rpa_simple.py
# Purpose: Automate AWS Console Login and Collect EC2 Evidence Screenshots
# Author: Sachin (Simplified version by ChatGPT)
# ==============================================

import os
import time
import json
from datetime import datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# ========================================================
# 1️⃣ Load Environment Variables (Email & Password)
# ========================================================
load_dotenv()

EMAIL = os.getenv("email")
PASSWORD = os.getenv("password")

if not EMAIL or not PASSWORD:
    print("❌ ERROR: Please check your .env file. It must contain 'email' and 'password'.")
    exit(1)

# ========================================================
# 2️⃣ Prepare Evidence Folder
# ========================================================
EVIDENCE_FOLDER = "ec2_evidence"
if not os.path.exists(EVIDENCE_FOLDER):
    os.makedirs(EVIDENCE_FOLDER)
    print(f"📁 Created evidence folder: {EVIDENCE_FOLDER}")

# ========================================================
# 3️⃣ Setup Variables and Helper Functions
# ========================================================
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
evidence_log = {
    "session_id": timestamp,
    "start_time": datetime.now().isoformat(),
    "steps": [],
    "screenshots": []
}

def log_step(name, status="success", details=None):
    """Save each step to the log"""
    step = {
        "step": name,
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "details": details
    }
    evidence_log["steps"].append(step)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {name}: {status}")

def take_screenshot(page, filename, description="", full_page=False):
    """Take screenshot and save with log"""
    path = os.path.join(EVIDENCE_FOLDER, f"{timestamp}_{filename}.png")
    try:
        page.screenshot(path=path, full_page=full_page)
        evidence_log["screenshots"].append({
            "name": filename,
            "path": path,
            "timestamp": datetime.now().isoformat(),
            "description": description
        })
        print(f"📸 Screenshot saved: {path}")
        return path
    except Exception as e:
        log_step(f"Screenshot {filename}", "failed", str(e))
        return None

# ========================================================
# 4️⃣ RPA Main Function
# ========================================================
def run_aws_rpa():
    log_step("Starting AWS Console RPA", "info", f"User: {EMAIL[:3]}***")

    with sync_playwright() as p:
        # Launch browser (not headless, so you can complete MFA)
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        log_step("Browser launched")

        # -------------------------------
        # Step 1: Open AWS Console
        # -------------------------------
        AWS_CONSOLE_URL = "https://console.aws.amazon.com/"
        log_step("Opening AWS Console", "info")
        page.goto(AWS_CONSOLE_URL)
        page.wait_for_load_state("networkidle")
        take_screenshot(page, "01_aws_console_home", "AWS Console Homepage")

        # -------------------------------
        # Step 2: Click “Sign In”
        # -------------------------------
        try:
            if page.locator("text=Sign in").count():
                page.click("text=Sign in")
                log_step("Clicked 'Sign in'")
        except Exception as e:
            log_step("Sign in click failed", "failed", str(e))

        # -------------------------------
        # Step 3: Select “Root user”
        # -------------------------------
        try:
            if page.locator("text=Sign in using root user email").count():
                page.click("text=Sign in using root user email")
                log_step("Selected root user login")
        except:
            log_step("Root user option not found", "info")

        # -------------------------------
        # Step 4: Enter Email
        # -------------------------------
        try:
            page.fill("input[type='email'], input#resolving_input, input[name='username']", EMAIL)
            page.keyboard.press("Enter")
            log_step("Email entered successfully")
        except Exception as e:
            log_step("Email entry failed", "failed", str(e))
            return

        # -------------------------------
        # Step 5: Enter Password
        # -------------------------------
        try:
            page.fill("input[type='password'], input#password", PASSWORD)
            page.keyboard.press("Enter")
            log_step("Password entered successfully")
        except Exception as e:
            log_step("Password entry failed", "failed", str(e))
            return

        # -------------------------------
        # Step 6: Wait for MFA
        # -------------------------------
        print("\n📱 Complete MFA on your device. Waiting up to 10 minutes...")
        try:
            page.wait_for_url("**/console/**", timeout=600000)
            log_step("Successfully logged in (MFA complete)")
        except Exception as e:
            log_step("MFA timeout", "failed", str(e))
            return

        # -------------------------------
        # Step 7: Navigate to EC2 Console
        # -------------------------------
        EC2_URL = "https://console.aws.amazon.com/ec2/v2/home"
        log_step("Opening EC2 Console", "info")
        page.goto(EC2_URL)
        page.wait_for_load_state("networkidle")
        time.sleep(3)
        take_screenshot(page, "07_ec2_dashboard", "EC2 Console dashboard")

        # -------------------------------
        # Step 8: Go to EC2 Instances
        # -------------------------------
        try:
            # Try to click “Instances” from sidebar
            if page.locator("text=Instances").count():
                page.click("text=Instances")
                log_step("Clicked 'Instances' link")
            else:
                log_step("Instances link not found, using direct URL", "info")
                page.goto("https://console.aws.amazon.com/ec2/v2/home#Instances:")
        except Exception as e:
            log_step("Instances navigation failed", "failed", str(e))

        # Wait for instances table
        page.wait_for_load_state("networkidle")
        time.sleep(3)
        take_screenshot(page, "08_ec2_instances_full", "Full EC2 Instances Page", full_page=True)

        # -------------------------------
        # Step 9: Detect Instance Table
        # -------------------------------
        try:
            table_locator = page.locator("table, [role='table'], .awsui-table")
            if table_locator.count() > 0:
                table_path = os.path.join(EVIDENCE_FOLDER, f"{timestamp}_09_ec2_table.png")
                table_locator.first.screenshot(path=table_path)
                log_step("Instances table screenshot taken")
            else:
                log_step("Instances table not found", "info")
        except Exception as e:
            log_step("Instances table screenshot failed", "failed", str(e))

        # -------------------------------
        # Step 10: Save Evidence
        # -------------------------------
        evidence_log["end_time"] = datetime.now().isoformat()
        evidence_log["status"] = "completed"
        log_path = os.path.join(EVIDENCE_FOLDER, f"{timestamp}_evidence_log.json")

        with open(log_path, "w") as file:
            json.dump(evidence_log, file, indent=2)

        print(f"\n✅ Evidence log saved: {log_path}")
        print(f"📂 Screenshots: {len(evidence_log['screenshots'])}")
        print("✅ AWS EC2 Evidence Collection Completed")

        input("\nPress Enter to close browser...")
        browser.close()

# ========================================================
# 5️⃣ Run the RPA Script
# ========================================================
if __name__ == "__main__":
    try:
        run_aws_rpa()
    except Exception as err:
        log_step("Critical error", "failed", str(err))
        evidence_log["status"] = "failed"
        evidence_log["error"] = str(err)

        log_file = os.path.join(EVIDENCE_FOLDER, f"{timestamp}_evidence_log.json")
        with open(log_file, "w") as f:
            json.dump(evidence_log, f, indent=2)
        print(f"❌ Error occurred: {err}")
        print(f"Evidence log saved: {log_file}")
