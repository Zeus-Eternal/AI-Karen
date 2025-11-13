"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

import {
  Role,
  User,
  Permission,
  RoleHierarchy,
  RoleConflict,
} from "@/types/rbac";
import { useRBAC } from "@/providers/rbac-hooks";
import { enhancedApiClient } from "@/lib/enhanced-api-client";

import { PermissionGate } from "./PermissionGate";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import { Checkbox } from "@/components/ui/checkbox";
import { Alert, AlertDescription } from "@/components/ui/alert";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import {
  Shield,
  Edit,
  Trash2,
  UserPlus,
  AlertTriangle,
  Plus,
  XCircle,
} from "lucide-react";

export interface RoleManagementProps {
  className?: string;
}

export function RoleManagement({ className }: RoleManagementProps) {
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");

  return (
    <PermissionGate permission="users:admin">
      <div className={className}>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold">Role Management</h2>
            <p className="text-muted-foreground">
              Manage roles, assignments, and RBAC hierarchy for Kari.
            </p>
          </div>
          <Button onClick={() => setIsCreateDialogOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Create role
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

        <CreateRoleDialog
          open={isCreateDialogOpen}
          onOpenChange={setIsCreateDialogOpen}
        />

        <EditRoleDialog
          role={selectedRole}
          open={isEditDialogOpen}
          onOpenChange={setIsEditDialogOpen}
        />
      </div>
    </PermissionGate>
  );
}

// --------------------------------------------------------
// Roles List
// --------------------------------------------------------

export interface RolesListProps {
  searchTerm: string;
  onSearchChange: (term: string) => void;
  onRoleSelect: (role: Role) => void;
  onEditRole: (role: Role) => void;
}

function RolesList({
  searchTerm,
  onSearchChange,
  onRoleSelect,
  onEditRole,
}: RolesListProps) {
  const queryClient = useQueryClient();

  const { data: rolesData, isLoading } = useQuery({
    queryKey: ["rbac", "roles"],
    queryFn: () => enhancedApiClient.get<Role[]>("/api/rbac/roles"),
  });

  const roles: Role[] = Array.isArray(rolesData)
    ? rolesData
    : rolesData?.data || [];

  const deleteRoleMutation = useMutation({
    mutationFn: (roleId: string) =>
      enhancedApiClient.delete(`/api/rbac/roles/${roleId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rbac", "roles"] });
    },
  });

  const filteredRoles = roles.filter((role) => {
    const name = role.name?.toLowerCase() || "";
    const desc = role.description?.toLowerCase() || "";
    const query = searchTerm.toLowerCase();
    return name.includes(query) || desc.includes(query);
  });

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
          <Card
            key={role.id}
            className="cursor-pointer hover:shadow-md transition-shadow"
            onClick={() => onRoleSelect(role)}
          >
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">{role.name}</CardTitle>
                <div className="flex items-center space-x-1">
                  {role.metadata?.isSystemRole && (
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
                  {!role.metadata?.isSystemRole && (
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
                    <Badge
                      key={permission}
                      variant="outline"
                      className="text-xs"
                    >
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
        {filteredRoles.length === 0 && (
          <div className="col-span-full text-sm text-muted-foreground">
            No roles match this search.
          </div>
        )}
      </div>
    </div>
  );
}

// --------------------------------------------------------
// User Role Assignments
// --------------------------------------------------------

function UserRoleAssignments() {
  const [selectedUser, setSelectedUser] = useState("");
  const [selectedRole, setSelectedRole] = useState("");

  const { data: usersData } = useQuery({
    queryKey: ["rbac", "users"],
    queryFn: () => enhancedApiClient.get<User[]>("/api/rbac/users"),
  });

  const { data: rolesData } = useQuery({
    queryKey: ["rbac", "roles"],
    queryFn: () => enhancedApiClient.get<Role[]>("/api/rbac/roles"),
  });

  const users: User[] = Array.isArray(usersData)
    ? usersData
    : usersData?.data || [];
  const roles: Role[] = Array.isArray(rolesData)
    ? rolesData
    : rolesData?.data || [];

  const { assignRole, removeRole } = useRBAC();

  const handleAssignRole = async () => {
    if (selectedUser && selectedRole) {
      await assignRole(selectedUser, selectedRole);
      setSelectedUser("");
      setSelectedRole("");
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Assign Role to User</CardTitle>
          <CardDescription>
            Grant or adjust access levels for users.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="user-select">Select User</Label>
              <Select
                value={selectedUser}
                onValueChange={setSelectedUser}
              >
                <SelectTrigger id="user-select">
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
              <Select
                value={selectedRole}
                onValueChange={setSelectedRole}
              >
                <SelectTrigger id="role-select">
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
          <Button
            onClick={handleAssignRole}
            disabled={!selectedUser || !selectedRole}
          >
            <UserPlus className="h-4 w-4 mr-2" />
            Assign role
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Current User Role Assignments</CardTitle>
        </CardHeader>
        <CardContent>
          <UserRoleTable users={users} roles={roles} removeRole={removeRole} />
        </CardContent>
      </Card>
    </div>
  );
}

export interface UserRoleTableProps {
  users: User[];
  roles: Role[];
  removeRole: (userId: string, roleId: string) => Promise<void> | void;
}

function UserRoleTable({ users, roles, removeRole }: UserRoleTableProps) {
  const getRoleName = (roleId: string) =>
    roles.find((role) => role.id === roleId)?.name || roleId;

  return (
    <div className="space-y-4">
      {users.map((user) => (
        <div
          key={user.id}
          className="border rounded-lg p-4 sm:p-4 md:p-6"
        >
          <div className="flex items-center justify-between mb-2">
            <div>
              <h4 className="font-medium">{user.username}</h4>
              <p className="text-sm text-muted-foreground">
                {user.email}
              </p>
            </div>
            <Badge
              variant={user.metadata?.isActive ? "default" : "secondary"}
            >
              {user.metadata?.isActive ? "Active" : "Inactive"}
            </Badge>
          </div>
          <div className="flex flex-wrap gap-2">
            {user.roles.map((roleId) => (
              <div
                key={roleId}
                className="flex items-center space-x-1"
              >
                <Badge variant="outline">
                  {getRoleName(roleId)}
                </Badge>
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
              <span className="text-sm text-muted-foreground">
                No roles assigned
              </span>
            )}
          </div>
        </div>
      ))}
      {users.length === 0 && (
        <p className="text-sm text-muted-foreground">
          No users found.
        </p>
      )}
    </div>
  );
}

// --------------------------------------------------------
// Role Hierarchy View
// --------------------------------------------------------

type RoleHierarchyItem = RoleHierarchy & { roleName?: string };
type RoleHierarchyResponse =
  | RoleHierarchyItem[]
  | { data?: RoleHierarchyItem[] | undefined };

function RoleHierarchyView() {
  const { data: hierarchyData } = useQuery<RoleHierarchyResponse>({
    queryKey: ["rbac", "role-hierarchy"],
    queryFn: () => enhancedApiClient.get("/api/rbac/role-hierarchy"),
  });

  const hierarchy = React.useMemo<RoleHierarchyItem[]>(() => {
    if (Array.isArray(hierarchyData)) {
      return hierarchyData;
    }
    if (
      hierarchyData &&
      typeof hierarchyData === "object" &&
      "data" in hierarchyData &&
      Array.isArray(hierarchyData.data)
    ) {
      return hierarchyData.data;
    }
    return [];
  }, [hierarchyData]);

  return (
    <div className="space-y-4">
      <Alert>
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>
          Role hierarchy allows roles to inherit permissions from
          parent roles. Conflicts are resolved based on the configured
          resolution strategy.
        </AlertDescription>
      </Alert>

      {hierarchy.map((item) => (
        <Card key={item.roleId}>
          <CardHeader>
            <CardTitle>{item.roleName ?? item.roleId}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {item.parentRoles?.length ? (
              <div>
                <Label className="text-sm font-medium">
                  Inherits from:
                </Label>
                <div className="flex flex-wrap gap-2 mt-1">
                  {item.parentRoles.map((parentRole: string) => (
                    <Badge key={parentRole} variant="secondary">
                      {parentRole}
                    </Badge>
                  ))}
                </div>
              </div>
            ) : null}

            {item.conflicts?.length ? (
              <div>
                <Label className="text-sm font-medium text-destructive">
                  Conflicts:
                </Label>
                <div className="space-y-2 mt-1">
                  {item.conflicts.map(
                    (conflict: RoleConflict, index: number) => (
                      <Alert key={index} variant="destructive">
                        <AlertTriangle className="h-4 w-4" />
                        <AlertDescription>
                          Permission &apos;{conflict.permission}
                          &apos; conflicts between roles:{" "}
                          {conflict.conflictingRoles.join(", ")}
                          <br />
                          Resolution: {conflict.resolution}
                        </AlertDescription>
                      </Alert>
                    )
                  )}
                </div>
              </div>
            ) : null}
          </CardContent>
        </Card>
      ))}

      {hierarchy.length === 0 && (
        <p className="text-sm text-muted-foreground">
          No hierarchy data available.
        </p>
      )}
    </div>
  );
}

// --------------------------------------------------------
// Create Role Dialog
// --------------------------------------------------------

interface RoleFormState {
  name: string;
  description: string;
  permissions: Permission[];
  parentRoles: string[];
}

function createRoleFormState(role?: Role | null): RoleFormState {
  return {
    name: role?.name ?? "",
    description: role?.description ?? "",
    permissions: role?.permissions ?? [],
    parentRoles: role?.parentRoles ?? [],
  };
}

export interface CreateRoleDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

function CreateRoleDialog({ open, onOpenChange }: CreateRoleDialogProps) {
  const [formData, setFormData] = useState<RoleFormState>(() => createRoleFormState());

  const queryClient = useQueryClient();

  const createRoleMutation = useMutation({
    mutationFn: (roleData: RoleFormState) =>
      enhancedApiClient.post("/api/rbac/roles", roleData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rbac", "roles"] });
      setFormData(createRoleFormState());
      onOpenChange(false);
    },
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
            Define a new role with precise permissions for Kari.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="create-role-name">Role Name</Label>
            <Input
              id="create-role-name"
              value={formData.name}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  name: e.target.value,
                })
              }
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="create-role-description">
              Description
            </Label>
            <Textarea
              id="create-role-description"
              value={formData.description}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  description: e.target.value,
                })
              }
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
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={createRoleMutation.isPending}
            >
              Create role
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// --------------------------------------------------------
// Edit Role Dialog
// --------------------------------------------------------

export interface EditRoleDialogProps {
  role: Role | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

function EditRoleDialog({
  role,
  open,
  onOpenChange,
}: EditRoleDialogProps) {
  const queryClient = useQueryClient();

  const updateRoleMutation = useMutation({
    mutationFn: (roleData: RoleFormState) =>
      enhancedApiClient.put(`/api/rbac/roles/${role?.id}`, roleData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rbac", "roles"] });
      onOpenChange(false);
    },
  });

  const handleSubmit = (values: RoleFormState) => {
    if (role) {
      updateRoleMutation.mutate(values);
    }
  };

  return (
    <Dialog open={open && !!role} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Edit Role</DialogTitle>
          <DialogDescription>
            Update role permissions and metadata. System roles may be
            restricted.
          </DialogDescription>
        </DialogHeader>

        {role && (
          <EditRoleForm
            key={role.id}
            role={role}
            onSubmit={handleSubmit}
            onCancel={() => onOpenChange(false)}
            isSubmitting={updateRoleMutation.isPending}
          />
        )}
      </DialogContent>
    </Dialog>
  );
}

interface EditRoleFormProps {
  role: Role;
  onSubmit: (values: RoleFormState) => void;
  onCancel: () => void;
  isSubmitting: boolean;
}

function EditRoleForm({
  role,
  onSubmit,
  onCancel,
  isSubmitting,
}: EditRoleFormProps) {
  const [formData, setFormData] = useState<RoleFormState>(() =>
    createRoleFormState(role),
  );

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="edit-role-name">Role Name</Label>
        <Input
          id="edit-role-name"
          value={formData.name}
          onChange={(e) =>
            setFormData({
              ...formData,
              name: e.target.value,
            })
          }
          required
          disabled={role.metadata?.isSystemRole}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="edit-role-description">Description</Label>
        <Textarea
          id="edit-role-description"
          value={formData.description}
          onChange={(e) =>
            setFormData({
              ...formData,
              description: e.target.value,
            })
          }
          required
        />
      </div>

      <PermissionSelector
        selectedPermissions={formData.permissions}
        onPermissionsChange={(permissions) =>
          setFormData({ ...formData, permissions })
        }
        disabled={role.metadata?.isSystemRole}
      />

      <DialogFooter>
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={isSubmitting}>
          Save changes
        </Button>
      </DialogFooter>
    </form>
  );
}

// --------------------------------------------------------
// Permission Selector
// --------------------------------------------------------

export interface PermissionSelectorProps {
  selectedPermissions: Permission[];
  onPermissionsChange: (permissions: Permission[]) => void;
  disabled?: boolean;
}

function PermissionSelector({
  selectedPermissions,
  onPermissionsChange,
  disabled,
}: PermissionSelectorProps) {
  const allPermissions: Permission[] = [
    "dashboard:view",
    "dashboard:edit",
    "dashboard:admin",
    "memory:view",
    "memory:edit",
    "memory:delete",
    "memory:admin",
    "plugins:view",
    "plugins:install",
    "plugins:configure",
    "plugins:admin",
    "models:view",
    "models:configure",
    "models:admin",
    "workflows:view",
    "workflows:create",
    "workflows:execute",
    "workflows:admin",
    "chat:basic",
    "chat:advanced",
    "chat:multimodal",
    "security:view",
    "security:audit",
    "security:admin",
    "security:evil_mode",
    "system:view",
    "system:configure",
    "system:admin",
    "users:view",
    "users:manage",
    "users:admin",
  ];

  const permissionCategories: Record<string, Permission[]> = {
    Dashboard: allPermissions.filter((p) => p.startsWith("dashboard:")),
    Memory: allPermissions.filter((p) => p.startsWith("memory:")),
    Plugins: allPermissions.filter((p) => p.startsWith("plugins:")),
    Models: allPermissions.filter((p) => p.startsWith("models:")),
    Workflows: allPermissions.filter((p) =>
      p.startsWith("workflows:")
    ),
    Chat: allPermissions.filter((p) => p.startsWith("chat:")),
    Security: allPermissions.filter((p) =>
      p.startsWith("security:")
    ),
    System: allPermissions.filter((p) => p.startsWith("system:")),
    Users: allPermissions.filter((p) => p.startsWith("users:")),
  };

  const handlePermissionToggle = (permission: Permission) => {
    if (disabled) return;

    const newPermissions = selectedPermissions.includes(permission)
      ? selectedPermissions.filter((p) => p !== permission)
      : [...selectedPermissions, permission];

    onPermissionsChange(newPermissions);
  };

  return (
    <div className="space-y-4">
      <Label>Permissions</Label>
      <div className="grid gap-4">
        {Object.entries(permissionCategories).map(
          ([category, permissions]) => (
            <div key={category} className="space-y-2">
              <h4 className="font-medium text-sm md:text-base">
                {category}
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {permissions.map((permission) => (
                  <div
                    key={permission}
                    className="flex items-center space-x-2"
                  >
                    <Checkbox
                      id={permission}
                      checked={selectedPermissions.includes(
                        permission
                      )}
                      onCheckedChange={() =>
                        handlePermissionToggle(permission)
                      }
                      disabled={disabled}
                    />
                    <Label
                      htmlFor={permission}
                      className="text-sm"
                    >
                      {permission.split(":")[1]}
                    </Label>
                  </div>
                ))}
              </div>
            </div>
          )
        )}
      </div>
      <Separator />
    </div>
  );
}

export default RoleManagement;
