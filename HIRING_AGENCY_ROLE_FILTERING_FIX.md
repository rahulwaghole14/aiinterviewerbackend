# Hiring Agency Role Filtering Fix

## Overview
This document outlines the fix for the hiring agency API to ensure it only returns hiring agencies, not other roles like Recruiter or Company users.

## Problem Statement

### Issue Identified:
The hiring agency API (`/api/hiring_agency/`) was returning records with roles other than "Hiring Agency", specifically:
- **Recruiter** roles
- **Company** roles
- **Other roles** besides Hiring Agency

### Root Cause:
The `get_queryset()` method in `UserDataViewSet` was not filtering by role, so it returned all `UserData` objects regardless of their role.

### Impact:
- **Data Leakage**: Company users could see users with other roles from their company
- **API Confusion**: The API name suggests it should only return hiring agencies
- **Security Issue**: Unintended exposure of user data

## Solution

### Fix Applied:
Updated the `get_queryset()` method in `hiring_agency/views.py` to always filter by `role='Hiring Agency'`.

### Code Changes:

**Before:**
```python
def get_queryset(self):
    user = self.request.user
    if user.role == "ADMIN":
        return UserData.objects.all()  # ❌ Returns all roles
    elif user.role == "COMPANY":
        if user.company:
            return UserData.objects.filter(company=user.company)  # ❌ Returns all roles
        else:
            return UserData.objects.filter(company_name=user.company_name)  # ❌ Returns all roles
    return UserData.objects.none()
```

**After:**
```python
def get_queryset(self):
    user = self.request.user
    # Always filter by role='Hiring Agency' to ensure only hiring agencies are returned
    base_queryset = UserData.objects.filter(role='Hiring Agency')  # ✅ Only hiring agencies
    
    if user.role == "ADMIN":
        return base_queryset
    elif user.role == "COMPANY":
        if user.company:
            return base_queryset.filter(company=user.company)  # ✅ Only hiring agencies from company
        else:
            return base_queryset.filter(company_name=user.company_name)  # ✅ Only hiring agencies from company
    return UserData.objects.none()
```

## Testing

### Test Results Before Fix:
```
📊 Role distribution: {'Recruiter': 1, 'Hiring Agency': 8, 'Company': 1}
❌ Found non-hiring agency roles in the response:
   - ID 1: priya@example.com (Role: Recruiter, Company: No Company)
   - ID 2: rohit.verma@nextgenlabs.io (Role: Company, Company: NextGen Labs)
```

### Test Results After Fix:
```
📊 Role distribution: {'Hiring Agency': 8}
✅ All returned records are hiring agencies
```

## API Behavior

### Current API Response:
The hiring agency API now correctly returns only hiring agencies:

**Endpoint:** `GET /api/hiring_agency/`

**Response (Admin):**
```json
[
    {
        "id": 3,
        "email": "hiring_agency@test.com",
        "role": "Hiring Agency",
        "first_name": "Hiring",
        "last_name": "Agency",
        "phone_number": "+1234567890",
        "company_name": "No Company",
        "linkedin_url": "https://linkedin.com/in/hiringagency",
        "permission_granted": "2025-08-08",
        "created_by": 1
    },
    {
        "id": 4,
        "email": "alice.updated@company.com",
        "role": "Hiring Agency",
        "first_name": "Alice",
        "last_name": "Williams",
        "phone_number": "+1234567891",
        "company_name": "TechVision Global",
        "linkedin_url": "https://linkedin.com/in/alicewilliams",
        "permission_granted": "2025-08-08",
        "created_by": 1
    }
]
```

### Company-Specific Filtering:
- **Admin**: Sees all hiring agencies from all companies
- **Company User**: Sees only hiring agencies from their own company
- **Other Users**: See no hiring agencies (empty list)

## Data Distribution

### Current Hiring Agencies by Company:
```
📊 Companies with hiring agencies:
   - No Company: 2 hiring agencies
   - TechVision Global: 1 hiring agencies
   - Updated Agency: 1 hiring agencies
   - Test Agency: 1 hiring agencies
   - Test Company: 3 hiring agencies
```

## Security Benefits

### 1. Data Isolation:
- ✅ Company users only see hiring agencies from their company
- ✅ No exposure of other user roles (Recruiter, Company, etc.)
- ✅ Proper role-based access control

### 2. API Consistency:
- ✅ API name matches returned data
- ✅ Clear separation of concerns
- ✅ Predictable behavior

### 3. Privacy Protection:
- ✅ Prevents accidental data leakage
- ✅ Maintains user privacy
- ✅ Follows principle of least privilege

## Verification

### Test Scripts Created:
1. **`test_hiring_agency_role_filtering.py`**: Verifies only hiring agencies are returned
2. **`test_company_user_hiring_agency_access.py`**: Analyzes company-specific access

### Test Results:
```
✅ Hiring agency API returns only hiring agencies: PASSED
✅ Company-specific filtering analysis: PASSED
```

## Future Considerations

### 1. Role-Specific APIs:
Consider creating separate APIs for different roles:
- `/api/recruiters/` - For recruiter management
- `/api/companies/` - For company user management
- `/api/hiring_agencies/` - For hiring agency management

### 2. Enhanced Filtering:
Add query parameters for additional filtering:
- `?company=company_id` - Filter by specific company
- `?status=active` - Filter by status
- `?role=hiring_agency` - Filter by role (redundant but explicit)

### 3. API Documentation:
Update API documentation to clearly specify:
- Only hiring agencies are returned
- Company-specific filtering behavior
- Role-based access control

## Conclusion

The fix successfully resolves the issue where the hiring agency API was returning users with roles other than "Hiring Agency". The API now:

- ✅ **Returns only hiring agencies** regardless of user role
- ✅ **Maintains company-specific filtering** for company users
- ✅ **Preserves admin access** to all hiring agencies
- ✅ **Improves security** by preventing data leakage
- ✅ **Ensures API consistency** with its name and purpose

The implementation is backward compatible and doesn't break existing functionality while significantly improving data security and API consistency.
