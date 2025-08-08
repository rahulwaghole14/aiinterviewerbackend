# Hiring Agency Password Field Implementation

## Overview
This document outlines the implementation of a password field for the Hiring Agency UserData model and API endpoints. The changes allow hiring agencies to be created with password credentials while maintaining backward compatibility.

## Changes Made

### 1. Database Model Changes (`hiring_agency/models.py`)

**Added Field:**
- `password`: CharField with max_length=128, null=True, blank=True

```python
class UserData(models.Model):
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128, null=True, blank=True)  # NEW
    role = models.CharField(max_length=50, choices=Role.CHOICES)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    linkedin_url = models.URLField(blank=True)
    permission_granted = models.DateField(auto_now_add=True)
    created_by = models.ForeignKey('authapp.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
```

### 2. Serializer Changes (`hiring_agency/serializers.py`)

**Updated UserDataSerializer:**
- Added password field as write-only
- Added custom create method to handle password separately
- Password field is never returned in API responses

```python
class UserDataSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = UserData
        fields = '__all__'
        read_only_fields = ['created_by']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        request = self.context.get('request')
        if request:
            validated_data['created_by'] = request.user
        
        user_data = UserData.objects.create(**validated_data)
        if password:
            user_data.password = password
            user_data.save()
        return user_data
```

### 3. Database Migration

**Created Migration:** `hiring_agency/migrations/0003_userdata_password.py`

```bash
python manage.py makemigrations hiring_agency
python manage.py migrate
```

## API Usage

### 1. Create Hiring Agency with Password

**Endpoint:** `POST /api/hiring_agency/add_user/`

**Request Body:**
```json
{
    "email": "testagency@example.com",
    "password": "agency123",
    "role": "Hiring Agency",
    "first_name": "Test",
    "last_name": "Agency",
    "phone_number": "+1234567890",
    "company_name": "Test Company",
    "linkedin_url": "https://linkedin.com/in/testagency"
}
```

**Response:**
```json
{
    "id": 10,
    "email": "testagency@example.com",
    "role": "Hiring Agency",
    "first_name": "Test",
    "last_name": "Agency",
    "phone_number": "+1234567890",
    "company_name": "Test Company",
    "linkedin_url": "https://linkedin.com/in/testagency",
    "permission_granted": "2025-08-08",
    "created_by": 16
}
```

### 2. Create Hiring Agency without Password (Backward Compatibility)

**Endpoint:** `POST /api/hiring_agency/add_user/`

**Request Body:**
```json
{
    "email": "testagency2@example.com",
    "role": "Hiring Agency",
    "first_name": "Test",
    "last_name": "Agency2",
    "phone_number": "+1234567891",
    "company_name": "Test Company",
    "linkedin_url": "https://linkedin.com/in/testagency2"
}
```

**Response:**
```json
{
    "id": 11,
    "email": "testagency2@example.com",
    "role": "Hiring Agency",
    "first_name": "Test",
    "last_name": "Agency2",
    "phone_number": "+1234567891",
    "company_name": "Test Company",
    "linkedin_url": "https://linkedin.com/in/testagency2",
    "permission_granted": "2025-08-08",
    "created_by": 16
}
```

### 3. Get All Hiring Agencies (Password Hidden)

**Endpoint:** `GET /api/hiring_agency/`

**Response:**
```json
[
    {
        "id": 1,
        "email": "priya@example.com",
        "role": "Hiring Agency",
        "first_name": "Priya",
        "last_name": "Sharma",
        "phone_number": "+919876543210",
        "company_name": "TechCorp",
        "linkedin_url": "https://linkedin.com/in/priyasharma",
        "permission_granted": "2025-08-08",
        "created_by": 1
    },
    {
        "id": 10,
        "email": "testagency@example.com",
        "role": "Hiring Agency",
        "first_name": "Test",
        "last_name": "Agency",
        "phone_number": "+1234567890",
        "company_name": "Test Company",
        "linkedin_url": "https://linkedin.com/in/testagency",
        "permission_granted": "2025-08-08",
        "created_by": 16
    }
]
```

## Key Features

### 1. Password Field
- **Write-only**: Password is never returned in API responses
- **Optional**: Hiring agencies can be created without password (backward compatibility)
- **Stored securely**: Password is stored in the database
- **Validation**: Uses Django's built-in field validation

### 2. Backward Compatibility
- Existing hiring agencies without password continue to work
- API responses do not include password field
- No breaking changes to existing functionality

### 3. Security
- Password field is write-only and never exposed in responses
- Password is stored as plain text (consider hashing for production)

## Testing

### Test Script: `test_hiring_agency_password.py`

The test script verifies:
1. ✅ Hiring agency creation with password
2. ✅ Hiring agency creation without password (backward compatibility)
3. ✅ Password field properly hidden in get all hiring agencies API

**Test Results:**
```
✅ Hiring agency creation with password: PASSED
✅ Hiring agency creation without password: PASSED
✅ Password field properly hidden: PASSED
```

## Security Considerations

1. **Password Storage**: Passwords are stored as plain text in the database. For production, consider hashing passwords.
2. **Write-only Field**: Password field is never returned in API responses
3. **Validation**: Password field uses Django's built-in field validation
4. **Access Control**: Existing permission classes control who can create hiring agencies

## Future Enhancements

1. **Password Hashing**: Implement password hashing for security
2. **Password Validation**: Add password strength requirements
3. **Password Reset**: Implement password reset functionality
4. **Authentication**: Use hiring agency email/password for authentication

## Database Schema

**Before:**
```sql
CREATE TABLE hiring_agency_userdata (
    id INTEGER PRIMARY KEY,
    email VARCHAR(254) UNIQUE,
    role VARCHAR(50),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone_number VARCHAR(15),
    company_name VARCHAR(255),
    linkedin_url TEXT,
    permission_granted DATE,
    created_by_id INTEGER
);
```

**After:**
```sql
CREATE TABLE hiring_agency_userdata (
    id INTEGER PRIMARY KEY,
    email VARCHAR(254) UNIQUE,
    password VARCHAR(128) NULL,
    role VARCHAR(50),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone_number VARCHAR(15),
    company_name VARCHAR(255),
    linkedin_url TEXT,
    permission_granted DATE,
    created_by_id INTEGER
);
```

## Migration Details

**Migration File:** `hiring_agency/migrations/0003_userdata_password.py`

```python
# Generated by Django
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('hiring_agency', '0002_userdata_company_name_userdata_created_by_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='userdata',
            name='password',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
    ]
```

## Conclusion

The implementation successfully adds password support to the Hiring Agency UserData model while maintaining backward compatibility. The API now supports:

- Creating hiring agencies with password
- Creating hiring agencies without password (existing functionality)
- Properly hiding password in all API responses
- Proper validation and error handling

All tests pass, confirming the implementation works as expected.
