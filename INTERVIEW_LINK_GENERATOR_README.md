# Public Interview Link Generator

This directory contains scripts to automatically generate public interview links for the Talaro platform.

## 📁 Files

- `generate_public_interview_link.py` - Main script to generate interview links
- `test_generated_link.py` - Test script to verify generated links
- `INTERVIEW_LINK_GENERATOR_README.md` - This documentation

## 🚀 Quick Start

### Prerequisites

1. **Django Server Running**: Make sure the Django server is running on port 8000
   ```bash
   python manage.py runserver 8000
   ```

2. **Python Dependencies**: Ensure all required packages are installed
   ```bash
   pip install requests pytz
   ```

### Generate Interview Link

#### Method 1: Default Candidate (AKSHAY PATIL)
```bash
python generate_public_interview_link.py
```

#### Method 2: Custom Candidate Name
```bash
python generate_public_interview_link.py "JOHN DOE"
python generate_public_interview_link.py "MARY JANE SMITH"
```

### Test Generated Link
```bash
python test_generated_link.py "http://127.0.0.1:8000/api/interviews/public/..."
```

## 🔧 What the Script Does

The `generate_public_interview_link.py` script automates the entire process:

### Step-by-Step Process:

1. **🔍 Server Check** - Verifies Django server is running
2. **👤 Admin Setup** - Creates admin user (admin@rslsolution.com)
3. **🔑 Admin Login** - Logs in and gets authentication token
4. **🏢 Company Setup** - Creates "RSL Solutions" company
5. **💼 Job Setup** - Creates "Software Engineer" job
6. **👨‍💼 Candidate Setup** - Creates candidate with provided name
7. **📅 Interview Creation** - Creates interview with current time
8. **🔗 Link Generation** - Generates public interview link
9. **🤖 AI Session Setup** - Creates AI interview session
10. **🌐 Portal Session Setup** - Creates interview session for portal
11. **⏰ Time Configuration** - Updates times for immediate use
12. **✅ Link Testing** - Tests the generated link

### Default Configuration:

- **Admin User**: admin@rslsolution.com / admin123456
- **Company**: RSL Solutions
- **Job**: Software Engineer
- **Interview Type**: Technical
- **Duration**: 2 hours from current time
- **Status**: Scheduled and ready to use

## 📊 Output Example

```
🚀 PUBLIC INTERVIEW LINK GENERATOR
============================================================
🎯 Target Candidate: AKSHAY PATIL
🌐 Server URL: http://127.0.0.1:8000

============================================================
🔧 STEP 1: SERVER CHECK
============================================================
📝 Verifying Django server is running

✅ Django server is running

============================================================
🔧 STEP 2: ADMIN USER SETUP
============================================================
📝 Creating admin user if not exists

✅ Admin user already exists: admin@rslsolution.com

[... more steps ...]

============================================================
🎉 SUCCESS! PUBLIC INTERVIEW LINK GENERATED
============================================================
👤 Candidate: AKSHAY PATIL
💼 Job: Software Engineer
🏢 Company: RSL Solutions
🔗 Interview Link: http://127.0.0.1:8000/api/interviews/public/...
⏰ Valid Until: 2025-08-19 20:45:30 IST
============================================================

✅ Ready to use! Copy this link:
🔗 http://127.0.0.1:8000/api/interviews/public/...
```

## 🎯 Usage Scenarios

### Scenario 1: Quick Interview Setup
```bash
# Generate link for default candidate
python generate_public_interview_link.py
```

### Scenario 2: Multiple Candidates
```bash
# Generate links for different candidates
python generate_public_interview_link.py "ALICE JOHNSON"
python generate_public_interview_link.py "BOB SMITH"
python generate_public_interview_link.py "CAROL DAVIS"
```

### Scenario 3: Test Existing Link
```bash
# Test a previously generated link
python test_generated_link.py "http://127.0.0.1:8000/api/interviews/public/..."
```

## 🔍 Troubleshooting

### Common Issues:

1. **Server Not Running**
   ```
   ❌ Django server is not running. Please start it with: python manage.py runserver 8000
   ```
   **Solution**: Start the Django server first

2. **Authentication Failed**
   ```
   ❌ Login failed: 400 - {"non_field_errors":["Invalid email/username or password."]}
   ```
   **Solution**: The script will automatically create the admin user

3. **Link Generation Failed**
   ```
   ❌ Failed to generate link: 400 - {"error":"Interview must be configured for AI interview"}
   ```
   **Solution**: The script handles this automatically by creating AI configuration

4. **Link Test Failed**
   ```
   ❌ Interview link test failed: 404
   ```
   **Solution**: Check if the server is running and the link is correct

### Debug Mode:

To see more detailed output, you can modify the script to add debug logging:

```python
# Add this to the script for debug output
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📝 Customization

### Change Default Values:

Edit the script to customize default values:

```python
class PublicInterviewLinkGenerator:
    def __init__(self):
        self.base_url = "http://127.0.0.1:8000"  # Change server URL
        self.admin_credentials = {
            "email": "admin@rslsolution.com",     # Change admin email
            "password": "admin123456"             # Change admin password
        }
```

### Change Company/Job Details:

```python
def create_company(self):
    company = Company.objects.create(
        company_name="Your Company",              # Change company name
        industry="Your Industry",                 # Change industry
        # ... other fields
    )

def create_job(self, company):
    job = Job.objects.create(
        job_title="Your Job Title",               # Change job title
        tech_stack_details="Your Tech Stack",     # Change tech stack
        # ... other fields
    )
```

## 🎉 Benefits

1. **⏱️ Time Saving**: No need to manually create admin, company, job, candidate, and interview
2. **🔄 Reusable**: Can be run multiple times for different candidates
3. **✅ Automated**: Handles all setup steps automatically
4. **🧪 Tested**: Includes built-in testing of generated links
5. **📊 Detailed Output**: Shows progress and status for each step
6. **🔧 Configurable**: Easy to customize for different needs

## 📞 Support

If you encounter any issues:

1. Check that the Django server is running
2. Verify all required packages are installed
3. Check the console output for specific error messages
4. Ensure the database is properly configured

The script is designed to be self-healing and will create missing components automatically.

