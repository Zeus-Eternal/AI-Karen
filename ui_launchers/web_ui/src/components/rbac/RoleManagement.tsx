'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Role, User, Permission, SYSTEM_ROLES } from '@/types/rbac';
import { useRBAC } from '@/providers/rbac-provider';
import { enhancedApiClient } from '@/lib/enhanced-api-client';
import { PermissionGate } from './PermissionGate';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogFooter, 
  DialogHeader, 
  DialogTitle,
  DialogTrigger 
} from '@/components/ui/dialog';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Alert, AlertDescription } from '@/components/ui/alert';

import { 
  Users, 
  Shield, 
  Plus, 
  Edit, 
  Trash2, 
  UserPlus, 
  UserMinus,
  AlertTriangle,
  CheckCircle,
  XCircle
} from 'lucide-react';

interface RoleManagementProps {
  className?: string;
}

export function RoleManagement({ className }: RoleManagementProps) {
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  return (
    <PermissionGate permission="users:admin">
      <div className={className}>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold">Role Management</h2>
            <p className="text-muted-foreground">
              Manage user roles and permissions across the system
            </p>
          </div>
          <Button onClick={() => setIsCreateDialogOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Create Role
          </Button>
        </div>

        <Tabs defaultValue="roles" className="space-y-4">
          <TabsList>
            <TabsTrigger value="roles">Roles</TabsTrigger>
            <TabsTrigger value="users">User Assignments</TabsTrigger>
            <TabsTrigger value="hierarchy">Role Hierarchy</TabsTrigger>
          </TabsList>

          <TabsContent value="roles">
            <RolesList 
              searchTerm={searchTerm}
              onSearchChange={setSearchTerm}
              onRoleSelect={setSelectedRole}
              onEditRole={(role) => {
                setSelectedRole(role);
                setIsEditDialogOpen(true);
              }}
            />
          </TabsContent>

          <TabsContent value="users">
            <UserRoleAssignments />
          </TabsContent>

          <TabsContent value="hierarchy">
            <RoleHierarchyView />
          </TabsContent>
        </Tabs>

        {/* Create Role Dialog */}
        <CreateRoleDialog 
          open={isCreateDialogOpen}
          onOpenChange={setIsCreateDialogOpen}
        />

        {/* Edit Role Dialog */}
        <EditRoleDialog
          role={selectedRole}
          open={isEditDialogOpen}
          onOpenChange={setIsEditDialogOpen}
        />
      </div>
    </PermissionGate>
  );
}

interface RolesListProps {
  searchTerm: string;
  onSearchChange: (term: string) => void;
  onRoleSelect: (role: Role) => void;
  onEditRole: (role: Role) => void;
}

function RolesList({ searchTerm, onSearchChange, onRoleSelect, onEditRole }: RolesListProps) {
  const queryClient = useQueryClient();

  const { data: roles = [], isLoading } = useQuery({
    queryKey: ['rbac', 'roles'],
    queryFn: () => enhancedApiClient.get<Role[]>('/api/rbac/roles'),
  });

  const deleteRoleMutation = useMutation({
    mutationFn: (roleId: string) => enhancedApiClient.delete(`/api/rbac/roles/${roleId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rbac', 'roles'] });
    }
  });

  const filteredRoles = roles.filter(role =>
    role.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    role.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (isLoading) {
    return <div>Loading roles...</div>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center space-x-2">
        <Input
          placeholder="Search roles..."
          value={searchTerm}
          onChange={(e) => onSearchChange(e.target.value)}
          className="max-w-sm"
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {filteredRoles.map((role) => (
          <Card key={role.id} className="cursor-pointer hover:shadow-md transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">{role.name}</CardTitle>
                <div className="flex items-center space-x-1">
                  {role.metadata.isSystemRole && (
                    <Badge variant="secondary">System</Badge>
                  )}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      onEditRole(role);
                    }}
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  {!role.metadata.isSystemRole && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteRoleMutation.mutate(role.id);
                      }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </div>
              <CardDescription>{role.description}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex items-center text-sm text-muted-foreground">
                  <Shield className="h-4 w-4 mr-2" />
                  {role.permissions.length} permissions
                </div>
                <div className="flex flex-wrap gap-1">
                  {role.permissions.slice(0, 3).map((permission) => (
                    <Badge key={permission} variant="outline" className="text-xs">
                      {permission}
                    </Badge>
                  ))}
                  {role.permissions.length > 3 && (
                    <Badge variant="outline" className="text-xs">
                      +{role.permissions.length - 3} more
                    </Badge>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

function UserRoleAssignments() {
  const [selectedUser, setSelectedUser] = useState<string>('');
  const [selectedRole, setSelectedRole] = useState<string>('');

  const { data: users = [] } = useQuery({
    queryKey: ['rbac', 'users'],
    queryFn: () => enhancedApiClient.get<User[]>('/api/rbac/users'),
  });

  const { data: roles = [] } = useQuery({
    queryKey: ['rbac', 'roles'],
    queryFn: () => enhancedApiClient.get<Role[]>('/api/rbac/roles'),
  });

  const { assignRole, removeRole } = useRBAC();

  const handleAssignRole = async () => {
    if (selectedUser && selectedRole) {
      await assignRole(selectedUser, selectedRole);
      setSelectedUser('');
      setSelectedRole('');
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Assign Role to User</CardTitle>
          <CardDescription>
            Grant roles to users to control their access permissions
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="user-select">Select User</Label>
              <Select value={selectedUser} onValueChange={setSelectedUser}>
                <SelectTrigger>
                  <SelectValue placeholder="Choose a user" />
                </SelectTrigger>
                <SelectContent>
                  {users.map((user) => (
                    <SelectItem key={user.id} value={user.id}>
                      {user.username} ({user.email})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="role-select">Select Role</Label>
              <Select value={selectedRole} onValueChange={setSelectedRole}>
                <SelectTrigger>
                  <SelectValue placeholder="Choose a role" />
                </SelectTrigger>
                <SelectContent>
                  {roles.map((role) => (
                    <SelectItem key={role.id} value={role.id}>
                      {role.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <Button onClick={handleAssignRole} disabled={!selectedUser || !selectedRole}>
            <UserPlus className="h-4 w-4 mr-2" />
            Assign Role
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Current User Role Assignments</CardTitle>
        </CardHeader>
        <CardContent>
          <UserRoleTable users={users} roles={roles} />
        </CardContent>
      </Card>
    </div>
  );
}

interface UserRoleTableProps {
  users: User[];
  roles: Role[];
}

function UserRoleTable({ users, roles }: UserRoleTableProps) {
  const { removeRole } = useRBAC();

  const getRoleName = (roleId: string) => {
    return roles.find(role => role.id === roleId)?.name || roleId;
  };

  return (
    <div className="space-y-4">
      {users.map((user) => (
        <div key={user.id} className="border rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <div>
              <h4 className="font-medium">{user.username}</h4>
              <p className="text-sm text-muted-foreground">{user.email}</p>
            </div>
            <Badge variant={user.metadata.isActive ? 'default' : 'secondary'}>
              {user.metadata.isActive ? 'Active' : 'Inactive'}
            </Badge>
          </div>
          <div className="flex flex-wrap gap-2">
            {user.roles.map((roleId) => (
              <div key={roleId} className="flex items-center space-x-1">
                <Badge variant="outline">{getRoleName(roleId)}</Badge>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => removeRole(user.id, roleId)}
                >
                  <XCircle className="h-3 w-3" />
                </Button>
              </div>
            ))}
            {user.roles.length === 0 && (
              <span className="text-sm text-muted-foreground">No roles assigned</span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

function RoleHierarchyView() {
  const { data: hierarchy = [] } = useQuery({
    queryKey: ['rbac', 'role-hierarchy'],
    queryFn: () => enhancedApiClient.get('/api/rbac/role-hierarchy'),
  });

  return (
    <div className="space-y-4">
      <Alert>
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>
          Role hierarchy allows roles to inherit permissions from parent roles. 
          Conflicts are resolved based on the configured resolution strategy.
        </AlertDescription>
      </Alert>

      {hierarchy.map((item: any) => (
        <Card key={item.roleId}>
          <CardHeader>
            <CardTitle>{item.roleName}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {item.parentRoles.length > 0 && (
              <div>
                <Label className="text-sm font-medium">Inherits from:</Label>
                <div className="flex flex-wrap gap-2 mt-1">
                  {item.parentRoles.map((parentRole: string) => (
                    <Badge key={parentRole} variant="secondary">
                      {parentRole}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {item.conflicts.length > 0 && (
              <div>
                <Label className="text-sm font-medium text-destructive">Conflicts:</Label>
                <div className="space-y-2 mt-1">
                  {item.conflicts.map((conflict: any, index: number) => (
                    <Alert key={index} variant="destructive">
                      <AlertTriangle className="h-4 w-4" />
                      <AlertDescription>
                        Permission '{conflict.permission}' conflicts between roles: {conflict.conflictingRoles.join(', ')}
                        <br />
                        Resolution: {conflict.resolution}
                      </AlertDescription>
                    </Alert>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

interface CreateRoleDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

function CreateRoleDialog({ open, onOpenChange }: CreateRoleDialogProps) {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    permissions: [] as Permission[],
    parentRoles: [] as string[]
  });

  const queryClient = useQueryClient();

  const createRoleMutation = useMutation({
    mutationFn: (roleData: typeof formData) => 
      enhancedApiClient.post('/api/rbac/roles', roleData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rbac', 'roles'] });
      onOpenChange(false);
      setFormData({ name: '', description: '', permissions: [], parentRoles: [] });
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createRoleMutation.mutate(formData);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Create New Role</DialogTitle>
          <DialogDescription>
            Define a new role with specific permissions and hierarchy
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Role Name</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              required
            />
          </div>

          <PermissionSelector
            selectedPermissions={formData.permissions}
            onPermissionsChange={(permissions) => 
              setFormData({ ...formData, permissions })
            }
          />

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={createRoleMutation.isPending}>
              Create Role
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

interface EditRoleDialogProps {
  role: Role | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

function EditRoleDialog({ role, open, onOpenChange }: EditRoleDialogProps) {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    permissions: [] as Permission[],
    parentRoles: [] as string[]
  });

  React.useEffect(() => {
    if (role) {
      setFormData({
        name: role.name,
        description: role.description,
        permissions: role.permissions,
        parentRoles: role.parentRoles || []
      });
    }
  }, [role]);

  const queryClient = useQueryClient();

  const updateRoleMutation = useMutation({
    mutationFn: (roleData: typeof formData) => 
      enhancedApiClient.put(`/api/rbac/roles/${role?.id}`, roleData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rbac', 'roles'] });
      onOpenChange(false);
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (role) {
      updateRoleMutation.mutate(formData);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Edit Role</DialogTitle>
          <DialogDescription>
            Modify role permissions and settings
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Role Name</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
              disabled={role?.metadata.isSystemRole}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              required
            />
          </div>

          <PermissionSelector
            selectedPermissions={formData.permissions}
            onPermissionsChange={(permissions) => 
              setFormData({ ...formData, permissions })
            }
            disabled={role?.metadata.isSystemRole}
          />

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={updateRoleMutation.isPending}>
              Update Role
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

interface PermissionSelectorProps {
  selectedPermissions: Permission[];
  onPermissionsChange: (permissions: Permission[]) => void;
  disabled?: boolean;
}

function PermissionSelector({ selectedPermissions, onPermissionsChange, disabled }: PermissionSelectorProps) {
  const allPermissions: Permission[] = [
    'dashboard:view', 'dashboard:edit', 'dashboard:admin',
    'memory:view', 'memory:edit', 'memory:delete', 'memory:admin',
    'plugins:view', 'plugins:install', 'plugins:configure', 'plugins:admin',
    'models:view', 'models:configure', 'models:admin',
    'workflows:view', 'workflows:create', 'workflows:execute', 'workflows:admin',
    'chat:basic', 'chat:advanced', 'chat:multimodal',
    'security:view', 'security:audit', 'security:admin', 'security:evil_mode',
    'system:view', 'system:configure', 'system:admin',
    'users:view', 'users:manage', 'users:admin'
  ];

  const permissionCategories = {
    'Dashboard': allPermissions.filter(p => p.startsWith('dashboard:')),
    'Memory': allPermissions.filter(p => p.startsWith('memory:')),
    'Plugins': allPermissions.filter(p => p.startsWith('plugins:')),
    'Models': allPermissions.filter(p => p.startsWith('models:')),
    'Workflows': allPermissions.filter(p => p.startsWith('workflows:')),
    'Chat': allPermissions.filter(p => p.startsWith('chat:')),
    'Security': allPermissions.filter(p => p.startsWith('security:')),
    'System': allPermissions.filter(p => p.startsWith('system:')),
    'Users': allPermissions.filter(p => p.startsWith('users:'))
  };

  const handlePermissionToggle = (permission: Permission) => {
    if (disabled) return;
    
    const newPermissions = selectedPermissions.includes(permission)
      ? selectedPermissions.filter(p => p !== permission)
      : [...selectedPermissions, permission];
    
    onPermissionsChange(newPermissions);
  };

  return (
    <div className="space-y-4">
      <Label>Permissions</Label>
      <div className="grid gap-4">
        {Object.entries(permissionCategories).map(([category, permissions]) => (
          <div key={category} className="space-y-2">
            <h4 className="font-medium text-sm">{category}</h4>
            <div className="grid grid-cols-2 gap-2">
              {permissions.map((permission) => (
                <div key={permission} className="flex items-center space-x-2">
                  <Checkbox
                    id={permission}
                    checked={selectedPermissions.includes(permission)}
                    onCheckedChange={() => handlePermissionToggle(permission)}
                    disabled={disabled}
                  />
                  <Label htmlFor={permission} className="text-sm">
                    {permission.split(':')[1]}
                  </Label>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}