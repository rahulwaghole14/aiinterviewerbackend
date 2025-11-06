// src/components/common/Modal.jsx
import React, { useEffect } from 'react';
import './Modal.css';

const Modal = ({
  isOpen,
  onClose,
  title,
  children,
  size = 'medium', // small, medium, large, fullscreen
  variant = 'default', // default, confirm, form
  showCloseButton = true,
  showHeader = true,
  showFooter = true,
  footer,
  className = '',
  overlayClassName = '',
  contentClassName = '',
  closeOnBackdrop = true,
  closeOnEscape = true,
  zIndex = 1000,
  animation = 'fade', // fade, slide, scale
  ...props
}) => {
  // Handle escape key
  useEffect(() => {
    if (!isOpen || !closeOnEscape) return;

    const handleEscape = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, closeOnEscape, onClose]);

  // Prevent body scroll when modal is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      return () => {
        document.body.style.overflow = 'unset';
      };
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleBackdropClick = (e) => {
    // Only close if clicking directly on the backdrop, not on any child elements
    if (e.target === e.currentTarget && closeOnBackdrop) {
      onClose();
    }
  };

  const handleContentClick = (e) => {
    // Prevent event bubbling to backdrop when clicking inside modal content
    e.stopPropagation();
  };

  const modalClasses = [
    'common-modal-overlay',
    `modal-${size}`,
    `modal-${variant}`,
    `modal-${animation}`,
    overlayClassName
  ].filter(Boolean).join(' ');

  const contentClasses = [
    'common-modal-content',
    `content-${size}`,
    `content-${variant}`,
    contentClassName
  ].filter(Boolean).join(' ');

  return (
    <div
      className={`${modalClasses} ${className}`}
      onClick={handleBackdropClick}
      style={{ zIndex }}
      {...props}
    >
      <div className={contentClasses} onClick={handleContentClick}>
        {showHeader && (title || showCloseButton) && (
          <div className="common-modal-header">
            {title && <h3 className="common-modal-title">{title}</h3>}
            {showCloseButton && (
              <button
                className="common-modal-close-btn"
                onClick={onClose}
                aria-label="Close modal"
                type="button"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        )}

        <div className="common-modal-body">
          {children}
        </div>

        {showFooter && footer && (
          <div className="common-modal-footer">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
};

// Predefined modal variants for common use cases
export const ConfirmModal = ({ 
  isOpen, 
  onClose, 
  onConfirm, 
  title = "Confirm Action", 
  message, 
  confirmText = "Confirm", 
  cancelText = "Cancel",
  confirmButtonClass = "btn-danger",
  ...props 
}) => {
  const footer = (
    <div className="modal-confirm-actions">
      <button 
        className="common-modal-btn btn-cancel" 
        onClick={onClose}
        type="button"
      >
        {cancelText}
      </button>
      <button 
        className={`common-modal-btn ${confirmButtonClass}`}
        onClick={onConfirm}
        type="button"
      >
        {confirmText}
      </button>
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      variant="confirm"
      size="small"
      showFooter={true}
      footer={footer}
      {...props}
    >
      <p className="confirm-message">{message}</p>
    </Modal>
  );
};

export const FormModal = ({ 
  isOpen, 
  onClose, 
  onSubmit, 
  title, 
  children, 
  submitText = "Submit", 
  cancelText = "Cancel",
  isSubmitting = false,
  submitDisabled = false,
  ...props 
}) => {
  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(e);
  };

  const footer = (
    <div className="modal-form-actions">
      <button 
        className="common-modal-btn btn-cancel" 
        onClick={onClose}
        type="button"
        disabled={isSubmitting}
      >
        {cancelText}
      </button>
      <button 
        className="common-modal-btn btn-primary"
        type="submit"
        disabled={isSubmitting || submitDisabled}
        onClick={(e) => {
          e.preventDefault();
          onSubmit(e);
        }}
      >
        {isSubmitting ? 'Processing...' : submitText}
      </button>
    </div>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      variant="form"
      showFooter={true}
      footer={footer}
      closeOnBackdrop={false} // Disable backdrop closing for forms
      closeOnEscape={!isSubmitting} // Only allow escape when not submitting
      {...props}
    >
      <form onSubmit={handleSubmit} className="modal-form">
        {children}
      </form>
    </Modal>
  );
};

export default Modal;
