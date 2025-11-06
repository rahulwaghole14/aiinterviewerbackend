# 📋 Interview Scheduling Details Required

## Overview
The `create_short_aiml_link.py` script now accepts command-line arguments to schedule interviews with custom details.

---

## 🔧 Required Details

### 1. **Candidate Name** (Optional)
- **Field**: Full name of the candidate
- **Default**: `"Test Candidate"`
- **Example**: `"John Doe"`, `"Jane Smith"`

### 2. **Candidate Email** (Optional)
- **Field**: Valid email address of the candidate
- **Default**: `"test@example.com"`
- **Example**: `"john@example.com"`, `"jane.smith@company.com"`
- **Note**: This email will receive the interview invitation automatically

### 3. **Scheduled Time** (Optional)
- **Field**: Date and time when the interview should take place
- **Format**: `YYYY-MM-DD HH:MM` (in IST - Indian Standard Time)
- **Default**: Current time (immediately)
- **Example**: `"2024-10-15 14:30"` (October 15, 2024 at 2:30 PM IST)
- **Example**: `"2024-10-20 10:00"` (October 20, 2024 at 10:00 AM IST)

### 4. **Coding Language** (Optional)
- **Field**: Programming language for coding round
- **Default**: `PYTHON`
- **Options**: `PYTHON`, `JAVASCRIPT`, `JAVA`, `PHP`, `RUBY`, `CSHARP`, `SQL`

---

## 📝 Usage Examples

### Example 1: Default (All defaults)
```bash
python create_short_aiml_link.py
```
**Creates interview with:**
- Name: "Test Candidate"
- Email: "test@example.com"
- Time: Current time (now)
- Language: PYTHON

---

### Example 2: Specify Language Only
```bash
python create_short_aiml_link.py JAVASCRIPT
```
**Creates interview with:**
- Name: "Test Candidate" (default)
- Email: "test@example.com" (default)
- Time: Current time (default)
- Language: JAVASCRIPT

---

### Example 3: Specify Name, Email, and Language
```bash
python create_short_aiml_link.py PYTHON "John Doe" "john@example.com"
```
**Creates interview with:**
- Name: "John Doe"
- Email: "john@example.com"
- Time: Current time (default)
- Language: PYTHON

---

### Example 4: Full Details (Recommended)
```bash
python create_short_aiml_link.py PYTHON "Jane Smith" "jane@example.com" "2024-10-20 14:30"
```
**Creates interview with:**
- Name: "Jane Smith"
- Email: "jane@example.com"
- Time: October 20, 2024 at 2:30 PM IST
- Language: PYTHON

---

### Example 5: Future Interview
```bash
python create_short_aiml_link.py PYTHON "Alice Johnson" "alice@company.com" "2024-11-01 10:00"
```
**Creates interview scheduled for:**
- November 1, 2024 at 10:00 AM IST

---

## ✅ What Happens After Running

1. **Session Created**: Interview session is created in the database
2. **Link Generated**: Unique interview link is generated with session_key
3. **Email Sent**: Automatic email is sent to candidate (if email is configured)
4. **Output Displayed**: All details are printed to console

---

## 📧 Email Configuration Required

For email notifications to work, ensure your `.env` file has:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

**Note**: If email is not configured, the script will still create the interview but won't send email.

---

## 🎯 Quick Reference

| Parameter | Position | Required | Default | Format |
|-----------|----------|----------|---------|--------|
| Language | 1st | No | PYTHON | PYTHON, JAVASCRIPT, etc. |
| Candidate Name | 2nd | No | "Test Candidate" | Any string |
| Candidate Email | 3rd | No | "test@example.com" | Valid email |
| Scheduled Time | 4th | No | Current time | YYYY-MM-DD HH:MM |

---

## 💡 Tips

1. **Always use quotes** for names and emails if they contain spaces
2. **Time format is strict**: Use `YYYY-MM-DD HH:MM` exactly (e.g., `"2024-10-15 14:30"`)
3. **Times are in IST**: The script automatically handles timezone conversion
4. **Email is sent automatically**: No need to send separately if configured
5. **Link is valid**: The interview link becomes active 30 seconds before scheduled time

---

## 🔍 View Help

To see all available options and examples:

```bash
python create_short_aiml_link.py --help
```

