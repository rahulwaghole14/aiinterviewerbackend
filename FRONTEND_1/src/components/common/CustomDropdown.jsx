import React, { useState, useRef, useEffect } from 'react';
import ReactDOM from 'react-dom';
import { FiChevronDown } from 'react-icons/fi';
import './CustomDropdown.css';

const CustomDropdown = ({ 
  value, 
  options, 
  onChange, 
  placeholder = "Select...",
  className = "",
  disabled = false,
  searchable = false,
  openAbove = false
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [menuPosition, setMenuPosition] = useState({ top: 0, left: 0, width: 0 });
  const [searchTerm, setSearchTerm] = useState('');
  const dropdownRef = useRef(null);
  const buttonRef = useRef(null);
  const searchInputRef = useRef(null);

  // Calculate menu position when opening
  useEffect(() => {
    if (isOpen && buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      const viewportHeight = window.innerHeight;
      const estimatedMenuHeight = Math.min(options.length * 40 + (searchable ? 50 : 0), 300);
      
      let top;
      if (openAbove || (rect.bottom + estimatedMenuHeight > viewportHeight && rect.top > estimatedMenuHeight)) {
        // Open above
        top = rect.top + window.scrollY - estimatedMenuHeight - 4;
      } else {
        // Open below (default)
        top = rect.bottom + window.scrollY + 4;
      }
      
      setMenuPosition({
        top,
        left: rect.left + window.scrollX,
        width: rect.width
      });
    }
  }, [isOpen, options.length, searchable, openAbove]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  // Focus search input when dropdown opens
  useEffect(() => {
    if (isOpen && searchable && searchInputRef.current) {
      setTimeout(() => {
        searchInputRef.current?.focus();
      }, 100);
    }
  }, [isOpen, searchable]);

  const handleSelect = (optionValue) => {
    if (onChange && typeof onChange === 'function') {
      onChange(optionValue);
    }
    setIsOpen(false);
    setSearchTerm(''); // Clear search when selection is made
  };

  const selectedOption = options.find(opt => {
    const optValue = String(opt.value);
    const currentValue = String(value);
    return optValue === currentValue;
  });

  // Filter options based on search term
  const filteredOptions = searchable && searchTerm 
    ? options.filter(option => 
        option.label.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : options;
  
  const displayText = selectedOption ? selectedOption.label : placeholder;

  return (
    <>
      <div className={`custom-dropdown ${className} ${isOpen ? 'open' : ''}`} ref={dropdownRef}>
        <button
          ref={buttonRef}
          type="button"
          className={`custom-dropdown-button ${isOpen ? 'open' : ''}`}
          onClick={() => {
            if (!disabled) {
              setIsOpen(!isOpen);
            }
          }}
          disabled={disabled}
        >
          <span className={`dropdown-selected-text ${!selectedOption ? 'placeholder' : ''}`}>
            {displayText}
          </span>
          <FiChevronDown className={`dropdown-icon ${isOpen ? 'open' : ''}`} />
        </button>
      </div>

      {isOpen && !disabled && ReactDOM.createPortal(
        <div 
          className="custom-dropdown-menu custom-dropdown-portal"
          style={{
            position: 'fixed',
            top: `${menuPosition.top}px`,
            left: `${menuPosition.left}px`,
            width: `${menuPosition.width}px`,
            zIndex: 999999,
            overflow: 'hidden',
            scrollbarWidth: 'none',
            msOverflowStyle: 'none',
            pointerEvents: 'auto'
          }}
        >
          {searchable && (
            <div className="custom-dropdown-search">
              <input
                ref={searchInputRef}
                type="text"
                placeholder="Search companies..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Escape') {
                    setIsOpen(false);
                    setSearchTerm('');
                  }
                }}
                className="custom-dropdown-search-input"
              />
            </div>
          )}
          <div className="custom-dropdown-options">
            {filteredOptions.length > 0 ? (
              filteredOptions.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  className={`custom-dropdown-item ${String(value) === String(option.value) ? 'active' : ''}`}
                  onMouseDown={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    handleSelect(option.value);
                  }}
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    handleSelect(option.value);
                  }}
                >
                  {option.label}
                </button>
              ))
            ) : (
              <div className="custom-dropdown-no-results">
                No companies found
              </div>
            )}
          </div>
        </div>,
        document.body
      )}
    </>
  );
};

export default CustomDropdown;