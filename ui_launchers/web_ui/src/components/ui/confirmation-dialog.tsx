/**
 * Confirmation Dialog Components
 * 
 * Reusable confirmation dialogs for destructive administrative actions
 * with clear messaging and keyboard navigation support.
 * 
 * Requirements: 7.2, 7.7
 */
"use client";

import React, { useEffect, useRef } from 'react';
import { AlertTriangle, Trash2, UserX, Shield, X } from 'lucide-react';
export interface ConfirmationDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  type?: 'danger' | 'warning' | 'info';
  loading?: boolean;
  requiresTyping?: boolean;
  confirmationText?: string;
  details?: string[];
  icon?: React.ReactNode;
}
export function ConfirmationDialog({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  type = 'warning',
  loading = false,
  requiresTyping = false,
  confirmationText,
  details,
  icon
}: ConfirmationDialogProps) {
  const [typedText, setTypedText] = React.useState('');
  const [isValid, setIsValid] = React.useState(!requiresTyping);
  const dialogRef = useRef<HTMLDivElement>(null);
  const confirmButtonRef = useRef<HTMLButtonElement>(null);
  const cancelButtonRef = useRef<HTMLButtonElement>(null);
  // Reset state when dialog opens/closes
  useEffect(() => {
    if (isOpen) {
      setTypedText('');
      setIsValid(!requiresTyping);
      // Focus the cancel button by default for safety
      setTimeout(() => cancelButtonRef.current?.focus(), 100);
    }
  }, [isOpen, requiresTyping]);
  // Validate typed text
  useEffect(() => {
    if (requiresTyping && confirmationText) {
      setIsValid(typedText.trim().toLowerCase() === confirmationText.toLowerCase());
    }
  }, [typedText, confirmationText, requiresTyping]);
  // Handle keyboard navigation
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        onClose();
      } else if (event.key === 'Enter' && isValid && !loading) {
        event.preventDefault();
        onConfirm();
      } else if (event.key === 'Tab') {
        // Trap focus within dialog
        const focusableElements = dialogRef.current?.querySelectorAll(
          'button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        if (focusableElements && focusableElements.length > 0) {
          const firstElement = focusableElements[0] as HTMLElement;
          const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;
          if (event.shiftKey && document.activeElement === firstElement) {
            event.preventDefault();
            lastElement.focus();
          } else if (!event.shiftKey && document.activeElement === lastElement) {
            event.preventDefault();
            firstElement.focus();
          }
        }
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, isValid, loading, onClose, onConfirm]);
  const getTypeStyles = () => {
    switch (type) {
      case 'danger':
        return {
          iconColor: 'text-red-600',
          confirmButton: 'bg-red-600 hover:bg-red-700 focus:ring-red-500',
          border: 'border-red-200'
        };
      case 'warning':
        return {
          iconColor: 'text-yellow-600',
          confirmButton: 'bg-yellow-600 hover:bg-yellow-700 focus:ring-yellow-500',
          border: 'border-yellow-200'
        };
      case 'info':
        return {
          iconColor: 'text-blue-600',
          confirmButton: 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500',
          border: 'border-blue-200'
        };
      default:
        return {
          iconColor: 'text-yellow-600',
          confirmButton: 'bg-yellow-600 hover:bg-yellow-700 focus:ring-yellow-500',
          border: 'border-yellow-200'
        };
    }
  };
  const getDefaultIcon = () => {
    switch (type) {
      case 'danger':
        return <AlertTriangle className="h-6 w-6 " />;
      case 'warning':
        return <AlertTriangle className="h-6 w-6 " />;
      case 'info':
        return <Shield className="h-6 w-6 " />;
      default:
        return <AlertTriangle className="h-6 w-6 " />;
    }
  };
  const styles = getTypeStyles();
  if (!isOpen) return null;
  return (
    <div 
      className="fixed inset-0 z-50 overflow-y-auto"
      aria-labelledby="confirmation-dialog-title"
      aria-describedby="confirmation-dialog-description"
      role="dialog"
      aria-modal="true"
    >
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />
      {/* Dialog */}
      <div className="flex min-h-full items-center justify-center p-4 sm:p-4 md:p-6">
        <div 
          ref={dialogRef}
          className={`relative bg-white rounded-lg shadow-xl max-w-md w-full border ${styles.border}`}
        >
          {/* Close button */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded"
            aria-label="Close dialog"
          >
            <X className="h-5 w-5 " />
          </button>
          <div className="p-6 sm:p-4 md:p-6">
            {/* Icon and Title */}
            <div className="flex items-center mb-4">
              <div className={`flex-shrink-0 ${styles.iconColor}`}>
                {icon || getDefaultIcon()}
              </div>
              <h3 
                id="confirmation-dialog-title"
                className="ml-3 text-lg font-medium text-gray-900"
              >
                {title}
              </h3>
            </div>
            {/* Message */}
            <div id="confirmation-dialog-description" className="mb-4">
              <p className="text-sm text-gray-700 mb-3 md:text-base lg:text-lg">
                {message}
              </p>
              {/* Additional details */}
              {details && details.length > 0 && (
                <div className="bg-gray-50 rounded-md p-3 mb-3 sm:p-4 md:p-6">
                  <ul className="text-sm text-gray-600 space-y-1 md:text-base lg:text-lg">
                    {details.map((detail, index) => (
                      <li key={index} className="flex items-start">
                        <span className="inline-block w-2 h-2 bg-gray-400 rounded-full mt-1.5 mr-2 flex-shrink-0 " />
                        {detail}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {/* Typing confirmation */}
              {requiresTyping && confirmationText && (
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2 md:text-base lg:text-lg">
                    Type <span className="font-mono bg-gray-100 px-1 rounded">{confirmationText}</span> to confirm:
                  </label>
                  <input
                    type="text"
                    value={typedText}
                    onChange={(e) => setTypedText(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    }
                    autoComplete="off"
                    spellCheck="false"
                  />
                </div>
              )}
            </div>
            {/* Actions */}
            <div className="flex justify-end space-x-3">
              <button
                ref={cancelButtonRef}
                onClick={onClose}
                disabled={loading}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed md:text-base lg:text-lg"
               aria-label="Button">
                {cancelText}
              </button>
              <button
                ref={confirmButtonRef}
                onClick={onConfirm}
                disabled={!isValid || loading}
                className={`px-4 py-2 text-sm font-medium text-white rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed ${styles.confirmButton}`}
               aria-label="Button">
                {loading ? (
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2 " />
                    Processing...
                  </div>
                ) : (
                  confirmText
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
// Predefined confirmation dialogs for common admin actions
export function DeleteUserConfirmation({
  isOpen,
  onClose,
  onConfirm,
  userEmail,
  loading = false
}: {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  userEmail: string;
  loading?: boolean;
}) {
  return (
    <ConfirmationDialog
      isOpen={isOpen}
      onClose={onClose}
      onConfirm={onConfirm}
      title="Delete User Account"
      message={`Are you sure you want to delete the user account for ${userEmail}?`}
      confirmText="Delete User"
      type="danger"
      loading={loading}
      requiresTyping={true}
      confirmationText="DELETE"
      details={[
        'This action cannot be undone',
        'All user data will be permanently removed',
        'The user will lose access immediately',
        'Any ongoing sessions will be terminated'
      ]}
      icon={<Trash2 className="h-6 w-6 " />}
    />
  );
}
export function DeactivateUserConfirmation({
  isOpen,
  onClose,
  onConfirm,
  userEmail,
  loading = false
}: {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  userEmail: string;
  loading?: boolean;
}) {
  return (
    <ConfirmationDialog
      isOpen={isOpen}
      onClose={onClose}
      onConfirm={onConfirm}
      title="Deactivate User Account"
      message={`Are you sure you want to deactivate the user account for ${userEmail}?`}
      confirmText="Deactivate"
      type="warning"
      loading={loading}
      details={[
        'The user will not be able to log in',
        'Existing sessions will be terminated',
        'The account can be reactivated later',
        'User data will be preserved'
      ]}
      icon={<UserX className="h-6 w-6 " />}
    />
  );
}
export function BulkOperationConfirmation({
  isOpen,
  onClose,
  onConfirm,
  operation,
  itemCount,
  loading = false
}: {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  operation: string;
  itemCount: number;
  loading?: boolean;
}) {
  return (
    <ConfirmationDialog
      isOpen={isOpen}
      onClose={onClose}
      onConfirm={onConfirm}
      title={`Bulk ${operation}`}
      message={`Are you sure you want to ${operation.toLowerCase()} ${itemCount} user${itemCount === 1 ? '' : 's'}?`}
      confirmText={`${operation} ${itemCount} User${itemCount === 1 ? '' : 's'}`}
      type="warning"
      loading={loading}
      details={[
        `This will affect ${itemCount} user account${itemCount === 1 ? '' : 's'}`,
        'The operation may take some time to complete',
        'You will receive a summary when finished',
        'Some operations may fail individually'
      ]}
    />
  );
}
export default ConfirmationDialog;
