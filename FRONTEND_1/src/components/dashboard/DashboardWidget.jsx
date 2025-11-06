// src/components/dashboard/DashboardWidget.jsx
import React, { useState, useRef, useEffect } from 'react';
import { FiMaximize2, FiMinimize2, FiX, FiRefreshCw, FiMove, FiDatabase } from 'react-icons/fi';
import WidgetDataSettings from './WidgetDataSettings';
import './DashboardWidget.css';

const DashboardWidget = ({ 
  widget, 
  index, 
  isEditing = false, 
  onUpdateWidget, 
  onRemoveWidget,
  onRefreshWidget,
  onMoveWidget,
  onSwapWidget,
  lastWidgetPosition,
  onDragStart,
  isDragging,
  children 
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [showDataSettings, setShowDataSettings] = useState(false);
  const widgetRef = useRef(null);

  const handleRefresh = async () => {
    if (onRefreshWidget) {
      setIsRefreshing(true);
      try {
        await onRefreshWidget(widget.id);
      } finally {
        setIsRefreshing(false);
      }
    }
  };

  const handleDataSettings = () => {
    setShowDataSettings(!showDataSettings);
  };

  const handleRemove = () => {
    if (onRemoveWidget) {
      onRemoveWidget(widget.id);
    }
  };


  const handleDragHandleMouseDown = (e) => {
    if (!isEditing) return;
    
    e.preventDefault();
    e.stopPropagation();
    
    // Use the new drag system
    if (onDragStart) {
      onDragStart(widget.id, e);
    }
  };

  // Remove old drag logic - now handled by the new drag system

  // Remove old drag logic - now handled by the new drag system

  const widgetContent = (
    <>
      {/* Data Settings Modal - Render outside widget container */}
      {showDataSettings && isEditing && (
        <>
          <div className="widget-backdrop" onClick={() => setShowDataSettings(false)} />
          <WidgetDataSettings
            widget={widget}
            onUpdateWidget={onUpdateWidget}
            onClose={() => setShowDataSettings(false)}
          />
        </>
      )}
      
      {/* Backdrop for expanded widget - positioned behind the widget */}
      {isExpanded && !showDataSettings && (
        <div className="widget-backdrop" onClick={() => setIsExpanded(false)} />
      )}
      
      <div 
        ref={widgetRef}
        className={`dashboard-widget ${isExpanded ? 'expanded' : ''} ${isEditing ? 'editing' : ''} ${isDragging ? 'dragging' : ''}`}
        style={{
          gridColumn: `${(widget.position?.x || 0) + 1} / span ${widget.size?.w || 1}`,
          gridRow: `${(widget.position?.y || 0) + 1} / span ${widget.size?.h || 1}`,
          ...(isExpanded && {
            position: 'fixed',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: '85vw',
            height: 'auto', // Auto height to fit content
            maxWidth: '1200px',
            maxHeight: '90vh', // Maximum height but can be smaller
            zIndex: 1000,
            gridColumn: 'unset',
            gridRow: 'unset'
          })
        }}
      >
      {/* Widget Header */}
      <div className="widget-header">
        <div className="widget-title">
          <h3>{widget.title}</h3>
          {widget.subtitle && <span className="widget-subtitle">{widget.subtitle}</span>}
        </div>
        
        <div className="widget-controls">
          {onRefreshWidget && (
            <button 
              className="widget-control-btn refresh"
              onClick={handleRefresh}
              disabled={isRefreshing}
              title="Refresh data"
            >
              <FiRefreshCw className={isRefreshing ? 'spinning' : ''} />
            </button>
          )}
          
          <button 
            className="widget-control-btn expand"
            onClick={() => setIsExpanded(!isExpanded)}
            title={isExpanded ? "Minimize" : "Maximize"}
          >
            {isExpanded ? <FiMinimize2 /> : <FiMaximize2 />}
          </button>
          
          {isEditing && (
            <>
              <button 
                className="widget-control-btn data-settings"
                onClick={handleDataSettings}
                title="Data source settings"
              >
                <FiDatabase />
              </button>
              <button 
                className="widget-control-btn remove"
                onClick={handleRemove}
                title="Remove widget"
              >
                <FiX />
              </button>
            </>
          )}
        </div>
      </div>

      {/* Widget Content */}
      <div className={`widget-content ${widget.type === 'chart' ? 'chart-widget' : ''}`}>
        {isRefreshing ? (
          <div className="widget-loading">
            <div className="loading-spinner"></div>
            <p>Refreshing...</p>
          </div>
        ) : (
          children
        )}
      </div>


      </div>
    </>
  );

  return widgetContent;
};

export default DashboardWidget;
