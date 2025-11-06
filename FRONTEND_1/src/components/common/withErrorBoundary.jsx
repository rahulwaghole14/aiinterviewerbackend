import React from 'react';
import ErrorBoundary from './ErrorBoundary';

/**
 * Higher-Order Component that wraps a component with an ErrorBoundary
 * @param {React.Component} WrappedComponent - The component to wrap
 * @param {Object} errorBoundaryProps - Props to pass to ErrorBoundary
 * @returns {React.Component} - Wrapped component with error boundary
 */
const withErrorBoundary = (WrappedComponent, errorBoundaryProps = {}) => {
  const WithErrorBoundaryComponent = (props) => {
    return (
      <ErrorBoundary {...errorBoundaryProps}>
        <WrappedComponent {...props} />
      </ErrorBoundary>
    );
  };

  // Set display name for debugging
  WithErrorBoundaryComponent.displayName = `withErrorBoundary(${WrappedComponent.displayName || WrappedComponent.name})`;

  return WithErrorBoundaryComponent;
};

export default withErrorBoundary;
