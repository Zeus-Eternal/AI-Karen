/**
 * Enhanced Bulk User Operations Component
 *
 * Bulk operations interface with progress indicators, cancellation support,
 * comprehensive error handling, and accessibility features.
 *
 * Requirements: 7.2, 7.5, 7.7
 */
"use client";

import React, { useCallback, useRef, useState } from "react";
import { useRole } from "@/hooks/useRole";
import ErrorDisplay from "@/components/ui/error-display";
import { BulkOperationConfirmation } from "@/components/ui/confirmation-dialog";
import {
  ProgressIndicator,
  type BulkOperationProgress,
} from "@/components/ui/progress-indicator";
import { useKeyboardNavigation } from "@/lib/accessibility/keyboard-navigation";
import { useAriaLiveRegion, AriaManager } from "@/lib/accessibility/aria-helpers";
import AdminErrorHandler, {
  type AdminError,
} from "@/lib/errors/admin-error-handler";
import { Button } from "@/components/ui/button";
import {
  Download,
  UserX,
  UserCheck,
  Trash2,
  Mail,
  FileText,
} from "lucide-react";

interface EnhancedBulkUserOperationsProps {
  selectedUserIds: string[];
  onOperationComplete: () => void;
  onCancel: () => void;
  className?: string;
}

type BulkOperation =
  | "activate"
  | "deactivate"
  | "delete"
  | "export"
  | "send_welcome_email"
  | "reset_password"
  | "verify_email";

interface BulkOperationConfig {
  id: BulkOperation;
  label: string;
  description: string;
  icon: React.ReactNode;
  confirmationRequired: boolean;
  destructive: boolean;
  requiresSuperAdmin?: boolean;
  estimatedTimePerItem?: number; // milliseconds
}

const bulkOperations: BulkOperationConfig[] = [
  {
    id: "activate",
    label: "Activate Users",
    description: "Enable login access for selected users",
    icon: <UserCheck className="h-5 w-5" />,
    confirmationRequired: true,
    destructive: false,
    estimatedTimePerItem: 500,
  },
  {
    id: "deactivate",
    label: "Deactivate Users",
    description: "Disable login access for selected users",
    icon: <UserX className="h-5 w-5" />,
    confirmationRequired: true,
    destructive: true,
    estimatedTimePerItem: 500,
  },
  {
    id: "delete",
    label: "Delete Users",
    description: "Permanently remove selected user accounts",
    icon: <Trash2 className="h-5 w-5" />,
    confirmationRequired: true,
    destructive: true,
    requiresSuperAdmin: true,
    estimatedTimePerItem: 1000,
  },
  {
    id: "export",
    label: "Export Users",
    description: "Download user data as CSV file",
    icon: <Download className="h-5 w-5" />,
    confirmationRequired: false,
    destructive: false,
    estimatedTimePerItem: 100,
  },
  {
    id: "send_welcome_email",
    label: "Send Welcome Emails",
    description: "Send welcome emails to selected users",
    icon: <Mail className="h-5 w-5" />,
    confirmationRequired: true,
    destructive: false,
    estimatedTimePerItem: 2000,
  },
  {
    id: "reset_password",
    label: "Reset Passwords",
    description: "Send password reset emails to selected users",
    icon: <FileText className="h-5 w-5" />,
    confirmationRequired: true,
    destructive: false,
    estimatedTimePerItem: 1500,
  },
  {
    id: "verify_email",
    label: "Mark as Verified",
    description: "Mark selected users as email verified",
    icon: <UserCheck className="h-5 w-5" />,
    confirmationRequired: true,
    destructive: false,
    estimatedTimePerItem: 300,
  },
];

export function EnhancedBulkUserOperations({
  selectedUserIds,
  onOperationComplete,
  onCancel,
  className = "",
}: EnhancedBulkUserOperationsProps) {
  const { hasRole } = useRole();
  const containerRef = useRef<HTMLDivElement>(null);
  const { announce } = useAriaLiveRegion();

  // State
  const [selectedOperation, setSelectedOperation] = useState<BulkOperation | null>(null);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [progress, setProgress] = useState<BulkOperationProgress | null>(null);
  const [error, setError] = useState<AdminError | null>(null);
  const [abortController, setAbortController] = useState<AbortController | null>(null);

  // Keyboard navigation
  useKeyboardNavigation(containerRef, {
    enableArrowKeys: true,
    enableHomeEndKeys: true,
    enableEscapeKey: true,
    onEscape: () => {
      if (showConfirmation) {
        setShowConfirmation(false);
      } else if (!progress || progress.status !== "running") {
        onCancel();
      }
    },
  });

  const getAvailableOperations = () => {
    return bulkOperations.filter((op) => {
      if (op.requiresSuperAdmin && !hasRole("super_admin")) return false;
      return true;
    });
  };

  const estimateOperationTime = (operation: BulkOperationConfig) => {
    const timePerItem = operation.estimatedTimePerItem ?? 1000;
    const totalTime = timePerItem * selectedUserIds.length;
    if (totalTime < 60000) {
      return `~${Math.ceil(totalTime / 1000)} seconds`;
    }
    return `~${Math.ceil(totalTime / 60000)} minutes`;
  };

  const handleOperationSelect = (operationId: BulkOperation) => {
    const operation = bulkOperations.find((op) => op.id === operationId);
    if (!operation) return;
    setSelectedOperation(operationId);
    if (operation.confirmationRequired) {
      setShowConfirmation(true);
      announce(`Selected ${operation.label}. Confirmation required.`);
    } else {
      void executeOperation(operationId);
    }
  };

  const executeOperation = useCallback(
    async (operationId: BulkOperation) => {
      const operation = bulkOperations.find((op) => op.id === operationId);
      if (!operation) return;

      try {
        setShowConfirmation(false);
        setError(null);

        // Create abort controller for cancellation
        const controller = new AbortController();
        setAbortController(controller);

        // Initialize progress
        const initialProgress: BulkOperationProgress = {
          operationId: `bulk-${operationId}-${Date.now()}`,
          operation: operation.label,
          totalItems: selectedUserIds.length,
          processedItems: 0,
          successfulItems: 0,
          failedItems: 0,
          status: "running",
          startTime: new Date(),
          steps: [
            {
              id: "initialize",
              label: "Initializing operation",
              status: "running",
              progress: 0,
            },
          ],
          errors: [],
          canCancel: true,
        };
        setProgress(initialProgress);

        announce(
          `Starting ${operation.label} for ${selectedUserIds.length} users`,
          "assertive"
        );

        // Execute operation
        const response = await fetch("/api/admin/users/bulk", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            operation: operationId,
            user_ids: selectedUserIds,
          }),
          signal: controller.signal,
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw AdminErrorHandler.fromHttpError(response.status, errorData);
        }

        // Stream NDJSON progress updates
        if (response.body) {
          const reader = response.body.getReader();
          const decoder = new TextDecoder();

          try {
            // eslint-disable-next-line no-constant-condition
            while (true) {
              const { done, value } = await reader.read();
              if (done) break;

              const chunk = decoder.decode(value, { stream: true });
              const lines = chunk
                .split("\n")
                .map((l) => l.trim())
                .filter(Boolean);

              for (const line of lines) {
                try {
                  const update = JSON.parse(line);

                  setProgress((prev) => {
                    if (!prev) return prev;

                    const updated: BulkOperationProgress = {
                      ...prev,
                      ...update,
                      endTime:
                        update.status === "completed" ||
                        update.status === "failed" ||
                        update.status === "cancelled"
                          ? new Date()
                          : prev.endTime,
                    };

                    if (
                      typeof update.processedItems === "number" &&
                      update.processedItems > 0 &&
                      update.processedItems % 10 === 0
                    ) {
                      AriaManager.announceProgress(
                        update.processedItems,
                        updated.totalItems,
                        updated.operation
                      );
                    }

                    return updated;
                  });
                } catch {
                  // ignore malformed lines
                }
              }
            }
          } finally {
            reader.releaseLock();
          }
        }

        // Mark completed
        setProgress((prev) =>
          prev
            ? {
                ...prev,
                status: "completed",
                endTime: new Date(),
              }
            : null
        );

        const success = (prev: BulkOperationProgress | null) =>
          prev?.successfulItems ?? 0;
        const fail = (prev: BulkOperationProgress | null) =>
          prev?.failedItems ?? 0;

        AriaManager.announceBulkOperationResult(
          operation.label,
          success(progress),
          fail(progress),
          selectedUserIds.length
        );
      } catch (err) {
        if (err instanceof Error && err.name === "AbortError") {
          setProgress((prev) =>
            prev
              ? {
                  ...prev,
                  status: "cancelled",
                  endTime: new Date(),
                }
              : null
          );
          announce(`${operation.label} was cancelled`, "assertive");
          return;
        }

        const adminError =
          err instanceof Error
            ? AdminErrorHandler.fromNetworkError(err)
            : (err as AdminError);

        AdminErrorHandler.logError(adminError, {
          operation: `bulk_${operationId}`,
          resource: `${selectedUserIds.length}_users`,
          timestamp: new Date(),
        });

        setError(adminError);
        setProgress((prev) =>
          prev
            ? {
                ...prev,
                status: "failed",
                endTime: new Date(),
              }
            : null
        );
        announce(`${operation.label} failed: ${adminError.message}`, "assertive");
      } finally {
        setAbortController(null);
      }
    },
    [announce, selectedUserIds, progress]
  );

  const handleCancelOperation = () => {
    if (abortController) {
      abortController.abort();
      announce("Cancelling operation...", "assertive");
    }
  };

  const handleCloseProgress = () => {
    setProgress(null);
    setSelectedOperation(null);
    onOperationComplete();
  };

  const renderOperationButton = (operation: BulkOperationConfig) => {
    const isDisabled = progress?.status === "running";
    return (
      <Button
        key={operation.id}
        onClick={() => handleOperationSelect(operation.id)}
        disabled={isDisabled}
        className={`flex items-center p-4 border rounded-lg text-left transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed ${
          operation.destructive
            ? "border-red-200 hover:bg-red-50 focus:ring-red-500"
            : "border-gray-200 hover:bg-gray-50"
        }`}
        aria-describedby={`${operation.id}-description`}
        variant="outline"
      >
        <div
          className={`flex-shrink-0 ${
            operation.destructive ? "text-red-600" : "text-blue-600"
          }`}
          aria-hidden="true"
        >
          {operation.icon}
        </div>
        <div className="ml-3 flex-1">
          <h3 className="text-sm font-medium text-gray-900 md:text-base lg:text-lg">
            {operation.label}
          </h3>
          <p
            id={`${operation.id}-description`}
            className="text-sm text-gray-600 mt-1 md:text-base lg:text-lg"
          >
            {operation.description}
          </p>
          <p className="text-xs text-gray-500 mt-1 sm:text-sm md:text-base">
            Estimated time: {estimateOperationTime(operation)}
          </p>
        </div>
      </Button>
    );
  };

  if (selectedUserIds.length === 0) {
    return (
      <div className={`bg-white p-6 rounded-lg shadow ${className}`}>
        <div className="text-center">
          <h2 className="text-lg font-medium text-gray-900 mb-2">
            No Users Selected
          </h2>
        </div>
        <p className="text-gray-600 mb-4">
          Please select one or more users to perform bulk operations.
        </p>
        <div className="text-center">
          <Button
            onClick={onCancel}
            className="px-4 py-2"
            aria-label="Close bulk operations"
            variant="outline"
          >
            Back to Users
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow ${className}`} ref={containerRef}>
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-medium text-gray-900">
              Bulk Operations
            </h2>
            <p className="text-sm text-gray-600 mt-1 md:text-base lg:text-lg">
              {selectedUserIds.length} user
              {selectedUserIds.length === 1 ? "" : "s"} selected
            </p>
          </div>
          <Button
            onClick={onCancel}
            className="text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded"
            aria-label="Close bulk operations"
            variant="ghost"
          >
            ×
          </Button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-4 border-b border-gray-200">
          <ErrorDisplay
            error={error}
            onRetry={
              selectedOperation ? () => executeOperation(selectedOperation) : undefined
            }
            onDismiss={() => setError(null)}
            compact={true}
          />
        </div>
      )}

      {/* Progress Indicator */}
      {progress && (
        <div className="p-4 border-b border-gray-200">
          <ProgressIndicator
            progress={progress}
            onCancel={
              progress.canCancel && progress.status === "running"
                ? handleCancelOperation
                : undefined
            }
            onClose={progress.status !== "running" ? handleCloseProgress : undefined}
            showDetails={true}
          />
        </div>
      )}

      {/* Operation Selection */}
      {!progress && (
        <div className="p-6">
          <h3 className="text-sm font-medium text-gray-900 mb-4 md:text-base lg:text-lg">
            Select an operation to perform:
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {getAvailableOperations().map(renderOperationButton)}
          </div>
          <div className="mt-6 flex justify-end space-x-3">
            <Button
              onClick={onCancel}
              aria-label="Back to Users"
              variant="outline"
            >
              Back to Users
            </Button>
          </div>
        </div>
      )}

      {/* Confirmation Dialog */}
      {showConfirmation && selectedOperation && (
        <BulkOperationConfirmation
          isOpen={true}
          onClose={() => setShowConfirmation(false)}
          onConfirm={() => executeOperation(selectedOperation)}
          operation={
            bulkOperations.find((op) => op.id === selectedOperation)?.label ||
            "Operation"
          }
          itemCount={selectedUserIds.length}
          loading={false}
        />
      )}
    </div>
  );
}

export default EnhancedBulkUserOperations;
