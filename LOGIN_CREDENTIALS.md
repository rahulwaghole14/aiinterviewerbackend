# Login Credentials for Live Website

## Default Admin Credentials

Based on the codebase, the default admin credentials are:

**Email:** `admin@rslsolution.com`  
**Password:** `admin123456`

## Important Notes

⚠️ **These credentials may not exist on the live Render deployment** if:
- The admin user was never created
- The password was changed
- A different admin user was created

## How to Verify or Create Admin User

### Option 1: Check if Admin User Exists
You can check if the admin user exists by logging into Django admin panel:
- URL: `https://aiinterviewerbackend-2.onrender.com/admin/`
- Use the credentials above if they exist

### Option 2: Create Admin User via Django Shell (Recommended)

If the admin user doesn't exist, you can create one using Django's management command:

**Via Render Shell:**
1. Go to Render dashboard
2. Open your backend service
3. Click on "Shell" tab
4. Run:
```bash
python manage.py createsuperuser
```
5. Follow the prompts to create a new admin user

**Via Local Terminal (if you have access):**
```bash
python manage.py createsuperuser
```

### Option 3: Create Admin User via Script

You can also run the integrated script which creates the admin user:
```bash
python integrated_ai_interview_link_generator.py
```

This will create:
- Admin user: `admin@rslsolution.com` / `admin123456`
- Company: RSL Solutions
- Sample job and candidate

## Login Endpoints

### Frontend Login Page
- **URL:** `https://aiinterviewerbackend-2.onrender.com/login`
- **API Endpoint:** `POST /api/auth/login/`
- **Request Body:**
```json
{
  "email": "admin@rslsolution.com",
  "password": "admin123456"
}
```

### Django Admin Panel
- **URL:** `https://aiinterviewerbackend-2.onrender.com/admin/`
- Uses Django's built-in admin authentication

## User Registration

If you need to create a new user account, you can register via:
- **URL:** `https://aiinterviewerbackend-2.onrender.com/register`
- **API Endpoint:** `POST /api/auth/register/`
- **Request Body:**
```json
{
  "email": "your-email@example.com",
  "password": "your-password",
  "full_name": "Your Name",
  "role": "ADMIN",
  "company_name": "Your Company"
}
```

## Available User Roles

- `ADMIN` - Full system access
- `COMPANY` - Company user
- `HIRING_AGENCY` - Hiring agency user
- `RECRUITER` - Recruiter user
- `OTHERS` - Other users

## Security Recommendation

⚠️ **For production, change the default password immediately!**

To change password:
1. Login to Django admin
2. Go to Users section
3. Select the admin user
4. Change password

Or via shell:
```bash
python manage.py changepassword admin@rslsolution.com
```

