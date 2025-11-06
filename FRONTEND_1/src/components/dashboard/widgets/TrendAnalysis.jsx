// src/components/dashboard/widgets/TrendAnalysis.jsx
import React, { useState, useEffect } from 'react';
import { FiTrendingUp, FiTrendingDown, FiCalendar, FiBarChart } from 'react-icons/fi';
import './TrendAnalysis.css';

const TrendAnalysis = ({ config, data }) => {
  const { period = '30d', metrics = ['candidates', 'interviews', 'jobs'], data: configData, chartType } = config;
  const [selectedMetric, setSelectedMetric] = useState(metrics[0]);
  const [trendData, setTrendData] = useState(null);

  useEffect(() => {
    // Use config data if available (from data source change), otherwise generate data
    if (configData) {
      setTrendData(configData.map(item => ({
        date: item.name,
        value: item.value,
        change: item.value > 50 ? 'up' : 'down',
        changePercent: Math.floor(Math.random() * 20) + 1
      })));
    } else {
      // Simulate trend analysis data
      const generateTrendData = () => {
        const days = period === '7d' ? 7 : period === '30d' ? 30 : 90;
        const data = [];
        
        for (let i = days - 1; i >= 0; i--) {
          const date = new Date();
          date.setDate(date.getDate() - i);
          
          data.push({
            date: date.toISOString().split('T')[0],
            value: Math.floor(Math.random() * 100) + 20,
            change: Math.random() > 0.5 ? 'up' : 'down',
            changePercent: Math.floor(Math.random() * 20) + 1
          });
        }
        
        return data;
      };

      setTrendData(generateTrendData());
    }
  }, [period, selectedMetric, configData]);

  const getTrendIcon = (change) => {
    return change === 'up' ? <FiTrendingUp /> : <FiTrendingDown />;
  };

  const getTrendColor = (change) => {
    return change === 'up' ? 'var(--color-success)' : 'var(--color-danger)';
  };

  const getMetricLabel = (metric) => {
    switch (metric) {
      case 'candidates':
        return 'Candidates';
      case 'interviews':
        return 'Interviews';
      case 'jobs':
        return 'Jobs';
      case 'resumes':
        return 'Resumes';
      default:
        return metric.charAt(0).toUpperCase() + metric.slice(1);
    }
  };

  const getMetricIcon = (metric) => {
    switch (metric) {
      case 'candidates':
        return <FiTrendingUp />;
      case 'interviews':
        return <FiCalendar />;
      case 'jobs':
        return <FiBarChart />;
      default:
        return <FiTrendingUp />;
    }
  };

  if (!trendData) {
    return (
      <div className="trend-analysis-loading">
        <div className="loading-spinner"></div>
        <p>Analyzing trends...</p>
      </div>
    );
  }

  const currentValue = trendData[trendData.length - 1]?.value || 0;
  const previousValue = trendData[trendData.length - 2]?.value || 0;
  const totalChange = currentValue - previousValue;
  const changePercent = previousValue > 0 ? ((totalChange / previousValue) * 100).toFixed(1) : 0;

  return (
    <div className="trend-analysis">
      <div className="trend-header">
        <div className="trend-title">
          <h3>Trend Analysis</h3>
          <p>Last {period}</p>
        </div>
        
        <div className="metric-selector">
          {metrics.map(metric => (
            <button
              key={metric}
              className={`metric-btn ${selectedMetric === metric ? 'active' : ''}`}
              onClick={() => setSelectedMetric(metric)}
            >
              {getMetricIcon(metric)}
              {getMetricLabel(metric)}
            </button>
          ))}
        </div>
      </div>

      <div className="trend-summary">
        <div className="current-value">
          <span className="value">{currentValue}</span>
          <span className="label">{getMetricLabel(selectedMetric)}</span>
        </div>
        
        <div 
          className="trend-change"
          style={{ color: getTrendColor(totalChange >= 0 ? 'up' : 'down') }}
        >
          {getTrendIcon(totalChange >= 0 ? 'up' : 'down')}
          <span>{Math.abs(changePercent)}%</span>
        </div>
      </div>

      <div className="trend-chart">
        <div className="chart-container">
          {trendData.map((point, index) => {
            const height = (point.value / Math.max(...trendData.map(d => d.value))) * 100;
            return (
              <div key={index} className="chart-bar">
                <div 
                  className="bar"
                  style={{ 
                    height: `${height}%`,
                    backgroundColor: point.change === 'up' ? 'var(--color-success)' : 'var(--color-danger)'
                  }}
                />
                <div className="bar-label">
                  {new Date(point.date).getDate()}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="trend-insights">
        <h4>Key Insights</h4>
        <ul>
          <li>
            {totalChange >= 0 ? 'Growth' : 'Decline'} of {Math.abs(changePercent)}% compared to previous period
          </li>
          <li>
            Average daily {getMetricLabel(selectedMetric).toLowerCase()}: {Math.round(trendData.reduce((sum, d) => sum + d.value, 0) / trendData.length)}
          </li>
          <li>
            Peak day: {Math.max(...trendData.map(d => d.value))} {getMetricLabel(selectedMetric).toLowerCase()}
          </li>
        </ul>
      </div>
    </div>
  );
};

export default TrendAnalysis;
