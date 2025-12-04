# Database Configuration

## Current Setup: SQLite (Local Development)

The application is currently configured to use **SQLite** for local development. PostgreSQL is paused and will not be used until explicitly enabled.

## Database Location

- **SQLite Database**: `db.sqlite3` (in project root)
- **PostgreSQL**: Paused (not in use)

## All Data Stored in SQLite

All interview data is currently saved to SQLite database:
- ✅ Verified ID card images
- ✅ Interview sessions and metadata
- ✅ Proctoring snapshots
- ✅ Interview videos (file paths)
- ✅ AI evaluations
- ✅ Evaluation PDFs (file paths)
- ✅ Interview questions and answers
- ✅ Code submissions

## Switching to PostgreSQL (When Ready)

When you want to use PostgreSQL:

1. **Wake up/resume your Render.com PostgreSQL database**

2. **Update `interview_app/settings.py`**:
   ```python
   USE_POSTGRESQL = True  # Change from False to True
   ```

3. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

4. **Verify connection**:
   ```bash
   python test_db_connection.py
   ```

## Current Configuration

The settings file has a flag `USE_POSTGRESQL = False` that controls which database is used:

- `USE_POSTGRESQL = False` → Uses SQLite (current)
- `USE_POSTGRESQL = True` → Uses PostgreSQL from DATABASE_URL

## Benefits of SQLite for Development

- ✅ No external dependencies
- ✅ No connection issues
- ✅ Fast and reliable
- ✅ Easy to backup (just copy `db.sqlite3`)
- ✅ Perfect for local development and testing

## When to Use PostgreSQL

- Production deployments
- Multiple server instances
- Need for concurrent connections
- Advanced PostgreSQL features required

## Database Files

- **SQLite**: `db.sqlite3` (in project root)
- **Media Files**: `media/` directory (images, videos, PDFs)
  - ID cards: `media/id_cards/`
  - Videos: `media/interview_videos_merged/`
  - Snapshots: `media/proctoring_snaps/`
  - PDFs: `media/proctoring_pdfs/`

## Backup SQLite Database

To backup your SQLite database:
```bash
# Windows
copy db.sqlite3 db.sqlite3.backup

# Linux/Mac
cp db.sqlite3 db.sqlite3.backup
```

## Current Status

✅ **Using SQLite** - All data is stored locally
✅ **PostgreSQL paused** - Not being used (no connection attempts)
✅ **Migrations applied** - All database tables are created
✅ **Ready for development** - Everything is working


