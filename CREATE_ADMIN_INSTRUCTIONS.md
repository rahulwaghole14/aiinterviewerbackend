# How to Create Admin User on Render Deployment

Since the default credentials (`admin@rslsolution.com` / `admin123456`) are not working, you need to create the admin user on your Render deployment.

## Method 1: Using Render Shell (Recommended)

1. **Go to Render Dashboard**
   - Visit: https://dashboard.render.com
   - Login to your account

2. **Navigate to Your Backend Service**
   - Find your backend service: `aiinterviewerbackend-2` (or similar)
   - Click on it

3. **Open Shell**
   - Click on the **"Shell"** tab in the Render dashboard
   - This opens a terminal connected to your live deployment

4. **Run the Create Admin Command**
   ```bash
   python manage.py create_admin
   ```
   
   This will create:
   - **Email:** `admin@rslsolution.com`
   - **Password:** `admin123456`
   - **Role:** ADMIN
   - **Superuser:** Yes

5. **If User Already Exists**
   If you get a warning that the user exists, update the password:
   ```bash
   python manage.py create_admin --force
   ```

## Method 2: Using Custom Credentials

You can also create an admin user with custom credentials:

```bash
python manage.py create_admin --email your-email@example.com --password your-secure-password --full-name "Your Name"
```

## Method 3: Using Django's Built-in Command

Alternatively, use Django's standard createsuperuser command:

```bash
python manage.py createsuperuser
```

Then follow the prompts:
- Username: `admin@rslsolution.com` (or your preferred username)
- Email: `admin@rslsolution.com`
- Password: `admin123456` (or your preferred password)

**Note:** After creating the user, you may need to:
1. Set the `role` field to `ADMIN` via Django shell:
   ```python
   from django.contrib.auth import get_user_model
   from authapp.models import Role
   User = get_user_model()
   user = User.objects.get(email='admin@rslsolution.com')
   user.role = Role.ADMIN
   user.save()
   ```

2. Set `full_name` if required:
   ```python
   user.full_name = "Admin User"
   user.save()
   ```

## Method 4: Via Django Admin (If You Have Access)

If you can access Django admin with another account:
1. Go to: `https://aiinterviewerbackend-2.onrender.com/admin/`
2. Navigate to **Users** → **Custom users**
3. Click **Add Custom user**
4. Fill in:
   - Username: `admin@rslsolution.com`
   - Email: `admin@rslsolution.com`
   - Password: Set a secure password
   - Full name: `Admin User`
   - Role: `ADMIN`
   - Check: **Staff status** and **Superuser status**
5. Click **Save**

## Verification

After creating the admin user, verify login:
1. Go to: `https://aiinterviewerbackend-2.onrender.com/login`
2. Enter:
   - Email: `admin@rslsolution.com`
   - Password: `admin123456` (or the password you set)
3. Click **Login**

## Troubleshooting

### If command not found:
Make sure you're in the correct directory:
```bash
cd /opt/render/project/src
python manage.py create_admin
```

### If database errors occur:
Check that migrations are up to date:
```bash
python manage.py migrate
```

### If user exists but password doesn't work:
Reset the password:
```bash
python manage.py create_admin --force
```

Or use Django's changepassword:
```bash
python manage.py changepassword admin@rslsolution.com
```

## Security Note

⚠️ **Important:** After creating the admin user, consider changing the default password for security:
```bash
python manage.py changepassword admin@rslsolution.com
```

