# Candidate Data Isolation Analysis & Fix

## 🔍 **Issue Identified**

### **Problem Statement**
Hiring agencies and recruiters should only be able to see candidates they added themselves, not candidates added by others. Currently, there is no data isolation implemented for candidates.

### **Root Cause Analysis**
1. **DataIsolationMixin Missing Logic**: The `DataIsolationMixin` didn't handle the `recruiter` field in the `Candidate` model
2. **No Recruiter Assignment**: Existing candidates don't have the `recruiter` field properly set
3. **Missing Object Permissions**: The hierarchy permissions didn't check recruiter relationships

## 🛠️ **Solution Implemented**

### **Fix Applied**
Updated the `DataIsolationMixin` in `utils/hierarchy_permissions.py` to:

1. **Handle Recruiter Field**: Added logic to filter candidates by recruiter's company
2. **Update Object Permissions**: Added recruiter field checking in `_is_object_in_user_company`
3. **Maintain Backward Compatibility**: Preserved existing field handling

### **Code Changes**
```python
# In utils/hierarchy_permissions.py - DataIsolationMixin.get_queryset()
elif hasattr(queryset.model, 'recruiter'):
    # For candidates, filter by recruiter's company
    return queryset.filter(recruiter__company_name=user_company)

# In utils/hierarchy_permissions.py - _is_object_in_user_company()
elif hasattr(obj, 'recruiter') and obj.recruiter:
    return obj.recruiter.get_company_name() == user_company
```

## 📊 **Test Results**

### **Before Fix:**
- **DataIsolationMixin**: Didn't handle `recruiter` field
- **Candidate Filtering**: No isolation - all users could see all candidates
- **Object Permissions**: Didn't check recruiter relationships

### **After Fix:**
- **DataIsolationMixin**: ✅ Now handles `recruiter` field
- **Candidate Filtering**: ✅ Filters by recruiter's company
- **Object Permissions**: ✅ Checks recruiter's company

### **Current Limitation:**
- **No candidates have recruiter assigned**: All 50 candidates have `recruiter: None`
- **Data isolation not effective**: Because candidates lack recruiter assignment
- **Fix is implemented but not functional**: Until recruiter assignment is fixed

## 🎯 **Expected Behavior**

### **Data Isolation Matrix:**

| User Type | Can See Candidates From | Notes |
|-----------|------------------------|-------|
| **ADMIN** | All candidates | Bypasses all isolation |
| **COMPANY** | Their company's recruiters only | Filtered by recruiter's company |
| **HIRING_AGENCY** | Their own candidates only | If they have company_name set |
| **RECRUITER** | Their own candidates only | If they have company_name set |

### **Implementation Details:**
1. **Admin Users**: Can see all candidates (bypasses isolation)
2. **Company Users**: Can see candidates from recruiters in their company
3. **Hiring Agency/Recruiter Users**: Can see candidates they created (if company_name is set)

## ⚠️ **Current Issues**

### **1. Missing Recruiter Assignment**
- **Issue**: All candidates have `recruiter: None`
- **Impact**: Data isolation cannot work without recruiter assignment
- **Solution Needed**: Fix candidate creation to properly set recruiter field

### **2. Existing Data**
- **Issue**: 50 existing candidates need recruiter assignment
- **Impact**: These candidates are visible to all users
- **Solution Needed**: Data migration to assign recruiters to existing candidates

### **3. Company Name Requirements**
- **Issue**: Recruiters need `company_name` for proper filtering
- **Impact**: Data isolation won't work for recruiters without company_name
- **Solution Needed**: Ensure all recruiters have company_name set

## 🔧 **Technical Implementation**

### **DataIsolationMixin Logic:**
```python
def get_queryset(self):
    queryset = super().get_queryset()
    user = self.request.user
    
    # Admin can see all data
    if user.is_admin():
        return queryset
    
    # Other users can only see data from their company
    user_company = user.get_company_name()
    
    # Filter based on different model structures
    if hasattr(queryset.model, 'recruiter'):
        # For candidates, filter by recruiter's company
        return queryset.filter(recruiter__company_name=user_company)
    # ... other field checks
```

### **Object Permission Logic:**
```python
def _is_object_in_user_company(self, user, obj):
    user_company = user.get_company_name()
    
    if hasattr(obj, 'recruiter') and obj.recruiter:
        return obj.recruiter.get_company_name() == user_company
    # ... other field checks
```

## 📋 **Next Steps Required**

### **1. Fix Candidate Creation**
- Investigate why `CandidateCreateSerializer.create()` doesn't set recruiter
- Ensure new candidates get proper recruiter assignment
- Test candidate creation with different user types

### **2. Update Existing Candidates**
- Create data migration to assign recruiters to existing candidates
- Determine appropriate recruiter for each existing candidate
- Run migration to update database

### **3. Verify Company Assignment**
- Ensure all recruiters have proper company_name
- Test data isolation with different user types
- Verify filtering works correctly

### **4. Comprehensive Testing**
- Test with hiring agency users
- Test with recruiter users
- Test with company users
- Verify admin bypass works

## 🚀 **Status: PARTIALLY IMPLEMENTED**

### **✅ What's Working:**
- DataIsolationMixin handles recruiter field
- Object permissions check recruiter relationships
- Code structure supports data isolation

### **❌ What's Not Working:**
- No candidates have recruiter assigned
- Data isolation not effective due to missing data
- Need to fix candidate creation process

### **🎯 Final Goal:**
Hiring agencies and recruiters should only see candidates they added themselves, with proper data isolation based on company relationships.
