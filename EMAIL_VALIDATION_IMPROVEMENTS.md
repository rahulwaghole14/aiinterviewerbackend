# 📧 Email Validation & Notification Improvements

## ⚠️ **Current Issue:**
If a candidate's email is incorrect or invalid, emails fail silently and recruiters are not notified.

---

## 🔧 **Recommended Improvements:**

### **1. Enhanced Email Validation**

#### **Add to `candidates/serializers.py`:**
```python
import re
from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError

class CandidateCreateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True, allow_blank=False)  # Make required
    
    def validate_email(self, value):
        """Enhanced email validation"""
        if not value or not value.strip():
            raise serializers.ValidationError("Email is required")
        
        # Basic format validation
        email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(email_regex, value):
            raise serializers.ValidationError("Invalid email format")
        
        # Django's built-in validation
        try:
            validate_email(value)
        except DjangoValidationError:
            raise serializers.ValidationError("Invalid email address")
        
        # Check for common typos
        common_domains = {
            'gmial.com': 'gmail.com',
            'gmai.com': 'gmail.com',
            'yahooo.com': 'yahoo.com',
            'outlok.com': 'outlook.com',
            'hotmial.com': 'hotmail.com',
        }
        
        domain = value.split('@')[-1].lower()
        if domain in common_domains:
            suggested = f"{value.split('@')[0]}@{common_domains[domain]}"
            raise serializers.ValidationError(
                f"Did you mean '{suggested}'? '{domain}' appears to be a typo."
            )
        
        return value.lower().strip()
```

---

### **2. Email Delivery Status Tracking**

#### **Add to `candidates/models.py`:**
```python
class Candidate(models.Model):
    # ... existing fields ...
    
    email_verified = models.BooleanField(default=False)
    last_email_sent_at = models.DateTimeField(null=True, blank=True)
    email_delivery_failed = models.BooleanField(default=False)
    email_failure_reason = models.TextField(blank=True)
    email_retry_count = models.IntegerField(default=0)
```

#### **Add to `notifications/models.py`:**
```python
class EmailLog(models.Model):
    """Track all email attempts"""
    
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"
        BOUNCED = "bounced", "Bounced"
    
    candidate = models.ForeignKey(
        'candidates.Candidate',
        on_delete=models.CASCADE,
        related_name='email_logs'
    )
    interview = models.ForeignKey(
        'interviews.Interview',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    email_address = models.EmailField()
    subject = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
```

---

### **3. Improved Notification Service**

#### **Update `notifications/services.py`:**
```python
@staticmethod
def send_candidate_interview_scheduled_notification(interview):
    """Send notification with tracking and error handling"""
    try:
        candidate = interview.candidate
        candidate_email = candidate.email
        
        # Validate email exists
        if not candidate_email or not candidate_email.strip():
            error_msg = "Candidate email is missing"
            logger.error(f"Email notification failed: {error_msg}")
            
            # Create email log
            EmailLog.objects.create(
                candidate=candidate,
                interview=interview,
                email_address="N/A",
                subject="Interview Scheduled",
                status=EmailLog.Status.FAILED,
                error_message=error_msg
            )
            
            # Notify recruiter
            NotificationService.send_notification(
                user=interview.candidate.recruiter,
                title="Email Notification Failed",
                message=f"Failed to send interview notification to {candidate.full_name}: Email address is missing.",
                notification_type=NotificationType.ERROR,
                priority=NotificationPriority.HIGH
            )
            
            return False
        
        # Validate email format
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        
        try:
            validate_email(candidate_email)
        except ValidationError:
            error_msg = f"Invalid email format: {candidate_email}"
            logger.error(f"Email notification failed: {error_msg}")
            
            # Create email log
            EmailLog.objects.create(
                candidate=candidate,
                interview=interview,
                email_address=candidate_email,
                subject="Interview Scheduled",
                status=EmailLog.Status.FAILED,
                error_message=error_msg
            )
            
            # Notify recruiter
            NotificationService.send_notification(
                user=interview.candidate.recruiter,
                title="Invalid Email Address",
                message=f"Cannot send notification to {candidate.full_name}: Invalid email '{candidate_email}'",
                notification_type=NotificationType.ERROR,
                priority=NotificationPriority.HIGH
            )
            
            return False
        
        # Generate email content
        subject, message = _generate_email_content(interview)
        
        # Try to send email
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[candidate_email],
                fail_silently=False,
            )
            
            # Success - log it
            logger.info(f"✅ Email sent successfully: {candidate_email}")
            
            EmailLog.objects.create(
                candidate=candidate,
                interview=interview,
                email_address=candidate_email,
                subject=subject,
                status=EmailLog.Status.SENT,
                sent_at=timezone.now()
            )
            
            # Update candidate
            candidate.last_email_sent_at = timezone.now()
            candidate.email_delivery_failed = False
            candidate.email_failure_reason = ""
            candidate.save(update_fields=['last_email_sent_at', 'email_delivery_failed', 'email_failure_reason'])
            
            # Notify recruiter of success
            NotificationService.send_notification(
                user=interview.candidate.recruiter,
                title="Interview Notification Sent",
                message=f"Email successfully sent to {candidate.full_name} ({candidate_email})",
                notification_type=NotificationType.SUCCESS,
                priority=NotificationPriority.MEDIUM
            )
            
            return True
            
        except Exception as email_error:
            # Email sending failed
            error_msg = str(email_error)
            logger.error(f"❌ SMTP email failed: {error_msg}")
            
            EmailLog.objects.create(
                candidate=candidate,
                interview=interview,
                email_address=candidate_email,
                subject=subject,
                status=EmailLog.Status.FAILED,
                error_message=error_msg
            )
            
            # Update candidate
            candidate.email_delivery_failed = True
            candidate.email_failure_reason = error_msg
            candidate.email_retry_count += 1
            candidate.save(update_fields=['email_delivery_failed', 'email_failure_reason', 'email_retry_count'])
            
            # Notify recruiter with interview link
            interview_url = interview.get_interview_url()
            NotificationService.send_notification(
                user=interview.candidate.recruiter,
                title="⚠️ Email Delivery Failed",
                message=f"""
Failed to send interview notification to {candidate.full_name}.

Email: {candidate_email}
Error: {error_msg}

ACTION REQUIRED:
Please manually share the interview link with the candidate:
{interview_url}

You can also update the candidate's email and retry.
                """.strip(),
                notification_type=NotificationType.ERROR,
                priority=NotificationPriority.HIGH
            )
            
            return False
            
    except Exception as e:
        logger.error(f"❌ Unexpected error in email notification: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
```

---

### **4. Frontend Improvements**

#### **Add Email Validation to `AddCandidates.jsx`:**
```javascript
const validateEmail = (email) => {
  if (!email || !email.trim()) {
    return { valid: false, message: "Email is required" };
  }
  
  // Basic format validation
  const emailRegex = /^[\w\.-]+@[\w\.-]+\.\w+$/;
  if (!emailRegex.test(email)) {
    return { valid: false, message: "Invalid email format" };
  }
  
  // Check for common typos
  const commonTypos = {
    'gmial.com': 'gmail.com',
    'gmai.com': 'gmail.com',
    'yahooo.com': 'yahoo.com',
    'outlok.com': 'outlook.com',
    'hotmial.com': 'hotmail.com',
  };
  
  const domain = email.split('@')[1]?.toLowerCase();
  if (domain && commonTypos[domain]) {
    return {
      valid: false,
      message: `Did you mean '${email.split('@')[0]}@${commonTypos[domain]}'?`,
      suggestion: `${email.split('@')[0]}@${commonTypos[domain]}`
    };
  }
  
  return { valid: true };
};

const handleSubmit = async (e) => {
  e.preventDefault();
  
  // Validate email
  const emailValidation = validateEmail(formData.email);
  if (!emailValidation.valid) {
    notify.error(emailValidation.message);
    if (emailValidation.suggestion) {
      // Show suggestion to user
      notify.info(`Suggestion: ${emailValidation.suggestion}`);
    }
    return;
  }
  
  // Continue with submission...
};
```

#### **Add Email Status Indicator:**
```javascript
// In candidate list/table
<div className="email-status">
  {candidate.email_delivery_failed ? (
    <span className="email-failed" title={candidate.email_failure_reason}>
      ⚠️ Email Failed
    </span>
  ) : candidate.last_email_sent_at ? (
    <span className="email-sent">
      ✅ Email Sent
    </span>
  ) : (
    <span className="email-pending">
      📧 No Email Sent
    </span>
  )}
</div>
```

---

### **5. Manual Retry Feature**

#### **Add API Endpoint:**
```python
# interviews/views.py

@action(detail=True, methods=['post'])
def resend_notification(self, request, pk=None):
    """Manually resend interview notification"""
    interview = self.get_object()
    
    # Update email if provided
    new_email = request.data.get('email')
    if new_email:
        interview.candidate.email = new_email
        interview.candidate.save(update_fields=['email'])
    
    # Resend notification
    success = NotificationService.send_candidate_interview_scheduled_notification(interview)
    
    if success:
        return Response({
            'message': 'Notification sent successfully',
            'email': interview.candidate.email
        })
    else:
        return Response({
            'error': 'Failed to send notification',
            'email': interview.candidate.email
        }, status=status.HTTP_400_BAD_REQUEST)
```

#### **Add Frontend Button:**
```javascript
// In AI Interview Scheduler
<button 
  onClick={() => handleResendEmail(interview.id)}
  className="resend-email-btn"
  title="Resend interview notification"
>
  🔄 Resend Email
</button>
```

---

## 📊 **Benefits of These Improvements:**

### **For Recruiters:**
✅ **Instant Feedback** - Know immediately if email failed
✅ **Interview Link Available** - Can manually share if email fails
✅ **Email Correction** - Can update email and retry
✅ **Email History** - Track all email attempts
✅ **Proactive Alerts** - Get notified of delivery issues

### **For Candidates:**
✅ **Better Validation** - Catch typos before submission
✅ **Suggestions** - Get corrections for common mistakes
✅ **Reliable Delivery** - Higher success rate
✅ **Retry Mechanism** - Can receive email after correction

### **For System:**
✅ **Error Tracking** - Complete audit trail
✅ **Monitoring** - Track email delivery rates
✅ **Debugging** - Detailed error logs
✅ **Analytics** - Understand email issues

---

## 🚀 **Implementation Priority:**

### **Phase 1: Critical (Implement First)**
1. ✅ Email validation in serializers
2. ✅ Recruiter notifications on email failure
3. ✅ Include interview link in failure notification

### **Phase 2: Important**
1. Email delivery tracking (EmailLog model)
2. Frontend email validation with suggestions
3. Resend email endpoint

### **Phase 3: Nice to Have**
1. Email status indicators in UI
2. Email delivery analytics
3. Automated retry mechanism
4. Email verification system

---

## 📧 **Quick Fix (Minimal Changes):**

If you want a quick fix without major changes, add this to `notifications/services.py`:

```python
# After email fails (line 362)
except Exception as console_error:
    logger.error(f"Both SMTP and console email failed: {console_error}")
    
    # ADD THIS: Notify recruiter
    try:
        interview_url = interview.get_interview_url() if hasattr(interview, 'get_interview_url') else "N/A"
        NotificationService.send_notification(
            user=interview.candidate.recruiter,
            title="⚠️ Interview Email Failed",
            message=f"Failed to email {interview.candidate.full_name} at {candidate_email}. Please manually share: {interview_url}",
            notification_type=NotificationType.ERROR,
            priority=NotificationPriority.HIGH
        )
    except Exception as notif_error:
        logger.error(f"Failed to send recruiter notification: {notif_error}")
```

This ensures recruiters are notified and can take manual action.

---

**Last Updated:** October 7, 2025  
**Status:** 📋 Recommendations Ready for Implementation

