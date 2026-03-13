"use client";

import React, { useState, useRef } from 'react';
import { cn } from '@/lib/utils';
import { MemoryImportExportProps } from '../types';

// Icon components
const Upload = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
  </svg>
);

const Download = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2v-6a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
  </svg>
);

const FileText = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
  </svg>
);

const Check = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
  </svg>
);

const AlertCircle = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const X = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
  </svg>
);

export function MemoryImportExport({ onImport, onExport, className }: MemoryImportExportProps) {
  const [activeTab, setActiveTab] = useState<'import' | 'export'>('import');
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [importResult, setImportResult] = useState<{
    success: boolean;
    message: string;
    details?: string;
  } | null>(null);
  
  // Export options
  const [exportFormat, setExportFormat] = useState<'json' | 'csv' | 'xlsx'>('json');
  const [includeMetadata, setIncludeMetadata] = useState(true);
  const [includeContent, setIncludeContent] = useState(true);
  const [compress, setCompress] = useState(false);
  const [encrypt, setEncrypt] = useState(false);
  const [password, setPassword] = useState('');
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0 && files[0]) {
      handleFileSelect(files[0]);
    }
  };

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    setImportResult(null);
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0 && files[0]) {
      handleFileSelect(files[0]);
    }
  };

  const handleImport = async () => {
    if (!selectedFile) return;
    
    setIsProcessing(true);
    setImportResult(null);
    
    try {
      await onImport(selectedFile);
      setImportResult({
        success: true,
        message: 'Import completed successfully',
        details: `Imported ${selectedFile.name}`
      });
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error) {
      setImportResult({
        success: false,
        message: 'Import failed',
        details: error instanceof Error ? error.message : 'Unknown error occurred'
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleExport = async () => {
    setIsProcessing(true);
    
    try {
      await onExport(exportFormat);
      setImportResult({
        success: true,
        message: 'Export completed successfully',
        details: `Exported memories as ${exportFormat.toUpperCase()}`
      });
    } catch (error) {
      setImportResult({
        success: false,
        message: 'Export failed',
        details: error instanceof Error ? error.message : 'Unknown error occurred'
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const clearResult = () => {
    setImportResult(null);
  };

  return (
    <div className={cn("bg-card rounded-lg border", className)}>
      {/* Header with tabs */}
      <div className="border-b p-4">
        <div className="flex space-x-1">
          <button
            className={cn(
              "flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors",
              activeTab === 'import'
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:text-foreground hover:bg-muted"
            )}
            onClick={() => setActiveTab('import')}
          >
            <Upload className="h-4 w-4" />
            Import Memories
          </button>
          <button
            className={cn(
              "flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors",
              activeTab === 'export'
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:text-foreground hover:bg-muted"
            )}
            onClick={() => setActiveTab('export')}
          >
            <Download className="h-4 w-4" />
            Export Memories
          </button>
        </div>
      </div>

      {/* Content area */}
      <div className="p-6">
        {/* Result notification */}
        {importResult && (
          <div className={cn(
            "mb-4 p-4 rounded-md flex items-start gap-3",
            importResult.success 
              ? "bg-green-50 text-green-800 border border-green-200" 
              : "bg-red-50 text-red-800 border border-red-200"
          )}>
            {importResult.success ? (
              <Check className="h-5 w-5 mt-0.5 flex-shrink-0" />
            ) : (
              <AlertCircle className="h-5 w-5 mt-0.5 flex-shrink-0" />
            )}
            <div className="flex-1">
              <p className="font-medium">{importResult.message}</p>
              {importResult.details && (
                <p className="text-sm mt-1 opacity-90">{importResult.details}</p>
              )}
            </div>
            <button
              className="ml-2 opacity-70 hover:opacity-100"
              onClick={clearResult}
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        {/* Import tab */}
        {activeTab === 'import' && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium mb-2">Import Memories</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Import memories from a previously exported file. Supported formats: JSON, CSV, XLSX.
              </p>
            </div>

            {/* File upload area */}
            <div
              className={cn(
                "border-2 border-dashed rounded-lg p-8 text-center transition-colors",
                isDragging 
                  ? "border-primary bg-primary/5" 
                  : "border-muted-foreground/25 hover:border-muted-foreground/50"
              )}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".json,.csv,.xlsx"
                onChange={handleFileInputChange}
                className="hidden"
              />
              
              <FileText className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              
              {selectedFile ? (
                <div className="space-y-2">
                  <p className="font-medium">{selectedFile.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {(selectedFile.size / 1024).toFixed(2)} KB
                  </p>
                  <div className="flex justify-center gap-2">
                    <button
                      className={cn(
                        "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 px-4 py-2",
                        isProcessing && "opacity-50 cursor-not-allowed"
                      )}
                      onClick={handleImport}
                      disabled={isProcessing}
                    >
                      {isProcessing ? 'Importing...' : 'Import'}
                    </button>
                    <button
                      className={cn(
                        "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 hover:bg-accent hover:text-accent-foreground px-4 py-2"
                      )}
                      onClick={() => {
                        setSelectedFile(null);
                        if (fileInputRef.current) {
                          fileInputRef.current.value = '';
                        }
                      }}
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div className="space-y-2">
                  <p className="text-muted-foreground">
                    Drag and drop your file here, or{' '}
                    <button
                      className="text-primary hover:underline"
                      onClick={() => fileInputRef.current?.click()}
                    >
                      browse
                    </button>
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Maximum file size: 10MB
                  </p>
                </div>
              )}
            </div>

            {/* Import options */}
            <div className="space-y-3">
              <h4 className="font-medium">Import Options</h4>
              <div className="space-y-2 text-sm">
                <label className="flex items-center gap-2">
                  <input type="checkbox" defaultChecked />
                  <span>Overwrite existing memories with same ID</span>
                </label>
                <label className="flex items-center gap-2">
                  <input type="checkbox" defaultChecked />
                  <span>Validate data before importing</span>
                </label>
                <label className="flex items-center gap-2">
                  <input type="checkbox" />
                  <span>Assign to current user</span>
                </label>
              </div>
            </div>
          </div>
        )}

        {/* Export tab */}
        {activeTab === 'export' && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium mb-2">Export Memories</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Export your memories for backup or sharing. Choose your preferred format and options.
              </p>
            </div>

            {/* Export format */}
            <div className="space-y-3">
              <h4 className="font-medium">Export Format</h4>
              <div className="grid grid-cols-3 gap-3">
                {(['json', 'csv', 'xlsx'] as const).map((format) => (
                  <label
                    key={format}
                    className={cn(
                      "flex flex-col items-center justify-center p-4 border rounded-md cursor-pointer transition-colors",
                      exportFormat === format
                        ? "border-primary bg-primary/5"
                        : "border-muted hover:border-muted-foreground/50"
                    )}
                  >
                    <input
                      type="radio"
                      name="format"
                      value={format}
                      checked={exportFormat === format}
                      onChange={() => setExportFormat(format)}
                      className="sr-only"
                    />
                    <FileText className="h-8 w-8 mb-2 text-muted-foreground" />
                    <span className="font-medium uppercase">{format}</span>
                    <span className="text-xs text-muted-foreground mt-1">
                      {format === 'json' && 'Full data structure'}
                      {format === 'csv' && 'Tabular format'}
                      {format === 'xlsx' && 'Spreadsheet format'}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            {/* Export options */}
            <div className="space-y-3">
              <h4 className="font-medium">Export Options</h4>
              <div className="space-y-2 text-sm">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={includeMetadata}
                    onChange={(e) => setIncludeMetadata(e.target.checked)}
                  />
                  <span>Include metadata</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={includeContent}
                    onChange={(e) => setIncludeContent(e.target.checked)}
                  />
                  <span>Include content</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={compress}
                    onChange={(e) => setCompress(e.target.checked)}
                  />
                  <span>Compress file</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={encrypt}
                    onChange={(e) => setEncrypt(e.target.checked)}
                  />
                  <span>Encrypt file</span>
                </label>
                {encrypt && (
                  <div className="ml-6">
                    <input
                      type="password"
                      placeholder="Enter password..."
                      className="px-3 py-2 text-sm bg-background border rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                    />
                  </div>
                )}
              </div>
            </div>

            {/* Export button */}
            <div className="flex justify-center">
              <button
                className={cn(
                  "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 px-6 py-2 gap-2",
                  isProcessing && "opacity-50 cursor-not-allowed"
                )}
                onClick={handleExport}
                disabled={isProcessing || (encrypt && !password.trim())}
              >
                <Download className="h-4 w-4" />
                {isProcessing ? 'Exporting...' : 'Export Memories'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default MemoryImportExport;