import React, { useState, useEffect, useRef } from 'react';
import { FiEdit2, FiTrash2, FiEye, FiDownload, FiCopy, FiShare2, FiSave } from 'react-icons/fi';
import './ContextMenu.css';

const ContextMenu = ({ 
  visible, 
  x, 
  y, 
  actions = [], 
  onAction, 
  onClose,
  rowData,
  rowIndex 
}) => {
  const contextMenuRef = useRef(null);

  // Close context menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (contextMenuRef.current && !contextMenuRef.current.contains(event.target)) {
        onClose();
      }
    };

    if (visible) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('contextmenu', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('contextmenu', handleClickOutside);
    };
  }, [visible, onClose]);

  // Close context menu on escape key
  useEffect(() => {
    const handleEscape = (event) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    if (visible) {
      document.addEventListener('keydown', handleEscape);
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
    };
  }, [visible, onClose]);

  if (!visible) return null;

  const getActionIcon = (action) => {
    const iconMap = {
      edit: FiEdit2,
      delete: FiTrash2,
      view: FiEye,
      download: FiDownload,
      copy: FiCopy,
      share: FiShare2,
      save: FiSave,
    };
    return iconMap[action] || FiEdit2;
  };

  const getActionLabel = (action) => {
    const labelMap = {
      edit: 'Edit',
      delete: 'Delete',
      view: 'View',
      download: 'Download',
      copy: 'Copy',
      share: 'Share',
      save: 'Save',
    };
    return labelMap[action] || action;
  };

  const handleActionClick = (action) => {
    if (onAction) {
      onAction(action, rowData, rowIndex);
    }
    onClose();
  };

  // Calculate position with boundary checks
  const getPosition = () => {
    const menuWidth = 180;
    const menuHeight = actions.length * 40 + 16;
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    let finalX = x;
    let finalY = y;

    // Adjust horizontal position if menu would go off-screen to the right
    if (x + menuWidth > viewportWidth) {
      finalX = x - menuWidth;
    }

    // Adjust vertical position if menu would go off-screen at the bottom
    if (y + menuHeight > viewportHeight) {
      finalY = y - menuHeight;
    }

    // Ensure menu doesn't go off-screen to the left or top
    finalX = Math.max(10, finalX);
    finalY = Math.max(10, finalY);

    return { left: finalX, top: finalY };
  };

  const position = getPosition();

  return (
    <div
      ref={contextMenuRef}
      className="context-menu"
      style={{
        position: 'fixed',
        left: `${position.left}px`,
        top: `${position.top}px`,
        zIndex: 10000,
      }}
      onClick={(e) => e.stopPropagation()}
    >
      {actions.map((action) => {
        const IconComponent = getActionIcon(action);
        return (
          <div
            key={action}
            className={`context-menu-item ${action}`}
            onClick={() => handleActionClick(action)}
          >
            <IconComponent className="context-menu-icon" size={14} />
            <span>{getActionLabel(action)}</span>
          </div>
        );
      })}
    </div>
  );
};

export default ContextMenu;


