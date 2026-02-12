# Interview Access System & Countdown Implementation Guide

## Overview
This document explains the complete interview access control system with 30-minute window (15 minutes before + 15 minutes after interview start time).

## Files to Modify

### 1. `interview_app/views.py` - Main Access Logic

#### Time Logic Structure (lines ~834-887):
```python
# Case 1: More than 15 minutes before start -> "Interview Not Started"
if now < (start_time - access_buffer_before):
    return render(request, 'interview_app/interview_not_started.html', {
        'page_title': 'Interview Not Started',
        'scheduled_time': start_time_local,
        'current_time': now.astimezone(pytz.timezone('Asia/Kolkata')),
        'session_key': session_key
    })

# Case 2: Within 15 minutes before start -> Countdown page
elif now < start_time:
    return render(request, 'interview_app/interview_not_started.html', {
        'page_title': 'Interview Starting Soon',
        'scheduled_time': start_time_local,
        'current_time': now.astimezone(pytz.timezone('Asia/Kolkata')),
        'session_key': session_key,
        'show_start_button': True
    })

# Case 3: Within 15 minutes after start -> Allow interview access
elif now <= access_window_end:
    # Allow access - interview can proceed
    pass

# Case 4: More than 15 minutes after start -> Link expired
else:
    session.status = 'EXPIRED'
    session.save()
    return render(request, 'interview_app/invalid_link.html', {
        'page_title': 'Interview Link Expired',
        'error': 'This interview link has expired. The link is only accessible from 15 minutes before until 15 minutes after the scheduled interview time.'
    })
```

#### Key Variables:
```python
access_buffer_before = timedelta(minutes=15)  # 15 minutes before start
access_buffer_after = timedelta(minutes=15)   # 15 minutes after start
access_window_end = start_time + access_buffer_after
```

### 2. `interviews/models.py` - Interview Link Generation

#### Critical Fix (line 491):
```python
# BEFORE (buggy):
" scheduled_at": self.started_at or timezone.now(),

# AFTER (fixed):
" scheduled_at": self.scheduled_time or timezone.now(),
```

This ensures InterviewSession.scheduled_at matches Interview.scheduled_time.

### 3. `interview_app/templates/interview_app/interview_not_started.html` - Countdown & Redirect

#### Critical Redirect Fix (line 206):
```html
<!-- BEFORE (buggy - redirects to root which tries to load React frontend): -->
<script>
    window.location.href = '/?session_key={{ session_key }}';
</script>

<!-- AFTER (fixed - redirects to interview portal): -->
<script>
    window.location.href = '/interview/?session_key={{ session_key }}';
</script>
```

#### Countdown JavaScript (lines ~176-214):
```javascript
function updateCountdown() {
    const scheduledTime = new Date('{{ scheduled_time|date:"c" }}');
    const now = new Date();
    const timeDiff = scheduledTime - now;
    
    if (timeDiff > 0) {
        // Show countdown
        const minutes = Math.floor((timeDiff % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((timeDiff % (1000 * 60)) / 1000);
        document.getElementById('countdown').textContent = `Interview starts in: ${minutes} minute${minutes !== 1 ? 's' : ''}, ${seconds} second${seconds !== 1 ? 's' : ''}`;
    } else {
        // Auto-start interview
        document.getElementById('countdown').textContent = 'Starting interview...';
        setTimeout(() => {
            window.location.href = '/interview/?session_key={{ session_key }}';
        }, 1000);
    }
}

// Start countdown immediately and update every second
updateCountdown();
setInterval(updateCountdown, 1000);
```

### 4. `interview_app/utils.py` - Localhost URL Generation

#### Force Localhost (lines 8-18):
```python
def get_backend_url(request=None):
    """
    Get the backend URL for generating interview links.
    For local development, always use localhost.
    """
    # For local development, always use localhost
    return "http://localhost:8000"

def get_interview_url(session_key, request=None):
    """
    Generate interview URL with session_key.
    Uses /interview/ route which serves the Django interview portal.
    """
    base_url = get_backend_url(request)
    return f"{base_url}/interview/?session_key={session_key}"
```

### 5. `interview_app/settings.py` - Localhost Configuration

#### Force Localhost (lines 390-393):
```python
# Backend URL for generating interview links (used in emails)
# For local development, always use localhost
# Override this in .env for production deployment
BACKEND_URL = "http://localhost:8000"  # Force localhost for local development
```

## Complete Implementation Steps

### Step 1: Update Interview Model
1. Open `interviews/models.py`
2. Find line 491 in `generate_interview_link()` method
3. Change `"scheduled_at": self.started_at or timezone.now()` to `"scheduled_at": self.scheduled_time or timezone.now()`

### Step 2: Update Views Time Logic
1. Open `interview_app/views.py`
2. Find `interview_portal()` function (~line 834)
3. Replace time logic with the 4-case structure shown above
4. Add debug logging for troubleshooting

### Step 3: Fix Template Redirect
1. Open `interview_app/templates/interview_app/interview_not_started.html`
2. Find line 206 in JavaScript countdown
3. Change `window.location.href = '/?session_key={{ session_key }}'` to `window.location.href = '/interview/?session_key={{ session_key }}'`

### Step 4: Force Localhost URLs
1. Open `interview_app/utils.py`
2. Replace `get_backend_url()` function to always return `"http://localhost:8000"`
3. Open `interview_app/settings.py`
4. Set `BACKEND_URL = "http://localhost:8000"`

## Testing Checklist

### Create Test Interviews:
```bash
# 5-minute interview (should show countdown)
python manage.py shell -c "
from django.utils import timezone
from interviews.models import Interview
# Create interview 5 minutes from now
scheduled_time = timezone.now() + timezone.timedelta(minutes=5)
# ... rest of creation code
"

# 1-hour interview (should show "Interview Not Started")
python manage.py shell -c "
# Create interview 1 hour from now
scheduled_time = timezone.now() + timezone.timedelta(hours=1)
# ... rest of creation code
"
```

### Expected Behaviors:
1. **Before 15-min window**: "Interview Not Started" page
2. **Within 15-min before start**: Countdown page with timer
3. **At interview start**: Auto-redirect to interview
4. **Within 15-min after start**: Direct interview access
5. **After 15-min window**: "Interview Link Expired" page

### Debug Logging:
Add these print statements to `views.py` for troubleshooting:
```python
print(f"DEBUG: Current time: {now}")
print(f"DEBUG: Start time: {start_time}")
print(f"DEBUG: Buffer start: {start_time - access_buffer_before}")
print(f"DEBUG: Current < buffer: {now < (start_time - access_buffer_before)}")
```

## URL Generation
All interview links will use: `http://localhost:8000/interview/?session_key=XXXXX`

## Common Issues & Solutions

### Issue: Countdown shows but interview doesn't start
**Cause**: Redirect goes to `/` instead of `/interview/`
**Solution**: Fix JavaScript redirect in template

### Issue: Wrong time logic
**Cause**: Using `self.started_at` instead of `self.scheduled_time`
**Solution**: Fix Interview model

### Issue: Deployment URLs instead of localhost
**Cause**: Environment variables or request-based URL detection
**Solution**: Force localhost in utils.py and settings.py

## Summary
This creates a 30-minute access window:
- **15 minutes before**: Countdown page
- **At scheduled time**: Auto-start interview  
- **15 minutes after**: Direct access allowed
- **After 30 minutes**: Link expires

All interview links use localhost for local development.
