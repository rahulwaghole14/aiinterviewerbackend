# Dashboard & Analytics System Implementation

## Overview

The Dashboard & Analytics system provides comprehensive insights and metrics for the AI Interviewer platform. It tracks user activities, system performance, and provides role-based analytics for different user types (Admin, Company, Hiring Agency, Recruiter).

## Features Implemented

### 1. Dashboard Models

#### DashboardMetric
- **Purpose**: Stores aggregated metrics and analytics data
- **Key Fields**:
  - `metric_type`: Type of metric (resume_upload, interview_scheduled, etc.)
  - `value`: Numeric value of the metric
  - `user`: Associated user (optional)
  - `company_name`: Company context (optional)
  - `data`: Additional JSON data
  - `date`: Date of the metric

#### UserActivity
- **Purpose**: Tracks user actions for analytics
- **Key Fields**:
  - `user`: User who performed the action
  - `activity_type`: Type of activity (login, resume_upload, etc.)
  - `details`: JSON details about the activity
  - `ip_address`: User's IP address
  - `user_agent`: Browser/device information

#### DashboardWidget
- **Purpose**: Stores user dashboard widget preferences
- **Key Fields**:
  - `user`: Widget owner
  - `widget_type`: Type of widget (resume_stats, interview_stats, etc.)
  - `position`: Widget position on dashboard
  - `is_enabled`: Whether widget is active
  - `settings`: Widget-specific configuration

#### SystemPerformance
- **Purpose**: Tracks system performance metrics
- **Key Fields**:
  - `metric_name`: Name of the performance metric
  - `value`: Metric value
  - `unit`: Unit of measurement
  - `timestamp`: When the metric was recorded
  - `metadata`: Additional performance data

### 2. DashboardAnalytics Utility Class

The `DashboardAnalytics` class provides static methods for calculating various analytics:

#### Main Methods:
- `get_user_dashboard_data(user, days=30)`: Comprehensive dashboard data for a user
- `_get_resume_stats()`: Resume upload statistics
- `_get_interview_stats()`: Interview scheduling and completion statistics
- `_get_candidate_stats()`: Candidate management statistics
- `_get_job_stats()`: Job posting statistics
- `_get_activity_data()`: User activity tracking
- `_get_performance_data()`: System performance metrics

#### Role-Based Filtering:
- **Admin**: Access to all data across the system
- **Company**: Access to data related to their company
- **Hiring Agency/Recruiter**: Access to their own data

### 3. API Endpoints

#### Main Dashboard Endpoints:
- `GET /api/dashboard/`: Comprehensive dashboard data
- `GET /api/dashboard/summary/`: Dashboard summary
- `GET /api/dashboard/resume-stats/`: Resume statistics
- `GET /api/dashboard/interview-stats/`: Interview statistics
- `GET /api/dashboard/candidate-stats/`: Candidate statistics
- `GET /api/dashboard/job-stats/`: Job statistics

#### Activity Tracking:
- `GET /api/dashboard/activities/`: User activity list
- `POST /api/dashboard/activities/`: Log new activity

#### Widget Management:
- `GET /api/dashboard/widgets/`: List user widgets
- `POST /api/dashboard/widgets/`: Create new widget
- `PUT /api/dashboard/widgets/{id}/`: Update widget
- `DELETE /api/dashboard/widgets/{id}/`: Delete widget
- `GET /api/dashboard/widgets/settings/`: Widget settings

#### Chart Data:
- `GET /api/dashboard/charts/{chart_type}/`: Chart-specific data
- Supported chart types: resume_trends, interview_performance, candidate_distribution, job_statistics

#### Data Export:
- `GET /api/dashboard/export/`: Export dashboard data
- Supports JSON and CSV formats
- Date range filtering

### 4. Analytics Features

#### Resume Analytics:
- Total uploads count
- Success/failure rates
- Daily upload trends
- Recent uploads list

#### Interview Analytics:
- Total interviews scheduled
- Completion rates
- Status distribution (scheduled, completed, cancelled)
- Upcoming interviews

#### Candidate Analytics:
- Total candidates
- Status distribution (new, interviewed, hired)
- Domain distribution
- Hiring success rates

#### Job Analytics:
- Total jobs posted
- Position level distribution
- Recent job postings

#### User Activity Analytics:
- Activity type distribution
- Daily activity trends
- Recent activities

#### System Performance:
- Latest performance metrics
- Performance trends over time

### 5. Integration with Existing Systems

#### Notification Integration:
- Dashboard events trigger notifications
- Performance alerts
- Activity summaries

#### Permission System:
- Role-based access control
- Data isolation between companies
- User-specific data filtering

#### Logging Integration:
- Activity logging for audit trails
- Performance monitoring
- Error tracking

## Technical Implementation

### Database Schema

```sql
-- Dashboard metrics table
CREATE TABLE dashboard_dashboardmetric (
    id SERIAL PRIMARY KEY,
    metric_type VARCHAR(50) NOT NULL,
    user_id INTEGER REFERENCES auth_user(id),
    company_name VARCHAR(255),
    value INTEGER DEFAULT 0,
    data JSONB DEFAULT '{}',
    date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User activity tracking
CREATE TABLE dashboard_useractivity (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES auth_user(id),
    activity_type VARCHAR(50) NOT NULL,
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dashboard widgets
CREATE TABLE dashboard_dashboardwidget (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES auth_user(id),
    widget_type VARCHAR(50) NOT NULL,
    position INTEGER DEFAULT 0,
    is_enabled BOOLEAN DEFAULT TRUE,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System performance metrics
CREATE TABLE dashboard_systemperformance (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    value FLOAT NOT NULL,
    unit VARCHAR(20),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);
```

### API Response Examples

#### Dashboard Data Response:
```json
{
  "resume_stats": {
    "total_uploads": 41,
    "successful_uploads": 41,
    "failed_uploads": 0,
    "success_rate": 100.0,
    "daily_trend": [
      {"date": "2025-07-30", "count": 25},
      {"date": "2025-08-01", "count": 12}
    ],
    "recent_uploads": [...]
  },
  "interview_stats": {
    "total_interviews": 0,
    "scheduled_interviews": 0,
    "completed_interviews": 0,
    "completion_rate": 0,
    "daily_trend": [],
    "upcoming_interviews": []
  },
  "candidate_stats": {
    "total_candidates": 29,
    "active_candidates": 29,
    "interviewed_candidates": 0,
    "hired_candidates": 0,
    "hiring_rate": 0.0,
    "domain_distribution": [...],
    "recent_candidates": [...]
  },
  "job_stats": {
    "total_jobs": 4,
    "active_jobs": 4,
    "closed_jobs": 0,
    "level_distribution": [...],
    "recent_jobs": [...]
  },
  "activity_data": {
    "total_activities": 1,
    "activity_distribution": [...],
    "daily_trend": [...],
    "recent_activities": [...]
  },
  "performance_data": {
    "latest_metrics": {...},
    "performance_trend": [...]
  },
  "date_range": {
    "start_date": "2025-07-05",
    "end_date": "2025-08-04",
    "days": 30
  }
}
```

## Testing

### Test Coverage:
- ✅ Model creation and validation
- ✅ Analytics calculations
- ✅ Role-based data filtering
- ✅ API endpoint functionality
- ✅ Widget management
- ✅ Data export functionality

### Test Results:
```
[2025-08-04 17:16:01] INFO: ✓ Dashboard models working correctly
[2025-08-04 17:16:01] INFO: ✓ DashboardAnalytics utility class working correctly
[2025-08-04 17:16:01] INFO: ✓ ADMIN user dashboard data: 7 keys
[2025-08-04 17:16:01] INFO: ✓ COMPANY user dashboard data: 7 keys
[2025-08-04 17:16:01] INFO: ✓ HIRING_AGENCY user dashboard data: 7 keys
```

## Configuration

### Settings:
- Dashboard app added to `INSTALLED_APPS`
- URL routing configured in main `urls.py`
- Admin interface configured for all models

### Dependencies:
- Django REST Framework
- Django Filter
- JSONField support

## Usage Examples

### Creating a Dashboard Widget:
```python
widget = DashboardWidget.objects.create(
    user=user,
    widget_type='resume_stats',
    position=1,
    settings={'chart_type': 'bar', 'refresh_interval': 300}
)
```

### Logging User Activity:
```python
UserActivity.objects.create(
    user=user,
    activity_type='resume_upload',
    details={'filename': 'resume.pdf', 'size': 1024000},
    ip_address='192.168.1.1'
)
```

### Getting Analytics Data:
```python
# Get comprehensive dashboard data
dashboard_data = DashboardAnalytics.get_user_dashboard_data(user, days=30)

# Get specific statistics
resume_stats = DashboardAnalytics._get_resume_stats(user, start_date, end_date, {})
```

## Future Enhancements

### Planned Features:
1. **Real-time Analytics**: WebSocket-based real-time dashboard updates
2. **Advanced Filtering**: More granular filtering options
3. **Custom Dashboards**: User-defined dashboard layouts
4. **Export Formats**: Additional export formats (Excel, PDF)
5. **Performance Optimization**: Caching and query optimization
6. **Mobile Dashboard**: Mobile-optimized dashboard views

### Performance Considerations:
- Database indexing on frequently queried fields
- Caching for expensive analytics calculations
- Pagination for large datasets
- Background task processing for heavy analytics

## Conclusion

The Dashboard & Analytics system provides a comprehensive solution for tracking and visualizing platform usage, user activities, and system performance. It supports role-based access control and provides actionable insights for different user types.

The implementation is production-ready with proper error handling, testing coverage, and scalable architecture for future enhancements. 