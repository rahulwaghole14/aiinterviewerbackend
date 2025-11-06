/**
 * Error Reporting Utility
 * Centralized error handling and reporting for the application
 */

class ErrorReporter {
  constructor() {
    this.errorQueue = [];
    this.maxRetries = 3;
    this.retryDelay = 1000; // 1 second
  }

  /**
   * Report an error to the error reporting service
   * @param {Error} error - The error object
   * @param {Object} context - Additional context about the error
   * @param {string} level - Error level (error, warning, info)
   */
  report(error, context = {}, level = 'error') {
    const errorReport = {
      message: error.message,
      stack: error.stack,
      level,
      context,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
    };

    // In development, log to console
    if (process.env.NODE_ENV === 'development') {
      console.group(`🚨 Error Report (${level.toUpperCase()})`);
      console.error('Error:', error);
      console.log('Context:', context);
      console.log('Full Report:', errorReport);
      console.groupEnd();
    }

    // Add to queue for potential retry
    this.errorQueue.push(errorReport);

    // In production, you would send this to your error reporting service
    // Example: this.sendToErrorService(errorReport);
  }

  /**
   * Report a warning
   * @param {string} message - Warning message
   * @param {Object} context - Additional context
   */
  warn(message, context = {}) {
    const error = new Error(message);
    this.report(error, context, 'warning');
  }

  /**
   * Report an info message
   * @param {string} message - Info message
   * @param {Object} context - Additional context
   */
  info(message, context = {}) {
    const error = new Error(message);
    this.report(error, context, 'info');
  }

  /**
   * Send error to external service (implement based on your needs)
   * @param {Object} errorReport - The error report object
   */
  async sendToErrorService(errorReport) {
    try {
      // Example implementation - replace with your actual error reporting service
      const response = await fetch('/api/errors', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(errorReport),
      });

      if (!response.ok) {
        throw new Error(`Error reporting failed: ${response.status}`);
      }
    } catch (error) {
      // If error reporting fails, log it locally
      console.error('Failed to report error to service:', error);
    }
  }

  /**
   * Clear the error queue
   */
  clearQueue() {
    this.errorQueue = [];
  }

  /**
   * Get the current error queue
   * @returns {Array} Array of error reports
   */
  getQueue() {
    return [...this.errorQueue];
  }
}

// Create a singleton instance
const errorReporter = new ErrorReporter();

// Export utility functions
export const reportError = (error, context, level) => {
  errorReporter.report(error, context, level);
};

export const reportWarning = (message, context) => {
  errorReporter.warn(message, context);
};

export const reportInfo = (message, context) => {
  errorReporter.info(message, context);
};

export const clearErrorQueue = () => {
  errorReporter.clearQueue();
};

export const getErrorQueue = () => {
  return errorReporter.getQueue();
};

export default errorReporter;
