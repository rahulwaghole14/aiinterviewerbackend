// src/components/dashboard/widgets/KPICard.jsx
import React from 'react';
import { FiTrendingUp, FiTrendingDown, FiMinus } from 'react-icons/fi';
import './KPICard.css';

const KPICard = ({ config }) => {
  const { value, change, trend, color = 'primary', subtitle } = config;

  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return <FiTrendingUp className="trend-icon up" />;
      case 'down':
        return <FiTrendingDown className="trend-icon down" />;
      default:
        return <FiMinus className="trend-icon neutral" />;
    }
  };

  const getTrendColor = () => {
    switch (trend) {
      case 'up':
        return 'var(--color-success)';
      case 'down':
        return 'var(--color-danger)';
      default:
        return 'var(--color-text-secondary)';
    }
  };

  const formatValue = (val) => {
    if (typeof val === 'number') {
      if (val >= 1000000) {
        return (val / 1000000).toFixed(1) + 'M';
      } else if (val >= 1000) {
        return (val / 1000).toFixed(1) + 'K';
      }
      return val.toLocaleString();
    }
    return val;
  };

  return (
    <div className={`kpi-card kpi-card--${color}`}>
      <div className="kpi-content">
        <div className="kpi-value">
          {formatValue(value)}
        </div>
        
        {change && (
          <div className="kpi-change" style={{ color: getTrendColor() }}>
            {getTrendIcon()}
            <span>{change}</span>
          </div>
        )}
        
        <div className="kpi-trend-indicator">
          <div 
            className={`trend-bar trend-bar--${trend}`}
            style={{ backgroundColor: getTrendColor() }}
          />
        </div>
      </div>
      
      {subtitle && (
        <div className="kpi-subtitle">
          {subtitle}
        </div>
      )}
    </div>
  );
};

export default KPICard;
