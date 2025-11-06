import React, {
    useState,
    useEffect,
    useRef,
    useCallback,
    useMemo,
  } from "react";
  import {
    FiMoreVertical,
    FiEdit2,
    FiTrash2,
    FiEye,
    FiDownload,
    FiCopy,
    FiShare2,
    FiSave,
    FiX,
    FiKey,
    FiArrowUp,
    FiArrowDown,
    FiChevronUp,
    FiChevronDown,
  } from "react-icons/fi";
import LoadingSpinner from "./LoadingSpinner";
import TimePicker12 from "./TimePicker12";
import { ConfirmModal } from "./Modal";
import { SkeletonTable } from "./SkeletonLoader";
import "./DataTable.css";
import PropTypes from "prop-types";
  
  /**
   * DataTable Component
   *
   * @param {Object} props - Component props
   * @param {string} props.title - Table title
   * @param {Array} props.columns - Array of column configurations
   * @param {Array} props.data - Array of row data objects
   * @param {boolean} [props.loading=false] - Loading state
   * @param {Function} [props.onRefresh] - Refresh callback
   * @param {Function} [props.onRowClick] - Row click handler
   * @param {Array} [props.actions=[]] - Array of action names (view, edit, delete, etc.)
   * @param {Function} [props.onAction] - Action handler function (receives action name, row data, and row index)
   * @param {boolean} [props.showRefresh=true] - Show refresh button
   * @param {boolean} [props.showActions=true] - Show actions column
   * @param {string} [props.className=''] - Additional CSS classes
   * @param {Array} [props.pageSizeOptions=[10, 20, 50, 100]] - Page size options
   * @param {number} [props.defaultPageSize=10] - Default page size
   * @param {Object} [props.actionIcons] - Custom action icons
   * @param {Object} [props.actionLabels] - Custom action labels
   * @param {boolean} [props.enableRowSelection=false] - Enable row selection
   * @param {Function} [props.onSelectionChange] - Callback when row selection changes
   * @param {Function} [props.onEdit] - Edit callback
   * @param {Function} [props.onDelete] - Delete callback
   */
  // Helper function to get nested values from object path
  const getNestedValue = (obj, path) => {
    if (!path || !obj) return "";
    try {
      const result = path
        .split(".")
        .reduce((o, p) => (o && o[p] !== undefined ? o[p] : ""), obj);
      // Ensure we return a primitive value
      if (result === null || result === undefined) return "";
      if (typeof result === "object") {
        // Handle objects safely
        if (Array.isArray(result)) return result.join(", ");
        return JSON.stringify(result);
      }
      return result;
    } catch (error) {
      console.warn("Error getting nested value:", error);
      return "";
    }
  };
  
  const DataTable = ({
    title,
    columns = [],
    data = [],
    loading = false,
    onRefresh,
    onRowClick,
    actions = [],
    onAction,
    onContextMenuClick,
    showRefresh = true,
    showActions = true,
    className = "",
    pageSizeOptions = [10, 20, 50, 100],
    defaultPageSize = 10,
    actionIcons = {
      view: <FiEye />,
      edit: <FiEdit2 />,
      delete: <FiTrash2 />,
      download: <FiDownload />,
      copy: <FiCopy />,
      share: <FiShare2 />,
      save: <FiSave />,
      cancel: <FiX />,
      reset_password: <FiKey />,
    },
    actionLabels = {
      view: "View",
      edit: "Edit",
      delete: "Delete",
      download: "Download",
      copy: "Copy",
      share: "Share",
      save: "Save",
      cancel: "Cancel",
      reset_password: "Reset Password",
    },
    enableRowSelection = false,
    onSelectionChange,
    onEdit,
    onDelete,
    editingRow: externalEditingRow,
    editingData: externalEditingData,
    setEditingRow: externalSetEditingRow,
    setEditingData: externalSetEditingData,
  }) => {
    
    // Sort configuration state
    const [sortConfig, setSortConfig] = useState({
      field: null,
      direction: null, // 'asc', 'desc', or null
    });
    
    // Process data for the table
    const processedData = useMemo(() => {
      if (!data || !Array.isArray(data)) {
        return [];
      }
  
      // Ensure all data items are plain objects
      let processedItems = data.map((item, index) => {
        if (!item || typeof item !== "object") {
          return {};
        }
        return item;
      });
  
      // Apply sorting if configured
      if (sortConfig.field && sortConfig.direction) {
        processedItems = [...processedItems].sort((a, b) => {
          const aValue = getNestedValue(a, sortConfig.field);
          const bValue = getNestedValue(b, sortConfig.field);
          
          // Handle null/undefined values
          if (aValue === null || aValue === undefined) return 1;
          if (bValue === null || bValue === undefined) return -1;
          
          // Convert to strings for comparison if needed
          const aStr = (aValue === null || aValue === undefined) ? "" : String(aValue).toLowerCase();
          const bStr = (bValue === null || bValue === undefined) ? "" : String(bValue).toLowerCase();
          
          // Numeric comparison if both are numbers
          const aNum = Number(aValue);
          const bNum = Number(bValue);
          if (!isNaN(aNum) && !isNaN(bNum)) {
            return sortConfig.direction === 'asc' ? aNum - bNum : bNum - aNum;
          }
          
          // String comparison
          if (aStr < bStr) return sortConfig.direction === 'asc' ? -1 : 1;
          if (aStr > bStr) return sortConfig.direction === 'asc' ? 1 : -1;
          return 0;
        });
      }
  
      return processedItems;
    }, [data, sortConfig]);
  
    // Process columns and data for the table
    const processedColumns = useMemo(() => {
      return columns.map((column) => {
        const cellRenderer =
          column.Cell ||
          (({ value }) => {
            if (value === null || value === undefined) return "";
            if (typeof value === "object") {
              try {
                return JSON.stringify(value);
              } catch (error) {
                return "[Object]";
              }
            }
            try {
              return String(value);
            } catch (error) {
              return "";
            }
          });
  
        return {
          ...column,
          Cell: cellRenderer,
        };
      });
    }, [columns]);
  
    // State management
    const [currentPage, setCurrentPage] = useState(1);
    const [pageSize, setPageSize] = useState(defaultPageSize);
    const [totalPages, setTotalPages] = useState(0);
    const [displayedData, setDisplayedData] = useState([]);
    const [activeMenu, setActiveMenu] = useState(null);
    const [internalEditingRow, setInternalEditingRow] = useState(null);
    const [internalEditingData, setInternalEditingData] = useState({});
  
    // Use external editing state if provided, otherwise use internal state
    const editingRow =
      externalEditingRow !== undefined ? externalEditingRow : internalEditingRow;
    const editingData = externalEditingData || internalEditingData;
    const setEditingRow = externalSetEditingRow || setInternalEditingRow;
    const setEditingData = externalSetEditingData || setInternalEditingData;
  
    const [selectedRows, setSelectedRows] = useState([]);
    const [dtDeleteConfirm, setDtDeleteConfirm] = useState({
      isOpen: false,
      row: null,
      rowIndex: null,
    });
    // Context menu state removed - using common ContextMenu component instead
  
    const menuRef = useRef(null);
    const tableRef = useRef(null);
  
    // Calculate pagination
    useEffect(() => {
      if (!processedData) return;
  
      const total = Math.ceil(processedData.length / pageSize);
      setTotalPages(total || 1);
  
      if (currentPage > total && total > 0) {
        setCurrentPage(1);
      }
  
      const startIndex = (currentPage - 1) * pageSize;
      const endIndex = startIndex + pageSize;
      setDisplayedData(processedData.slice(startIndex, endIndex));
    }, [processedData, currentPage, pageSize]);
  
    // Sort handler function
    const handleSort = useCallback((field) => {
      if (!field || field === 'actions') return; // Don't sort actions column
      
      setSortConfig(prevConfig => {
        if (prevConfig.field === field) {
          // Same field - cycle through asc -> desc -> none
          if (prevConfig.direction === 'asc') {
            return { field, direction: 'desc' };
          } else if (prevConfig.direction === 'desc') {
            return { field: null, direction: null };
          } else {
            return { field, direction: 'asc' };
          }
        } else {
          // Different field - start with asc
          return { field, direction: 'asc' };
        }
      });
    }, []);

    // Get sort icon for column
    const getSortIcon = useCallback((field) => {
      if (!field || field === 'actions') return <FiChevronUp className="sort-icon" />;
      
      if (sortConfig.field === field) {
        if (sortConfig.direction === 'asc') {
          return <FiArrowUp className="sort-icon active" />;
        } else if (sortConfig.direction === 'desc') {
          return <FiArrowDown className="sort-icon active" />;
        }
      }
      return <FiChevronUp className="sort-icon" />;
    }, [sortConfig]);

    // Enhanced menu and context menu handling
    useEffect(() => {
      const handleClickOutside = (event) => {
        if (menuRef.current && !menuRef.current.contains(event.target)) {
          setActiveMenu(null);
        }
      };
  
      const handleEscape = (e) => {
        if (e.key === "Escape") {
          setActiveMenu(null);
        }
      };
  
      const handleScroll = () => {
        setActiveMenu(null);
      };
  
      document.addEventListener("mousedown", handleClickOutside);
      document.addEventListener("keydown", handleEscape);
      document.addEventListener("scroll", handleScroll, true);
  
      return () => {
        document.removeEventListener("mousedown", handleClickOutside);
        document.removeEventListener("keydown", handleEscape);
        document.removeEventListener("scroll", handleScroll, true);
      };
    }, []);
  
    useEffect(() => {
      const handleClickOutside = (event) => {
      };
  
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);
  
    const handlePageChange = (page) => {
      if (page < 1 || page > totalPages) return;
      setCurrentPage(page);
    };
  
    const handlePageSizeChange = (e) => {
      const newSize = Number(e.target.value);
      setPageSize(newSize);
      setCurrentPage(1);
    };
  
    const handleContextMenu = (event, rowIndex, rowData) => {
      event.preventDefault();
      event.stopPropagation();
      
      // Call the parent's context menu handler if provided
      if (onContextMenuClick) {
        onContextMenuClick(event, rowData, rowIndex);
      }
    };
  
    const handleActionButtonClick = (e, rowIndex, row) => {
      e.preventDefault();
      e.stopPropagation();
  
      if (!actions.length) return;
  
      const button = e.currentTarget;
      const rect = tableRef.current.getBoundingClientRect();
      const buttonRect = button.getBoundingClientRect();
      const menuWidth = 180;
      const menuHeight = actions.length * 40 + 16;
  
      // Position menu relative to the button
      let x = buttonRect.left - rect.left - menuWidth + buttonRect.width;
      let y = buttonRect.top - rect.top + buttonRect.height + 4;
  
      // Adjust position if menu would go outside table bounds
      if (x < 0) {
        x = buttonRect.left - rect.left;
      }
      if (x + menuWidth > rect.width) {
        x = rect.width - menuWidth - 10;
      }
      if (y + menuHeight > rect.height) {
        y = buttonRect.top - rect.top - menuHeight - 4;
      }
  
      // Ensure menu doesn't go off-screen to the left or top
      x = Math.max(0, x);
      y = Math.max(0, y);
  
      setActiveMenu({ rowIndex, row, menuPosition: { x, y } });
    };
  
    const handleEditClick = useCallback(
      (rowData, rowIndex) => {
        try {
          if (!rowData) {
            return false;
          }
  
          // Create a deep copy of the row data
          let initialData = JSON.parse(JSON.stringify(rowData));
  
          // Process nested fields from columns configuration
          processedColumns.forEach((column) => {
            if (column.field && column.field.includes(".")) {
              const [parent, child] = column.field.split(".");
              if (parent && child && initialData[parent]?.[child] !== undefined) {
                // Set the flattened field for editing
                initialData[column.field] = initialData[parent][child];
              } else if (initialData[column.field] === undefined) {
                // Initialize with empty value if not set
                initialData[column.field] = "";
              }
            }
          });
  
          setEditingRow(rowIndex);
          setEditingData(initialData);
  
          // Only call onAction for edit start, not onEdit (onEdit is for saving)
          if (onAction) {
            onAction("edit", initialData, rowIndex);
          }
        } catch (error) {
          // Handle edit error silently
        }
      },
      [processedColumns, onAction, onEdit]
    );
  
    const handleSaveClick = useCallback(async () => {
      if (editingRow === null) return;
  
      try {
        // Call the onEdit prop if provided, otherwise use onAction
        if (onEdit) {
          await onEdit(editingData);
        } else if (onAction) {
          await onAction("save", editingData, editingRow);
        }
  
        // Reset editing state
        setEditingRow(null);
        setEditingData({});
      } catch (error) {
        // Handle save error silently
      }
    }, [editingRow, editingData, onAction, onEdit]);
  
    const handleCancelEdit = useCallback(() => {
      setEditingRow(null);
      setEditingData({});
    }, []);
  
    const handleInputChange = (field, value) => {
      setEditingData((prev) => {
        // Create a new object to avoid mutating the previous state
        const newData = { ...prev };
  
        // Handle nested fields (e.g., 'ai_configuration.difficulty_level')
        if (field.includes(".")) {
          const [parent, ...rest] = field.split(".");
          const lastKey = rest.pop();
  
          // Initialize parent if it doesn't exist
          if (!newData[parent]) {
            newData[parent] = {};
          }
  
          // Create nested structure if it doesn't exist
          let current = newData[parent];
          for (const key of rest) {
            if (!current[key]) {
              current[key] = {};
            }
            current = current[key];
          }
  
          // Set the nested value
          current[lastKey] = value;
  
          // Also set the flat version for direct access
          newData[field] = value;
        } else {
          // Handle top-level fields
          newData[field] = value;
        }
  
        return newData;
      });
    };
  
    const getActionIcon = (action) => {
      const iconMap = {
        view: actionIcons?.view || <FiEye />,
        edit: actionIcons?.edit || <FiEdit2 />,
        delete: actionIcons?.delete || <FiTrash2 />,
        download: actionIcons?.download || <FiDownload />,
        copy: actionIcons?.copy || <FiCopy />,
        share: actionIcons?.share || <FiShare2 />,
        save: actionIcons?.save || <FiSave />,
        cancel: actionIcons?.cancel || <FiX />,
      };
      return iconMap[action] || null;
    };
  
    const getActionLabel = (action) => {
      if (actionLabels && actionLabels[action]) {
        return actionLabels[action];
      }
      return action.charAt(0).toUpperCase() + action.slice(1);
    };
  
    const handleActionClick = (action, rowData, rowIndex, e) => {
      e?.stopPropagation();
      setActiveMenu(null);
      onAction?.(action, rowData, rowIndex);
    };
  
    const handleDeleteConfirm = async () => {
      if (onAction && dtDeleteConfirm.row) {
        try {
          await onAction("delete", dtDeleteConfirm.row, dtDeleteConfirm.rowIndex);
          // Only close the modal if the delete was successful
          setDtDeleteConfirm({ isOpen: false, row: null, rowIndex: null });
        } catch (error) {
          // Keep the modal open if there was an error
        }
      } else {
        setDtDeleteConfirm({ isOpen: false, row: null, rowIndex: null });
      }
    };
  
    const handleDeleteCancel = () => {
      setDtDeleteConfirm({ isOpen: false, row: null, rowIndex: null });
    };
  
    // Alias for backward compatibility
    const handleDtConfirmDelete = handleDeleteConfirm;
    const handleDtCancelDelete = handleDeleteCancel;
  
    // Context menu click handler removed - using common ContextMenu component instead
  
    // Context menu action click handler removed - using common ContextMenu component instead
  
    const renderPageNumbers = () => {
      const pageNumbers = [];
      const maxPagesToShow = 5;
      let startPage = 1;
      let endPage = totalPages;
  
      if (totalPages > maxPagesToShow) {
        const maxPagesBeforeCurrent = Math.floor(maxPagesToShow / 2);
        const maxPagesAfterCurrent = Math.ceil(maxPagesToShow / 2) - 1;
  
        if (currentPage <= maxPagesBeforeCurrent) {
          endPage = maxPagesToShow;
        } else if (currentPage + maxPagesAfterCurrent >= totalPages) {
          startPage = totalPages - maxPagesToShow + 1;
        } else {
          startPage = currentPage - maxPagesBeforeCurrent;
          endPage = currentPage + maxPagesAfterCurrent;
        }
      }
  
      for (let i = startPage; i <= endPage; i++) {
        pageNumbers.push(
          <button
            key={i}
            onClick={() => handlePageChange(i)}
            className={`pagination-button ${currentPage === i ? "active" : ""}`}
            disabled={loading}
          >
            {i}
          </button>
        );
      }
  
      return pageNumbers;
    };
  
    const renderActionMenu = (rowData, rowIndex) => {
      if (!showActions || actions.length === 0) return null;
  
      return (
        <div className="action-menu-container" ref={menuRef}>
          <button
            className="action-menu-button"
            onClick={(e) => {
              e.stopPropagation();
              setActiveMenu(activeMenu === rowIndex ? null : rowIndex);
 // Close context menu if open
            }}
            onContextMenu={(e) => {
              e.preventDefault();
              setActiveMenu(activeMenu === rowIndex ? null : rowIndex);
            }}
            aria-label="Actions"
            aria-haspopup="true"
            aria-expanded={activeMenu === rowIndex}
          >
            <FiMoreVertical />
          </button>
  
          {activeMenu === rowIndex && (
            <div
              className="action-menu"
              role="menu"
              aria-orientation="vertical"
              aria-labelledby={`action-button-${rowIndex}`}
            >
              {actions.map((action) => {
                const Icon = actionIcons[action]?.type || FiMoreVertical;
                return (
                  <button
                    key={action}
                    className={`action-menu-item ${action}`}
                    onClick={(e) =>
                      handleActionClick(action, rowData, rowIndex, e)
                    }
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        handleActionClick(action, rowData, rowIndex, e);
                      } else if (e.key === "Escape") {
                        e.stopPropagation();
                        setActiveMenu(null);
                      }
                    }}
                    role="menuitem"
                    tabIndex="0"
                  >
                    <span className="action-icon">{actionIcons[action]}</span>
                    <span className="action-label">
                      {actionLabels[action] || action}
                    </span>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      );
    };
  
    const renderActionsCell = (rowData, rowIndex) => {
      return (
        <div className="actions-cell">{renderActionMenu(rowData, rowIndex)}</div>
      );
    };
  
    // Context menu render function removed - using common ContextMenu component instead
  
    // Generate table columns from data if not provided
    const tableColumns = useMemo(() => {
      let cols = [];
  
      if (processedColumns && processedColumns.length > 0) {
        cols = [...processedColumns];
      } else if (processedData && processedData.length > 0) {
        cols = Object.keys(processedData[0])
          .filter((key) => key !== "id" && key !== "_id")
          .map((key) => ({
            field: key,
            header:
              key.charAt(0).toUpperCase() +
              key
                .slice(1)
                .replace(/([A-Z])/g, " $1")
                .trim(),
            width: "auto",
            // Add default renderer for status fields
            ...(key.toLowerCase().includes("status")
              ? {
                  render: (value) => (
                    <div
                      className="status-cell"
                      data-status={value?.toLowerCase?.() || ""}
                    >
                      {value || ""}
                    </div>
                  ),
                }
              : {}),
          }));
      }
  
      // Add actions column if needed
      if (showActions) {
        cols.push({
          field: "actions",
          header: "Actions",
          width: "100px",
          render: (_, rowData, rowIndex) => renderActionsCell(rowData, rowIndex),
        });
      }
  
      return cols;
    }, [columns, data, showActions]);
  
    const handleRowClick = useCallback(
      (rowData, e) => {
        // Prevent event propagation to avoid multiple clicks
        e.stopPropagation();
  
        // Only trigger onRowClick if the click wasn't on an action button
        const isActionButton =
          e.target.closest(".action-btn") ||
          e.target.closest("button") ||
          e.target.closest("a");
  
        if (!isActionButton && onRowClick) {
          onRowClick(rowData);
        }
      },
      [onRowClick]
    );
  
    const renderTableRow = (rowData, rowIndex) => {
      const isEditing = editingRow === rowIndex;
      const rowKey = `row-${rowIndex}`;
  
      return (
        <tr
          key={rowKey}
          className={`table-row fade-in ${onRowClick ? "clickable" : ""} ${
            selectedRows.some((r) => r.id === rowData.id) ? "selected" : ""
          } ${isEditing ? "editing" : ""}`}
          // Context menu removed - using common ContextMenu component instead
        >
          {enableRowSelection && (
            <td className="selection-cell">
              <input
                type="checkbox"
                checked={selectedRows.some((r) => r.id === rowData.id)}
                onChange={(e) => {
                  e.stopPropagation();
                  handleRowSelection(rowData, e.target.checked);
                }}
              />
            </td>
          )}
  
          {tableColumns.map((column, colIndex) => {
            if (column.field === "actions" && showActions) {
              const actionsKey = `actions-${rowIndex}`;
              return (
                <td key={actionsKey} className="actions-column">
                  {isEditing ? (
                    <div className="actions-cell">
                      <button
                        key={`save-${rowIndex}`}
                        className="action-button save"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleSaveClick();
                        }}
                        title="Save"
                      >
                        <FiSave />
                      </button>
                      <button
                        key={`cancel-${rowIndex}`}
                        className="action-button cancel"
                        onClick={handleCancelEdit}
                        title="Cancel"
                      >
                        <FiX />
                      </button>
                    </div>
                  ) : (
                    <div className="actions-cell">
                      <button
                        key={`menu-${rowIndex}`}
                        className="action-menu-button"
                        onClick={(e) => {
                          e.stopPropagation();
                          if (onContextMenuClick) {
                            onContextMenuClick(e, rowData, rowIndex);
                          }
                        }}
                        aria-label="Actions"
                      >
                        <FiMoreVertical size={14} />
                      </button>
                    </div>
                  )}
                </td>
              );
            }
  
            // Skip rendering if it's the actions column but showActions is false
            if (column.field === "actions" && !showActions) {
              return null;
            }
  
            return (
              <td
                key={column.key || column.field || colIndex}
                className={`${column.className || ""} ${
                  isEditing ? "editing" : ""
                }`}
                style={{
                  ...(column.width && { width: column.width }),
                  ...(column.align && { textAlign: column.align }),
                  ...(column.style || {}),
                }}
              >
                {isEditing &&
                column.editable !== false &&
                editingRow === rowIndex &&
                column.field &&
                column.field !== "actions" ? (
                  column.type === "checkbox" ? (
                    <div className="checkbox-wrapper">
                      <input
                        type="checkbox"
                        checked={Boolean(
                          getNestedValue(editingData, column.field)
                        )}
                        onChange={(e) =>
                          handleInputChange(column.field, e.target.checked)
                        }
                        className="edit-input"
                        onClick={(e) => e.stopPropagation()}
                      />
                    </div>
                  ) : column.type === "select" && column.options ? (
                    <select
                      value={
                        column.formatForEdit
                          ? column.formatForEdit(getNestedValue(editingData, column.field), editingData)
                          : getNestedValue(editingData, column.field) || ""
                      }
                      onChange={(e) => {
                        const value = column.parseFromEdit
                          ? column.parseFromEdit(e.target.value, editingData)
                          : e.target.value;
                        handleInputChange(column.field, value);
                      }}
                      className="edit-input"
                      style={{ width: "100%" }}
                      onClick={(e) => e.stopPropagation()}
                    >
                      {column.placeholder && (
                        <option value="">{column.placeholder}</option>
                      )}
                      {column.options.map((option) => (
                        <option
                          key={option.value}
                          value={option.value}
                          disabled={option.disabled}
                        >
                          {option.label || option.value}
                        </option>
                      ))}
                    </select>
                  ) : column.type === "date" ? (
                    <input
                      type="date"
                      value={
                        column.formatForEdit
                          ? column.formatForEdit(getNestedValue(editingData, column.field), editingData)
                          : getNestedValue(editingData, column.field) || ""
                      }
                      onChange={(e) => {
                        const value = column.parseFromEdit
                          ? column.parseFromEdit(e.target.value, editingData)
                          : e.target.value;
                        handleInputChange(column.field, value);
                      }}
                      className="edit-input"
                      style={{ width: "100%" }}
                      onClick={(e) => e.stopPropagation()}
                    />
                  ) : column.type === "time" ? (
                    <input
                      type="time"
                      value={
                        column.formatForEdit
                          ? column.formatForEdit(getNestedValue(editingData, column.field), editingData)
                          : getNestedValue(editingData, column.field) || ""
                      }
                      onChange={(e) => {
                        const value = column.parseFromEdit
                          ? column.parseFromEdit(e.target.value, editingData)
                          : e.target.value;
                        handleInputChange(column.field, value);
                      }}
                      className="edit-input"
                      style={{ width: "100%" }}
                      onClick={(e) => e.stopPropagation()}
                    />
                  ) : column.type === "time12" ? (
                    <TimePicker12
                      value={
                        column.formatForEdit
                          ? column.formatForEdit(getNestedValue(editingData, column.field), editingData)
                          : getNestedValue(editingData, column.field) || ""
                      }
                      onChange={(timeValue) => {
                        const value = column.parseFromEdit
                          ? column.parseFromEdit(timeValue, editingData)
                          : timeValue;
                        handleInputChange(column.field, value);
                      }}
                      placeholder="Select time"
                    />
                  ) : column.type === "number" ? (
                    <input
                      type="number"
                      value={getNestedValue(editingData, column.field) || ""}
                      onChange={(e) =>
                        handleInputChange(column.field, parseInt(e.target.value) || 0)
                      }
                      className="edit-input"
                      style={{ width: "100%" }}
                      onClick={(e) => e.stopPropagation()}
                      min={column.min || 1}
                      max={column.max || 100}
                    />
                  ) : column.type === "time-range" ? (
                    <input
                      type="text"
                      value={getNestedValue(editingData, column.field) || ""}
                      onChange={(e) => {
                        // Allow only time range format like "9:00 AM - 10:00 AM"
                        const value = e.target.value;
                        if (
                          /^\s*\d{1,2}:?\d{0,2}\s*[AP]?M?\s*-?\s*\d{0,2}:?\d{0,2}\s*[AP]?M?\s*$/.test(
                            value
                          ) ||
                          value === ""
                        ) {
                          handleInputChange(column.field, value);
                        }
                      }}
                      className="edit-input"
                      style={{ width: "100%" }}
                      onClick={(e) => e.stopPropagation()}
                      placeholder="e.g., 9:00 AM - 10:00 AM"
                    />
                  ) : column.readOnly ? (
                    <div className="read-only-cell">
                      {getNestedValue(editingData, column.field) || ""}
                    </div>
                  ) : (
                    <input
                      type={column.type || "text"}
                      value={getNestedValue(editingData, column.field) || ""}
                      onChange={(e) =>
                        handleInputChange(column.field, e.target.value)
                      }
                      className="edit-input"
                      style={{ width: "100%" }}
                      onClick={(e) => e.stopPropagation()}
                      step={
                        column.type === "number"
                          ? column.step || "any"
                          : undefined
                      }
                      min={column.min}
                      max={column.max}
                      placeholder={
                        column.placeholder ||
                        `Enter ${column.header || column.field}`
                      }
                      disabled={column.disabled}
                    />
                  )
                ) : column.render ? (
                  column.render(
                    getNestedValue(rowData, column.field),
                    rowData,
                    rowIndex
                  )
                ) : (
                  <div
                    className={`cell-content ${
                      column.field?.toLowerCase()?.includes("status")
                        ? "status-cell"
                        : ""
                    }`}
                    data-status={
                      column.field?.toLowerCase()?.includes("status")
                        ? (() => {
                            try {
                              const value = getNestedValue(rowData, column.field) || "";
                              return String(value).toLowerCase();
                            } catch (error) {
                              return "";
                            }
                          })()
                        : undefined
                    }
                  >
                    {column.format
                      ? column.format(
                          getNestedValue(rowData, column.field),
                          rowData
                        )
                      : (() => {
                          try {
                            const value = getNestedValue(rowData, column.field);
                            return value !== undefined && value !== null
                              ? String(value)
                              : "";
                          } catch (error) {
                            return "";
                          }
                        })()}
                  </div>
                )}
              </td>
            );
          })}
        </tr>
      );
    };
  
    const renderTableBody = () => {
      if (loading) {
        return null; // Skeleton will be rendered outside the table
      }
  
      if (!displayedData.length) {
        return (
          <tr>
            <td
              colSpan={tableColumns.length + (enableRowSelection ? 1 : 0)}
              className="no-data"
            >
              No data available
            </td>
          </tr>
        );
      }
  
      return displayedData.map((row, index) => renderTableRow(row, index));
    };
  
    const DeleteConfirmationModal = ({
      isOpen,
      onConfirm,
      onCancel,
      itemName = "this item",
    }) => {
      if (!isOpen) return null;
  
      return (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3>Confirm Delete</h3>
            <p>
              Are you sure you want to delete {itemName}? This action cannot be
              undone.
            </p>
            <div className="modal-actions">
              <button onClick={onCancel} className="btn btn-secondary">
                Cancel
              </button>
              <button onClick={onConfirm} className="btn btn-danger">
                Delete
              </button>
            </div>
          </div>
        </div>
      );
    };
  
    return (
      <div className={`data-table-container ${className}`}>
        {dtDeleteConfirm.isOpen && (
          <div className="modal-overlay">
            <div className="modal-content">
              <h3>Confirm Delete</h3>
              <p>
                Are you sure you want to delete{" "}
                {dtDeleteConfirm.row
                  ? `"${dtDeleteConfirm.row.title || "this item"}"`
                  : "this item"}
                ? This action cannot be undone.
              </p>
              <div className="modal-actions">
                <button
                  onClick={handleDeleteCancel}
                  className="btn btn-secondary"
                >
                  Cancel
                </button>
                <button onClick={handleDeleteConfirm} className="btn btn-danger">
                  Delete
                </button>
              </div>
            </div>
          </div>
        )}
        <div className="table-box">
          <div className="data-table-header">
            <h3 className="data-table-title">{title}</h3>
            <div className="table-controls">
              {showRefresh && onRefresh && (
                <button
                  className="refresh-button"
                  onClick={onRefresh}
                  disabled={loading}
                  aria-label="Refresh table"
                >
                  {loading ? (
                    <LoadingSpinner size={8} message="" />
                  ) : (
                    <span>Refresh</span>
                  )}
                </button>
              )}
              {enableRowSelection && selectedRows.length > 0 && (
                <span className="selected-count">
                  {selectedRows.length} selected
                </span>
              )}
            </div>
          </div>
  
          <div className="table-responsive" ref={tableRef}>
            {loading ? (
              <SkeletonTable />
            ) : (
              <table className="data-table" role="table" aria-label={title || "Data table"}>
                <thead>
                  <tr>
                    {enableRowSelection && (
                      <th className="selection-header" scope="col" aria-label="Select row">
                        <input
                          type="checkbox"
                          checked={selectedRows.length === displayedData.length && displayedData.length > 0}
                          onChange={handleSelectAll}
                          aria-label="Select all rows"
                        />
                      </th>
                    )}
                    {tableColumns.map((column, index) => (
                      <th
                        key={column.key || column.field || index}
                        className={`${column.className || ""} ${column.field && column.field !== 'actions' ? 'sortable' : ''}`}
                        style={{
                          ...(column.width && { width: column.width }),
                          ...(column.align && { textAlign: column.align }),
                          ...(column.style || {}),
                        }}
                        onClick={() => handleSort(column.field)}
                        scope="col"
                        aria-sort={
                          column.field && column.field !== 'actions' && sortConfig.field === column.field
                            ? sortConfig.direction === 'asc' ? 'ascending' : 'descending'
                            : 'none'
                        }
                        aria-label={`${column.header || column.title}${column.field && column.field !== 'actions' ? ', click to sort' : ''}`}
                      >
                        <div className="header-content">
                          <span className="header-text">{column.header || column.title}</span>
                          {column.field && column.field !== 'actions' && (
                            <span className="sort-icon-container" aria-hidden="true">
                              {getSortIcon(column.field)}
                            </span>
                          )}
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>{renderTableBody()}</tbody>
              </table>
            )}
          </div>
        </div>
  
        <div className="pagination" role="navigation" aria-label="Table pagination">
          <div className="records-per-page">
            <span>Show</span>
            <select
              className="records-select"
              value={pageSize}
              onChange={handlePageSizeChange}
              disabled={loading}
              aria-label="Number of entries per page"
            >
              {pageSizeOptions.map((size) => (
                <option key={size} value={size}>
                  {size}
                </option>
              ))}
            </select>
            <span>entries</span>
          </div>
  
          <div className="pagination-info">
            Showing {data.length ? (currentPage - 1) * pageSize + 1 : 0} to{" "}
            {Math.min(currentPage * pageSize, data.length)} of {data.length}{" "}
            entries
          </div>
  
          <div className="pagination-controls">
            <button
              className="pagination-button pagination-arrow"
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1 || loading}
              title="Previous page"
              aria-label="Go to previous page"
            >
              ‹
            </button>

            {renderPageNumbers()}

            <button
              className="pagination-button pagination-arrow"
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === totalPages || loading}
              title="Next page"
              aria-label="Go to next page"
            >
              ›
            </button>
          </div>
        </div>
  
        {/* Context Menu removed - using common ContextMenu component instead */}
  
        {/* Delete Confirmation Modal */}
        <ConfirmModal
          isOpen={dtDeleteConfirm.isOpen}
          onClose={handleDtCancelDelete}
          onConfirm={handleDtConfirmDelete}
          title="Confirm Delete"
          message="Are you sure you want to delete this item? This action cannot be undone."
          confirmText="Delete"
          cancelText="Cancel"
          confirmButtonClass="btn-danger"
        />
      </div>
    );
  };
  
  DataTable.propTypes = {
    title: PropTypes.string,
    columns: PropTypes.arrayOf(PropTypes.object).isRequired,
    data: PropTypes.array.isRequired,
    loading: PropTypes.bool,
    onRefresh: PropTypes.func,
    onRowClick: PropTypes.func,
    actions: PropTypes.arrayOf(PropTypes.string),
    onAction: PropTypes.func,
    showRefresh: PropTypes.bool,
    showActions: PropTypes.bool,
    className: PropTypes.string,
    pageSizeOptions: PropTypes.arrayOf(PropTypes.number),
    defaultPageSize: PropTypes.number,
    actionIcons: PropTypes.object,
    actionLabels: PropTypes.object,
    enableRowSelection: PropTypes.bool,
    onSelectionChange: PropTypes.func,
    onEdit: PropTypes.func,
    onDelete: PropTypes.func,
    editingRow: PropTypes.number,
  editingData: PropTypes.object,
  setEditingRow: PropTypes.func,
  setEditingData: PropTypes.func,
};

export default React.memo(DataTable);
