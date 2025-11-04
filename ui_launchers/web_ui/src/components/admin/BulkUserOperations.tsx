/**
 * Bulk User Operations Component
 * 
 * Provides bulk operations for user management including export, import,
 * status changes, and role modifications with progress tracking.
 * 
 * Requirements: 4.5, 4.6, 7.3
 */
"use client";

import React, { useState } from 'react';
import { useRole } from '@/hooks/useRole';
import type {  BulkUserOperation, AdminApiResponse, ExportConfig, ImportConfig } from '@/types/admin';
interface BulkUserOperationsProps {
  selectedUserIds: string[];
  onOperationComplete: () => void;
  onCancel: () => void;
  className?: string;
}
type OperationType = 'activate' | 'deactivate' | 'delete' | 'export' | 'import' | 'role_change';
interface OperationProgress {
  total: number;
  completed: number;
  failed: number;
  errors: string[];
}
export function BulkUserOperations({
  selectedUserIds,
  onOperationComplete,
  onCancel,
  className = ''
}: BulkUserOperationsProps) {
  const { hasRole } = useRole();
  const [selectedOperation, setSelectedOperation] = useState<OperationType>('activate');
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState<OperationProgress | null>(null);
  const [newRole, setNewRole] = useState<'admin' | 'user'>('user');
  const [exportFormat, setExportFormat] = useState<'csv' | 'json' | 'xlsx'>('csv');
  const [importFile, setImportFile] = useState<File | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const operations = [
    { id: 'activate', label: 'Activate Users', description: 'Enable selected user accounts', dangerous: false },
    { id: 'deactivate', label: 'Deactivate Users', description: 'Disable selected user accounts', dangerous: false },
    { id: 'role_change', label: 'Change Role', description: 'Update role for selected users', dangerous: false },
    { id: 'export', label: 'Export Users', description: 'Download user data in selected format', dangerous: false },
    { id: 'delete', label: 'Delete Users', description: 'Permanently remove selected users', dangerous: true },
  ];
  const handleBulkOperation = async () => {
    if (selectedOperation === 'delete' && !confirmDelete) {
      alert('Please confirm deletion by checking the confirmation box.');
      return;
    }
    setLoading(true);
    setProgress({
      total: selectedUserIds.length,
      completed: 0,
      failed: 0,
      errors: []

    try {
      const operationData: BulkUserOperation = {
        operation: selectedOperation,
        user_ids: selectedUserIds,
        parameters: {}
      };
      // Add operation-specific parameters
      if (selectedOperation === 'role_change') {
        operationData.parameters = { new_role: newRole };
      } else if (selectedOperation === 'export') {
        operationData.parameters = { format: exportFormat };
      }
      const response = await fetch('/api/admin/users/bulk', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(operationData),

      const data: AdminApiResponse<any> = await response.json();
      if (!response.ok || !data.success) {
        throw new Error(data.error?.message || 'Bulk operation failed');
      }
      // Handle export operation differently
      if (selectedOperation === 'export' && data.data?.download_url) {
        // Trigger download
        const link = document.createElement('a');
        link.href = data.data?.download_url || '';
        link.download = data.data?.filename || `users_export.${exportFormat}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }
      // Update progress
      setProgress(prev => prev ? {
        ...prev,
        completed: prev.total,
        failed: 0
      } : null);
      // Show success message
      setTimeout(() => {
        onOperationComplete();
      }, 1500);
    } catch (err) {
      setProgress(prev => prev ? {
        ...prev,
        failed: prev.total - prev.completed,
        errors: [err instanceof Error ? err.message : 'Operation failed']
      } : null);
    } finally {
      setLoading(false);
    }
  };
  const handleImport = async () => {
    if (!importFile) {
      alert('Please select a file to import.');
      return;
    }
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', importFile);
      formData.append('format', importFile.name.endsWith('.json') ? 'json' : 'csv');
      formData.append('skip_duplicates', 'true');
      formData.append('send_invitations', 'true');
      formData.append('default_role', 'user');
      const response = await fetch('/api/admin/users/import', {
        method: 'POST',
        body: formData,

      const data: AdminApiResponse<any> = await response.json();
      if (!response.ok || !data.success) {
        throw new Error(data.error?.message || 'Import failed');
      }
      alert(`Import completed successfully! ${data.data?.imported_count || 0} users imported.`);
      onOperationComplete();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Import failed');
    } finally {
      setLoading(false);
    }
  };
  const canPerformOperation = (operation: OperationType) => {
    switch (operation) {
      case 'role_change':
      case 'delete':
        return hasRole('super_admin');
      case 'activate':
      case 'deactivate':
      case 'export':
        return hasRole('admin');
      case 'import':
        return hasRole('admin');
      default:
        return false;
    }
  };
  const renderOperationForm = () => {
    switch (selectedOperation) {
      case 'role_change':
        return (
          <div className="space-y-4">
            <div>
              <label htmlFor="new_role" className="block text-sm font-medium text-gray-700 mb-1 md:text-base lg:text-lg">
              </label>
              <select
                id="new_role"
                value={newRole}
                onChange={(e) => setNewRole(e.target.value as 'admin' | 'user')}
                className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={loading}
              >
                <option value="user">User</option>
                {hasRole('super_admin') && (
                  <option value="admin">Admin</option>
                )}
              </select>
            </div>
          </div>
        );
      case 'export':
        return (
          <div className="space-y-4">
            <div>
              <label htmlFor="export_format" className="block text-sm font-medium text-gray-700 mb-1 md:text-base lg:text-lg">
              </label>
              <select
                id="export_format"
                value={exportFormat}
                onChange={(e) => setExportFormat(e.target.value as 'csv' | 'json' | 'xlsx')}
                className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={loading}
              >
                <option value="csv">CSV</option>
                <option value="json">JSON</option>
                <option value="xlsx">Excel (XLSX)</option>
              </select>
            </div>
          </div>
        );
      case 'delete':
        return (
          <div className="space-y-4">
            <div className="bg-red-50 border border-red-200 rounded-md p-4 sm:p-4 md:p-6">
              <div className="flex">
                <svg className="h-5 w-5 text-red-400 " fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800 md:text-base lg:text-lg">Warning: Permanent Deletion</h3>
                  <p className="text-sm text-red-700 mt-1 md:text-base lg:text-lg">
                    This action will permanently delete {selectedUserIds.length} user(s) and cannot be undone.
                    All user data, including their history and associated records, will be removed.
                  </p>
                </div>
              </div>
            </div>
            <div className="flex items-center">
              <input
                id="confirm_delete"
                type="checkbox"
                checked={confirmDelete}
                onChange={(e) => setConfirmDelete(e.target.checked)}
                className="h-4 w-4 text-red-600 focus:ring-red-500 border-gray-300 rounded "
                disabled={loading}
              />
              <label htmlFor="confirm_delete" className="ml-2 block text-sm text-gray-900 md:text-base lg:text-lg">
              </label>
            </div>
          </div>
        );
      default:
        return null;
    }
  };
  const renderImportSection = () => (
    <div className="border-t border-gray-200 pt-6 mt-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Import Users</h3>
      <div className="space-y-4">
        <div>
          <label htmlFor="import_file" className="block text-sm font-medium text-gray-700 mb-1 md:text-base lg:text-lg">
            Select File (CSV or JSON)
          </label>
          <input
            id="import_file"
            type="file"
            accept=".csv,.json"
            onChange={(e) => setImportFile(e.target.files?.[0] || null)}
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 md:text-base lg:text-lg"
            disabled={loading}
          />
          <p className="text-sm text-gray-500 mt-1 md:text-base lg:text-lg">
            CSV format: email, full_name, role (optional). JSON format: array of user objects.
          </p>
        </div>
        <Button
          onClick={handleImport}
          disabled={!importFile || loading}
          className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed md:text-base lg:text-lg"
         aria-label="Button">
          {loading ? 'Importing...' : 'Import Users'}
        </Button>
      </div>
    </div>
  );
  const renderProgress = () => {
    if (!progress) return null;
    const percentage = progress.total > 0 ? (progress.completed / progress.total) * 100 : 0;
    return (
      <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-md sm:p-4 md:p-6">
        <h4 className="text-sm font-medium text-blue-900 mb-2 md:text-base lg:text-lg">Operation Progress</h4>
        <div className="w-full bg-blue-200 rounded-full h-2 mb-2">
          <div 
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${percentage}%` }}
          ></div>
        </div>
        <div className="flex justify-between text-sm text-blue-800 md:text-base lg:text-lg">
          <span>Completed: {progress.completed}/{progress.total}</span>
          <span>Failed: {progress.failed}</span>
        </div>
        {progress.errors.length > 0 && (
          <div className="mt-2">
            <p className="text-sm font-medium text-red-800 md:text-base lg:text-lg">Errors:</p>
            <ul className="text-sm text-red-700 list-disc list-inside md:text-base lg:text-lg">
              {progress.errors.map((error, index) => (
                <li key={index}>{error}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };
  return (
    <div className={`bg-white shadow rounded-lg ${className}`}>
      <div className="px-6 py-4 border-b border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900">Bulk Operations</h2>
        <p className="text-sm text-gray-600 mt-1 md:text-base lg:text-lg">
          Perform operations on {selectedUserIds.length} selected user(s)
        </p>
      </div>
      <div className="px-6 py-4 space-y-6">
        {/* Operation Selection */}
        <div>
          <label htmlFor="operation" className="block text-sm font-medium text-gray-700 mb-2 md:text-base lg:text-lg">
          </label>
          <div className="space-y-2">
            {operations.map((op) => (
              <div key={op.id} className="flex items-center">
                <input
                  id={op.id}
                  type="radio"
                  name="operation"
                  value={op.id}
                  checked={selectedOperation === op.id}
                  onChange={(e) => setSelectedOperation(e.target.value as OperationType)}
                  disabled={!canPerformOperation(op.id as OperationType) || loading}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 "
                />
                <label htmlFor={op.id} className="ml-2 block text-sm text-gray-900 md:text-base lg:text-lg">
                  <span className={op.dangerous ? 'text-red-600 font-medium' : ''}>{op.label}</span>
                  <span className="text-gray-500 ml-2">- {op.description}</span>
                  {!canPerformOperation(op.id as OperationType) && (
                    <span className="text-red-500 ml-2">(Insufficient permissions)</span>
                  )}
                </label>
              </div>
            ))}
          </div>
        </div>
        {/* Operation-specific form */}
        {renderOperationForm()}
        {/* Progress display */}
        {renderProgress()}
        {/* Action buttons */}
        <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
          <Button
            onClick={onCancel}
            disabled={loading}
            className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed md:text-base lg:text-lg"
           aria-label="Button">
          </Button>
          <Button
            onClick={handleBulkOperation}
            disabled={!canPerformOperation(selectedOperation) || loading || (selectedOperation === 'delete' && !confirmDelete)}
            className={`px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed ${
              selectedOperation === 'delete'
                ? 'bg-red-600 hover:bg-red-700 focus:ring-red-500'
                : 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500'
            }`}
           aria-label="Button">
            {loading ? (
              <div className="flex items-center">
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white " fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Processing...
              </div>
            ) : (
              `Execute ${operations.find(op => op.id === selectedOperation)?.label}`
            )}
          </Button>
        </div>
        {/* Import section */}
        {hasRole('admin') && renderImportSection()}
      </div>
    </div>
  );
}
