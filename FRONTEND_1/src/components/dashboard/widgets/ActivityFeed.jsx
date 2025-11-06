// src/components/dashboard/widgets/ActivityFeed.jsx
import React from 'react';
import { FiUser, FiFileText, FiBriefcase, FiCalendar, FiClock } from 'react-icons/fi';
import './ActivityFeed.css';

const ActivityFeed = ({ config, data }) => {
  const { limit = 10, showTimestamps = true, data: configData } = config;

  // Use config data if available (from data source change), otherwise use dashboard data
  const allActivities = configData ? 
    configData.map(item => ({
      id: item.id,
      type: item.type,
      title: item.message.split(':')[0] || 'Activity',
      description: item.message,
      timestamp: new Date(item.timestamp),
      icon: <FiClock />,
      color: 'primary'
    })) :
    [
      ...(data?.resume_stats?.recent_uploads || []).map(item => ({
        id: item.id,
        type: 'resume_upload',
        title: 'Resume Uploaded',
        description: `New resume: ${item.file.split('/').pop()}`,
        timestamp: new Date(item.uploaded_at),
        icon: <FiFileText />,
        color: 'primary'
      })),
      ...(data?.candidate_stats?.recent_candidates || []).map(item => ({
        id: item.id,
        type: 'new_candidate',
        title: 'New Candidate',
        description: `${item.full_name || 'N/A'} added in ${item.domain} domain`,
        timestamp: new Date(item.created_at),
        icon: <FiUser />,
        color: 'success'
      })),
      ...(data?.job_stats?.recent_jobs || []).map(item => ({
        id: item.id,
        type: 'job_posted',
        title: 'Job Posted',
        description: `${item.job_title} at ${item.company_name}`,
        timestamp: new Date(item.created_at),
        icon: <FiBriefcase />,
        color: 'info'
      })),
      ...(data?.activity_data?.recent_activities || []).map(item => ({
        id: item.id,
        type: item.type || 'activity',
        title: item.name || 'Activity',
        description: item.detail || 'System activity',
        timestamp: new Date(item.date),
        icon: <FiCalendar />,
        color: 'warning'
      }))
    ]
      .sort((a, b) => b.timestamp - a.timestamp)
      .slice(0, limit);

  const getTimeAgo = (timestamp) => {
    const now = new Date();
    const diff = now - timestamp;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    return timestamp.toLocaleDateString();
  };

  const getActivityIcon = (type) => {
    switch (type) {
      case 'resume_upload':
        return <FiFileText />;
      case 'new_candidate':
        return <FiUser />;
      case 'job_posted':
        return <FiBriefcase />;
      case 'interview_scheduled':
        return <FiCalendar />;
      default:
        return <FiClock />;
    }
  };

  const getActivityColor = (color) => {
    switch (color) {
      case 'primary':
        return 'var(--color-primary)';
      case 'success':
        return 'var(--color-success)';
      case 'info':
        return 'var(--color-info)';
      case 'warning':
        return 'var(--color-warning)';
      case 'danger':
        return 'var(--color-danger)';
      default:
        return 'var(--color-text-secondary)';
    }
  };

  if (allActivities.length === 0) {
    return (
      <div className="activity-feed-no-data">
        <div className="no-data-icon">📋</div>
        <p>No recent activities</p>
        <small>Activities will appear here as they happen</small>
      </div>
    );
  }

  return (
    <div className="activity-feed">
      <div className="activity-list">
        {allActivities.map((activity, index) => (
          <div key={activity.id || index} className="activity-item">
            <div 
              className="activity-icon"
              style={{ color: getActivityColor(activity.color) }}
            >
              {getActivityIcon(activity.type)}
            </div>
            
            <div className="activity-content">
              <div className="activity-title">
                {activity.title}
              </div>
              <div className="activity-description">
                {activity.description}
              </div>
              {showTimestamps && (
                <div className="activity-timestamp">
                  {getTimeAgo(activity.timestamp)}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ActivityFeed;

