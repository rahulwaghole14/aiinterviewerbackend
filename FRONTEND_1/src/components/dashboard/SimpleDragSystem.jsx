// Simple drag system that prevents overlapping
import React, { useState, useRef, useEffect } from 'react';

const useSimpleDrag = (widgets, onMoveWidget) => {
  const [draggedWidget, setDraggedWidget] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [originalLayout, setOriginalLayout] = useState([]);

  const handleDragStart = (widgetId, e) => {
    e.preventDefault();
    const widget = widgets.find(w => w.id === widgetId);
    if (widget && widgets && widgets.length > 0) {
      setDraggedWidget(widget);
      setIsDragging(true);
      // Store original layout - ensure we have a proper copy
      setOriginalLayout(widgets.map(w => ({ ...w })));
    }
  };

  const handleDragMove = (e) => {
    if (!isDragging || !draggedWidget || !originalLayout || originalLayout.length === 0) return;

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

    // Create a simple layout that maintains all widgets from original layout
    const newLayout = createSimpleLayout(originalLayout, draggedWidget, { x: clampedCol, y: clampedRow });
    onMoveWidget(draggedWidget.id, { x: clampedCol, y: clampedRow }, newLayout, true);
  };

  const handleDragEnd = () => {
    if (isDragging && draggedWidget && originalLayout && originalLayout.length > 0) {
      // Final move using simple layout - just update the position
      const currentPosition = draggedWidget.position || { x: 0, y: 0 };
      const newLayout = createSimpleLayout(originalLayout, draggedWidget, currentPosition);
      onMoveWidget(draggedWidget.id, currentPosition, newLayout, false);
    }
    
    setDraggedWidget(null);
    setIsDragging(false);
    setOriginalLayout([]);
  };

  const canPlaceWidgetAtPosition = (x, y, width, height, existingWidgets) => {
    // Check if the position is within grid bounds
    if (x + width > 4 || y + height > 20) {
      return false;
    }
    
    // Check if any existing widget occupies this space
    for (const widget of existingWidgets) {
      const wX = widget.position?.x || 0;
      const wY = widget.position?.y || 0;
      const wW = widget.size?.w || 1;
      const wH = widget.size?.h || 1;
      
      // Check for overlap
      if (x < wX + wW && x + width > wX && y < wY + wH && y + height > wY) {
        return false;
      }
    }
    
    return true;
  };

  const createSimpleLayout = (originalWidgets, movingWidget, newPosition) => {
    // Ensure we have all widgets and just update the position of the moving one
    if (!originalWidgets || originalWidgets.length === 0) {
      return [];
    }
    
    // Get the size of the moving widget
    const movingWidgetWidth = movingWidget.size?.w || 1;
    const movingWidgetHeight = movingWidget.size?.h || 1;
    
    // Check if the new position can accommodate the moving widget's size
    const canFit = canPlaceWidgetAtPosition(newPosition.x, newPosition.y, movingWidgetWidth, movingWidgetHeight, originalWidgets.filter(w => w.id !== movingWidget.id));
    
    if (!canFit) {
      // Find the next available position that can fit the moving widget
      let foundPosition = null;
      for (let y = 0; y < 20 && !foundPosition; y++) {
        for (let x = 0; x < 4 && !foundPosition; x++) {
          if (canPlaceWidgetAtPosition(x, y, movingWidgetWidth, movingWidgetHeight, originalWidgets.filter(w => w.id !== movingWidget.id))) {
            foundPosition = { x, y };
          }
        }
      }
      
      if (foundPosition) {
        newPosition = foundPosition;
      }
    }
    
    // Get all widgets except the moving one
    const otherWidgets = originalWidgets.filter(w => w.id !== movingWidget.id);
    
    // Sort other widgets by their current position (left to right, top to bottom)
    const sortedWidgets = otherWidgets.sort((a, b) => {
      const aY = a.position?.y || 0;
      const bY = b.position?.y || 0;
      const aX = a.position?.x || 0;
      const bX = b.position?.x || 0;
      
      if (aY !== bY) return aY - bY;
      return aX - bX;
    });

    // Create new layout with proper positioning to avoid overlaps
    const newLayout = [];
    const usedPositions = new Set();
    
    // First, place the moving widget
    newLayout.push({
      ...movingWidget,
      position: newPosition
    });
    
    // Mark positions as used by the moving widget
    for (let dy = 0; dy < movingWidgetHeight; dy++) {
      for (let dx = 0; dx < movingWidgetWidth; dx++) {
        usedPositions.add(`${newPosition.x + dx},${newPosition.y + dy}`);
      }
    }

    // Place other widgets in the next available positions
    sortedWidgets.forEach(widget => {
      const w = widget.size?.w || 1;
      const h = widget.size?.h || 1;
      
      let placed = false;
      for (let y = 0; y < 20 && !placed; y++) {
        for (let x = 0; x < 4 && !placed; x++) {
          if (canPlaceWidgetAtPosition(x, y, w, h, newLayout)) {
            newLayout.push({
              ...widget,
              position: { x, y }
            });
            
            // Mark positions as used
            for (let dy = 0; dy < h; dy++) {
              for (let dx = 0; dx < w; dx++) {
                usedPositions.add(`${x + dx},${y + dy}`);
              }
            }
            placed = true;
          }
        }
      }
    });
    
    return newLayout;
  };

  const createSmartLayout = (originalWidgets, movingWidget, newPosition) => {
    const otherWidgets = originalWidgets.filter(w => w.id !== movingWidget.id);
    
    // Get the size of the moving widget
    const widgetWidth = movingWidget.size?.w || 1;
    const widgetHeight = movingWidget.size?.h || 1;
    
    // Sort other widgets by their current position (left to right, top to bottom)
    const sortedWidgets = otherWidgets.sort((a, b) => {
      const aY = a.position?.y || 0;
      const bY = b.position?.y || 0;
      const aX = a.position?.x || 0;
      const bX = b.position?.x || 0;
      
      if (aY !== bY) return aY - bY;
      return aX - bX;
    });

    // Calculate the target index based on the new position
    const targetIndex = newPosition.y * 4 + newPosition.x;
    
    // Create new layout with insertion behavior
    const newLayout = [];
    let currentIndex = 0;
    let inserted = false;

    // Insert the moving widget at the calculated position
    for (let i = 0; i <= sortedWidgets.length; i++) {
      if (i === targetIndex && !inserted) {
        // Insert the moving widget here
        newLayout.push({
          ...movingWidget,
          position: newPosition
        });
        inserted = true;
      }
      
      if (i < sortedWidgets.length) {
        // Calculate new position for this widget
        const widget = sortedWidgets[i];
        const newY = Math.floor(currentIndex / 4);
        const newX = currentIndex % 4;
        
        newLayout.push({
          ...widget,
          position: { x: newX, y: newY }
        });
        currentIndex++;
      }
    }

    // If we haven't inserted yet, add at the end
    if (!inserted) {
      newLayout.push({
        ...movingWidget,
        position: newPosition
      });
    }

    return newLayout;
  };

  const createNonOverlappingLayout = (originalWidgets, movingWidget, newPosition) => {
    const otherWidgets = originalWidgets.filter(w => w.id !== movingWidget.id);
    
    // Sort other widgets by their current position
    const sortedWidgets = otherWidgets.sort((a, b) => {
      const aY = a.position?.y || 0;
      const bY = b.position?.y || 0;
      const aX = a.position?.x || 0;
      const bX = b.position?.x || 0;
      
      if (aY !== bY) return aY - bY;
      return aX - bX;
    });

    // Get the size of the moving widget
    const widgetWidth = movingWidget.size?.w || 1;
    const widgetHeight = movingWidget.size?.h || 1;
    
    // Check if the new position can accommodate the widget size
    const canFit = checkIfPositionFits(newPosition, widgetWidth, widgetHeight, sortedWidgets);
    
    if (!canFit) {
      // Find the next available position that can fit the widget
      const availablePosition = findAvailablePosition(widgetWidth, widgetHeight, sortedWidgets);
      if (availablePosition) {
        newPosition = availablePosition;
      }
    }

    // Create a grid to track occupied positions
    const grid = Array(20).fill(null).map(() => Array(4).fill(null));
    
    // Mark occupied positions
    sortedWidgets.forEach(widget => {
      const x = widget.position?.x || 0;
      const y = widget.position?.y || 0;
      const w = widget.size?.w || 1;
      const h = widget.size?.h || 1;
      
      for (let dy = 0; dy < h; dy++) {
        for (let dx = 0; dx < w; dx++) {
          if (y + dy < 20 && x + dx < 4) {
            grid[y + dy][x + dx] = widget.id;
          }
        }
      }
    });

    // Place the moving widget
    const newWidgets = [...sortedWidgets];
    newWidgets.push({
      ...movingWidget,
      position: newPosition
    });

    // Recalculate positions for all widgets to avoid overlaps
    const finalWidgets = [];
    const usedPositions = new Set();

    // Sort widgets by their original order
    const allWidgets = [...sortedWidgets, { ...movingWidget, position: newPosition }];
    allWidgets.sort((a, b) => {
      const aY = a.position?.y || 0;
      const bY = b.position?.y || 0;
      const aX = a.position?.x || 0;
      const bX = b.position?.x || 0;
      
      if (aY !== bY) return aY - bY;
      return aX - bX;
    });

    // Place each widget in the first available position
    allWidgets.forEach(widget => {
      const w = widget.size?.w || 1;
      const h = widget.size?.h || 1;
      
      let placed = false;
      for (let y = 0; y < 20 && !placed; y++) {
        for (let x = 0; x < 4 && !placed; x++) {
          if (canPlaceWidget(x, y, w, h, usedPositions)) {
            finalWidgets.push({
              ...widget,
              position: { x, y }
            });
            
            // Mark positions as used
            for (let dy = 0; dy < h; dy++) {
              for (let dx = 0; dx < w; dx++) {
                usedPositions.add(`${x + dx},${y + dy}`);
              }
            }
            placed = true;
          }
        }
      }
    });

    return finalWidgets;
  };

  const checkIfPositionFits = (position, width, height, otherWidgets) => {
    const { x, y } = position;
    
    // Check if the position is within grid bounds
    if (x + width > 4 || y + height > 20) {
      return false;
    }
    
    // Check if any other widget occupies this space
    for (let dy = 0; dy < height; dy++) {
      for (let dx = 0; dx < width; dx++) {
        const checkX = x + dx;
        const checkY = y + dy;
        
        const isOccupied = otherWidgets.some(widget => {
          const widgetX = widget.position?.x || 0;
          const widgetY = widget.position?.y || 0;
          const widgetW = widget.size?.w || 1;
          const widgetH = widget.size?.h || 1;
          
          return checkX >= widgetX && checkX < widgetX + widgetW &&
                 checkY >= widgetY && checkY < widgetY + widgetH;
        });
        
        if (isOccupied) {
          return false;
        }
      }
    }
    
    return true;
  };

  const findAvailablePosition = (width, height, otherWidgets) => {
    for (let y = 0; y < 20; y++) {
      for (let x = 0; x < 4; x++) {
        if (checkIfPositionFits({ x, y }, width, height, otherWidgets)) {
          return { x, y };
        }
      }
    }
    return null;
  };

  const canPlaceWidget = (x, y, width, height, usedPositions) => {
    // Check if the position is within grid bounds
    if (x + width > 4 || y + height > 20) {
      return false;
    }
    
    // Check if any position is already used
    for (let dy = 0; dy < height; dy++) {
      for (let dx = 0; dx < width; dx++) {
        if (usedPositions.has(`${x + dx},${y + dy}`)) {
          return false;
        }
      }
    }
    
    return true;
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
  }, [isDragging, draggedWidget, originalLayout]);

  return {
    draggedWidget,
    isDragging,
    handleDragStart
  };
};

export default useSimpleDrag;
