import React, { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { useTheme } from '../../contexts/ThemeContext';
import { FaSun, FaMoon, FaDesktop } from 'react-icons/fa';
import './ThemeToggle.css';

const ThemeToggle = ({ variant = 'button', showLabels = true, className = '' }) => {
  const { theme, isSystemTheme, toggleTheme, setSystemTheme, setLightTheme, setDarkTheme } = useTheme();
  const [isOpen, setIsOpen] = useState(false);
  const [position, setPosition] = useState({ top: 0, left: 0 });
  const [isPositioned, setIsPositioned] = useState(false);
  const dropdownRef = useRef(null);
  const triggerRef = useRef(null);

  // Calculate position when dropdown opens
  const calculatePosition = () => {
    if (triggerRef.current) {
      const rect = triggerRef.current.getBoundingClientRect();
      const dropdownWidth = 128; // 8rem = 128px
      const viewportWidth = window.innerWidth;
      const triggerCenter = rect.left + (rect.width / 2);
      const dropdownLeft = triggerCenter - (dropdownWidth / 2);
      
      // Ensure dropdown doesn't go off-screen
      const adjustedLeft = Math.max(8, Math.min(dropdownLeft, viewportWidth - dropdownWidth - 8));
      
      setPosition({
        top: rect.bottom - 5,
        left: adjustedLeft - 20
      });
      setIsPositioned(true);
    }
  };

  // Handle click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target) && 
          triggerRef.current && !triggerRef.current.contains(event.target)) {
        setIsOpen(false);
        setIsPositioned(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('touchstart', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('touchstart', handleClickOutside);
    };
  }, [isOpen]);

  const handleThemeSelect = (themeFunction) => {
    themeFunction();
    setIsOpen(false);
    setIsPositioned(false);
  };

  if (variant === 'dropdown') {
    return (
      <>
        <div className={`theme-dropdown ${className}`}>
                 <div 
                   ref={triggerRef}
                   className="theme-dropdown-trigger"
                   onClick={() => {
                     if (!isOpen) {
                       setIsPositioned(false);
                       calculatePosition();
                     }
                     setIsOpen(!isOpen);
                   }}
                 >
            <span className="theme-icon">
              {isSystemTheme ? <FaDesktop /> : theme === 'dark' ? <FaMoon /> : <FaSun />}
            </span>
            {showLabels && <span className="theme-label">Theme</span>}
          </div>
        </div>
        
               {isOpen && createPortal(
                 <div 
                   ref={dropdownRef} 
                   className={`theme-dropdown-menu theme-dropdown-portal ${!isPositioned ? 'hidden' : ''}`}
                   style={{
                     top: `${position.top}px`,
                     left: `${position.left}px`
                   }}
                 >
            <button
              className={`theme-option ${theme === 'light' && !isSystemTheme ? 'active' : ''}`}
              onClick={() => handleThemeSelect(setLightTheme)}
            >
              <FaSun className="theme-option-icon" />
              <span>Light</span>
            </button>
            <button
              className={`theme-option ${theme === 'dark' && !isSystemTheme ? 'active' : ''}`}
              onClick={() => handleThemeSelect(setDarkTheme)}
            >
              <FaMoon className="theme-option-icon" />
              <span>Dark</span>
            </button>
            <button
              className={`theme-option ${isSystemTheme ? 'active' : ''}`}
              onClick={() => handleThemeSelect(setSystemTheme)}
            >
              <FaDesktop className="theme-option-icon" />
              <span>System</span>
            </button>
          </div>,
          document.body
        )}
      </>
    );
  }

  if (variant === 'switch') {
    return (
      <div className={`theme-switch ${className}`}>
        <label className="theme-switch-label">
          <input
            type="checkbox"
            checked={theme === 'dark'}
            onChange={toggleTheme}
            className="theme-switch-input"
          />
          <span className="theme-switch-slider">
            <span className="theme-switch-icon">
              {theme === 'dark' ? <FaMoon /> : <FaSun />}
            </span>
          </span>
          {showLabels && <span className="theme-switch-text">Dark Mode</span>}
        </label>
      </div>
    );
  }

  // Default button variant
  return (
    <button
      className={`theme-toggle-button ${className}`}
      onClick={toggleTheme}
      title={`Switch to ${theme === 'light' ? 'dark' : 'light'} theme`}
      aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} theme`}
    >
      <span className="theme-toggle-icon">
        {theme === 'dark' ? <FaSun /> : <FaMoon />}
      </span>
      {showLabels && (
        <span className="theme-toggle-text">
          {theme === 'dark' ? 'Light' : 'Dark'}
        </span>
      )}
    </button>
  );
};

export default ThemeToggle;
