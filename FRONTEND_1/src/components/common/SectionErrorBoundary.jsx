import React from 'react';
import ErrorBoundary from './ErrorBoundary';
import { FaExclamationCircle } from 'react-icons/fa';

const SectionErrorBoundary = ({ 
  children, 
  sectionName, 
  fallback = null,
  onError = null 
}) => {
  const handleError = (error, errorInfo, retry) => {
    // Call custom error handler if provided
    if (onError) {
      onError(error, errorInfo);
    }

    // Return custom fallback if provided
    if (fallback) {
      return fallback(error, errorInfo, retry);
    }

    // Default section-specific error UI
    return (
      <div className="section-error">
        <div className="section-error-content">
          <div className="section-error-icon">
            <FaExclamationCircle />
          </div>
          <h3 className="section-error-title">
            {sectionName} Error
          </h3>
          <p className="section-error-message">
            There was a problem loading the {sectionName.toLowerCase()} section. 
            Please try refreshing or contact support if the issue persists.
          </p>
          <button 
            className="section-error-retry"
            onClick={retry}
          >
            Retry
          </button>
        </div>
      </div>
    );
  };

  return (
    <ErrorBoundary
      fallback={handleError}
      showDetails={process.env.NODE_ENV === 'development'}
    >
      {children}
    </ErrorBoundary>
  );
};

export default SectionErrorBoundary;
