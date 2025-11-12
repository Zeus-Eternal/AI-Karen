"use client";

/**
 * Bulk User Operations Component (Prod-Grade)
 *
 * Provides bulk operations for user management including export, import,
 * status changes, role modifications, and deletion with progress tracking.
 *
 * Requirements: 4.5, 4.6, 7.3
 */

import React, { useCallback, useMemo, useState } from "react";
import { useRole } from "@/hooks/useRole";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import type { AdminApiResponse, BulkUserOperation } from "@/types/admin";
import { Download, UploadCloud, AlertTriangle } from "lucide-react";

type GenericAdminResponse = AdminApiResponse<Record<string, unknown>>;

export interface BulkUserOperationsProps {
  selectedUserIds: string[];
  onOperationComplete: () => void;
  onCancel: () => void;
  className?: string;
}

export type OperationType = "activate" | "deactivate" | "delete" | "export" | "import" | "role_change";
export type RoleTarget = "admin" | "user";
export type ExportFormat = "csv" | "json" | "xlsx";

export interface OperationProgress {
  total: number;
  completed: number;
  failed: number;
  errors: string[];
}

export function BulkUserOperations({
  selectedUserIds,
  onOperationComplete,
  onCancel,
  className = ""
}: BulkUserOperationsProps) {
  const { hasRole } = useRole();
  const { toast } = useToast();

  const [selectedOperation, setSelectedOperation] = useState<OperationType>("activate");
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState<OperationProgress | null>(null);

  const [newRole, setNewRole] = useState<RoleTarget>("user");
  const [exportFormat, setExportFormat] = useState<ExportFormat>("csv");
  const [importFile, setImportFile] = useState<File | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const operations = useMemo(
    () => [
      { id: "activate", label: "Activate Users", description: "Enable selected user accounts", dangerous: false },
      { id: "deactivate", label: "Deactivate Users", description: "Disable selected user accounts", dangerous: false },
      { id: "role_change", label: "Change Role", description: "Update role for selected users", dangerous: false },
      { id: "export", label: "Export Users", description: "Download user data in selected format", dangerous: false },
      { id: "delete", label: "Delete Users", description: "Permanently remove selected users", dangerous: true },
      { id: "import", label: "Import Users", description: "Upload CSV/JSON and create users", dangerous: false }
    ],
    []
  );

  const canPerformOperation = useCallback(
    (operation: OperationType) => {
      switch (operation) {
        case "role_change":
        case "delete":
          return hasRole("super_admin");
        case "activate":
        case "deactivate":
        case "export":
        case "import":
          return hasRole("admin");
        default:
          return false;
      }
    },
    [hasRole]
  );

  const beginProgress = useCallback(
    (count: number) => setProgress({ total: count, completed: 0, failed: 0, errors: [] }),
    []
  );

  const completeProgress = useCallback(() => {
    setProgress((p) => (p ? { ...p, completed: p.total, failed: 0 } : p));
  }, []);

  const failProgress = useCallback((message: string) => {
    setProgress((p) => (p ? { ...p, failed: p.total - p.completed, errors: [...p.errors, message] } : p));
  }, []);

  const handleImport = useCallback(async () => {
    if (!canPerformOperation("import")) {
      toast({ title: "Insufficient permissions", variant: "destructive" });
      return;
    }
    if (!importFile) {
      toast({ title: "No file selected", description: "Choose a CSV or JSON file to import.", variant: "destructive" });
      return;
    }

    setLoading(true);
    beginProgress(1);

    try {
      const formData = new FormData();
      formData.append("file", importFile);
      formData.append("format", importFile.name.endsWith(".json") ? "json" : "csv");
      formData.append("skip_duplicates", "true");
      formData.append("send_invitations", "true");
      formData.append("default_role", "user");

      const res = await fetch("/api/admin/users/import", { method: "POST", body: formData });
      const data = await safeJson<GenericAdminResponse>(res);

      if (!res.ok || !data?.success) {
        throw new Error(data?.error?.message || "Import failed");
      }

      completeProgress();
      toast({
        title: "Import completed",
        description: `${data.data?.imported_count ?? 0} user(s) imported successfully.`
      });
      onOperationComplete();
    } catch (error) {
      const msg = error instanceof Error ? error.message : "Import failed";
      failProgress(msg);
      toast({ title: "Import failed", description: msg, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  }, [beginProgress, canPerformOperation, completeProgress, failProgress, importFile, onOperationComplete, toast]);

  const handleBulkOperation = useCallback(async () => {
    if (!canPerformOperation(selectedOperation)) {
      toast({ title: "Insufficient permissions", variant: "destructive" });
      return;
    }

    if (selectedOperation !== "import" && selectedUserIds.length === 0) {
      toast({ title: "No users selected", description: "Select at least one user to proceed.", variant: "destructive" });
      return;
    }

    if (selectedOperation === "delete" && !confirmDelete) {
      toast({
        title: "Confirmation required",
        description: "Check the confirmation box before deleting users.",
        variant: "destructive"
      });
      return;
    }

    if (selectedOperation === "import") {
      await handleImport();
      return;
    }

    setLoading(true);
    beginProgress(selectedUserIds.length);

    try {
      const payload: BulkUserOperation = {
        operation: selectedOperation,
        user_ids: selectedUserIds,
        parameters: {}
      };

      if (selectedOperation === "role_change") {
        payload.parameters = { new_role: newRole };
      } else if (selectedOperation === "export") {
        payload.parameters = { format: exportFormat };
      }

      const res = await fetch("/api/admin/users/bulk", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const data = await safeJson<GenericAdminResponse>(res);

      if (!res.ok || !data?.success) {
        throw new Error(data?.error?.message || "Bulk operation failed");
      }

      if (selectedOperation === "export" && data.data?.download_url) {
        const link = document.createElement("a");
        link.href = data.data.download_url as string;
        link.download = (data.data.filename as string) || `users_export.${exportFormat}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }

      completeProgress();
      toast({
        title: "Bulk operation completed",
        description:
          selectedOperation === "export"
            ? "Export is ready."
            : `${operations.find((o) => o.id === selectedOperation)?.label} completed successfully.`
      });

      setTimeout(() => onOperationComplete(), 600);
    } catch (error) {
      const msg = error instanceof Error ? error.message : "Operation failed";
      failProgress(msg);
      toast({ title: "Bulk operation failed", description: msg, variant: "destructive" });
    } finally {
      setLoading(false);
    }
  }, [
    beginProgress,
    canPerformOperation,
    completeProgress,
    confirmDelete,
    exportFormat,
    failProgress,
    handleImport,
    newRole,
    onOperationComplete,
    handleImport,
    operations,
    selectedOperation,
    selectedUserIds,
    toast
  ]);

  /* ------------------------------ UI Builders ------------------------------ */

  const renderOperationForm = () => {
    switch (selectedOperation) {
      case "role_change":
        return (
          <div className="space-y-2">
            <Label htmlFor="new_role">New Role</Label>
            <Select value={newRole} onValueChange={(v) => setNewRole(v as RoleTarget)}>
              <SelectTrigger id="new_role" className="w-52">
                <SelectValue placeholder="Select role" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="user">User</SelectItem>
                {hasRole("super_admin") && <SelectItem value="admin">Admin</SelectItem>}
              </SelectContent>
            </Select>
          </div>
        );

      case "export":
        return (
          <div className="space-y-2">
            <Label htmlFor="export_format">Export Format</Label>
            <Select value={exportFormat} onValueChange={(v) => setExportFormat(v as ExportFormat)}>
              <SelectTrigger id="export_format" className="w-52">
                <SelectValue placeholder="Select format" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="csv">CSV</SelectItem>
                <SelectItem value="json">JSON</SelectItem>
                <SelectItem value="xlsx">Excel (XLSX)</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-xs text-gray-500">For large datasets, export will stream the file server-side.</p>
          </div>
        );

      case "delete":
        return (
          <div className="space-y-4">
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="h-5 w-5 text-red-500 mt-0.5" />
                <div>
                  <h4 className="text-sm font-medium text-red-800">Warning: Permanent Deletion</h4>
                  <p className="text-sm text-red-700 mt-1">
                    This action will permanently delete {selectedUserIds.length} user(s) and cannot be undone.
                    All user data, including history and associated records, will be removed.
                  </p>
                </div>
              </div>
            </div>
            <div className="flex items-center">
              <Input
                id="confirm_delete"
                type="checkbox"
                checked={confirmDelete}
                onChange={(e) => setConfirmDelete(e.currentTarget.checked)}
                className="h-4 w-4 mr-2"
              />
              <Label htmlFor="confirm_delete">I understand the consequences of deleting these users.</Label>
            </div>
          </div>
        );

      case "import":
        return renderImportSection();

      default:
        return null;
    }
  };

  const renderImportSection = () => (
    <div className="border rounded-md p-4">
      <h3 className="text-base font-semibold mb-3 flex items-center gap-2">
        <UploadCloud className="h-4 w-4" /> Import Users
      </h3>
      <div className="space-y-3">
        <div>
          <Label htmlFor="import_file">Select File (CSV or JSON)</Label>
          <Input
            id="import_file"
            type="file"
            accept=".csv,.json"
            onChange={(e) => setImportFile(e.target.files?.[0] || null)}
            disabled={loading}
          />
          <p className="text-xs text-gray-500 mt-1">
            CSV: <code>email, full_name, role (optional)</code>. JSON: array of user objects.
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={handleImport} disabled={!importFile || loading}>
            {loading ? "Importing..." : "Import Users"}
          </Button>
          {importFile && (
            <Button
              type="button"
              variant="outline"
              onClick={() => setImportFile(null)}
              disabled={loading}
              title="Clear file"
            >
              Clear
            </Button>
          )}
        </div>
      </div>
    </div>
  );

  const renderProgress = () => {
    if (!progress) return null;
    const pct = progress.total > 0 ? Math.round((progress.completed / progress.total) * 100) : 0;
    return (
      <div className="mt-2 p-4 bg-blue-50 border border-blue-200 rounded-md">
        <h4 className="text-sm font-medium text-blue-900 mb-2">Operation Progress</h4>
        <div className="w-full bg-blue-200 rounded-full h-2 mb-2">
          <div className="bg-blue-600 h-2 rounded-full transition-all duration-300" style={{ width: `${pct}%` }} />
        </div>
        <div className="flex justify-between text-sm text-blue-800">
          <span>
            Completed: {progress.completed}/{progress.total}
          </span>
          <span>Failed: {progress.failed}</span>
        </div>
        {progress.errors.length > 0 && (
          <div className="mt-2">
            <p className="text-sm font-medium text-red-800">Errors:</p>
            <ul className="text-sm text-red-700 list-disc list-inside">
              {progress.errors.map((e, i) => (
                <li key={i}>{e}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  /* -------------------------------- Render -------------------------------- */

  return (
    <div className={`bg-white shadow rounded-lg ${className}`}>
      <div className="px-6 py-4 border-b border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
          Bulk Operations
          {selectedOperation === "export" && <Download className="h-4 w-4 text-gray-500" />}
        </h2>
        <p className="text-sm text-gray-600 mt-1">
          {selectedOperation === "import"
            ? "Import new users from a file."
            : `Perform operations on ${selectedUserIds.length} selected user(s).`}
        </p>
      </div>

      <div className="px-6 py-4 space-y-6">
        {/* Operation selection */}
        <div className="space-y-2">
          <Label htmlFor="operation">Operation</Label>
          <Select
            value={selectedOperation}
            onValueChange={(v) => {
              setSelectedOperation(v as OperationType);
              // Reset delete confirmation when switching away
              if (v !== "delete") setConfirmDelete(false);
            }}
          >
            <SelectTrigger id="operation" className="w-64">
              <SelectValue placeholder="Choose an operation" />
            </SelectTrigger>
            <SelectContent>
              {operations.map((op) => (
                <SelectItem key={op.id} value={op.id} disabled={!canPerformOperation(op.id as OperationType)}>
                  <span className={op.dangerous ? "text-red-600 font-medium" : ""}>{op.label}</span>
                  {!canPerformOperation(op.id as OperationType) && " (No permission)"}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <p className="text-xs text-gray-500">
            Only operations you have permission for are enabled. Role/Deletion require super admin.
          </p>
        </div>

        {/* Operation-specific form */}
        {renderOperationForm()}

        {/* Progress */}
        {renderProgress()}

        {/* Action buttons */}
        <div className="flex justify-end gap-2 pt-4 border-t border-gray-200">
          <Button
            onClick={onCancel}
            variant="outline"
            disabled={loading}
            aria-label="Cancel bulk operation"
          >
            Cancel
          </Button>
          <Button
            onClick={handleBulkOperation}
            disabled={
              loading ||
              !canPerformOperation(selectedOperation) ||
              (selectedOperation === "delete" && !confirmDelete) ||
              (selectedOperation !== "import" && selectedUserIds.length === 0)
            }
            aria-label="Execute bulk operation"
            className={
              selectedOperation === "delete"
                ? "bg-red-600 hover:bg-red-700 focus:ring-red-500"
                : undefined
            }
          >
            {loading ? "Processing..." : `Execute ${operations.find((o) => o.id === selectedOperation)?.label}`}
          </Button>
        </div>
      </div>
    </div>
  );
}

/* --------------------------------- Utils --------------------------------- */

async function safeJson<T>(res: Response): Promise<T | null> {
  try {
    return (await res.json()) as T;
  } catch {
    return null;
  }
}
