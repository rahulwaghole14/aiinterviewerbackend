// src/components/dashboard/widgets/RealTimeUpdates.jsx
import React, { useState, useEffect, useRef } from 'react';
import { FiWifi, FiWifiOff, FiRefreshCw, FiClock, FiActivity } from 'react-icons/fi';
import './RealTimeUpdates.css';

const RealTimeUpdates = ({ config }) => {
  const { refreshInterval = 5000, showLiveIndicator = true, data: configData } = config;
  const [isConnected, setIsConnected] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [updateCount, setUpdateCount] = useState(0);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const intervalRef = useRef(null);

  // Simulate real-time updates
  useEffect(() => {
    const startUpdates = () => {
      intervalRef.current = setInterval(() => {
        setIsRefreshing(true);
        
        // Simulate API call
        setTimeout(() => {
          setLastUpdate(new Date());
          setUpdateCount(prev => prev + 1);
          setIsRefreshing(false);
        }, 1000);
      }, refreshInterval);
    };

    startUpdates();

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [refreshInterval]);

  // Simulate connection status changes
  useEffect(() => {
    const handleOnline = () => setIsConnected(true);
    const handleOffline = () => setIsConnected(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const handleManualRefresh = () => {
    setIsRefreshing(true);
    setTimeout(() => {
      setLastUpdate(new Date());
      setUpdateCount(prev => prev + 1);
      setIsRefreshing(false);
    }, 1000);
  };

  const getTimeAgo = (timestamp) => {
    const now = new Date();
    const diff = now - timestamp;
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(diff / 60000);

    if (seconds < 60) return `${seconds}s ago`;
    if (minutes < 60) return `${minutes}m ago`;
    return timestamp.toLocaleTimeString();
  };

  return (
    <div className="realtime-updates">
      <div className="realtime-header">
        <div className="connection-status">
          <div className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
            {isConnected ? <FiWifi /> : <FiWifiOff />}
          </div>
          <span className="status-text">
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
        
        {showLiveIndicator && (
          <div className="live-indicator">
            <div className="live-dot" />
            <span>LIVE</span>
          </div>
        )}
      </div>

      <div className="update-info">
        <div className="update-stats">
          <div className="stat-item">
            <FiActivity />
            <span>Updates: {updateCount}</span>
          </div>
          <div className="stat-item">
            <FiClock />
            <span>Last: {getTimeAgo(lastUpdate)}</span>
          </div>
        </div>
        
        <button
          className={`refresh-btn ${isRefreshing ? 'refreshing' : ''}`}
          onClick={handleManualRefresh}
          disabled={isRefreshing || !isConnected}
        >
          <FiRefreshCw className={isRefreshing ? 'spinning' : ''} />
          {isRefreshing ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      <div className="realtime-content">
        <div className="update-feed">
          <h4>Recent Updates</h4>
          <div className="update-list">
            {configData ? (
              configData.map((item, index) => (
                <div key={index} className="update-item">
                  <div className="update-time">{getTimeAgo(new Date(item.timestamp || lastUpdate))}</div>
                  <div className="update-message">{item.name}: {item.value}</div>
                </div>
              ))
            ) : (
              <>
                <div className="update-item">
                  <div className="update-time">{getTimeAgo(lastUpdate)}</div>
                  <div className="update-message">Dashboard data refreshed</div>
                </div>
                <div className="update-item">
                  <div className="update-time">{getTimeAgo(new Date(lastUpdate - 30000))}</div>
                  <div className="update-message">New candidate added</div>
                </div>
                <div className="update-item">
                  <div className="update-time">{getTimeAgo(new Date(lastUpdate - 60000))}</div>
                  <div className="update-message">Interview completed</div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {!isConnected && (
        <div className="connection-error">
          <FiWifiOff />
          <p>Connection lost. Attempting to reconnect...</p>
        </div>
      )}
    </div>
  );
};

export default RealTimeUpdates;

