// src/components/dashboard/WidgetLibrary.jsx
import React, { useState } from 'react';
import { FiX, FiBarChart, FiTrendingUp, FiUsers, FiActivity, FiTarget, FiClock, FiPieChart } from 'react-icons/fi';
import './WidgetLibrary.css';

const WidgetLibrary = ({ onAddWidget, onClose, currentRowHeight = null }) => {
  const [selectedCategory, setSelectedCategory] = useState('all');

  const widgetTemplates = [
    // KPI Widgets
    {
      id: 'kpi-template',
      type: 'kpi',
      title: 'KPI Card',
      description: 'Display key performance indicators with trends',
      icon: <FiTarget />,
      category: 'metrics',
      defaultSize: { w: 1, h: 1 },
      config: {
        value: 0,
        change: '+0%',
        trend: 'neutral',
        color: 'primary'
      }
    },
    {
      id: 'metric-card-template',
      type: 'kpi',
      title: 'Metric Card',
      description: 'Simple metric display with comparison',
      icon: <FiBarChart />,
      category: 'metrics',
      defaultSize: { w: 1, h: 1 },
      config: {
        value: 0,
        change: '+0%',
        trend: 'neutral',
        color: 'success'
      }
    },

    // Chart Widgets
    {
      id: 'line-chart-template',
      type: 'chart',
      title: 'Line Chart',
      description: 'Time series data visualization',
      icon: <FiTrendingUp />,
      category: 'charts',
      defaultSize: { w: 2, h: 2 },
      config: {
        chartType: 'line',
        data: [],
        colors: ['#8b5cf6']
      }
    },
    {
      id: 'bar-chart-template',
      type: 'chart',
      title: 'Bar Chart',
      description: 'Comparative data visualization',
      icon: <FiBarChart />,
      category: 'charts',
      defaultSize: { w: 2, h: 2 },
      config: {
        chartType: 'bar',
        data: [],
        colors: ['#8b5cf6', '#10b981', '#f59e0b']
      }
    },
    {
      id: 'doughnut-chart-template',
      type: 'chart',
      title: 'Doughnut Chart',
      description: 'Proportional data visualization',
      icon: <FiPieChart />,
      category: 'charts',
      defaultSize: { w: 2, h: 2 },
      config: {
        chartType: 'doughnut',
        data: [],
        colors: ['#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#06b6d4']
      }
    },

    // Activity Widgets
    {
      id: 'activity-feed-template',
      type: 'activity',
      title: 'Activity Feed',
      description: 'Recent system activities and updates',
      icon: <FiActivity />,
      category: 'activity',
      defaultSize: { w: 2, h: 2 },
      config: {
        limit: 10,
        showTimestamps: true
      }
    },
    {
      id: 'recent-updates-template',
      type: 'activity',
      title: 'Recent Updates',
      description: 'Latest changes and notifications',
      icon: <FiClock />,
      category: 'activity',
      defaultSize: { w: 2, h: 2 },
      config: {
        limit: 5,
        showTimestamps: false
      }
    },

    // Performance Widgets
    {
      id: 'performance-metrics-template',
      type: 'performance',
      title: 'Performance Metrics',
      description: 'Key performance indicators dashboard',
      icon: <FiTarget />,
      category: 'performance',
      defaultSize: { w: 2, h: 2 },
      config: {
        metrics: [
          { name: 'Success Rate', value: '0%', trend: 'neutral' },
          { name: 'Response Time', value: '0s', trend: 'neutral' },
          { name: 'Satisfaction', value: '0/5', trend: 'neutral' }
        ]
      }
    },

    // Trend Analysis Widgets
    {
      id: 'trend-analysis-template',
      type: 'trend',
      title: 'Trend Analysis',
      description: 'Historical data trends and patterns',
      icon: <FiTrendingUp />,
      category: 'analysis',
      defaultSize: { w: 2, h: 2 },
      config: {
        period: '30d',
        metrics: ['candidates', 'interviews', 'jobs']
      }
    },

    // Real-time Widgets
    {
      id: 'realtime-updates-template',
      type: 'realtime',
      title: 'Real-time Updates',
      description: 'Live data updates and notifications',
      icon: <FiClock />,
      category: 'realtime',
      defaultSize: { w: 2, h: 2 },
      config: {
        refreshInterval: 5000,
        showLiveIndicator: true
      }
    }
  ];

  const categories = [
    { id: 'all', name: 'All Widgets', count: widgetTemplates.length },
    { id: 'metrics', name: 'Metrics', count: widgetTemplates.filter(w => w.category === 'metrics').length },
    { id: 'charts', name: 'Charts', count: widgetTemplates.filter(w => w.category === 'charts').length },
    { id: 'activity', name: 'Activity', count: widgetTemplates.filter(w => w.category === 'activity').length },
    { id: 'performance', name: 'Performance', count: widgetTemplates.filter(w => w.category === 'performance').length },
    { id: 'analysis', name: 'Analysis', count: widgetTemplates.filter(w => w.category === 'analysis').length },
    { id: 'realtime', name: 'Real-time', count: widgetTemplates.filter(w => w.category === 'realtime').length }
  ];

  // Filter widgets based on category and current row height
  const getFilteredWidgets = () => {
    let filtered = selectedCategory === 'all' 
      ? widgetTemplates 
      : widgetTemplates.filter(widget => widget.category === selectedCategory);
    
    // If we have a current row height, filter widgets to only show those with matching height
    if (currentRowHeight) {
      filtered = filtered.filter(widget => {
        const widgetHeight = widget.defaultSize?.h || 1;
        return widgetHeight === currentRowHeight;
      });
    }
    
    return filtered;
  };

  const filteredWidgets = getFilteredWidgets();

  const handleAddWidget = (template) => {
    onAddWidget(template);
  };

  return (
    <div className="widget-library-overlay">
      <div className="widget-library">
        <div className="widget-library-header">
          <h2>Widget Library</h2>
          <p>
            {currentRowHeight 
              ? `Choose widgets with height ${currentRowHeight} to match your current row`
              : 'Choose widgets to add to your dashboard'
            }
          </p>
          <button className="close-btn" onClick={onClose}>
            <FiX />
          </button>
        </div>

        <div className="widget-library-content">
          {/* Categories */}
          <div className="widget-categories">
            {categories.map(category => (
              <button
                key={category.id}
                className={`category-btn ${selectedCategory === category.id ? 'active' : ''}`}
                onClick={() => setSelectedCategory(category.id)}
              >
                {category.name}
                <span className="category-count">({category.count})</span>
              </button>
            ))}
          </div>

          {/* Widget Templates */}
          <div className="widget-templates">
            {filteredWidgets.map(template => (
              <div key={template.id} className="widget-template">
                <div className="template-header">
                  <div className="template-icon">
                    {template.icon}
                  </div>
                  <div className="template-info">
                    <h3>{template.title}</h3>
                    <p>{template.description}</p>
                  </div>
                </div>
                
                <div className="template-actions">
                  <button
                    className="add-widget-btn"
                    onClick={() => handleAddWidget(template)}
                  >
                    Add to Dashboard
                  </button>
                </div>
              </div>
            ))}
          </div>

          {filteredWidgets.length === 0 && (
            <div className="no-widgets">
              <p>No widgets found in this category.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default WidgetLibrary;
