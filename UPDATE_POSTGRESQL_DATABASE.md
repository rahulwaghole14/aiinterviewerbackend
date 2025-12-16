# Update to New PostgreSQL Database

## New Database URL
```
postgresql://ai_interview_platform_db_user:B5NCPLg8er6rFaKRUp6HWUnL7WjYt0GO@dpg-d4pt6ikhg0os73ftr9l0-a.singapore-postgres.render.com/ai_interview_platform_db
```

## Database Details
- **Host:** `dpg-d4pt6ikhg0os73ftr9l0-a.singapore-postgres.render.com`
- **Database:** `ai_interview_platform_db`
- **User:** `ai_interview_platform_db_user`
- **Status:** ✅ **Connection Verified - Working!**

## Step 1: Update .env File

Update your `.env` file (lines 8-9) with the new DATABASE_URL:

```env
DATABASE_URL=postgresql://ai_interview_platform_db_user:B5NCPLg8er6rFaKRUp6HWUnL7WjYt0GO@dpg-d4pt6ikhg0os73ftr9l0-a.singapore-postgres.render.com/ai_interview_platform_db
USE_POSTGRESQL=True
```

**Or manually edit `.env` file:**
1. Open `.env` file
2. Find the line with `DATABASE_URL=`
3. Replace the entire value with the new URL above
4. Add or update: `USE_POSTGRESQL=True`

## Step 2: Settings Already Updated

The `interview_app/settings.py` has been updated to:
- ✅ Enable PostgreSQL by default (`USE_POSTGRESQL = True`)
- ✅ Use the DATABASE_URL from environment variables
- ✅ Configure SSL for Render.com databases

## Step 3: Run Migrations

After updating `.env`, run migrations to create all tables:

```bash
python manage.py migrate
```

This will create all Django tables in the new PostgreSQL database:
- User tables
- Interview sessions
- Candidates
- Jobs
- Evaluations
- And all other app tables

## Step 4: Create Admin User

After migrations, create the admin user:

```bash
python manage.py create_admin
```

Or use the migration (already created):
```bash
python manage.py migrate authapp
```

## Step 5: Verify Connection

Test the connection anytime:
```bash
python test_new_postgresql.py
```

## For Render Deployment

### Update Environment Variables on Render:

1. Go to Render Dashboard → Your Backend Service
2. Go to "Environment" tab
3. Update `DATABASE_URL` environment variable with the new URL:
   ```
   postgresql://ai_interview_platform_db_user:B5NCPLg8er6rFaKRUp6HWUnL7WjYt0GO@dpg-d4pt6ikhg0os73ftr9l0-a.singapore-postgres.render.com/ai_interview_platform_db
   ```
4. Add or update `USE_POSTGRESQL=True`
5. Save changes
6. Render will automatically redeploy

## Migration Commands

After updating `.env`:

```bash
# Test connection
python test_new_postgresql.py

# Run all migrations
python manage.py migrate

# Create admin user (if not created by migration)
python manage.py create_admin

# Verify database
python manage.py dbshell
```

## What Will Be Migrated

All Django apps will create their tables:
- ✅ `authapp` - User authentication
- ✅ `interview_app` - Interview sessions, videos, audio
- ✅ `candidates` - Candidate data
- ✅ `jobs` - Job postings
- ✅ `companies` - Company information
- ✅ `evaluation` - AI evaluation results
- ✅ `interviews` - Interview scheduling
- ✅ `notifications` - Notification system
- ✅ `dashboard` - Dashboard metrics
- ✅ And all other apps

## Important Notes

1. **Old Database:** The previous database (`ai_interviewer_db`) will no longer be used
2. **Data Migration:** If you have data in the old database, you'll need to export and import it separately
3. **Local Development:** You can still use SQLite locally by setting `USE_POSTGRESQL=False` in `.env`
4. **Render Deployment:** Make sure to update the `DATABASE_URL` environment variable on Render

## Verification

After migrations, verify tables were created:
```bash
python manage.py dbshell
```

Then in PostgreSQL shell:
```sql
\dt  -- List all tables
SELECT COUNT(*) FROM authapp_customuser;  -- Check if admin user exists
\q   -- Exit
```

## Summary

✅ **New database connection verified**  
✅ **Settings updated to enable PostgreSQL**  
📝 **Update `.env` file with new DATABASE_URL**  
🔄 **Run migrations to create all tables**  
👤 **Create admin user**  

Once you update the `.env` file and run migrations, all your data will be stored in the new PostgreSQL database!



