// Simple drag and drop system for dashboard widgets
import React, { useState, useRef, useEffect } from 'react';

const useDragAndDrop = (widgets, onMoveWidget) => {
  const [draggedWidget, setDraggedWidget] = useState(null);
  const [dragPreview, setDragPreview] = useState(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleDragStart = (widgetId, e) => {
    e.preventDefault();
    const widget = widgets.find(w => w.id === widgetId);
    if (widget) {
      setDraggedWidget(widget);
      setIsDragging(true);
      setDragPreview(null);
    }
  };

  const handleDragMove = (e) => {
    if (!isDragging || !draggedWidget) return;

    const gridContainer = document.querySelector('.dashboard-grid-container');
    if (!gridContainer) return;

    const gridRect = gridContainer.getBoundingClientRect();
    const relativeX = e.clientX - gridRect.left;
    const relativeY = e.clientY - gridRect.top;

    const colWidth = gridRect.width / 4;
    const rowHeight = 220;

    const newCol = Math.floor(relativeX / colWidth);
    const newRow = Math.floor(relativeY / rowHeight);

    const clampedCol = Math.max(0, Math.min(3, newCol));
    const clampedRow = Math.max(0, newRow);

    setDragPreview({ x: clampedCol, y: clampedRow });

    // Move other widgets to make space
    if (onMoveWidget) {
      onMoveWidget(draggedWidget.id, { x: clampedCol, y: clampedRow }, true);
    }
  };

  const handleDragEnd = () => {
    if (isDragging && draggedWidget && dragPreview) {
      // Final move
      if (onMoveWidget) {
        onMoveWidget(draggedWidget.id, dragPreview, false);
      }
    }
    
    setDraggedWidget(null);
    setDragPreview(null);
    setIsDragging(false);
  };

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleDragMove);
      document.addEventListener('mouseup', handleDragEnd);
      
      return () => {
        document.removeEventListener('mousemove', handleDragMove);
        document.removeEventListener('mouseup', handleDragEnd);
      };
    }
  }, [isDragging, draggedWidget, dragPreview]);

  return {
    draggedWidget,
    dragPreview,
    isDragging,
    handleDragStart
  };
};

export default useDragAndDrop;

