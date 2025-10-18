# AWS Evidence Collection RPA Tool

## Overview
Simple RPA tool to automatically collect AWS EC2 evidence with MFA support. The tool logs into AWS, waits for MFA completion, navigates to EC2 services, and takes screenshots for compliance documentation.

## What You Need

### Prerequisites
- **AWS Account**: With email/password login and MFA enabled
- **Chrome Browser**: Must be installed on your system
- **Python 3.7+**: With pip package manager
- **MFA Device**: Ready to provide code within 5 minutes

### Required Information
- AWS account email address
- AWS account password
- MFA device (phone/authenticator app)

## Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify Chrome Installation**:
   - Make sure Google Chrome is installed
   - The tool will automatically download ChromeDriver

## How to Use

### Step 1: Run the Tool
```bash
python AWS_RAP_TOOL.py
```

### Step 2: Enter Credentials
- Enter your AWS email when prompted
- Enter your AWS password when prompted

### Step 3: Complete MFA
- The tool will open AWS login page
- Enter your email and password automatically
- **You have 5 minutes** to complete MFA authentication
- Check your MFA device and enter the code in the browser

### Step 4: Evidence Collection
- Tool automatically navigates to EC2 Dashboard
- Takes screenshots of:
  - EC2 Dashboard
  - EC2 Instances
  - Security Groups
- Saves all screenshots in `evidence/` folder

## What the Tool Does

1. **🚀 Setup**: Opens Chrome browser with automation settings
2. **🌐 Login**: Goes to AWS console and enters your credentials
3. **🔐 MFA Wait**: Waits 5 minutes for you to complete MFA
4. **🖥️ Navigate**: Automatically goes to EC2 services
5. **📸 Capture**: Takes screenshots of important EC2 pages
6. **💾 Save**: Stores evidence in timestamped files

## Output Files

Evidence files are saved in the `evidence/` folder with timestamps:
- `ec2_dashboard_YYYYMMDD_HHMMSS.png`
- `ec2_instances_YYYYMMDD_HHMMSS.png`
- `ec2_security_groups_YYYYMMDD_HHMMSS.png`

## Important Notes

### Security
- **Never hardcode credentials** in the script
- Credentials are entered at runtime only
- Browser closes automatically after completion

### Timing
- **5-minute MFA timeout**: Complete MFA within this time
- Tool shows countdown timer every 30 seconds
- If timeout occurs, restart the tool

### Troubleshooting
- **Chrome not found**: Install Google Chrome browser
- **Login fails**: Check email/password accuracy
- **MFA timeout**: Ensure MFA device is ready
- **Navigation fails**: Check AWS console layout changes

## Example Usage

```bash
$ python AWS_RAP_TOOL.py
🤖 AWS Evidence Collection RPA Tool
========================================
📧 Enter your AWS email: your-email@company.com
🔒 Enter your AWS password: ********

🤖 Starting AWS Evidence Collection RPA Tool
==================================================
🚀 Setting up Chrome WebDriver...
✅ Chrome WebDriver setup complete
🌐 Opening AWS Console...
✅ Clicked Sign In button
✅ Entered email: your-email@company.com
✅ Entered password

🔐 MFA Required!
⏰ You have 5 minutes to complete MFA authentication
📱 Please check your MFA device and enter the code in the browser
⏳ Waiting...
✅ MFA completed successfully!

🖥️ Navigating to EC2 service...
✅ Successfully navigated to EC2 Dashboard

📋 Collecting EC2 Evidence...
📸 Taking EC2 Dashboard screenshot...
📸 Screenshot saved: evidence\ec2_dashboard_20241018_111730.png
📸 Taking EC2 Instances screenshot...
📸 Screenshot saved: evidence\ec2_instances_20241018_111745.png
📸 Taking Security Groups screenshot...
📸 Screenshot saved: evidence\ec2_security_groups_20241018_111800.png

==================================================
✅ AWS Evidence Collection Complete!
📁 Evidence folder: C:\RPA\evidence
📸 Screenshots collected: 3
   - evidence\ec2_dashboard_20241018_111730.png
   - evidence\ec2_instances_20241018_111745.png
   - evidence\ec2_security_groups_20241018_111800.png

🧹 Browser closed
🎉 Evidence collection completed successfully!
```

## Customization

To collect additional evidence, modify the `collect_ec2_evidence()` method:
- Add more AWS services (S3, RDS, etc.)
- Capture additional EC2 pages
- Add custom screenshot naming

## Support

If you encounter issues:
1. Check Chrome browser installation
2. Verify AWS credentials
3. Ensure MFA device is working
4. Check internet connectivity
5. Review error messages in console output
