import React from 'react';
import { FaExclamationTriangle, FaRedo, FaHome } from 'react-icons/fa';
import { reportError } from '../../utils/errorReporting';
import './ErrorBoundary.css';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: 0,
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log error details for debugging
    this.setState({
      error,
      errorInfo,
    });

    // Report error using centralized error reporting
    reportError(error, {
      componentStack: errorInfo.componentStack,
      errorBoundary: this.constructor.name,
      props: this.props,
    });
  }

  handleRetry = () => {
    this.setState(prevState => ({
      hasError: false,
      error: null,
      errorInfo: null,
      retryCount: prevState.retryCount + 1,
    }));
  };

  handleReload = () => {
    window.location.reload();
  };

  handleGoHome = () => {
    window.location.href = '/dashboard';
  };

  render() {
    if (this.state.hasError) {
      const { fallback, showDetails = false } = this.props;
      const { error, errorInfo, retryCount } = this.state;

      // If a custom fallback is provided, use it
      if (fallback) {
        return fallback(error, errorInfo, this.handleRetry);
      }

      // Default error UI
      return (
        <div className="error-boundary">
          <div className="error-boundary-content">
            <div className="error-icon">
              <FaExclamationTriangle />
            </div>
            
            <h2 className="error-title">
              {this.props.title || 'Something went wrong'}
            </h2>
            
            <p className="error-message">
              {this.props.message || 
                'We encountered an unexpected error. This has been reported and we\'re working to fix it.'}
            </p>

            {retryCount > 0 && (
              <p className="retry-count">
                Retry attempt: {retryCount}
              </p>
            )}

            <div className="error-actions">
              <button 
                className="error-btn primary" 
                onClick={this.handleRetry}
                disabled={retryCount >= 3}
              >
                <FaRedo />
                Try Again
              </button>
              
              <button 
                className="error-btn secondary" 
                onClick={this.handleGoHome}
              >
                <FaHome />
                Go to Dashboard
              </button>
              
              <button 
                className="error-btn secondary" 
                onClick={this.handleReload}
              >
                Reload Page
              </button>
            </div>

            {showDetails && process.env.NODE_ENV === 'development' && (
              <details className="error-details">
                <summary>Error Details (Development Only)</summary>
                <div className="error-stack">
                  <h4>Error:</h4>
                  <pre>{error && error.toString()}</pre>
                  
                  <h4>Component Stack:</h4>
                  <pre>{errorInfo.componentStack}</pre>
                </div>
              </details>
            )}

            {retryCount >= 3 && (
              <div className="max-retries-message">
                <p>Maximum retry attempts reached. Please try reloading the page or contact support.</p>
              </div>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
