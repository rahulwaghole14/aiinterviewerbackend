# 🔗 Link-Based Interview Access System

## 🎯 **Overview**

The Link-Based Interview Access System allows candidates to join AI interviews without requiring user registration or login. Candidates receive secure, time-limited links via email when interviews are scheduled by recruiters, and can only access the interview at the scheduled date and time.

---

## ✅ **Key Features**

### **🔐 Security Features**
- **HMAC-based secure links** with cryptographic signatures
- **Time-based access control** - links only work during interview window
- **Automatic link expiration** - links expire 2 hours after interview ends
- **No authentication required** - candidates access directly via links
- **Link validation** - prevents unauthorized access and tampering

### **📅 Time Management**
- **15-minute early access** - candidates can join 15 minutes before scheduled time
- **2-hour post-interview access** - links remain valid for 2 hours after interview ends
- **Real-time validation** - checks current time against interview schedule
- **Automatic timezone handling** - uses UTC for consistency

### **📧 Email Integration**
- **Automatic email notifications** when interviews are scheduled
- **Secure interview links** included in email body
- **Professional email templates** with interview details
- **Direct candidate communication** - no recruiter intervention needed

---

## 🏗️ **System Architecture**

### **Database Schema**

```python
class Interview(models.Model):
    # ... existing fields ...
    
    # Secure interview link for candidate access
    interview_link = models.CharField(max_length=255, blank=True, help_text="Secure link for candidate to join interview")
    link_expires_at = models.DateTimeField(null=True, blank=True, help_text="When the interview link expires")
```

### **Link Generation Process**

1. **Token Creation**: Combines interview ID, candidate email, and scheduled time
2. **HMAC Signing**: Uses secret key to create cryptographic signature
3. **Base64 Encoding**: Creates URL-safe token
4. **Expiration Setting**: Sets link to expire 2 hours after interview ends

### **Link Validation Process**

1. **Token Decoding**: Decodes base64 token to extract interview ID and signature
2. **Signature Verification**: Validates HMAC signature against secret key
3. **Time Validation**: Checks if current time is within interview window
4. **Access Control**: Allows access only during valid time period

---

## 🔧 **API Endpoints**

### **Public Interview Access (No Authentication Required)**

#### **1. Get Interview Details**
```
GET /api/interviews/public/{link_token}/
```

**Response:**
```json
{
    "interview_id": "uuid",
    "candidate_name": "John Doe",
    "candidate_email": "john.doe@example.com",
    "job_title": "Senior Software Engineer",
    "company_name": "Tech Corp",
    "interview_round": "Technical Round 1",
    "scheduled_date": "January 15, 2025",
    "scheduled_time": "10:00 AM",
    "duration_minutes": 60,
    "ai_interview_type": "technical",
    "status": "scheduled",
    "video_url": "https://meet.google.com/...",
    "can_join": true,
    "message": "You can now join your interview"
}
```

#### **2. Join Interview**
```
POST /api/interviews/public/{link_token}/
```

**Response:**
```json
{
    "interview_id": "uuid",
    "candidate_name": "John Doe",
    "ai_interview_type": "technical",
    "started_at": "2025-01-15T10:00:00Z",
    "status": "started",
    "message": "Interview started successfully",
    "ai_configuration": {
        "difficulty_level": "intermediate",
        "question_count": 10,
        "time_limit": 60
    }
}
```

### **Admin/Recruiter Endpoints (Authentication Required)**

#### **3. Generate Interview Link**
```
POST /api/interviews/{interview_id}/generate-link/
```

**Response:**
```json
{
    "interview_link": "base64_encoded_token",
    "interview_url": "http://localhost:3000/interview/base64_encoded_token",
    "expires_at": "2025-01-15T12:00:00Z",
    "message": "Interview link generated successfully"
}
```

---

## 📧 **Email Notification System**

### **Email Template**
```
Subject: Interview Scheduled - Senior Software Engineer at Tech Corp

Dear John Doe,

Your interview has been scheduled successfully!

📋 **Interview Details:**
• Position: Senior Software Engineer
• Company: Tech Corp
• Date & Time: January 15, 2025 at 10:00 AM
• Interview Type: Technical Interview

🔗 **Join Your Interview:**
Click the link below to join your interview at the scheduled time:
http://localhost:3000/interview/base64_encoded_token

⚠️ **Important Notes:**
• Please join the interview 5-10 minutes before the scheduled time
• You can only access the interview link at the scheduled date and time
• The link will be active 15 minutes before the interview starts
• Make sure you have a stable internet connection and a quiet environment

📧 **Contact Information:**
If you have any questions or need to reschedule, please contact your recruiter.

Best regards,
Tech Corp Recruitment Team

---
This is an automated message. Please do not reply to this email.
```

---

## 🔒 **Security Implementation**

### **Link Generation**
```python
def generate_interview_link(self):
    """Generate a secure interview link for the candidate"""
    if not self.started_at:
        return None
    
    # Create a unique token based on interview ID and candidate email
    token_data = f"{self.id}:{self.candidate.email}:{self.started_at.isoformat()}"
    
    # Use HMAC with a secret key for security
    secret_key = getattr(settings, 'INTERVIEW_LINK_SECRET', 'default-secret-key')
    signature = hmac.new(
        secret_key.encode('utf-8'),
        token_data.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # Create the link token
    link_token = base64.urlsafe_b64encode(f"{self.id}:{signature}".encode('utf-8')).decode('utf-8')
    
    # Set expiration to 2 hours after interview end time
    self.link_expires_at = self.ended_at + timedelta(hours=2) if self.ended_at else None
    self.interview_link = link_token
    self.save()
    
    return link_token
```

### **Link Validation**
```python
def validate_interview_link(self, link_token):
    """Validate if the interview link is valid and accessible"""
    if not self.interview_link or self.interview_link != link_token:
        return False, "Invalid interview link"
    
    if self.link_expires_at and timezone.now() > self.link_expires_at:
        return False, "Interview link has expired"
    
    # Check if it's within the interview window (15 minutes before to 2 hours after)
    now = timezone.now()
    if self.started_at and self.ended_at:
        interview_start = self.started_at - timedelta(minutes=15)
        interview_end = self.ended_at + timedelta(hours=2)
        
        if now < interview_start:
            return False, f"Interview hasn't started yet. Please join at {self.started_at.strftime('%B %d, %Y at %I:%M %p')}"
        
        if now > interview_end:
            return False, "Interview has ended"
    
    return True, "Link is valid"
```

---

## 🚀 **Usage Flow**

### **1. Interview Scheduling (Recruiter)**
1. Recruiter schedules interview via API
2. System automatically generates secure interview link
3. Email notification sent to candidate with interview link
4. Interview link stored in database with expiration time

### **2. Interview Access (Candidate)**
1. Candidate receives email with interview link
2. Candidate clicks link at scheduled time (or 15 minutes before)
3. System validates link and time window
4. Candidate can view interview details and join interview
5. Interview starts and AI configuration is provided

### **3. Security Validation**
1. Link token is decoded and signature verified
2. Current time is checked against interview window
3. Access is granted only if all validations pass
4. All access attempts are logged for security

---

## ⚙️ **Configuration**

### **Environment Variables**
```bash
# Required for interview link security
INTERVIEW_LINK_SECRET=your-secret-key-here

# Frontend URL for interview links
FRONTEND_URL=http://localhost:3000

# Email configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@talaro.com
```

### **Settings Configuration**
```python
# In settings.py
INTERVIEW_LINK_SECRET = config('INTERVIEW_LINK_SECRET', default='default-secret-key')
FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:3000')
```

---

## 🧪 **Testing**

### **Test Script**
Run the comprehensive test script to verify the system:
```bash
python test_link_based_interview_access.py
```

### **Manual Testing**
1. Schedule an interview via API
2. Check email notification is sent with link
3. Test link access before scheduled time (should be rejected)
4. Test link access during scheduled time (should work)
5. Test link access after expiration (should be rejected)
6. Test invalid link (should be rejected)

---

## 📊 **Monitoring & Logging**

### **Access Logging**
All interview access attempts are logged with:
- Interview ID
- Candidate email
- Access timestamp
- Link validation result
- IP address (if available)

### **Security Monitoring**
- Failed access attempts
- Expired link attempts
- Invalid signature attempts
- Time-based access violations

---

## 🔄 **Integration Points**

### **With Interview Scheduling**
- Automatic link generation when interview is created
- Email notification integration
- Link storage in interview record

### **With AI Interview System**
- AI configuration provided when interview starts
- Interview type and settings passed to frontend
- Real-time interview status updates

### **With Notification System**
- Email template integration
- Candidate notification service
- Recruiter notification for interview scheduling

---

## 🛡️ **Security Considerations**

### **Link Security**
- **Cryptographic signatures** prevent tampering
- **Time-based expiration** limits access window
- **Unique per interview** prevents link reuse
- **No sensitive data** in link tokens

### **Access Control**
- **No authentication bypass** - links are specific to interviews
- **Time window validation** - prevents early/late access
- **Interview-specific access** - links only work for specific interviews
- **Automatic expiration** - links become invalid after interview

### **Data Protection**
- **No candidate credentials** stored in links
- **Minimal data exposure** in public endpoints
- **Secure token generation** using HMAC
- **Audit logging** for all access attempts

---

## 📈 **Performance Considerations**

### **Link Generation**
- **Fast HMAC computation** for link generation
- **Efficient database queries** for validation
- **Caching opportunities** for frequently accessed interviews

### **Validation Performance**
- **Single database query** for link validation
- **Efficient time comparisons** using database indexes
- **Minimal computational overhead** for security checks

---

## 🔮 **Future Enhancements**

### **Planned Features**
- **QR Code generation** for mobile access
- **SMS notifications** with interview links
- **Calendar integration** with interview links
- **Multi-language support** for email templates

### **Security Enhancements**
- **Rate limiting** for link access attempts
- **Geographic restrictions** for interview access
- **Device fingerprinting** for additional security
- **Two-factor authentication** for sensitive interviews

---

## 📝 **Conclusion**

The Link-Based Interview Access System provides a secure, user-friendly way for candidates to join AI interviews without requiring registration or login. The system ensures:

✅ **Security**: HMAC-based links with time-based access control
✅ **Usability**: Simple link-based access for candidates
✅ **Reliability**: Automatic email notifications and link generation
✅ **Monitoring**: Comprehensive logging and access tracking
✅ **Integration**: Seamless integration with existing interview system

The system successfully eliminates the need for candidate login while maintaining security and providing a smooth interview experience.
