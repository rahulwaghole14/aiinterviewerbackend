# Interview Time Fields Explanation

## Overview
The `Interview` model has two important time-related fields: `started_at` and `ended_at`. These fields represent the **actual interview execution times** rather than the scheduled slot times.

## Field Definitions

### `started_at` (DateTimeField)
- **Purpose**: Records when the interview actually **started** (when the candidate joined/accessed the interview)
- **Type**: `DateTimeField(null=True, blank=True)`
- **Default**: `null` (not set until interview actually starts)

### `ended_at` (DateTimeField)
- **Purpose**: Records when the interview actually **ended** (when the candidate completed or left the interview)
- **Type**: `DateTimeField(null=True, blank=True)`
- **Default**: `null` (not set until interview actually ends)

## Key Distinctions

### 🕐 **Scheduled vs Actual Times**

| Field | Represents | When Set | Example |
|-------|------------|----------|---------|
| `started_at` | **Actual start time** | When candidate joins interview | `2025-08-12 10:15:30` |
| `ended_at` | **Actual end time** | When candidate completes interview | `2025-08-12 11:05:45` |
| `slot.start_time` | **Scheduled start time** | When slot is created | `2025-08-12 10:00:00` |
| `slot.end_time` | **Scheduled end time** | When slot is created | `2025-08-12 11:00:00` |

## How These Fields Are Used

### 1. **Initial Setup (Scheduling)**
When an interview is scheduled with a slot, the `started_at` and `ended_at` are automatically set to the slot's scheduled times:

```python
# In InterviewSchedule.save() method
def save(self, *args, **kwargs):
    # Auto-update interview times when schedule is created/updated
    if self.slot and self.interview:
        self.interview.started_at = self.slot.start_time  # Scheduled start
        self.interview.ended_at = self.slot.end_time      # Scheduled end
        self.interview.save()
    super().save(*args, **kwargs)
```

### 2. **Actual Interview Execution**
When the candidate actually joins the interview, these fields are updated with the real start time:

```python
# In PublicInterviewAccessView.post() method
if not interview.started_at:
    interview.started_at = now  # Actual start time when candidate joins
```

### 3. **Duration Calculation**
The system calculates the actual interview duration:

```python
@property
def duration_seconds(self):
    if self.started_at and self.ended_at:
        return int((self.ended_at - self.started_at).total_seconds())
    return 0
```

### 4. **Link Validation**
These fields are used to validate interview access windows:

```python
def validate_interview_link(self, link_token):
    # Check if it's within the interview window (15 minutes before to 2 hours after)
    now = timezone.now()
    if self.started_at and self.ended_at:
        interview_start = self.started_at - timedelta(minutes=15)
        interview_end = self.ended_at + timedelta(hours=2)
        
        if now < interview_start:
            return False, f"Interview hasn't started yet. Please join at {self.started_at.strftime('%B %d, %Y at %I:%M %p')}"
        
        if now > interview_end:
            return False, "Interview has ended"
```

## Business Logic Flow

### 📅 **Interview Lifecycle**

1. **Scheduling Phase**:
   - Interview is created with `status = "scheduled"`
   - `started_at` and `ended_at` are set to slot's scheduled times
   - Interview link is generated

2. **Access Phase**:
   - Candidate clicks interview link
   - System validates access window (15 min before to 2 hours after scheduled time)
   - If valid, candidate can join

3. **Execution Phase**:
   - When candidate actually joins: `started_at` is updated to actual join time
   - Interview status may change to "in_progress" (if implemented)
   - AI interview begins

4. **Completion Phase**:
   - When candidate finishes: `ended_at` is updated to actual completion time
   - Interview status changes to "completed"
   - Duration is calculated from actual times

## Use Cases

### ✅ **Scheduled Times (Slot Times)**
- **Purpose**: Planning and scheduling
- **Used for**: Calendar display, availability checking, conflict detection
- **Example**: "Interview scheduled for 10:00 AM - 11:00 AM"

### ✅ **Actual Times (Interview Times)**
- **Purpose**: Execution tracking and analytics
- **Used for**: Duration calculation, performance metrics, audit trails
- **Example**: "Interview actually ran from 10:15 AM to 11:05 AM"

## Data Examples

### 📊 **Sample Interview Record**

```json
{
  "id": "uuid-123",
  "candidate": "John Doe",
  "status": "completed",
  "started_at": "2025-08-12T10:15:30Z",  // Actual start
  "ended_at": "2025-08-12T11:05:45Z",    // Actual end
  "duration_seconds": 3015,              // Calculated: 50 min 15 sec
  "schedule": {
    "slot": {
      "start_time": "2025-08-12T10:00:00Z",  // Scheduled start
      "end_time": "2025-08-12T11:00:00Z"     // Scheduled end
    }
  }
}
```

## Validation Rules

### ⏰ **Time Constraints**
- `started_at` and `ended_at` must be between 08:00-22:00 UTC (business hours)
- `ended_at` must be after `started_at`
- Both fields are required when updating time-related data

### 🔗 **Link Access Window**
- Candidates can join 15 minutes before scheduled start time
- Interview link expires 2 hours after actual end time
- Access is denied outside this window

## Summary

**`started_at` and `ended_at` represent the actual execution times of the interview**, not the scheduled times. They track when the candidate actually joined and completed the interview, providing valuable data for:

- **Analytics**: Actual interview durations vs scheduled durations
- **Performance**: How long interviews typically take
- **Audit**: When interviews actually occurred
- **Billing**: If time-based billing is implemented
- **Quality**: Identifying interviews that ran significantly longer/shorter than expected

The scheduled times (from the slot) are used for planning, while these actual times are used for execution tracking and analysis.

---
*Last Updated: 2025-08-12*

