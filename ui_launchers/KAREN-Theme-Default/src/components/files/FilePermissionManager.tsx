// ui_launchers/KAREN-Theme-Default/src/components/files/FilePermissionManager.tsx
"use client";

import React, { useState, useMemo, useCallback } from "react";
import { ErrorBoundary, type ErrorFallbackProps } from "@/components/error-handling/ErrorBoundary";

import { AgGridReact } from "ag-grid-react";
import { ColDef, ICellRendererParams, SelectionChangedEvent } from "ag-grid-community";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import "ag-grid-community/styles/ag-grid.css";
import "ag-grid-community/styles/ag-theme-alpine.css";

import {
  Eye,
  Pencil as Edit,
  Trash2,
  Download,
  Users,
  Settings,
  User as UserIcon,
  Check,
  X,
  Shield,
  Plus,
  Unlock,
  Lock,
  AlertTriangle,
  RefreshCw,
} from "lucide-react";
import { cn } from "@/lib/utils";

/* ----------------------------------------------------------------------------
 * Types
 * ---------------------------------------------------------------------------*/
export type PermissionType =
  | "read"
  | "write"
  | "delete"
  | "download"
  | "share"
  | "admin";

export interface FilePermission {
  id: string;
  file_id: string;
  user_id?: string;
  role?: string;
  permission_type: PermissionType;
  granted_by: string;
  granted_at: string;
  expires_at?: string;
  conditions?: Record<string, unknown>;
  is_active: boolean;
}

export interface PermissionRule {
  id: string;
  name: string;
  description: string;
  file_types: string[];
  user_roles: string[];
  permissions: PermissionType[];
  conditions: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface FilePermissionManagerProps {
  fileId: string;
  fileName: string;
  currentPermissions: FilePermission[];
  availableUsers: Array<{ id: string; name: string; email?: string; roles: string[] }>;
  availableRoles: Array<{ id: string; name: string; description?: string }>;
  permissionRules: PermissionRule[];
  onPermissionUpdate: (permissions: FilePermission[]) => void;
  onRuleUpdate: (rules: PermissionRule[]) => void;
  className?: string;
  readOnly?: boolean;
}

/* ----------------------------------------------------------------------------
 * Constants & Utilities
 * ---------------------------------------------------------------------------*/
const PERMISSION_TYPES: Array<{
  value: PermissionType;
  label: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  description: string;
}> = [
  { value: "read", label: "Read", icon: Eye, description: "View file content" },
  {
    value: "write",
    label: "Write",
    icon: Edit,
    description: "Modify file content",
  },
  {
    value: "delete",
    label: "Delete",
    icon: Trash2,
    description: "Delete the file",
  },
  {
    value: "download",
    label: "Download",
    icon: Download,
    description: "Download the file",
  },
  {
    value: "share",
    label: "Share",
    icon: Users,
    description: "Share with others",
  },
  {
    value: "admin",
    label: "Admin",
    icon: Settings,
    description: "Manage permissions",
  },
];

const genId = (prefix: string) => {
  try {
    return `${prefix}_${crypto.randomUUID()}`;
  } catch {
    return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 11)}`;
  }
};

const formatDate = (dateString: string): string => {
  try {
    const d = new Date(dateString);
    if (Number.isNaN(d.getTime())) return dateString;
    return d.toLocaleString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return dateString;
  }
};

const PermissionManagerFallback: React.FC<ErrorFallbackProps> = ({
  error,
  resetError,
}) => (
  <Card className="border-destructive/30 bg-destructive/5">
    <CardHeader>
      <CardTitle className="text-destructive text-lg">Permissions unavailable</CardTitle>
      <p className="text-sm text-muted-foreground">
        {error.message || "Failed to render the permission manager."}
      </p>
    </CardHeader>
    <CardContent className="flex items-center gap-3">
      <Button size="sm" variant="outline" onClick={resetError}>
        Retry
      </Button>
    </CardContent>
  </Card>
);

/* ----------------------------------------------------------------------------
 * Cell Renderers
 * ---------------------------------------------------------------------------*/
const PermissionTypeRenderer: React.FC<{ value: PermissionType }> = ({
  value,
}) => {
  const permission = PERMISSION_TYPES.find((p) => p.value === value);
  if (!permission) return <span>{value}</span>;
  const Icon = permission.icon;
  return (
    <div className="flex items-center gap-2">
      <Icon className="h-4 w-4" aria-hidden />
      <span>{permission.label}</span>
    </div>
  );
};

const UserRenderer: React.FC<{ data?: FilePermission | null }> = ({ data }) => {
  if (!data) {
    return <span>-</span>;
  }
  if (data.user_id) {
    const label = data.user_id;
    return (
      <div className="flex items-center gap-2">
        <UserIcon className="h-4 w-4" aria-hidden />
        <span>{label}</span>
      </div>
    );
  }
  if (data.role) {
    return (
      <div className="flex items-center gap-2">
        <Users className="h-4 w-4" aria-hidden />
        <Badge variant="outline">{data.role}</Badge>
      </div>
    );
  }
  return <span>-</span>;
};

const StatusRenderer: React.FC<{ data?: FilePermission | null }> = ({ data }) => {
  if (!data) {
    return null;
  }
  const isExpired = !!(data.expires_at && new Date(data.expires_at) < new Date());
  const isActive = data.is_active && !isExpired;
  return (
    <div className="flex items-center gap-2">
      {isActive ? (
        <Badge variant="secondary" className="bg-green-100 text-green-800">
          <Check className="mr-1 h-3 w-3" aria-hidden />
          Active
        </Badge>
      ) : (
        <Badge variant="secondary" className="bg-red-100 text-red-800">
          <X className="mr-1 h-3 w-3" aria-hidden />
          {isExpired ? "Expired" : "Inactive"}
        </Badge>
      )}
    </div>
  );
};

const ActionsRenderer: React.FC<{
  data?: FilePermission | null;
  onEdit: (permission: FilePermission) => void;
  onDelete: (permissionId: string) => void;
  readOnly: boolean;
}> = ({ data, onEdit, onDelete, readOnly }) => {
  if (readOnly || !data) return null;
  return (
    <div className="flex items-center gap-1">
      <Button
        variant="ghost"
        size="sm"
        onClick={() => onEdit(data)}
        className="h-8 w-8 p-0"
        aria-label="Edit permission"
        title="Edit permission"
      >
        <Edit className="h-4 w-4" aria-hidden />
      </Button>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => onDelete(data.id)}
        className="h-8 w-8 p-0 text-destructive hover:text-destructive"
        aria-label="Delete permission"
        title="Delete permission"
      >
        <Trash2 className="h-4 w-4" aria-hidden />
      </Button>
    </div>
  );
};

const NoRowsOverlay: React.FC = () => (
  <div className="flex h-full flex-col items-center justify-center text-muted-foreground">
    <Shield className="mb-2 h-12 w-12" aria-hidden />
    <p>No permissions configured</p>
  </div>
);

/* ----------------------------------------------------------------------------
 * Component
 * ---------------------------------------------------------------------------*/
export const FilePermissionManager: React.FC<FilePermissionManagerProps> = ({
  fileId,
  fileName,
  currentPermissions,
  availableUsers,
  availableRoles,
  permissionRules, // currently unused in UI (reserved for rule editor tab)
  onPermissionUpdate,
  onRuleUpdate,
  className,
  readOnly = false,
}) => {
  const [selectedPermissions, setSelectedPermissions] = useState<FilePermission[]>([]);
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [editingPermission, setEditingPermission] = useState<FilePermission | null>(null);
  const [newPermission, setNewPermission] = useState<Partial<FilePermission>>({
    permission_type: "read",
    is_active: true,
  });

  const handleEditPermission = useCallback((permission: FilePermission) => {
    setEditingPermission(permission);
    setIsEditDialogOpen(true);
  }, []);

  const handleDeletePermission = useCallback(
    (permissionId: string) => {
      const updated = currentPermissions.filter((p) => p.id !== permissionId);
      onPermissionUpdate(updated);
    },
    [currentPermissions, onPermissionUpdate]
  );

  const onSelectionChanged = useCallback((event: SelectionChangedEvent) => {
    const selectedRows = event.api.getSelectedRows() as FilePermission[];
    setSelectedPermissions(selectedRows);
  }, []);

  const permissionColumns = useMemo<ColDef<FilePermission>[]>(
    () => [
      {
        headerName: "User/Role",
        flex: 1,
        minWidth: 150,
        cellRenderer: (params: ICellRendererParams<FilePermission>) => (
          <UserRenderer data={params.data ?? null} />
        ),
        filter: "agTextColumnFilter",
      },
      {
        headerName: "Permission",
        field: "permission_type",
        width: 140,
        cellRenderer: (params: ICellRendererParams<FilePermission>) => (
          <PermissionTypeRenderer value={params.data?.permission_type ?? "read"} />
        ),
        filter: "agSetColumnFilter",
      },
      {
        headerName: "Status",
        width: 130,
        cellRenderer: (params: ICellRendererParams<FilePermission>) => (
          <StatusRenderer data={params.data ?? null} />
        ),
        filter: "agSetColumnFilter",
      },
      {
        headerName: "Granted By",
        field: "granted_by",
        width: 150,
        filter: "agTextColumnFilter",
      },
      {
        headerName: "Granted",
        field: "granted_at",
        width: 170,
        cellRenderer: ({ value }: { value: string }) => formatDate(value),
        filter: "agDateColumnFilter",
      },
      {
        headerName: "Expires",
        field: "expires_at",
        width: 170,
        cellRenderer: ({ value }: { value?: string }) =>
          value ? formatDate(value) : (
            <span className="text-muted-foreground">Never</span>
          ),
        filter: "agDateColumnFilter",
      },
      {
        headerName: "Actions",
        field: undefined,
        width: 110,
        sortable: false,
        filter: false,
        pinned: "right",
        cellRenderer: (params: ICellRendererParams<FilePermission>) => (
          <ActionsRenderer
            data={params.data ?? null}
            onEdit={handleEditPermission}
            onDelete={handleDeletePermission}
            readOnly={readOnly}
          />
        ),
      },
    ],
    [handleDeletePermission, handleEditPermission, readOnly]
  );

  const defaultColDef = useMemo<ColDef>(
    () => ({
      resizable: true,
      sortable: true,
      filter: true,
      floatingFilter: true,
    }),
    []
  );

  const handleAddPermission = useCallback(() => {
    if (!newPermission.permission_type) return;

    const permission: FilePermission = {
      id: genId("perm"),
      file_id: fileId,
      user_id: newPermission.user_id,
      role: newPermission.role,
      permission_type: newPermission.permission_type as PermissionType,
      granted_by: "current_user", // TODO: inject from auth context
      granted_at: new Date().toISOString(),
      expires_at: newPermission.expires_at,
      conditions: newPermission.conditions,
      is_active: newPermission.is_active ?? true,
    };

    onPermissionUpdate([...currentPermissions, permission]);
    setNewPermission({ permission_type: "read", is_active: true });
    setIsAddDialogOpen(false);
  }, [currentPermissions, fileId, newPermission, onPermissionUpdate]);

  const handleUpdatePermission = useCallback(() => {
    if (!editingPermission) return;
    const updated = currentPermissions.map((p) =>
      p.id === editingPermission.id ? editingPermission : p
    );
    onPermissionUpdate(updated);
    setEditingPermission(null);
    setIsEditDialogOpen(false);
  }, [currentPermissions, editingPermission, onPermissionUpdate]);

  const permissionStats = useMemo(() => {
    const activePermissions = currentPermissions.filter((p) => p.is_active);
    const expiredPermissions = currentPermissions.filter(
      (p) => p.expires_at && new Date(p.expires_at) < new Date()
    );
    const typeDistribution = currentPermissions.reduce<Record<PermissionType, number>>(
      (acc, p) => {
        acc[p.permission_type] = (acc[p.permission_type] || 0) + 1;
        return acc;
      },
      {} as Record<PermissionType, number>
    );
    return {
      total: currentPermissions.length,
      active: activePermissions.length,
      expired: expiredPermissions.length,
      typeDistribution,
    };
  }, [currentPermissions]);

  const ruleSummaries = useMemo(
    () =>
      permissionRules.map((rule) => ({
        id: rule.id,
        name: rule.name,
        scope: rule.file_types.length ? rule.file_types.join(", ") : "All file types",
        roles: rule.user_roles.length ? rule.user_roles.join(", ") : "All roles",
        permissions: rule.permissions.join(", "),
        active: rule.is_active,
      })),
    [permissionRules]
  );

  const handleRuleSync = useCallback(() => {
    if (onRuleUpdate) {
      onRuleUpdate(permissionRules);
    }
  }, [onRuleUpdate, permissionRules]);

  return (
    <ErrorBoundary fallback={PermissionManagerFallback}>
      <div className={cn("w-full space-y-6", className)}>
        {/* Header */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5" aria-hidden />
                  File Permissions: {fileName}
                </CardTitle>
                <p className="mt-1 text-sm text-muted-foreground md:text-base lg:text-lg">
                  Manage access controls and expiration policies for this file.
                </p>
              </div>

              {!readOnly && (
                <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
                  <DialogTrigger asChild>
                    <Button aria-label="Add permission">
                      <Plus className="mr-2 h-4 w-4" aria-hidden />
                      Add Permission
                    </Button>
                  </DialogTrigger>

                  <DialogContent className="max-w-md">
                    <DialogHeader>
                      <DialogTitle>Add New Permission</DialogTitle>
                    </DialogHeader>

                    <div className="space-y-4">
                      {/* Grant To */}
                      <div className="space-y-2">
                        <Label>Grant To</Label>
                        <Tabs defaultValue="user" className="w-full">
                          <TabsList className="grid w-full grid-cols-2">
                            <TabsTrigger value="user">User</TabsTrigger>
                            <TabsTrigger value="role">Role</TabsTrigger>
                          </TabsList>

                          <TabsContent value="user" className="space-y-2">
                            <Select
                              value={newPermission.user_id ?? ""}
                              onValueChange={(value) =>
                                setNewPermission((p) => ({
                                  ...p,
                                  user_id: value || undefined,
                                  role: undefined,
                                }))
                              }
                            >
                              <SelectTrigger aria-label="Select user">
                                <SelectValue placeholder="Select user" />
                              </SelectTrigger>
                              <SelectContent>
                                {availableUsers.map((u) => (
                                  <SelectItem key={u.id} value={u.id}>
                                    {u.name} ({u.email ?? "unknown"})
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </TabsContent>

                          <TabsContent value="role" className="space-y-2">
                            <Select
                              value={newPermission.role ?? ""}
                              onValueChange={(value) =>
                                setNewPermission((p) => ({
                                  ...p,
                                  role: value || undefined,
                                  user_id: undefined,
                                }))
                              }
                            >
                              <SelectTrigger aria-label="Select role">
                                <SelectValue placeholder="Select role" />
                              </SelectTrigger>
                              <SelectContent>
                                {availableRoles.map((r) => (
                                  <SelectItem key={r.id} value={r.id}>
                                    {r.name}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </TabsContent>
                        </Tabs>
                      </div>

                      {/* Permission Type */}
                      <div className="space-y-2">
                        <Label>Permission Type</Label>
                        <Select
                          value={(newPermission.permission_type as PermissionType) ?? "read"}
                          onValueChange={(value) =>
                            setNewPermission((p) => ({
                              ...p,
                              permission_type: value as PermissionType,
                            }))
                          }
                        >
                          <SelectTrigger aria-label="Select permission type">
                            <SelectValue placeholder="Select permission" />
                          </SelectTrigger>
                          <SelectContent>
                            {PERMISSION_TYPES.map((permission) => {
                              const Icon = permission.icon;
                              return (
                                <SelectItem key={permission.value} value={permission.value}>
                                  <div className="flex items-center gap-2">
                                    <Icon className="h-4 w-4" aria-hidden />
                                    <div>
                                      <div>{permission.label}</div>
                                      <div className="text-xs text-muted-foreground">
                                        {permission.description}
                                      </div>
                                    </div>
                                  </div>
                                </SelectItem>
                              );
                            })}
                          </SelectContent>
                        </Select>
                      </div>

                      {/* Expires */}
                      <div className="space-y-2">
                        <Label>Expires At (Optional)</Label>
                        <input
                          type="datetime-local"
                          className="w-full rounded border p-2"
                          value={newPermission.expires_at?.slice(0, 16) || ""}
                          onChange={(e) =>
                            setNewPermission((p) => ({
                              ...p,
                              expires_at: e.target.value
                                ? new Date(e.target.value).toISOString()
                                : undefined,
                            }))
                          }
                        />
                      </div>

                      {/* Active */}
                      <div className="flex items-center space-x-2">
                        <Switch
                          id="new-is-active"
                          checked={!!newPermission.is_active}
                          onCheckedChange={(checked) =>
                            setNewPermission((p) => ({ ...p, is_active: checked }))
                          }
                        />
                        <Label htmlFor="new-is-active">Active</Label>
                      </div>

                      {/* (Optional) Conditions */}
                      <div className="space-y-2">
                        <Label>Conditions (JSON, optional)</Label>
                        <Textarea
                          placeholder='{"ip_range":"10.0.0.0/8"}'
                          value={
                            newPermission.conditions
                              ? JSON.stringify(newPermission.conditions, null, 2)
                              : ""
                          }
                          onChange={(e) => {
                            try {
                              const val = e.target.value.trim();
                              setNewPermission((p) => ({
                                ...p,
                                conditions: val ? JSON.parse(val) : undefined,
                              }));
                            } catch {
                              // Keep typing; validation would happen server-side or with a toast
                            }
                          }}
                        />
                      </div>
                    </div>

                    <DialogFooter>
                      <Button
                        variant="outline"
                        onClick={() => setIsAddDialogOpen(false)}
                        aria-label="Cancel"
                      >
                        Cancel
                      </Button>
                      <Button onClick={handleAddPermission} aria-label="Add permission">
                        Add
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              )}
            </div>
          </CardHeader>
        </Card>

        {/* Statistics */}
        <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
          <Card>
            <CardContent className="p-4 md:p-6">
              <div className="flex items-center gap-2">
                <Shield className="h-4 w-4 text-muted-foreground" aria-hidden />
                <div>
                  <p className="text-sm font-medium md:text-base lg:text-lg">
                    Total Permissions
                  </p>
                  <p className="text-2xl font-bold">{permissionStats.total}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4 md:p-6">
              <div className="flex items-center gap-2">
                <Check className="h-4 w-4 text-green-600" aria-hidden />
                <div>
                  <p className="text-sm font-medium md:text-base lg:text-lg">Active</p>
                  <p className="text-2xl font-bold text-green-600">
                    {permissionStats.active}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4 md:p-6">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-yellow-600" aria-hidden />
                <div>
                  <p className="text-sm font-medium md:text-base lg:text-lg">Expired</p>
                  <p className="text-2xl font-bold text-yellow-600">
                    {permissionStats.expired}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4 md:p-6">
              <div className="flex items-center gap-2">
                <Users className="h-4 w-4 text-muted-foreground" aria-hidden />
                <div>
                  <p className="text-sm font-medium md:text-base lg:text-lg">Selected</p>
                  <p className="text-2xl font-bold">{selectedPermissions.length}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {ruleSummaries.length > 0 && (
          <Card>
            <CardHeader className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
              <CardTitle>Rule Overview</CardTitle>
              <Button
                variant="outline"
                size="sm"
                onClick={handleRuleSync}
                aria-label="Sync permission rules"
              >
                <RefreshCw className="mr-2 h-4 w-4" aria-hidden />
                Sync Rules
              </Button>
            </CardHeader>
            <CardContent className="space-y-3 md:space-y-4">
              {ruleSummaries.map((rule) => (
                <div
                  key={rule.id}
                  className="rounded-lg border border-border p-3 md:p-4"
                >
                  <div className="flex items-center justify-between gap-2">
                    <div>
                      <p className="text-sm font-semibold md:text-base lg:text-lg">
                        {rule.name}
                      </p>
                      <p className="text-xs text-muted-foreground md:text-sm lg:text-base">
                        Applies to: {rule.scope}
                      </p>
                    </div>
                    <Badge variant={rule.active ? "default" : "secondary"}>
                      {rule.active ? "Active" : "Disabled"}
                    </Badge>
                  </div>
                  <div className="mt-2 grid gap-1 text-xs text-muted-foreground md:grid-cols-2 md:text-sm lg:text-base">
                    <span>Roles: {rule.roles}</span>
                    <span>Permissions: {rule.permissions}</span>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Permissions Grid */}
        <Card>
          <CardHeader>
            <CardTitle>Current Permissions</CardTitle>
          </CardHeader>
          <CardContent className="p-0 md:p-6">
            <div className="ag-theme-alpine w-full" style={{ height: 420 }}>
              <AgGridReact<FilePermission>
                rowData={currentPermissions}
                columnDefs={permissionColumns}
                defaultColDef={defaultColDef}
                rowSelection="multiple"
                onSelectionChanged={onSelectionChanged}
                animateRows
                enableCellTextSelection
                suppressRowClickSelection
                rowMultiSelectWithClick
                getRowStyle={({ data }) => {
                  if (!data) return undefined;
                  const expired = !!(data.expires_at && new Date(data.expires_at) < new Date());
                  if (!data.is_active || expired) {
                    return { backgroundColor: "#fef2f2", opacity: 0.75 };
                  }
                  return undefined;
                }}
                noRowsOverlayComponent={NoRowsOverlay}
              />
            </div>
          </CardContent>
        </Card>

        {/* Bulk Actions */}
        {selectedPermissions.length > 0 && !readOnly && (
          <Card>
            <CardContent className="p-4 md:p-6">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium md:text-base lg:text-lg">
                  {selectedPermissions.length} permission
                  {selectedPermissions.length !== 1 ? "s" : ""} selected
                </span>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      const ids = new Set(selectedPermissions.map((p) => p.id));
                      const updated = currentPermissions.map((p) =>
                        ids.has(p.id) ? { ...p, is_active: true } : p
                      );
                      onPermissionUpdate(updated);
                    }}
                    aria-label="Activate selected"
                  >
                    <Unlock className="mr-2 h-4 w-4" aria-hidden />
                    Activate
                  </Button>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      const ids = new Set(selectedPermissions.map((p) => p.id));
                      const updated = currentPermissions.map((p) =>
                        ids.has(p.id) ? { ...p, is_active: false } : p
                      );
                      onPermissionUpdate(updated);
                    }}
                    aria-label="Deactivate selected"
                  >
                    <Lock className="mr-2 h-4 w-4" aria-hidden />
                    Deactivate
                  </Button>

                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => {
                      const ids = new Set(selectedPermissions.map((p) => p.id));
                      const updated = currentPermissions.filter((p) => !ids.has(p.id));
                      onPermissionUpdate(updated);
                    }}
                    aria-label="Delete selected"
                  >
                    <Trash2 className="mr-2 h-4 w-4" aria-hidden />
                    Delete
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Edit Permission Dialog */}
        <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Edit Permission</DialogTitle>
            </DialogHeader>

            {editingPermission && (
              <div className="space-y-4">
                {/* Permission Type */}
                <div className="space-y-2">
                  <Label>Permission Type</Label>
                  <Select
                    value={editingPermission.permission_type}
                    onValueChange={(value) =>
                      setEditingPermission((p) =>
                        p
                          ? { ...p, permission_type: value as PermissionType }
                          : p
                      )
                    }
                  >
                    <SelectTrigger aria-label="Select permission type">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {PERMISSION_TYPES.map((permission) => {
                        const Icon = permission.icon;
                        return (
                          <SelectItem key={permission.value} value={permission.value}>
                            <div className="flex items-center gap-2">
                              <Icon className="h-4 w-4" aria-hidden />
                              {permission.label}
                            </div>
                          </SelectItem>
                        );
                      })}
                    </SelectContent>
                  </Select>
                </div>

                {/* Expires */}
                <div className="space-y-2">
                  <Label>Expires At</Label>
                  <input
                    type="datetime-local"
                    className="w-full rounded border p-2"
                    value={editingPermission.expires_at?.slice(0, 16) || ""}
                    onChange={(e) =>
                      setEditingPermission((p) =>
                        p
                          ? {
                              ...p,
                              expires_at: e.target.value
                                ? new Date(e.target.value).toISOString()
                                : undefined,
                            }
                          : p
                      )
                    }
                  />
                </div>

                {/* Active */}
                <div className="flex items-center space-x-2">
                  <Switch
                    id="edit-is-active"
                    checked={editingPermission.is_active}
                    onCheckedChange={(checked) =>
                      setEditingPermission((p) => (p ? { ...p, is_active: checked } : p))
                    }
                  />
                  <Label htmlFor="edit-is-active">Active</Label>
                </div>
              </div>
            )}

            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setIsEditDialogOpen(false)}
                aria-label="Cancel edit"
              >
                Cancel
              </Button>
              <Button onClick={handleUpdatePermission} aria-label="Save changes">
                Save
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </ErrorBoundary>
  );
};

export default FilePermissionManager;
