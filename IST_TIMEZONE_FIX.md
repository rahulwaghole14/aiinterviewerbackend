# IST Timezone Display Fix

## Issue

Interviews scheduled at Indian Standard Time (IST) were showing incorrect times in candidate details. For example:
- Scheduled: 12:50 PM IST
- Displayed: 6:30 PM - 6:40 PM (5.5-6 hour difference)

## Root Cause

1. **Backend:** Times were correctly interpreted as IST and converted to UTC for storage ✅
2. **Frontend:** Times were displayed using browser's local timezone instead of IST ❌
   - If browser timezone was not IST, times would display incorrectly
   - Example: UTC stored time converted to browser's timezone (e.g., UTC, EST, etc.)

## Solution

**Force all time displays to use IST (Asia/Kolkata) timezone** in the frontend.

### Changes Made

**File: `frontend/src/components/CandidateDetails.jsx`**

1. **Time Display (Slot Times):**
   - Added `timeZone: 'Asia/Kolkata'` to `toLocaleTimeString()` calls
   - Ensures times are always displayed in IST regardless of browser timezone

2. **Date Display:**
   - Added `timeZone: 'Asia/Kolkata'` to `toLocaleDateString()` calls
   - Ensures dates are shown in IST timezone context

### Code Changes

```javascript
// Before (using browser timezone):
startDate.toLocaleTimeString('en-US', {
  hour: 'numeric',
  minute: '2-digit',
  hour12: true
})

// After (forcing IST):
startDate.toLocaleTimeString('en-US', {
  hour: 'numeric',
  minute: '2-digit',
  hour12: true,
  timeZone: 'Asia/Kolkata'  // Force IST timezone display
})
```

## How It Works Now

1. **Scheduling:** User selects 12:50 PM (assumed IST)
2. **Backend:** Interprets as IST → Converts to UTC (7:20 AM UTC) → Stores in database
3. **Frontend Display:** 
   - Reads UTC datetime from database
   - Uses `toLocaleTimeString()` with `timeZone: 'Asia/Kolkata'`
   - Converts UTC → IST for display
   - Shows: 12:50 PM ✅

## Testing

1. Schedule an interview at a specific IST time (e.g., 12:50 PM)
2. Check candidate details page
3. Verify the displayed time matches the scheduled IST time
4. Test from different browser timezones - should always show IST

## Notes

- This fix ensures **consistent IST display** regardless of:
  - User's browser timezone
  - Server location
  - System timezone
- All interview times will now display in IST (Indian Standard Time)
- Backend still stores in UTC (standard practice)
- Frontend converts UTC → IST only for display

