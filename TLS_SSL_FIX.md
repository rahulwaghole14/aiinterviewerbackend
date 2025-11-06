# TLS/SSL Conflict Fix

## Issue Found
Both `EMAIL_USE_TLS=True` and `EMAIL_USE_SSL=True` are set in `.env`, which is invalid. They are mutually exclusive.

## Error Message
```
EMAIL_USE_TLS/EMAIL_USE_SSL are mutually exclusive, so only set one of those settings to True.
```

## Fix Applied

### Automatic Fix in Code
Both `test_email_sending_live.py` and `notifications/services.py` now automatically:
1. Detect the conflict when both are True
2. For port 587 (Gmail SMTP), automatically disable SSL (set to False)
3. Use TLS only for port 587

### Manual Fix in .env
Update your `.env` file:

```env
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
```

**For Gmail:**
- Port **587**: Use `EMAIL_USE_TLS=True` and `EMAIL_USE_SSL=False`
- Port **465**: Use `EMAIL_USE_TLS=False` and `EMAIL_USE_SSL=True`

## How to Fix

### Option 1: Run fix_email_config.py
```bash
python fix_email_config.py
```
This will automatically update `.env` to set `EMAIL_USE_SSL=False`.

### Option 2: Manual Fix
Edit `.env` file and change:
```
EMAIL_USE_SSL=False
```

### Option 3: Automatic Fix in Code (Already Applied)
The code now automatically fixes this at runtime, but it's better to fix `.env` permanently.

## After Fix

1. **Restart Django server** (required after .env changes)
2. **Test email**:
   ```bash
   python test_email_sending_live.py
   ```

## Summary

✅ **Code updated** - Both test script and notification service now auto-fix TLS/SSL conflict
✅ **`.env` fix recommended** - Set `EMAIL_USE_SSL=False` permanently
✅ **Runtime protection** - Code will disable SSL automatically if both are True

