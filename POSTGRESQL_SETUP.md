# PostgreSQL Database Setup Guide

## Overview
The application is now configured to use PostgreSQL when `DATABASE_URL` is provided in the `.env` file. If `DATABASE_URL` is not set, it will fallback to SQLite for development.

## Database Configuration

The database configuration in `interview_app/settings.py` now:
1. Checks for `DATABASE_URL` environment variable
2. Uses PostgreSQL if `DATABASE_URL` is provided
3. Falls back to SQLite if `DATABASE_URL` is not set

## Setup Steps

### 1. Install PostgreSQL Dependencies

You need to install the PostgreSQL adapter for Python:

```bash
pip install psycopg2-binary
```

Or if you prefer the newer version:
```bash
pip install psycopg2-binary>=2.9.0
```

Optional (recommended): Install `dj-database-url` for easier URL parsing:
```bash
pip install dj-database-url
```

### 2. Configure DATABASE_URL in .env

Add your PostgreSQL connection string to the `.env` file:

```env
DATABASE_URL=postgresql://username:password@host:port/database_name
```

**Example formats:**
```env
# Local PostgreSQL
DATABASE_URL=postgresql://postgres:password@localhost:5432/ai_interview_db

# PostgreSQL with SSL
DATABASE_URL=postgresql://user:pass@host:5432/dbname?sslmode=require

# Cloud PostgreSQL (e.g., AWS RDS, Azure, Heroku)
DATABASE_URL=postgresql://user:pass@your-db-host.amazonaws.com:5432/dbname
```

### 3. Create PostgreSQL Database

If you're setting up a new database:

```sql
CREATE DATABASE ai_interview_db;
CREATE USER your_username WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE ai_interview_db TO your_username;
```

### 4. Run Migrations

After setting up the database URL, run migrations:

```bash
python manage.py migrate
```

This will create all the necessary tables in PostgreSQL.

## Database URL Format

The `DATABASE_URL` follows this format:
```
postgresql://[user[:password]@][host][:port][/database][?parameter_list]
```

**Components:**
- `postgresql://` - Protocol
- `user` - Database username
- `password` - Database password (optional if using peer authentication)
- `host` - Database host (localhost, IP address, or domain)
- `port` - Database port (default: 5432)
- `database` - Database name
- `parameter_list` - Optional parameters (e.g., `?sslmode=require`)

## Verification

To verify the database connection is working:

```bash
python manage.py dbshell
```

Or test the connection:
```python
python manage.py shell
>>> from django.db import connection
>>> connection.ensure_connection()
>>> print("✅ Database connection successful!")
```

## Troubleshooting

### Error: "No module named 'psycopg2'"
**Solution:** Install psycopg2-binary:
```bash
pip install psycopg2-binary
```

### Error: "could not connect to server"
**Solutions:**
1. Check if PostgreSQL is running: `pg_isready` or check service status
2. Verify host, port, username, and password in DATABASE_URL
3. Check firewall settings if connecting to remote database
4. Verify database exists: `psql -l`

### Error: "database does not exist"
**Solution:** Create the database:
```sql
CREATE DATABASE your_database_name;
```

### Error: "password authentication failed"
**Solution:** 
1. Verify password in DATABASE_URL
2. Check PostgreSQL authentication settings in `pg_hba.conf`
3. Reset password if needed: `ALTER USER username WITH PASSWORD 'new_password';`

## Environment Variables

Make sure your `.env` file includes:

```env
# Database
DATABASE_URL=postgresql://user:password@host:port/database

# Other required variables
DJANGO_SECRET_KEY=your-secret-key
GEMINI_API_KEY=your-gemini-key
DEEPGRAM_API_KEY=your-deepgram-key
```

## Production Considerations

1. **Use SSL**: For production, always use SSL:
   ```
   DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
   ```

2. **Connection Pooling**: Consider using connection pooling for high-traffic applications

3. **Backups**: Set up regular database backups

4. **Environment Variables**: Never commit `.env` file to version control

5. **Database Migrations**: Always test migrations in staging before production

## Current Database Models

All data is stored in PostgreSQL:
- ✅ **InterviewSession** - Interview metadata, ID card images, videos
- ✅ **WarningLog** - Proctoring snapshots and warnings
- ✅ **InterviewQuestion** - Questions and answers
- ✅ **Evaluation** - AI evaluation results and PDFs
- ✅ **CodeSubmission** - Coding challenge submissions

## Migration Status

After setting up PostgreSQL, run:
```bash
python manage.py migrate
```

This will create all tables and apply pending migrations including:
- `interview_app.0008_add_database_storage_fields` (snapshot_image field)
- `evaluation.0005_add_database_storage_fields` (evaluation_pdf field)

