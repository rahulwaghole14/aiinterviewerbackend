# 🎯 Interview Slot Management System

## 📋 Overview

The Interview Slot Management System is a comprehensive solution for managing interview scheduling, availability, and conflict detection. It addresses the missing functionality for interview slots on selected dates by providing a robust, scalable, and user-friendly system.

## 🏗️ Architecture

### Core Models

#### 1. **InterviewSlot** - The Foundation
```python
class InterviewSlot(models.Model):
    # Slot details
    slot_type = models.CharField(choices=[FIXED, FLEXIBLE, RECURRING])
    status = models.CharField(choices=[AVAILABLE, BOOKED, CANCELLED, COMPLETED])
    
    # Time details
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    
    # Interviewer and context
    interviewer = models.ForeignKey(CustomUser)
    company = models.ForeignKey(Company)
    job = models.ForeignKey(Job, null=True, blank=True)
    
    # Recurring support
    is_recurring = models.BooleanField(default=False)
    recurring_pattern = models.JSONField()
    
    # Capacity management
    max_candidates = models.PositiveIntegerField(default=1)
    current_bookings = models.PositiveIntegerField(default=0)
```

#### 2. **InterviewSchedule** - Booking Management
```python
class InterviewSchedule(models.Model):
    # Core relationships
    interview = models.OneToOneField(Interview)
    slot = models.ForeignKey(InterviewSlot)
    
    # Status tracking
    status = models.CharField(choices=[PENDING, CONFIRMED, CANCELLED, RESCHEDULED])
    
    # Timestamps and metadata
    booked_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True)
    cancelled_at = models.DateTimeField(null=True)
    
    # Cancellation details
    cancellation_reason = models.TextField()
    cancelled_by = models.ForeignKey(CustomUser)
```

#### 3. **InterviewerAvailability** - Pattern Management
```python
class InterviewerAvailability(models.Model):
    # Core relationships
    interviewer = models.ForeignKey(CustomUser)
    company = models.ForeignKey(Company)
    
    # Availability pattern
    day_of_week = models.IntegerField(choices=[MONDAY=1, ..., SUNDAY=7])
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # Slot configuration
    slot_duration = models.PositiveIntegerField(default=60)
    break_duration = models.PositiveIntegerField(default=15)
    
    # Settings
    is_available = models.BooleanField(default=True)
    max_slots_per_day = models.PositiveIntegerField(default=8)
    
    # Date range
    valid_from = models.DateField()
    valid_until = models.DateField(null=True)
```

#### 4. **InterviewConflict** - Conflict Tracking
```python
class InterviewConflict(models.Model):
    # Conflict details
    conflict_type = models.CharField(choices=[OVERLAP, INTERVIEWER_UNAVAILABLE, CANDIDATE_UNAVAILABLE])
    resolution = models.CharField(choices=[PENDING, RESCHEDULED, CANCELLED, RESOLVED])
    
    # Related interviews
    primary_interview = models.ForeignKey(Interview)
    conflicting_interview = models.ForeignKey(Interview, null=True)
    
    # Details and resolution
    conflict_details = models.JSONField()
    resolution_notes = models.TextField()
    
    # Timestamps
    detected_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True)
    resolved_by = models.ForeignKey(CustomUser)
```

## 🚀 Key Features

### 1. **Individual Slot Management**
- ✅ Create fixed-time interview slots
- ✅ Set slot duration and capacity
- ✅ Assign interviewers and jobs
- ✅ Add notes and metadata

### 2. **Recurring Slot Creation**
- ✅ Create slots for multiple days
- ✅ Set day-of-week patterns
- ✅ Configure time windows
- ✅ Automatic conflict detection

### 3. **Smart Booking System**
- ✅ Book interviews to available slots
- ✅ Prevent double-booking
- ✅ Automatic slot status updates
- ✅ Booking confirmation workflow

### 4. **Conflict Detection & Resolution**
- ✅ Real-time overlap detection
- ✅ Interviewer availability validation
- ✅ Candidate conflict checking
- ✅ Conflict resolution tracking

### 5. **Availability Patterns**
- ✅ Set weekly availability patterns
- ✅ Configure slot durations and breaks
- ✅ Date range validity
- ✅ Maximum daily slots

### 6. **Advanced Search & Filtering**
- ✅ Search by date range
- ✅ Filter by interviewer/company
- ✅ Time window filtering
- ✅ Availability status filtering

### 7. **Calendar Integration**
- ✅ Calendar view of all interviews
- ✅ Date range filtering
- ✅ Schedule status tracking
- ✅ Interview details display

## 📡 API Endpoints

### Interview Slots

#### **GET** `/api/interviews/slots/`
List all interview slots with filtering options.

**Query Parameters:**
- `status` - Filter by slot status (available, booked, cancelled, completed)
- `interviewer_id` - Filter by interviewer
- `company_id` - Filter by company
- `job_id` - Filter by job

**Response:**
```json
{
  "id": "uuid",
  "slot_type": "fixed",
  "status": "available",
  "start_time": "2024-01-15T10:00:00Z",
  "end_time": "2024-01-15T11:00:00Z",
  "duration_minutes": 60,
  "interviewer": 1,
  "interviewer_name": "John Interviewer",
  "company": 1,
  "company_name": "Test Company",
  "job": 1,
  "job_title": "Software Engineer",
  "is_available": true,
  "available_spots": 1,
  "max_candidates": 1,
  "current_bookings": 0,
  "notes": "Technical interview slot"
}
```

#### **POST** `/api/interviews/slots/`
Create a new interview slot.

**Request Body:**
```json
{
  "slot_type": "fixed",
  "start_time": "2024-01-15T10:00:00Z",
  "end_time": "2024-01-15T11:00:00Z",
  "duration_minutes": 60,
  "interviewer": 1,
  "company": 1,
  "job": 1,
  "notes": "Technical interview slot",
  "max_candidates": 1
}
```

#### **POST** `/api/interviews/slots/create_recurring/`
Create recurring interview slots.

**Request Body:**
```json
{
  "interviewer_id": 1,
  "company_id": 1,
  "job_id": 1,
  "start_date": "2024-01-15",
  "end_date": "2024-01-20",
  "start_time": "09:00:00",
  "end_time": "17:00:00",
  "days_of_week": [1, 2, 3, 4, 5],
  "slot_duration": 60,
  "break_duration": 15,
  "max_candidates_per_slot": 1,
  "notes": "Recurring interview slots"
}
```

#### **POST** `/api/interviews/slots/{id}/book_slot/`
Book a specific slot.

#### **POST** `/api/interviews/slots/{id}/release_slot/`
Release a booked slot.

#### **POST** `/api/interviews/slots/search_available/`
Search for available slots based on criteria.

**Request Body:**
```json
{
  "start_date": "2024-01-15",
  "end_date": "2024-01-22",
  "company_id": 1,
  "interviewer_id": 1,
  "start_time": "09:00:00",
  "end_time": "18:00:00",
  "duration_minutes": 60
}
```

### Interview Schedules

#### **GET** `/api/interviews/schedules/`
List all interview schedules.

#### **POST** `/api/interviews/schedules/book_interview/`
Book an interview to a slot.

**Request Body:**
```json
{
  "interview_id": "uuid",
  "slot_id": "uuid",
  "booking_notes": "Technical interview for Alice Candidate"
}
```

#### **POST** `/api/interviews/schedules/{id}/confirm_schedule/`
Confirm an interview schedule.

#### **POST** `/api/interviews/schedules/{id}/cancel_schedule/`
Cancel an interview schedule.

**Request Body:**
```json
{
  "reason": "Candidate requested reschedule"
}
```

### Interviewer Availability

#### **GET** `/api/interviews/availability/`
List interviewer availability patterns.

#### **POST** `/api/interviews/availability/`
Create interviewer availability pattern.

**Request Body:**
```json
{
  "interviewer": 1,
  "company": 1,
  "day_of_week": 2,
  "start_time": "09:00:00",
  "end_time": "17:00:00",
  "slot_duration": 60,
  "break_duration": 15,
  "is_available": true,
  "max_slots_per_day": 8,
  "valid_from": "2024-01-15",
  "valid_until": "2024-12-31"
}
```

### Interview Conflicts

#### **GET** `/api/interviews/conflicts/`
List interview conflicts.

#### **POST** `/api/interviews/conflicts/{id}/resolve_conflict/`
Resolve an interview conflict.

**Request Body:**
```json
{
  "resolution": "rescheduled",
  "notes": "Interview rescheduled to next week"
}
```

### Utility Endpoints

#### **GET** `/api/interviews/available-slots/`
Get available slots for a specific date range.

**Query Parameters:**
- `start_date` - Start date for search
- `end_date` - End date for search
- `company_id` - Filter by company
- `interviewer_id` - Filter by interviewer

#### **GET** `/api/interviews/calendar/`
Get interview calendar view.

**Query Parameters:**
- `start_date` - Start date for calendar
- `end_date` - End date for calendar

## 🔧 Business Logic

### Slot Availability Rules

1. **Time Validation**
   - End time must be after start time
   - Slots must be in the future
   - Default business hours: 08:00-22:00 UTC

2. **Conflict Detection**
   - No overlapping slots for same interviewer
   - No overlapping interviews for same candidate
   - Respect interviewer availability patterns

3. **Capacity Management**
   - Track current bookings vs. maximum capacity
   - Automatic status updates (available → booked)
   - Prevent overbooking

### Booking Workflow

1. **Slot Creation**
   - Admin/Company creates available slots
   - Set interviewer, time, duration, capacity
   - Optional: Link to specific job

2. **Interview Creation**
   - Create interview record for candidate
   - Set interview round and status

3. **Slot Booking**
   - Book interview to available slot
   - Create schedule record
   - Update slot booking count

4. **Schedule Confirmation**
   - Confirm the schedule
   - Update interview times
   - Send notifications

5. **Conflict Resolution**
   - Detect conflicts automatically
   - Allow manual resolution
   - Track resolution history

### Data Isolation

- **Admin**: Can see all slots and schedules
- **Company**: Can see slots and schedules for their company
- **Hiring Agency/Recruiter**: Can see slots and schedules for their company

## 🎨 Usage Examples

### Creating Individual Slots

```python
# Create a single interview slot
slot_data = {
    "slot_type": "fixed",
    "start_time": "2024-01-15T10:00:00Z",
    "end_time": "2024-01-15T11:00:00Z",
    "duration_minutes": 60,
    "interviewer": interviewer_id,
    "company": company_id,
    "job": job_id,
    "notes": "Technical interview slot",
    "max_candidates": 1
}

response = requests.post("/api/interviews/slots/", json=slot_data)
```

### Creating Recurring Slots

```python
# Create recurring slots for a week
recurring_data = {
    "interviewer_id": interviewer_id,
    "company_id": company_id,
    "start_date": "2024-01-15",
    "end_date": "2024-01-19",
    "start_time": "09:00:00",
    "end_time": "17:00:00",
    "days_of_week": [1, 2, 3, 4, 5],  # Monday to Friday
    "slot_duration": 60,
    "break_duration": 15,
    "max_candidates_per_slot": 1
}

response = requests.post("/api/interviews/slots/create_recurring/", json=recurring_data)
```

### Booking an Interview

```python
# Book an interview to a slot
booking_data = {
    "interview_id": interview_id,
    "slot_id": slot_id,
    "booking_notes": "Technical interview for Alice Candidate"
}

response = requests.post("/api/interviews/schedules/book_interview/", json=booking_data)
```

### Searching Available Slots

```python
# Search for available slots
search_data = {
    "start_date": "2024-01-15",
    "end_date": "2024-01-22",
    "company_id": company_id,
    "interviewer_id": interviewer_id,
    "start_time": "09:00:00",
    "end_time": "18:00:00",
    "duration_minutes": 60
}

response = requests.post("/api/interviews/slots/search_available/", json=search_data)
```

## 🔍 Testing

Run the comprehensive test script to verify all functionality:

```bash
python test_interview_slot_management.py
```

The test script covers:
- ✅ Individual slot creation
- ✅ Recurring slot creation
- ✅ Slot booking and releasing
- ✅ Interview scheduling
- ✅ Conflict detection
- ✅ Availability patterns
- ✅ Search and filtering
- ✅ Calendar view
- ✅ Data isolation by role

## 🚀 Benefits

### For Administrators
- **Centralized Management**: All interview slots in one place
- **Conflict Prevention**: Automatic detection and resolution
- **Scalability**: Handle multiple interviewers and companies
- **Audit Trail**: Complete history of all scheduling activities

### For Companies
- **Efficient Scheduling**: Quick slot creation and booking
- **Resource Optimization**: Maximize interviewer utilization
- **Quality Control**: Ensure proper interview setup
- **Reporting**: Track interview metrics and success rates

### For Interviewers
- **Clear Schedule**: Know exactly when interviews are scheduled
- **Availability Management**: Set and update availability patterns
- **Conflict Avoidance**: No double-booking issues
- **Flexibility**: Easy rescheduling when needed

### For Candidates
- **Reliable Scheduling**: Confirmed interview times
- **Clear Communication**: Know interview details upfront
- **Professional Experience**: Well-organized interview process
- **Rescheduling Options**: Easy to handle conflicts

## 🔮 Future Enhancements

### Planned Features
1. **Calendar Integration**: Google Calendar, Outlook sync
2. **Email Notifications**: Automated reminders and confirmations
3. **Video Conferencing**: Direct integration with Zoom, Teams
4. **Mobile App**: Native mobile scheduling interface
5. **AI Scheduling**: Intelligent slot recommendations
6. **Analytics Dashboard**: Advanced reporting and insights

### Technical Improvements
1. **Caching**: Redis-based slot availability caching
2. **Async Processing**: Background job processing
3. **Webhooks**: Real-time notifications
4. **API Rate Limiting**: Protect against abuse
5. **Database Optimization**: Advanced indexing and query optimization

## 📚 Conclusion

The Interview Slot Management System provides a comprehensive solution for the missing interview slot functionality. It addresses all the key requirements:

- ✅ **Slot Creation**: Individual and recurring slots
- ✅ **Booking Management**: Secure and conflict-free booking
- ✅ **Availability Tracking**: Real-time slot status
- ✅ **Conflict Detection**: Automatic overlap prevention
- ✅ **Calendar Integration**: Visual scheduling interface
- ✅ **Data Isolation**: Role-based access control
- ✅ **Scalability**: Handle multiple companies and interviewers
- ✅ **Extensibility**: Easy to add new features

This system transforms the interview scheduling process from a manual, error-prone activity into a streamlined, automated, and reliable system that benefits all stakeholders in the recruitment process.
