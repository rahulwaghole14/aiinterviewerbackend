// src/components/dashboard/WidgetDataSettings.jsx
import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { FiX, FiCheck, FiDatabase, FiBarChart2, FiTrendingUp, FiActivity, FiUsers, FiClock } from 'react-icons/fi';
import './WidgetDataSettings.css';

const WidgetDataSettings = ({ widget, onUpdateWidget, onClose }) => {
  const [selectedData, setSelectedData] = useState(widget.dataSource || 'default');
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    return () => setMounted(false);
  }, []);

  const getDataOptions = (widgetType) => {
    const baseOptions = {
      kpi: [
        { id: 'revenue', label: 'Revenue', icon: <FiTrendingUp />, description: 'Total revenue metrics' },
        { id: 'users', label: 'Active Users', icon: <FiUsers />, description: 'User engagement metrics' },
        { id: 'conversion', label: 'Conversion Rate', icon: <FiBarChart2 />, description: 'Conversion analytics' },
        { id: 'sessions', label: 'Sessions', icon: <FiActivity />, description: 'Session data' },
        { id: 'bounce', label: 'Bounce Rate', icon: <FiTrendingUp />, description: 'Bounce rate metrics' },
        { id: 'retention', label: 'Retention', icon: <FiClock />, description: 'User retention data' }
      ],
      chart: [
        { id: 'revenue', label: 'Revenue Trends', icon: <FiTrendingUp />, description: 'Revenue trend analysis (Line Chart)' },
        { id: 'users', label: 'User Analytics', icon: <FiUsers />, description: 'User behavior patterns (Bar Chart)' },
        { id: 'conversion', label: 'Conversion Funnel', icon: <FiBarChart2 />, description: 'Conversion funnel data (Doughnut Chart)' },
        { id: 'sessions', label: 'Session Analytics', icon: <FiActivity />, description: 'Session data analysis (Bar Chart)' },
        { id: 'bounce', label: 'Bounce Analysis', icon: <FiTrendingUp />, description: 'Bounce rate trends (Line Chart)' },
        { id: 'retention', label: 'Retention Trends', icon: <FiClock />, description: 'Retention analysis (Line Chart)' }
      ],
      activity: [
        { id: 'revenue', label: 'Revenue Activities', icon: <FiTrendingUp />, description: 'Revenue-related activities' },
        { id: 'users', label: 'User Activities', icon: <FiUsers />, description: 'User engagement activities' },
        { id: 'conversion', label: 'Conversion Events', icon: <FiBarChart2 />, description: 'Conversion-related events' },
        { id: 'sessions', label: 'Session Events', icon: <FiActivity />, description: 'Session-related activities' },
        { id: 'bounce', label: 'Bounce Events', icon: <FiTrendingUp />, description: 'Bounce-related activities' },
        { id: 'retention', label: 'Retention Events', icon: <FiClock />, description: 'Retention-related activities' }
      ],
      performance: [
        { id: 'revenue', label: 'Revenue Performance', icon: <FiTrendingUp />, description: 'Revenue performance metrics' },
        { id: 'users', label: 'User Performance', icon: <FiUsers />, description: 'User engagement performance' },
        { id: 'conversion', label: 'Conversion Performance', icon: <FiBarChart2 />, description: 'Conversion performance metrics' },
        { id: 'sessions', label: 'Session Performance', icon: <FiActivity />, description: 'Session performance metrics' },
        { id: 'bounce', label: 'Bounce Performance', icon: <FiTrendingUp />, description: 'Bounce rate performance' },
        { id: 'retention', label: 'Retention Performance', icon: <FiClock />, description: 'Retention performance metrics' }
      ],
      trend: [
        { id: 'revenue', label: 'Revenue Trends', icon: <FiTrendingUp />, description: 'Revenue trend analysis' },
        { id: 'users', label: 'User Trends', icon: <FiUsers />, description: 'User engagement trends' },
        { id: 'conversion', label: 'Conversion Trends', icon: <FiBarChart2 />, description: 'Conversion trend analysis' },
        { id: 'sessions', label: 'Session Trends', icon: <FiActivity />, description: 'Session trend analysis' },
        { id: 'bounce', label: 'Bounce Trends', icon: <FiTrendingUp />, description: 'Bounce rate trends' },
        { id: 'retention', label: 'Retention Trends', icon: <FiClock />, description: 'Retention trend analysis' }
      ],
      realtime: [
        { id: 'revenue', label: 'Live Revenue', icon: <FiTrendingUp />, description: 'Real-time revenue data' },
        { id: 'users', label: 'Live Users', icon: <FiUsers />, description: 'Real-time user data' },
        { id: 'conversion', label: 'Live Conversion', icon: <FiBarChart2 />, description: 'Real-time conversion data' },
        { id: 'sessions', label: 'Live Sessions', icon: <FiActivity />, description: 'Real-time session data' },
        { id: 'bounce', label: 'Live Bounce', icon: <FiTrendingUp />, description: 'Real-time bounce data' },
        { id: 'retention', label: 'Live Retention', icon: <FiClock />, description: 'Real-time retention data' }
      ]
    };

    return baseOptions[widgetType] || baseOptions.kpi;
  };

  const handleDataSelect = (dataId) => {
    setSelectedData(dataId);
  };

  const handleApply = () => {
    if (onUpdateWidget) {
      // Update the widget with new data source and generate complete widget data
      const widgetData = generateDataForSource(selectedData, widget.type);
      
      // Update the entire widget with new title, subtitle, and data
      const updates = {
        dataSource: selectedData,
        title: widgetData.title,
        subtitle: widgetData.subtitle,
        lastUpdated: new Date().toISOString()
      };

      // Add data based on widget type
      if (widget.type === 'kpi') {
        updates.config = widgetData.kpi;
      } else if (widget.type === 'chart') {
        updates.config = {
          ...widget.config,
          chartType: widgetData.chart.chartType,
          data: widgetData.chart.data,
          colors: widgetData.chart.colors
        };
      } else if (widget.type === 'activity') {
        updates.config = {
          ...widget.config,
          ...widgetData.activity
        };
      } else if (widget.type === 'performance') {
        updates.config = {
          ...widget.config,
          ...widgetData.performance
        };
      } else if (widget.type === 'trend') {
        updates.config = {
          ...widget.config,
          ...widgetData.trend
        };
      } else if (widget.type === 'realtime') {
        updates.config = {
          ...widget.config,
          ...widgetData.realtime
        };
      }

      onUpdateWidget(widget.id, updates);
    }
    onClose();
  };

  const generateDataForSource = (dataSource, widgetType) => {
    // Generate complete widget data based on the selected data source and widget type
    const baseData = {
      revenue: {
        title: 'Total Revenue',
        subtitle: 'Monthly revenue',
        data: [
          { name: 'Q1', value: 125000 },
          { name: 'Q2', value: 145000 },
          { name: 'Q3', value: 138000 },
          { name: 'Q4', value: 162000 }
        ],
        kpi: { value: 162000, change: '+12%', trend: 'up', color: 'primary' },
        chartType: 'line',
        colors: ['#8b5cf6']
      },
      users: {
        title: 'Active Users',
        subtitle: 'User engagement',
        data: [
          { name: 'Jan', value: 1200 },
          { name: 'Feb', value: 1350 },
          { name: 'Mar', value: 1280 },
          { name: 'Apr', value: 1420 }
        ],
        kpi: { value: 1420, change: '+8%', trend: 'up', color: 'success' },
        chartType: 'bar',
        colors: ['#10b981']
      },
      conversion: {
        title: 'Conversion Rate',
        subtitle: 'Conversion analytics',
        data: [
          { name: 'Mobile', value: 3.2 },
          { name: 'Desktop', value: 4.8 },
          { name: 'Tablet', value: 2.1 }
        ],
        kpi: { value: 4.8, change: '+15%', trend: 'up', color: 'info' },
        chartType: 'doughnut',
        colors: ['#06b6d4', '#f59e0b', '#ef4444']
      },
      sessions: {
        title: 'Sessions',
        subtitle: 'Session data',
        data: [
          { name: 'Direct', value: 45 },
          { name: 'Search', value: 32 },
          { name: 'Social', value: 18 },
          { name: 'Email', value: 5 }
        ],
        kpi: { value: 45, change: '+5%', trend: 'up', color: 'warning' },
        chartType: 'bar',
        colors: ['#f59e0b']
      },
      bounce: {
        title: 'Bounce Rate',
        subtitle: 'Bounce rate metrics',
        data: [
          { name: 'Homepage', value: 35 },
          { name: 'Product', value: 28 },
          { name: 'Blog', value: 42 },
          { name: 'Contact', value: 15 }
        ],
        kpi: { value: 35, change: '-3%', trend: 'down', color: 'danger' },
        chartType: 'line',
        colors: ['#ef4444']
      },
      retention: {
        title: 'Retention',
        subtitle: 'User retention data',
        data: [
          { name: 'Day 1', value: 85 },
          { name: 'Day 7', value: 65 },
          { name: 'Day 30', value: 45 },
          { name: 'Day 90', value: 25 }
        ],
        kpi: { value: 65, change: '+8%', trend: 'up', color: 'primary' },
        chartType: 'line',
        colors: ['#8b5cf6']
      }
    };

    const selectedData = baseData[dataSource] || baseData.revenue;

    // Return data based on widget type
    if (widgetType === 'kpi') {
      return {
        title: selectedData.title,
        subtitle: selectedData.subtitle,
        kpi: selectedData.kpi
      };
    } else if (widgetType === 'chart') {
      return {
        title: selectedData.title,
        subtitle: selectedData.subtitle,
        chart: {
          chartType: selectedData.chartType,
          data: selectedData.data,
          colors: selectedData.colors
        }
      };
    } else if (widgetType === 'activity') {
      return {
        title: selectedData.title,
        subtitle: selectedData.subtitle,
        activity: {
          limit: 10,
          showTimestamps: true,
          data: selectedData.data.map(item => ({
            id: Math.random().toString(36).substr(2, 9),
            type: 'info',
            message: `${selectedData.title}: ${item.name} - ${item.value}`,
            timestamp: new Date().toISOString(),
            user: 'System'
          }))
        }
      };
    } else if (widgetType === 'performance') {
      return {
        title: selectedData.title,
        subtitle: selectedData.subtitle,
        performance: {
          metrics: [
            { name: `${selectedData.title} Rate`, value: `${selectedData.kpi.value}%`, trend: selectedData.kpi.trend },
            { name: 'Growth Rate', value: selectedData.kpi.change, trend: selectedData.kpi.trend },
            { name: 'Status', value: 'Active', trend: 'up' }
          ]
        }
      };
    } else if (widgetType === 'trend') {
      return {
        title: selectedData.title,
        subtitle: selectedData.subtitle,
        trend: {
          data: selectedData.data,
          chartType: selectedData.chartType,
          colors: selectedData.colors
        }
      };
    } else if (widgetType === 'realtime') {
      return {
        title: selectedData.title,
        subtitle: selectedData.subtitle,
        realtime: {
          data: selectedData.data,
          updateInterval: 5000
        }
      };
    }

    return selectedData;
  };

  const dataOptions = getDataOptions(widget.type);

  const modalContent = (
    <div className="widget-data-settings">
      <div className="settings-header">
        <h3>Data Source Settings</h3>
        <button className="close-btn" onClick={onClose}>
          <FiX />
        </button>
      </div>
      
      <div className="settings-content">
        <div className="current-selection">
          <h4>Current Data Source</h4>
          <div className="current-data">
            <FiDatabase />
            <span>{dataOptions.find(opt => opt.id === selectedData)?.label || 'Default'}</span>
          </div>
        </div>

        <div className="data-options">
          <h4>Available Data Sources</h4>
          <div className="options-grid">
            {dataOptions.map((option) => (
              <div
                key={option.id}
                className={`data-option ${selectedData === option.id ? 'selected' : ''}`}
                onClick={() => handleDataSelect(option.id)}
              >
                <div className="option-icon">
                  {option.icon}
                </div>
                <div className="option-content">
                  <h5>{option.label}</h5>
                  <p>{option.description}</p>
                </div>
                {selectedData === option.id && (
                  <div className="selected-indicator">
                    <FiCheck />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="settings-footer">
        <button className="cancel-btn" onClick={onClose}>
          Cancel
        </button>
        <button className="apply-btn" onClick={handleApply}>
          <FiCheck />
          Apply Changes
        </button>
      </div>
    </div>
  );

  if (!mounted) return null;

  return createPortal(modalContent, document.body);
};

export default WidgetDataSettings;
