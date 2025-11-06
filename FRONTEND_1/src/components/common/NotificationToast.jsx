// src/components/common/NotificationToast.jsx
import React, { useEffect, useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { hideNotification } from '../../redux/slices/notificationSlice';
import './NotificationToast.css';

const NotificationToast = () => {
  const dispatch = useDispatch();
  const notifications = useSelector(state => state.notification.notifications);
  const [expandedNotifications, setExpandedNotifications] = useState(new Set());

  const handleClose = (notificationId) => {
    dispatch(hideNotification(notificationId));
    setExpandedNotifications(prev => {
      const newSet = new Set(prev);
      newSet.delete(notificationId);
      return newSet;
    });
  };

  const handleViewDetails = (notificationId) => {
    setExpandedNotifications(prev => {
      const newSet = new Set(prev);
      if (newSet.has(notificationId)) {
        newSet.delete(notificationId);
      } else {
        newSet.add(notificationId);
      }
      return newSet;
    });
  };

  useEffect(() => {
    // Auto-dismiss notifications that have duration > 0 and are not expanded
    const timers = [];
    
    notifications.forEach(notification => {
      if (notification.duration > 0 && !expandedNotifications.has(notification.id)) {
        const timer = setTimeout(() => {
          dispatch(hideNotification(notification.id));
        }, notification.duration);
        timers.push(timer);
      }
    });

    return () => {
      timers.forEach(timer => clearTimeout(timer));
    };
  }, [notifications, expandedNotifications, dispatch]);

  if (notifications.length === 0) {
    return null;
  }

  const getIcon = (type) => {
    switch (type) {
      case 'success':
        return (
          <svg className="toast-icon" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
        );
      case 'error':
        return (
          <svg className="toast-icon" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        );
      case 'warning':
        return (
          <svg className="toast-icon" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        );
      case 'info':
        return (
          <svg className="toast-icon" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
        );
      default:
        return null;
    }
  };

  return (
    <div className="toast-container">
      {notifications.map((notification, index) => {
        const isExpanded = expandedNotifications.has(notification.id);
        
        return (
          <div
            key={notification.id}
            className={`toast toast-${notification.type} ${isExpanded ? 'toast-expanded' : ''}`}
            style={{
              transform: `translateY(-${index * 10}px)`,
              zIndex: 1000 - index
            }}
          >
            {/* Progress bar for auto-dismiss */}
            {notification.duration > 0 && !isExpanded && (
              <div className="toast-progress-bar">
                <div 
                  className="toast-progress-fill"
                  style={{
                    animationDuration: `${notification.duration}ms`
                  }}
                ></div>
              </div>
            )}

            <div className="toast-content">
              <div className="toast-header">
                <div className="toast-icon-title">
                  {getIcon(notification.type)}
                  <span className="toast-title">{notification.title}</span>
                </div>
                
                <div className="toast-actions">
                  {!isExpanded && (
                    <button 
                      className="toast-action-btn toast-details-btn"
                      onClick={() => handleViewDetails(notification.id)}
                      title="View details"
                    >
                      View Details
                    </button>
                  )}
                  <button 
                    className="toast-action-btn toast-close-btn"
                    onClick={() => handleClose(notification.id)}
                    title="Close"
                  >
                    Close
                  </button>
                </div>
              </div>

              <div className="toast-message">
                {isExpanded ? (
                  <div className="toast-expanded-content">
                    <p className="toast-message-text">{notification.message}</p>
                    <div className="toast-meta">
                      <span className="toast-timestamp">
                        {new Date(notification.timestamp).toLocaleTimeString('en-US', {
                          hour: 'numeric',
                          minute: '2-digit',
                          hour12: true
                        })}
                      </span>
                      <span className="toast-type-badge">
                        {notification.type.toUpperCase()}
                      </span>
                    </div>
                    <div className="toast-expanded-actions">
                      <button 
                        className="toast-collapse-btn"
                        onClick={() => handleViewDetails(notification.id)}
                      >
                        Collapse
                      </button>
                    </div>
                  </div>
                ) : (
                  <p className="toast-message-text toast-message-truncated">
                    {notification.message.length > 60 
                      ? `${notification.message.substring(0, 60)}...` 
                      : notification.message
                    }
                  </p>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default NotificationToast;
