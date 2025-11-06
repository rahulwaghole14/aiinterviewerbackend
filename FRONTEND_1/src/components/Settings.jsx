// src/components/Settings.jsx
import React, { useState, useEffect } from 'react';
import { useNotification } from '../hooks/useNotification';
import { useTheme } from '../contexts/ThemeContext';
import ThemeToggle from './common/ThemeToggle';
import CustomDropdown from './common/CustomDropdown';
import './Settings.css';

const Settings = ({ onTitleChange }) => {
  const notify = useNotification();
  const { theme, isSystemTheme } = useTheme();
  
  // State for various settings
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [smsNotifications, setSmsNotifications] = useState(false);
  const [dataExportFormat, setDataExportFormat] = useState('csv'); // 'csv', 'json', 'pdf'
  const [defaultJobStatus, setDefaultJobStatus] = useState('Open'); // 'Open', 'Closed', 'On Hold'
  const [autoArchiveJobs, setAutoArchiveJobs] = useState(false); // Toggle for auto-archiving

  useEffect(() => {
    // Update the header title when this component mounts
    if (onTitleChange) {
      onTitleChange('Settings');
    }
  }, [onTitleChange]);

  const handleEmailNotificationsToggle = () => {
    setEmailNotifications((prev) => !prev);
  };

  const handleSmsNotificationsToggle = () => {
    setSmsNotifications((prev) => !prev);
  };

  const handleDataExportFormatChange = (e) => {
    setDataExportFormat(e.target.value);
  };

  const handleDefaultJobStatusChange = (e) => {
    setDefaultJobStatus(e.target.value);
  };

  const handleAutoArchiveJobsToggle = () => {
    setAutoArchiveJobs((prev) => !prev);
  };

  const handleSaveChanges = () => {
    // In a real application, you would send these settings to a backend API
    // Save settings

    // Show success notification
    notify.success('Settings saved successfully!');
  };

  return (
    <div className="settings-container">
      <h2 className="settings-header">Application Settings</h2>

      <div className="settings-section card">
        <h3>General Settings</h3>
        <div className="setting-item">
          <label>Application Theme</label>
          <div className="theme-settings">
            <ThemeToggle variant="dropdown" showLabels={true} />
            {isSystemTheme && (
              <p className="theme-system-note">
                Currently using system theme preference
              </p>
            )}
          </div>
        </div>
      </div>

      <div className="settings-section card">
        <h3>Notification Preferences</h3>
        <div className="setting-item toggle-item">
          <label>Email Notifications</label>
          <label className="switch">
            <input type="checkbox" checked={emailNotifications} onChange={handleEmailNotificationsToggle} />
            <span className="slider round"></span>
          </label>
        </div>
        <div className="setting-item toggle-item">
          <label>SMS Notifications</label>
          <label className="switch">
            <input type="checkbox" checked={smsNotifications} onChange={handleSmsNotificationsToggle} />
            <span className="slider round"></span>
          </label>
        </div>
      </div>

      <div className="settings-section card">
        <h3>Data Management</h3>
        <div className="setting-item">
          <label htmlFor="data-export-format">Default Data Export Format</label>
          <CustomDropdown
            value={dataExportFormat}
            options={[
              { value: 'csv', label: 'CSV' },
              { value: 'json', label: 'JSON' },
              { value: 'pdf', label: 'PDF' }
            ]}
            onChange={(value) => setDataExportFormat(value)}
            placeholder="Select Format"
          />
        </div>
        <div className="setting-item action-item">
          <button className="settings-button">Export All Data</button>
        </div>
      </div>

      <div className="settings-section card">
        <h3>Job Management Defaults</h3>
        <div className="setting-item">
          <label htmlFor="default-job-status">Default New Job Status</label>
          <CustomDropdown
            value={defaultJobStatus}
            options={[
              { value: 'Open', label: 'Open' },
              { value: 'Closed', label: 'Closed' },
              { value: 'On Hold', label: 'On Hold' }
            ]}
            onChange={(value) => setDefaultJobStatus(value)}
            placeholder="Select Status"
          />
        </div>
        <div className="setting-item toggle-item">
          <label>Auto-archive Closed Jobs (after 30 days)</label>
          <label className="switch">
            <input type="checkbox" checked={autoArchiveJobs} onChange={handleAutoArchiveJobsToggle} />
            <span className="slider round"></span>
          </label>
        </div>
      </div>

      <div className="settings-actions">
        <button className="save-changes-btn" onClick={handleSaveChanges}>
          Save Changes
        </button>
      </div>
    </div>
  );
};

export default Settings;
