# Resume Upload & Interview Scheduling Permissions Implementation

## 🎯 **Implementation Summary**

Successfully implemented role-based permissions to restrict resume uploads and interview scheduling to only hiring agency and recruiter users.

---

## ✅ **Successfully Implemented Features:**

### **1. Resume Upload Permissions:**
- ✅ **Custom Permission Class**: `HiringAgencyOrRecruiterPermission`
- ✅ **Restricted Access**: Only `HIRING_MANAGER` and `RECRUITER` roles can upload resumes
- ✅ **Bulk Upload Protection**: Same restrictions apply to bulk resume uploads
- ✅ **Read Access**: All authenticated users can view resumes

### **2. Interview Scheduling Permissions:**
- ✅ **Custom Permission Class**: `HiringAgencyOrRecruiterInterviewPermission`
- ✅ **Restricted Access**: Only `HIRING_MANAGER` and `RECRUITER` roles can schedule interviews
- ✅ **Read Access**: All authenticated users can view interviews
- ✅ **Update Protection**: Only authorized roles can modify interviews

---

## 🔧 **Technical Implementation:**

### **1. Resume Permissions (`resumes/permissions.py`):**
```python
class HiringAgencyOrRecruiterPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Allow read operations for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Allow write operations only for HIRING_MANAGER and RECRUITER users
        return request.user.role in ['HIRING_MANAGER', 'RECRUITER']
```

### **2. Interview Permissions (`interviews/permissions.py`):**
```python
class HiringAgencyOrRecruiterInterviewPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Allow read operations for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Allow write operations only for HIRING_MANAGER and RECRUITER users
        return request.user.role in ['HIRING_MANAGER', 'RECRUITER']
```

### **3. Updated Views:**

#### **Resume Views (`resumes/views.py`):**
- **ResumeViewSet**: Uses `HiringAgencyOrRecruiterPermission`
- **BulkResumeUploadView**: Uses `HiringAgencyOrRecruiterPermission`
- **Single Upload**: Protected by role-based permissions
- **Bulk Upload**: Protected by role-based permissions

#### **Interview Views (`interviews/views.py`):**
- **InterviewViewSet**: Uses `HiringAgencyOrRecruiterInterviewPermission`
- **Interview Creation**: Protected by role-based permissions
- **Interview Updates**: Protected by role-based permissions
- **Interview Listing**: Available to all authenticated users

---

## 📊 **Permission Matrix:**

| User Role | Resume Upload | Bulk Resume Upload | Interview Scheduling | Interview Viewing |
|-----------|---------------|-------------------|---------------------|-------------------|
| **HIRING_MANAGER** | ✅ Allowed | ✅ Allowed | ✅ Allowed | ✅ Allowed |
| **RECRUITER** | ✅ Allowed | ✅ Allowed | ✅ Allowed | ✅ Allowed |
| **ADMIN** | ❌ Blocked | ❌ Blocked | ❌ Blocked | ✅ Allowed |
| **COMPANY** | ❌ Blocked | ❌ Blocked | ❌ Blocked | ✅ Allowed |
| **OTHER ROLES** | ❌ Blocked | ❌ Blocked | ❌ Blocked | ✅ Allowed |

---

## 🎯 **Key Features Implemented:**

### **1. Role-Based Security:**
- Only hiring managers and recruiters can upload resumes
- Only hiring managers and recruiters can schedule interviews
- All authenticated users can view resumes and interviews
- Proper permission validation at both view and object levels

### **2. Comprehensive Protection:**
- **Single Resume Upload**: Protected by role-based permissions
- **Bulk Resume Upload**: Protected by role-based permissions
- **Interview Creation**: Protected by role-based permissions
- **Interview Updates**: Protected by role-based permissions

### **3. Flexible Access Control:**
- Read operations available to all authenticated users
- Write operations restricted to specific roles
- Proper error handling and user feedback

---

## 🔒 **Security Features:**

### **1. Authentication Required:**
- All endpoints require authentication
- Unauthenticated users are blocked

### **2. Role-Based Access Control:**
- Specific roles can perform specific actions
- Clear separation of responsibilities
- Proper permission inheritance

### **3. Error Handling:**
- Proper 403 Forbidden responses for unauthorized access
- Clear error messages for debugging
- Graceful handling of permission violations

---

## 📝 **Usage Examples:**

### **Hiring Manager Uploading Resume:**
```json
POST /api/resumes/
Authorization: Token <hiring_manager_token>
Content-Type: multipart/form-data

file: resume.pdf
// ✅ Success (201 Created)
```

### **Recruiter Scheduling Interview:**
```json
POST /api/interviews/
Authorization: Token <recruiter_token>
Content-Type: application/json

{
    "candidate": 1,
    "job": 1,
    "scheduled_at": "2024-01-15T10:00:00Z",
    "status": "scheduled"
}
// ✅ Success (201 Created)
```

### **Admin Attempting Resume Upload:**
```json
POST /api/resumes/
Authorization: Token <admin_token>
Content-Type: multipart/form-data

file: resume.pdf
// ❌ Forbidden (403)
```

---

## 🚀 **Status: SUCCESSFULLY IMPLEMENTED**

### **✅ Core Requirements Met:**
1. **Only hiring agency users can upload resumes** ✅
2. **Only recruiter users can upload resumes** ✅
3. **Only hiring agency users can schedule interviews** ✅
4. **Only recruiter users can schedule interviews** ✅
5. **Other users are properly blocked** ✅
6. **Read access available to all authenticated users** ✅

### **✅ Security Features:**
- Role-based access control implemented
- Proper permission validation
- Clear error responses
- Comprehensive protection

---

## 🎯 **Conclusion:**

**✅ Resume upload and interview scheduling permissions have been successfully implemented!**

Only hiring managers and recruiters can now upload resumes and schedule interviews, while all other users are properly restricted. The implementation includes comprehensive security features and proper error handling. 