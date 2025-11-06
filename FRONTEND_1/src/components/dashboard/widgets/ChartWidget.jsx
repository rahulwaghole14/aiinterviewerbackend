// src/components/dashboard/widgets/ChartWidget.jsx
import React, { useEffect, useRef, useState } from 'react';
import { Bar, Line, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import './ChartWidget.css';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

const ChartWidget = ({ config }) => {
  const { chartType, data, colors: configColors, title } = config;
  const [isDarkMode, setIsDarkMode] = useState(false);
  const chartRef = useRef(null);

  useEffect(() => {
    const checkTheme = () => {
      const root = document.documentElement;
      const isDark = root.getAttribute('data-theme') === 'dark';
      setIsDarkMode(isDark);
    };

    checkTheme();
    
    const observer = new MutationObserver(checkTheme);
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-theme']
    });

    return () => observer.disconnect();
  }, []);

  const getThemeColors = () => {
    const root = document.documentElement;
    const getCSSVar = (property) => 
      getComputedStyle(root).getPropertyValue(property).trim();

    return {
      textPrimary: getCSSVar('--color-text-primary') || (isDarkMode ? '#ffffff' : '#000000'),
      textSecondary: getCSSVar('--color-text-secondary') || (isDarkMode ? '#cbd5e1' : '#64748b'),
      background: getCSSVar('--color-background-elevated') || (isDarkMode ? '#1e1b2e' : '#ffffff'),
      border: getCSSVar('--color-border-light') || (isDarkMode ? '#4c4066' : '#e2e8f0'),
      primary: getCSSVar('--color-primary') || '#8b5cf6'
    };
  };

  const themeColors = getThemeColors();

  const getChartOptions = () => {
    const baseOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          position: 'bottom',
          labels: {
            color: themeColors.textPrimary,
            font: {
              size: 12,
              weight: 500
            },
            padding: 20,
            usePointStyle: true,
            pointStyle: 'circle'
          }
        },
        tooltip: {
          backgroundColor: themeColors.background,
          titleColor: themeColors.textPrimary,
          bodyColor: themeColors.textSecondary,
          borderColor: themeColors.border,
          borderWidth: 1,
          cornerRadius: 8,
          displayColors: true,
          titleFont: {
            size: 13,
            weight: 600
          },
          bodyFont: {
            size: 12
          }
        }
      },
      scales: chartType !== 'doughnut' ? {
        x: {
          grid: {
            color: themeColors.border,
            drawBorder: false
          },
          ticks: {
            color: themeColors.textSecondary,
            font: {
              size: 11,
              weight: 500
            }
          }
        },
        y: {
          grid: {
            color: themeColors.border,
            drawBorder: false
          },
          ticks: {
            color: themeColors.textSecondary,
            font: {
              size: 11,
              weight: 500
            }
          }
        }
      } : {}
    };

    return baseOptions;
  };

  const getChartData = () => {
    if (!data || data.length === 0) {
      return {
        labels: ['No Data'],
        datasets: [{
          data: [1],
          backgroundColor: [themeColors.border],
          borderColor: [themeColors.border],
          borderWidth: 1
        }]
      };
    }

    const labels = data.map(item => {
      const label = item.name || item.label || item.domain || item.date || 'Unknown';
      return label === 'undefined' || label === null ? 'Unknown' : label;
    });
    const values = data.map(item => {
      const value = item.value || item.count || item.uploads || 0;
      return isNaN(value) ? 0 : value;
    });

    const baseDataset = {
      data: values,
      backgroundColor: configColors || [
        '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#06b6d4',
        '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#06b6d4'
      ],
      borderColor: configColors || [
        '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#06b6d4',
        '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#06b6d4'
      ],
      borderWidth: 2
    };

    switch (chartType) {
      case 'line':
        return {
          labels,
          datasets: [{
            ...baseDataset,
            fill: false,
            tension: 0.4,
            pointBackgroundColor: baseDataset.backgroundColor,
            pointBorderColor: baseDataset.borderColor,
            pointRadius: 4,
            pointHoverRadius: 6
          }]
        };
      
      case 'bar':
        return {
          labels,
          datasets: [{
            ...baseDataset,
            borderRadius: 4,
            borderSkipped: false
          }]
        };
      
      case 'doughnut':
        return {
          labels,
          datasets: [{
            ...baseDataset,
            cutout: '60%',
            hoverOffset: 4
          }]
        };
      
      default:
        return {
          labels,
          datasets: [baseDataset]
        };
    }
  };

  const renderChart = () => {
    const chartData = getChartData();
    const options = getChartOptions();

    switch (chartType) {
      case 'line':
        return <Line ref={chartRef} data={chartData} options={options} />;
      case 'bar':
        return <Bar ref={chartRef} data={chartData} options={options} />;
      case 'doughnut':
        return <Doughnut ref={chartRef} data={chartData} options={options} />;
      default:
        return <Bar ref={chartRef} data={chartData} options={options} />;
    }
  };

  if (!data || data.length === 0) {
    return (
      <div className="chart-widget-no-data">
        <div className="no-data-icon">📊</div>
        <p>No data available</p>
        <small>Data will appear here when available</small>
      </div>
    );
  }

  return (
    <div className="chart-widget">
      <div className="chart-container">
        {renderChart()}
      </div>
    </div>
  );
};

export default ChartWidget;
