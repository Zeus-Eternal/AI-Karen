'use client';

import React, { useState, useMemo, useCallback } from 'react';
import { AgGridReact } from 'ag-grid-react';
import { ColDef, GridReadyEvent, SelectionChangedEvent } from 'ag-grid-community';
import {
  Shield,
  Users,
  User,
  Lock,
  Unlock,
  Eye,
  Edit,
  Download,
  Trash2,
  Plus,
  Settings,
  Check,
  X,
  AlertTriangle
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn } from '@/lib/utils';

// AG-Grid theme imports
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';

export interface FilePermission {
  id: string;
  file_id: string;
  user_id?: string;
  role?: string;
  permission_type: 'read' | 'write' | 'delete' | 'share' | 'admin';
  granted_by: string;
  granted_at: string;
  expires_at?: string;
  conditions?: Record<string, any>;
  is_active: boolean;
}

export interface PermissionRule {
  id: string;
  name: string;
  description: string;
  file_types: string[];
  user_roles: string[];
  permissions: string[];
  conditions: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface FilePermissionManagerProps {
  fileId: string;
  fileName: string;
  currentPermissions: FilePermission[];
  availableUsers: Array<{ id: string; name: string; email: string; roles: string[] }>;
  availableRoles: Array<{ id: string; name: string; description: string }>;
  permissionRules: PermissionRule[];
  onPermissionUpdate: (permissions: FilePermission[]) => void;
  onRuleUpdate: (rules: PermissionRule[]) => void;
  className?: string;
  readOnly?: boolean;
}

const PERMISSION_TYPES = [
  { value: 'read', label: 'Read', icon: Eye, description: 'View file content' },
  { value: 'write', label: 'Write', icon: Edit, description: 'Modify file content' },
  { value: 'delete', label: 'Delete', icon: Trash2, description: 'Delete the file' },
  { value: 'download', label: 'Download', icon: Download, description: 'Download the file' },
  { value: 'share', label: 'Share', icon: Users, description: 'Share with others' },
  { value: 'admin', label: 'Admin', icon: Settings, description: 'Manage permissions' }
];

const formatDate = (dateString: string): string => {
  try {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch {
    return dateString;
  }
};

// Custom cell renderers
const PermissionTypeRenderer = ({ value }: { value: string }) => {
  const permission = PERMISSION_TYPES.find(p => p.value === value);
  if (!permission) return <span>{value}</span>;

  const Icon = permission.icon;
  return (
    <div className="flex items-center gap-2">
      <Icon className="h-4 w-4" />
      <span>{permission.label}</span>
    </div>
  );
};

const UserRenderer = ({ data }: { data: FilePermission }) => {
  if (data.user_id) {
    return (
      <div className="flex items-center gap-2">
        <User className="h-4 w-4" />
        <span>{data.user_id}</span>
      </div>
    );
  } else if (data.role) {
    return (
      <div className="flex items-center gap-2">
        <Users className="h-4 w-4" />
        <Badge variant="outline">{data.role}</Badge>
      </div>
    );
  }
  return <span>-</span>;
};

const StatusRenderer = ({ data }: { data: FilePermission }) => {
  const isExpired = data.expires_at && new Date(data.expires_at) < new Date();
  const isActive = data.is_active && !isExpired;

  return (
    <div className="flex items-center gap-2">
      {isActive ? (
        <Badge variant="secondary" className="bg-green-100 text-green-800">
          <Check className="mr-1 h-3 w-3" />
          Active
        </Badge>
      ) : (
        <Badge variant="secondary" className="bg-red-100 text-red-800">
          <X className="mr-1 h-3 w-3" />
          {isExpired ? 'Expired' : 'Inactive'}
        </Badge>
      )}
    </div>
  );
};

const ActionsRenderer = ({
  data,
  onEdit,
  onDelete,
  readOnly
}: {
  data: FilePermission;
  onEdit: (permission: FilePermission) => void;
  onDelete: (permissionId: string) => void;
  readOnly: boolean;
}) => {
  if (readOnly) return null;

  return (
    <div className="flex items-center gap-1">
      <Button
        variant="ghost"
        size="sm"
        onClick={() => onEdit(data)}
        className="h-8 w-8 p-0"
      >
        <Edit className="h-4 w-4" />
      </Button>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => onDelete(data.id)}
        className="h-8 w-8 p-0 text-destructive hover:text-destructive"
      >
        <Trash2 className="h-4 w-4" />
      </Button>
    </div>
  );
};

export const FilePermissionManager: React.FC<FilePermissionManagerProps> = ({
  fileId,
  fileName,
  currentPermissions,
  availableUsers,
  availableRoles,
  permissionRules,
  onPermissionUpdate,
  onRuleUpdate,
  className,
  readOnly = false
}) => {
  const [selectedPermissions, setSelectedPermissions] = useState<FilePermission[]>([]);
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [editingPermission, setEditingPermission] = useState<FilePermission | null>(null);
  const [newPermission, setNewPermission] = useState<Partial<FilePermission>>({
    permission_type: 'read',
    is_active: true
  });

  // Permission grid columns
  const permissionColumns = useMemo<ColDef[]>(() => [
    {
      headerName: 'User/Role',
      field: 'user_role',
      flex: 1,
      minWidth: 150,
      cellRenderer: UserRenderer,
      filter: 'agTextColumnFilter'
    },
    {
      headerName: 'Permission',
      field: 'permission_type',
      width: 120,
      cellRenderer: PermissionTypeRenderer,
      filter: 'agSetColumnFilter'
    },
    {
      headerName: 'Status',
      field: 'status',
      width: 100,
      cellRenderer: StatusRenderer,
      filter: 'agSetColumnFilter'
    },
    {
      headerName: 'Granted By',
      field: 'granted_by',
      width: 120,
      filter: 'agTextColumnFilter'
    },
    {
      headerName: 'Granted',
      field: 'granted_at',
      width: 150,
      cellRenderer: ({ value }: { value: string }) => formatDate(value),
      filter: 'agDateColumnFilter'
    },
    {
      headerName: 'Expires',
      field: 'expires_at',
      width: 150,
      cellRenderer: ({ value }: { value?: string }) =>
        value ? formatDate(value) : <span className="text-muted-foreground">Never</span>,
      filter: 'agDateColumnFilter'
    },
    {
      headerName: 'Actions',
      field: 'actions',
      width: 100,
      sortable: false,
      filter: false,
      pinned: 'right',
      cellRenderer: (params: any) => (
        <ActionsRenderer
          data={params.data}
          onEdit={handleEditPermission}
          onDelete={handleDeletePermission}
          readOnly={readOnly}
        />
      )
    }
  ], [readOnly]);

  const defaultColDef = useMemo(() => ({
    resizable: true,
    sortable: true,
    filter: true,
    floatingFilter: true,
  }), []);

  const handleEditPermission = (permission: FilePermission) => {
    setEditingPermission(permission);
    setIsEditDialogOpen(true);
  };

  const handleDeletePermission = (permissionId: string) => {
    const updatedPermissions = currentPermissions.filter(p => p.id !== permissionId);
    onPermissionUpdate(updatedPermissions);
  };

  const handleAddPermission = () => {
    if (!newPermission.permission_type) return;

    const permission: FilePermission = {
      id: `perm_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      file_id: fileId,
      user_id: newPermission.user_id,
      role: newPermission.role,
      permission_type: newPermission.permission_type as any,
      granted_by: 'current_user', // This would come from auth context
      granted_at: new Date().toISOString(),
      expires_at: newPermission.expires_at,
      conditions: newPermission.conditions,
      is_active: newPermission.is_active ?? true
    };

    onPermissionUpdate([...currentPermissions, permission]);
    setNewPermission({ permission_type: 'read', is_active: true });
    setIsAddDialogOpen(false);
  };

  const handleUpdatePermission = () => {
    if (!editingPermission) return;

    const updatedPermissions = currentPermissions.map(p =>
      p.id === editingPermission.id ? editingPermission : p
    );
    onPermissionUpdate(updatedPermissions);
    setEditingPermission(null);
    setIsEditDialogOpen(false);
  };

  const onSelectionChanged = useCallback((event: SelectionChangedEvent) => {
    const selectedRows = event.api.getSelectedRows();
    setSelectedPermissions(selectedRows);
  }, []);

  // Permission statistics
  const permissionStats = useMemo(() => {
    const activePermissions = currentPermissions.filter(p => p.is_active);
    const expiredPermissions = currentPermissions.filter(p =>
      p.expires_at && new Date(p.expires_at) < new Date()
    );

    const typeDistribution = currentPermissions.reduce((acc, p) => {
      acc[p.permission_type] = (acc[p.permission_type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return {
      total: currentPermissions.length,
      active: activePermissions.length,
      expired: expiredPermissions.length,
      typeDistribution
    };
  }, [currentPermissions]);

  return (
    <div className={cn('w-full space-y-6', className)}>
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5" />
                File Permissions: {fileName}
              </CardTitle>
              <p className="text-sm text-muted-foreground mt-1">
                Manage access permissions for this file
              </p>
            </div>
            {!readOnly && (
              <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
                <DialogTrigger asChild>
                  <Button>
                    <Plus className="mr-2 h-4 w-4" />
                    Add Permission
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-md">
                  <DialogHeader>
                    <DialogTitle>Add New Permission</DialogTitle>
                  </DialogHeader>
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label>Grant To</Label>
                      <Tabs defaultValue="user" className="w-full">
                        <TabsList className="grid w-full grid-cols-2">
                          <TabsTrigger value="user">User</TabsTrigger>
                          <TabsTrigger value="role">Role</TabsTrigger>
                        </TabsList>
                        <TabsContent value="user" className="space-y-2">
                          <Select
                            value={newPermission.user_id}
                            onValueChange={(value) => setNewPermission({
                              ...newPermission,
                              user_id: value,
                              role: undefined
                            })}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Select user" />
                            </SelectTrigger>
                            <SelectContent>
                              {availableUsers.map(user => (
                                <SelectItem key={user.id} value={user.id}>
                                  {user.name} ({user.email ?? 'Unknown'})
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </TabsContent>
                        <TabsContent value="role" className="space-y-2">
                          <Select
                            value={newPermission.role}
                            onValueChange={(value) => setNewPermission({
                              ...newPermission,
                              role: value,
                              user_id: undefined
                            })}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Select role" />
                            </SelectTrigger>
                            <SelectContent>
                              {availableRoles.map(role => (
                                <SelectItem key={role.id} value={role.id}>
                                  {role.name}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </TabsContent>
                      </Tabs>
                    </div>

                    <div className="space-y-2">
                      <Label>Permission Type</Label>
                      <Select
                        value={newPermission.permission_type}
                        onValueChange={(value) => setNewPermission({
                          ...newPermission,
                          permission_type: value as any
                        })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {PERMISSION_TYPES.map(permission => {
                            const Icon = permission.icon;
                            return (
                              <SelectItem key={permission.value} value={permission.value}>
                                <div className="flex items-center gap-2">
                                  <Icon className="h-4 w-4" />
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

                    <div className="space-y-2">
                      <Label>Expires At (Optional)</Label>
                      <Input
                        type="datetime-local"
                        value={newPermission.expires_at?.slice(0, 16) || ''}
                        onChange={(e) => setNewPermission({
                          ...newPermission,
                          expires_at: e.target.value ? new Date(e.target.value).toISOString() : undefined
                        })}
                      />
                    </div>

                    <div className="flex items-center space-x-2">
                      <Switch
                        id="is-active"
                        checked={newPermission.is_active}
                        onCheckedChange={(checked) => setNewPermission({
                          ...newPermission,
                          is_active: checked
                        })}
                      />
                      <Label htmlFor="is-active">Active</Label>
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setIsAddDialogOpen(false)}>
                      Cancel
                    </Button>
                    <Button onClick={handleAddPermission}>
                      Add Permission
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            )}
          </div>
        </CardHeader>
      </Card>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Shield className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">Total Permissions</p>
                <p className="text-2xl font-bold">{permissionStats.total}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Check className="h-4 w-4 text-green-600" />
              <div>
                <p className="text-sm font-medium">Active</p>
                <p className="text-2xl font-bold text-green-600">{permissionStats.active}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-yellow-600" />
              <div>
                <p className="text-sm font-medium">Expired</p>
                <p className="text-2xl font-bold text-yellow-600">{permissionStats.expired}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-sm font-medium">Selected</p>
                <p className="text-2xl font-bold">{selectedPermissions.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Permissions Grid */}
      <Card>
        <CardHeader>
          <CardTitle>Current Permissions</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div
            className="ag-theme-alpine w-full"
            style={{ height: '400px' }}
          >
            <AgGridReact
              rowData={currentPermissions}
              columnDefs={permissionColumns}
              defaultColDef={defaultColDef}
              rowSelection="multiple"
              onSelectionChanged={onSelectionChanged}
              animateRows={true}
              enableCellTextSelection={true}
              suppressRowClickSelection={true}
              rowMultiSelectWithClick={true}
              getRowStyle={(params) => {
                const permission = params.data as FilePermission;
                const isExpired = permission.expires_at && new Date(permission.expires_at) < new Date();

                if (!permission.is_active || isExpired) {
                  return { backgroundColor: '#fef2f2', opacity: 0.7 };
                }
                return undefined;
              }}
              noRowsOverlayComponent={() => (
                <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
                  <Shield className="h-12 w-12 mb-2" />
                  <p>No permissions configured</p>
                </div>
              )}
            />
          </div>
        </CardContent>
      </Card>

      {/* Bulk Actions */}
      {selectedPermissions.length > 0 && !readOnly && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">
                {selectedPermissions.length} permission{selectedPermissions.length !== 1 ? 's' : ''} selected
              </span>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    const updatedPermissions = currentPermissions.map(p =>
                      selectedPermissions.find(sp => sp.id === p.id)
                        ? { ...p, is_active: true }
                        : p
                    );
                    onPermissionUpdate(updatedPermissions);
                  }}
                >
                  <Unlock className="mr-2 h-4 w-4" />
                  Activate
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    const updatedPermissions = currentPermissions.map(p =>
                      selectedPermissions.find(sp => sp.id === p.id)
                        ? { ...p, is_active: false }
                        : p
                    );
                    onPermissionUpdate(updatedPermissions);
                  }}
                >
                  <Lock className="mr-2 h-4 w-4" />
                  Deactivate
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => {
                    const selectedIds = selectedPermissions.map(p => p.id);
                    const updatedPermissions = currentPermissions.filter(p => !selectedIds.includes(p.id));
                    onPermissionUpdate(updatedPermissions);
                  }}
                >
                  <Trash2 className="mr-2 h-4 w-4" />
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
              <div className="space-y-2">
                <Label>Permission Type</Label>
                <Select
                  value={editingPermission.permission_type}
                  onValueChange={(value) => setEditingPermission({
                    ...editingPermission,
                    permission_type: value as any
                  })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {PERMISSION_TYPES.map(permission => {
                      const Icon = permission.icon;
                      return (
                        <SelectItem key={permission.value} value={permission.value}>
                          <div className="flex items-center gap-2">
                            <Icon className="h-4 w-4" />
                            {permission.label}
                          </div>
                        </SelectItem>
                      );
                    })}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Expires At</Label>
                <Input
                  type="datetime-local"
                  value={editingPermission.expires_at?.slice(0, 16) || ''}
                  onChange={(e) => setEditingPermission({
                    ...editingPermission,
                    expires_at: e.target.value ? new Date(e.target.value).toISOString() : undefined
                  })}
                />
              </div>

              <div className="flex items-center space-x-2">
                <Switch
                  id="edit-is-active"
                  checked={editingPermission.is_active}
                  onCheckedChange={(checked) => setEditingPermission({
                    ...editingPermission,
                    is_active: checked
                  })}
                />
                <Label htmlFor="edit-is-active">Active</Label>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleUpdatePermission}>
              Update Permission
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default FilePermissionManager;
