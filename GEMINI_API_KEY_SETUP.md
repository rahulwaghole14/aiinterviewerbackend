# 🔐 Gemini API Key Setup Guide

## ⚠️ IMPORTANT: Your API Key Was Leaked

Your Gemini API key was reported as leaked and has been disabled. You need to:

1. **Generate a NEW API key** from Google AI Studio
2. **Set it in your `.env` file** (never hardcode it in source code)
3. **Restart your server** to load the new key

---

## 🔑 Step 1: Generate New API Key

1. **Go to Google AI Studio:**
   - Visit: https://aistudio.google.com/apikey
   - Sign in with your Google account

2. **Create New API Key:**
   - Click **"Create API Key"**
   - Select your Google Cloud project (or create a new one)
   - Copy the generated API key (starts with `AIzaSy...`)

3. **Important Security:**
   - ⚠️ **Never** share your API key publicly
   - ⚠️ **Never** commit it to Git
   - ✅ **Always** use environment variables
   - ✅ **Always** add `.env` to `.gitignore`

---

## 📝 Step 2: Set API Key in .env File

Create or edit your `.env` file in the project root:

```env
# Gemini API Key (REQUIRED)
GEMINI_API_KEY=your-new-api-key-here

# OR use GOOGLE_API_KEY (alternative name)
# GOOGLE_API_KEY=your-new-api-key-here
```

**Example:**
```env
GEMINI_API_KEY=AIzaSyYourNewKeyHere1234567890
```

---

## 🔄 Step 3: Restart Server

After updating `.env`, restart your Django/Daphne server:

### Windows:
```powershell
# Stop current server (Ctrl+C)
# Then restart
daphne -b 127.0.0.1 -p 8000 interview_app.asgi:application
```

### Or use your start script:
```bash
python start_servers.py
```

---

## ✅ Verification

### Check if API Key is Loaded:

1. **Start your server** - you should see:
   ```
   ✅ Gemini API configured successfully
   ```

2. **If you see warnings:**
   ```
   ⚠️ WARNING: GEMINI_API_KEY not set. Set GEMINI_API_KEY or GOOGLE_API_KEY in .env file
   ```
   - This means your `.env` file is not being read
   - Check that `.env` is in the project root
   - Check that `python-dotenv` is installed: `pip install python-dotenv`

3. **Test API Key:**
   - Try scheduling an interview
   - Check server logs for Gemini API calls
   - If you see `403 Forbidden` or `API key was reported as leaked`, the key is still invalid

---

## 🛠️ Troubleshooting

### Issue 1: "GEMINI_API_KEY not set"
**Solution:**
- Check `.env` file exists in project root
- Verify variable name is exactly `GEMINI_API_KEY` or `GOOGLE_API_KEY`
- Restart server after adding `.env` file

### Issue 2: "403 API key was reported as leaked"
**Solution:**
- Generate a **NEW** API key (old one is permanently disabled)
- Update `.env` with new key
- Restart server

### Issue 3: "API key not found" or "Invalid API key"
**Solution:**
- Verify you copied the entire key (should be ~39 characters)
- Check for extra spaces or quotes in `.env`
- Ensure `.env` file is in the project root directory

### Issue 4: Environment variable not loading
**Solution:**
- Install `python-dotenv`: `pip install python-dotenv`
- Check that `load_dotenv()` is called in your Django settings
- Try hardcoding temporarily in `settings.py` to test (then remove immediately!)

---

## 📋 Files Updated

All hardcoded API keys have been removed from:

- ✅ `interview_app/settings.py` - Now uses environment variable only
- ✅ `interview_app/views.py` - Uses `settings.GEMINI_API_KEY`
- ✅ `interview_app/complete_ai_bot.py` - Uses `settings.GEMINI_API_KEY`
- ✅ `interview_app/simple_ai_bot.py` - Uses `settings.GEMINI_API_KEY`
- ✅ `interview_app/coding_service.py` - Uses `settings.GEMINI_API_KEY`
- ✅ `interview_app/ai_chatbot.py` - Uses `settings.GEMINI_API_KEY`
- ✅ `interview_app/comprehensive_pdf.py` - Uses `settings.GEMINI_API_KEY`
- ✅ `interview_app_11/views.py` - Uses `settings.GEMINI_API_KEY`
- ✅ `interview_app_11/coding_question_generator.py` - Uses `settings.GEMINI_API_KEY`
- ✅ `interview_app_11/evaluation_service.py` - Uses `settings.GEMINI_API_KEY`

---

## 🔒 Security Best Practices

1. **Never commit `.env` to Git:**
   ```bash
   # Check .gitignore has:
   .env
   *.env
   ```

2. **Use different keys for development/production:**
   - Development: `.env.local`
   - Production: Set via environment variables in hosting platform

3. **Rotate keys regularly:**
   - If a key is leaked, generate a new one immediately
   - Revoke old keys in Google AI Studio

4. **Monitor API usage:**
   - Check Google Cloud Console for unusual activity
   - Set up usage quotas if needed

---

## 📞 Need Help?

If you continue to see API key errors:

1. **Verify API key is valid:**
   - Go to https://aistudio.google.com/apikey
   - Check if key is active and not revoked

2. **Check server logs:**
   - Look for detailed error messages
   - Check if `.env` file is being loaded

3. **Test API key directly:**
   ```python
   # In Django shell
   from django.conf import settings
   print(f"API Key set: {bool(settings.GEMINI_API_KEY)}")
   print(f"API Key length: {len(settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY else 0}")
   ```

---

## ✅ Checklist

- [ ] Generated new API key from Google AI Studio
- [ ] Added `GEMINI_API_KEY=your-key` to `.env` file
- [ ] Verified `.env` is in project root
- [ ] Restarted Django/Daphne server
- [ ] Checked server logs for "Gemini API configured successfully"
- [ ] Tested interview scheduling (should work without 403 errors)
- [ ] Verified `.env` is in `.gitignore`

---

**After completing these steps, your Gemini API should work correctly!** 🎉





