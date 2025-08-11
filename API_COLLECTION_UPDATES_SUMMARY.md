# API Collection Updates Summary

## Overview
Updated the Postman collection (`AI_Interviewer_API_Collection.json`) to fix URL issues and improve accuracy for the Interview Slot Management System endpoints.

## Issues Fixed

### 1. **Incorrect URL Patterns**
**Problem**: The collection was using hyphens in URLs for `@action` decorated methods, but Django REST Framework uses underscores.

**Fixed URLs**:
- ❌ `create-recurring` → ✅ `create_recurring`
- ❌ `book-slot` → ✅ `book_slot` 
- ❌ `release-slot` → ✅ `release_slot`

### 2. **Missing Search Available Slots Endpoint**
**Problem**: The `search_available` action endpoint was missing from the collection.

**Added**: New "Search Available Slots" endpoint with:
- URL: `/api/interviews/slots/search_available/`
- Method: POST
- Advanced filtering capabilities
- Request body parameters for complex searches

### 3. **Incorrect Response Descriptions**
**Problem**: Response descriptions didn't match actual API responses.

**Updated**:
- **Book Slot Response**: Updated to reflect actual response fields (`id`, `interview`, `slot`, `status`, `created_at`)
- **Release Slot Response**: Updated to include `message`, `slot_available`, `current_bookings`, `max_candidates`
- **Recurring Slot Response**: Updated to include `created_slots`, `skipped_slots`, `message`

### 4. **Missing Required Fields**
**Problem**: Request bodies were missing required fields.

**Added**:
- **Slot Creation**: Added `company` and `job` fields
- **Recurring Slot Creation**: Added `company_id` and `job_id` fields

## Updated Endpoints

### 🤖 AI Interview Slot Management

#### 1. **Create Interview Slot**
- **URL**: `POST /api/interviews/slots/`
- **Added Fields**: `company`, `job`
- **Updated Description**: Added required field documentation

#### 2. **Search Available Slots** *(NEW)*
- **URL**: `POST /api/interviews/slots/search_available/`
- **Method**: POST with request body
- **Features**: Advanced filtering by date range, AI type, company, job, time, duration

#### 3. **Book Interview Slot**
- **URL**: `POST /api/interviews/slots/{slot_id}/book_slot/`
- **Fixed**: URL pattern (was `book/`)
- **Updated Response**: Correct field descriptions

#### 4. **Release Interview Slot**
- **URL**: `POST /api/interviews/slots/{slot_id}/release_slot/`
- **Fixed**: URL pattern (was `release/`)
- **Updated Response**: Correct field descriptions

#### 5. **Create Recurring Slots**
- **URL**: `POST /api/interviews/slots/create_recurring/`
- **Fixed**: URL pattern (was `create-recurring`)
- **Added Fields**: `company_id`, `job_id`
- **Updated Response**: Correct field descriptions

## Request Body Examples

### Slot Creation
```json
{
    "date": "2025-01-15",
    "start_time": "10:00:00",
    "end_time": "11:00:00",
    "ai_interview_type": "technical",
    "ai_configuration": {
        "difficulty_level": "intermediate",
        "question_count": 10,
        "time_limit": 60,
        "topics": ["algorithms", "data_structures", "system_design"]
    },
    "max_candidates": 1,
    "is_available": true,
    "company": "{{company_id}}",
    "job": "{{job_id}}"
}
```

### Recurring Slot Creation
```json
{
    "start_date": "2025-01-15",
    "end_date": "2025-01-22",
    "start_time": "10:00:00",
    "end_time": "11:00:00",
    "ai_interview_type": "technical",
    "ai_configuration": {
        "difficulty_level": "intermediate",
        "question_count": 10,
        "time_limit": 60
    },
    "days_of_week": [1, 3, 5],
    "max_candidates": 1,
    "company_id": "{{company_id}}",
    "job_id": "{{job_id}}"
}
```

### Search Available Slots
```json
{
    "start_date": "2025-01-15",
    "end_date": "2025-01-20",
    "ai_interview_type": "technical",
    "company_id": "{{company_id}}"
}
```

## Response Examples

### Book Slot Response
```json
{
    "id": "2cb69fc2-7771-47ff-9721-0edcd8a73fdc",
    "interview": "9262acd3-8506-44ca-8000-fa9f166f3def",
    "slot": "8e07af73-8af4-4e98-bbd0-9ae093cafbc1",
    "status": "pending",
    "created_at": "2025-08-11T19:40:35.123456Z"
}
```

### Release Slot Response
```json
{
    "message": "Slot released successfully",
    "slot_available": true,
    "current_bookings": 0,
    "max_candidates": 1
}
```

### Recurring Slot Creation Response
```json
{
    "created_slots": 0,
    "skipped_slots": [
        {
            "date": "2025-08-18",
            "reason": "Time conflict with existing slot"
        }
    ],
    "message": "Created 0 slots, 5 skipped due to conflicts"
}
```

## Testing Results
✅ All 9 Interview Slot Management System tests are passing:
- Slot creation
- Slot listing  
- Available slots
- Slot search
- Recurring slots
- Availability status
- Slot booking
- Slot release
- Calendar view

## Collection Variables
The collection uses these variables for dynamic data:
- `{{base_url}}`: API base URL
- `{{auth_token}}`: Authentication token
- `{{company_id}}`: Company ID
- `{{job_id}}`: Job ID
- `{{slot_id}}`: Slot ID
- `{{interview_id}}`: Interview ID
- `{{candidate_id}}`: Candidate ID

## Next Steps
The API collection is now fully updated and accurate. Users can:
1. Import the updated collection into Postman
2. Set up the collection variables
3. Test all Interview Slot Management System endpoints
4. Use the collection for API documentation and testing

---
*Last Updated: 2025-08-11*
*Status: ✅ Complete - All endpoints working correctly*
