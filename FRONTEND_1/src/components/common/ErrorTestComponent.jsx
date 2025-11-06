import React, { useState } from 'react';
import ErrorBoundary from './ErrorBoundary';
import SectionErrorBoundary from './SectionErrorBoundary';

/**
 * Test component to demonstrate error boundary functionality
 * This component can be used for testing error boundaries in development
 */
const ErrorTestComponent = () => {
  const [shouldThrow, setShouldThrow] = useState(false);

  if (shouldThrow) {
    throw new Error('This is a test error to demonstrate error boundary functionality!');
  }

  return (
    <div style={{ padding: '1rem', border: '1px solid #ccc', margin: '1rem 0' }}>
      <h3>Error Boundary Test Component</h3>
      <p>Click the button below to trigger an error and test the error boundary:</p>
      <button 
        onClick={() => setShouldThrow(true)}
        style={{
          padding: '0.5rem 1rem',
          backgroundColor: '#ff4444',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer'
        }}
      >
        Trigger Error
      </button>
    </div>
  );
};

/**
 * Wrapped version with error boundary for testing
 */
export const ErrorTestWithBoundary = () => (
  <ErrorBoundary
    title="Test Error"
    message="This is a test error boundary. Click 'Try Again' to reset."
    showDetails={true}
  >
    <ErrorTestComponent />
  </ErrorBoundary>
);

/**
 * Wrapped version with section error boundary for testing
 */
export const ErrorTestWithSectionBoundary = () => (
  <SectionErrorBoundary sectionName="Test Section">
    <ErrorTestComponent />
  </SectionErrorBoundary>
);

export default ErrorTestComponent;
