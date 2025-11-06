// src/components/dashboard/widgets/PerformanceMetrics.jsx
import React from 'react';
import { FiTrendingUp, FiTrendingDown, FiMinus, FiTarget, FiClock, FiStar } from 'react-icons/fi';
import './PerformanceMetrics.css';

const PerformanceMetrics = ({ config }) => {
  const { metrics = [] } = config;

  const getTrendIcon = (trend) => {
    switch (trend) {
      case 'up':
        return <FiTrendingUp className="trend-icon up" />;
      case 'down':
        return <FiTrendingDown className="trend-icon down" />;
      default:
        return <FiMinus className="trend-icon neutral" />;
    }
  };

  const getTrendColor = (trend) => {
    switch (trend) {
      case 'up':
        return 'var(--color-success)';
      case 'down':
        return 'var(--color-danger)';
      default:
        return 'var(--color-text-secondary)';
    }
  };

  const getMetricIcon = (name) => {
    const lowerName = name.toLowerCase();
    if (lowerName.includes('success') || lowerName.includes('rate')) {
      return <FiTarget />;
    } else if (lowerName.includes('time') || lowerName.includes('response')) {
      return <FiClock />;
    } else if (lowerName.includes('satisfaction') || lowerName.includes('rating')) {
      return <FiStar />;
    }
    return <FiTarget />;
  };

  if (metrics.length === 0) {
    return (
      <div className="performance-metrics-no-data">
        <div className="no-data-icon">📊</div>
        <p>No performance data</p>
        <small>Performance metrics will appear here</small>
      </div>
    );
  }

  return (
    <div className="performance-metrics">
      <div className="metrics-grid">
        {metrics.map((metric, index) => (
          <div key={index} className="metric-card">
            <div className="metric-header">
              <div className="metric-icon">
                {getMetricIcon(metric.name)}
              </div>
              <div className="metric-trend" style={{ color: getTrendColor(metric.trend) }}>
                {getTrendIcon(metric.trend)}
              </div>
            </div>
            
            <div className="metric-content">
              <div className="metric-value">
                {metric.value}
              </div>
              <div className="metric-name">
                {metric.name}
              </div>
            </div>
            
            <div className="metric-progress">
              <div 
                className="progress-bar"
                style={{ 
                  width: `${Math.min(100, Math.max(0, parseFloat(metric.value) || 0))}%`,
                  backgroundColor: getTrendColor(metric.trend)
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PerformanceMetrics;





