# AI Interviewer Platform - Hierarchy Analysis

## 🎯 **Current vs Required Hierarchy**

### **❌ Current Issues Found:**

1. **Role Inconsistencies**: Multiple role definitions across different models
2. **Missing HIRING_AGENCY Role**: The main authapp doesn't have HIRING_AGENCY role
3. **Permission Mismatches**: Current permissions don't match the required hierarchy
4. **Relationship Issues**: No proper company-user relationships defined

---

## 📊 **Current State Analysis**

### **🔍 Role Definitions Found:**

#### **1. authapp/models.py (Main User Model)**
```python
class Role(models.TextChoices):
    ADMIN = 'ADMIN', 'Admin'
    COMPANY = 'COMPANY', 'Company'
    HIRING_MANAGER = 'HIRING_MANAGER', 'Hiring Manager'  # ❌ Should be HIRING_AGENCY
    RECRUITER = 'RECRUITER', 'Recruiter'
    # ... other roles
```

#### **2. hiring_agency/models.py (Separate Model)**
```python
class Role:
    ADMIN = 'Admin'
    COMPANY = 'Company'
    RECRUITER = 'Recruiter'
    HIRING_AGENCY = 'Hiring Agency'  # ✅ Correct but separate model
```

### **❌ Problems Identified:**

1. **Duplicate Role Definitions**: Roles defined in multiple places
2. **Missing HIRING_AGENCY**: Main authapp uses HIRING_MANAGER instead
3. **No Company Relationships**: Users not properly linked to companies
4. **Permission Confusion**: Permissions check for wrong role names

---

## ✅ **Required Hierarchy**

### **🎯 Target Structure:**

```
ADMIN (Super User)
├── All Access to all data
├── Can manage all companies
├── Can manage all hiring agencies
└── Can manage all recruiters

COMPANY (Under Admin)
├── Access to own company data
├── Can manage hiring agencies under their company
├── Can manage recruiters under their company
└── Can view all data within their company

HIRING_AGENCY (Under Company)
├── Access to own data
├── Can upload resumes
├── Can schedule interviews
├── Can check interview results and feedback
└── Limited to their company's scope

RECRUITER (Under Company)
├── Access to own data
├── Can upload resumes
├── Can schedule interviews
├── Can check interview results and feedback
└── Limited to their company's scope
```

---

## 🔧 **Required Changes**

### **1. Fix Role Definitions**
- Add HIRING_AGENCY to main authapp models
- Remove duplicate role definitions
- Standardize role names across the system

### **2. Add Company Relationships**
- Link users to companies properly
- Add company field to user model
- Ensure proper data isolation

### **3. Update Permissions**
- Fix permission classes to use correct roles
- Implement proper hierarchy-based access
- Add company-based data filtering

### **4. Update Models**
- Ensure all models support the hierarchy
- Add proper foreign key relationships
- Implement data isolation by company

---

## 📋 **Implementation Plan**

### **Phase 1: Fix Role Definitions**
1. Update authapp/models.py to include HIRING_AGENCY
2. Remove duplicate role definitions
3. Create migration for role changes

### **Phase 2: Add Company Relationships**
1. Add company field to CustomUser model
2. Update hiring_agency models to link to companies
3. Ensure proper data isolation

### **Phase 3: Update Permissions**
1. Fix all permission classes
2. Implement hierarchy-based access control
3. Add company-based filtering

### **Phase 4: Testing**
1. Test all role combinations
2. Verify data isolation
3. Ensure proper access control

---

## 🚨 **Critical Issues to Fix**

### **1. Role Name Mismatch**
- **Current**: `HIRING_MANAGER` in permissions
- **Required**: `HIRING_AGENCY` 
- **Impact**: Hiring agencies can't access resume/interview features

### **2. Missing Company Relationships**
- **Current**: No proper company-user links
- **Required**: Users must be linked to companies
- **Impact**: No data isolation between companies

### **3. Permission Logic Errors**
- **Current**: Permissions check for wrong roles
- **Required**: Proper hierarchy-based permissions
- **Impact**: Wrong access control

### **4. Data Isolation Issues**
- **Current**: Users can potentially see other companies' data
- **Required**: Strict company-based data isolation
- **Impact**: Security and privacy concerns

---

## 🎯 **Next Steps**

1. **Immediate**: Fix role definitions and add HIRING_AGENCY
2. **Short-term**: Add company relationships and data isolation
3. **Medium-term**: Update all permissions and test thoroughly
4. **Long-term**: Implement advanced hierarchy features

**Status: ❌ REQUIRES IMMEDIATE FIXES** 