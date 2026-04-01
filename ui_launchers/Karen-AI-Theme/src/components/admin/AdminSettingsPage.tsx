"use client";

import { useEffect, useState } from "react";
import { Users, BarChart, Bell, Database, MoreHorizontal, PlusCircle, Search, Trash2, UserPlus, BrainCircuit, Eye, PenSquare, UserCog, Ban, Bot, Shield, FileText, Activity, GraduationCap } from "lucide-react";
import { apiClient, ApiError } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuLabel, DropdownMenuSeparator } from "@/components/ui/dropdown-menu";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogClose } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import FallbackModelSettings from "./FallbackModelSettings";
import SystemConfigPanel from "./SystemConfigPanel";
import AuditLogPanel from "./AuditLogPanel";
import TrainingSettingsPanel from "./TrainingSettingsPanel";
import CommsCenterPage from "@/components/comms/CommsCenterPage";
import AdminAnalyticsPanel from "./AdminAnalyticsPanel";
import AdminDatabasePanel from "./AdminDatabasePanel";

type UserRole = "Admin" | "User" | "Editor";
type UserStatus = "Active" | "Suspended" | "Pending";

type User = {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  status: UserStatus;
  createdAt: string;
  lastLogin: string | null;
  timeSpent: string | null;
  tokenUsage: number | null;
};

type BackendUserResponse = {
  user_id: string;
  email: string;
  full_name?: string | null;
  tenant_id: string;
  roles: string[];
  preferences: Record<string, unknown>;
  is_active: boolean;
  is_verified: boolean;
  last_login?: string | null;
  created_at: string;
  updated_at: string;
};

type UserMetricsResponse = {
  user_id: string;
  hours: number;
  event_count: number;
  session_count: number;
  total_session_minutes: number;
  average_session_minutes: number;
  last_seen?: string | null;
  token_usage?: number | null;
  token_usage_supported: boolean;
};

const getInitials = (name: string) => {
  const names = name.split(' ');
  if (names.length === 1) return names[0].charAt(0).toUpperCase();
  return (names[0].charAt(0) + names[names.length - 1].charAt(0)).toUpperCase();
};

const getStatusBadgeVariant = (status: UserStatus) => {
  switch (status) {
    case 'Active': return 'secondary' as const;
    case 'Suspended': return 'destructive' as const;
    case 'Pending': return 'outline' as const;
    default: return 'secondary' as const;
  }
};

const getRoleBadgeVariant = (role: UserRole) => {
  switch (role) {
    case 'Admin': return 'default' as const;
    case 'Editor': return 'secondary' as const;
    default: return 'outline' as const;
  }
};

const formatNumber = (num: number) => {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
  return num.toString();
};

const formatLastLogin = (value: string | null) => {
  if (!value) {
    return "Not recorded";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleString();
};

export default function AdminSettingsPage() {
  const { toast } = useToast();
  const [users, setUsers] = useState<User[]>([]);
  const [usersLoading, setUsersLoading] = useState(true);
  const [usersAuthRequired, setUsersAuthRequired] = useState(false);
  const [usersAccessDenied, setUsersAccessDenied] = useState(false);
  const [usersLoadError, setUsersLoadError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [editDialogMode, setEditDialogMode] = useState<"view" | "edit">("edit");
  const [userMetrics, setUserMetrics] = useState<UserMetricsResponse | null>(null);
  const [userMetricsLoading, setUserMetricsLoading] = useState(false);
  const [userMetricsError, setUserMetricsError] = useState<string | null>(null);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isCreatingUser, setIsCreatingUser] = useState(false);
  const [isUpdatingUser, setIsUpdatingUser] = useState(false);
  const [createForm, setCreateForm] = useState({
    name: "",
    email: "",
    password: "",
    role: "user",
  });
  const [editForm, setEditForm] = useState({
    name: "",
    email: "",
    role: "User",
  });

  const mapBackendUser = (user: BackendUserResponse): User => ({
    id: user.user_id,
    name: user.full_name || user.email || user.user_id,
    email: user.email,
    role: user.roles.includes("admin") ? "Admin" : user.roles.includes("editor") ? "Editor" : "User",
    status: !user.is_verified ? "Pending" : user.is_active ? "Active" : "Suspended",
    createdAt: new Date(user.created_at).toLocaleDateString(),
    lastLogin: user.last_login || null,
    timeSpent: null,
    tokenUsage: null,
  });

  useEffect(() => {
    let mounted = true;

    const loadUsers = async () => {
      setUsersLoading(true);
      setUsersAuthRequired(false);
      setUsersAccessDenied(false);
      try {
        const response = await apiClient.get<BackendUserResponse[]>("/api/users");
        if (!mounted) {
          return;
        }
        setUsers(Array.isArray(response) ? response.map(mapBackendUser) : []);
        setUsersLoadError(null);
      } catch (error) {
        if (!mounted) {
          return;
        }
        if (error instanceof ApiError && error.status === 401) {
          setUsers([]);
          setUsersAuthRequired(true);
          setUsersAccessDenied(false);
          setUsersLoadError(null);
        } else if (error instanceof ApiError && error.status === 403) {
          setUsers([]);
          setUsersAuthRequired(false);
          setUsersAccessDenied(true);
          setUsersLoadError(null);
        } else {
          setUsers([]);
          setUsersAuthRequired(false);
          setUsersAccessDenied(false);
          setUsersLoadError(error instanceof Error ? error.message : "Karen could not load backend users.");
        }
      } finally {
        if (mounted) {
          setUsersLoading(false);
        }
      }
    };

    void loadUsers();
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    if (!editingUser) {
      return;
    }

    setEditForm({
      name: editingUser.name,
      email: editingUser.email,
      role: editingUser.role,
    });
  }, [editingUser]);

  useEffect(() => {
    if (!editingUser) {
      setUserMetrics(null);
      setUserMetricsError(null);
      setUserMetricsLoading(false);
      return;
    }

    let mounted = true;

    const loadUserMetrics = async () => {
      setUserMetricsLoading(true);
      setUserMetricsError(null);
      try {
        const response = await apiClient.get<UserMetricsResponse>(`/api/users/${editingUser.id}/metrics?hours=168`);
        if (!mounted) {
          return;
        }
        setUserMetrics(response);
      } catch (error) {
        if (!mounted) {
          return;
        }
        setUserMetrics(null);
        setUserMetricsError(error instanceof Error ? error.message : "Karen could not load backend user metrics.");
      } finally {
        if (mounted) {
          setUserMetricsLoading(false);
        }
      }
    };

    void loadUserMetrics();
    return () => {
      mounted = false;
    };
  }, [editingUser]);

  const filteredUsers = users.filter(user =>
    user.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    user.email.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleToggleSuspend = async (userId: string) => {
    const targetUser = users.find((user) => user.id === userId);
    if (!targetUser) {
      return;
    }

    const nextActiveState = targetUser.status !== "Active";

    try {
      await apiClient.put(`/api/users/${userId}`, {
        is_active: nextActiveState,
      });
      setUsers(users.map(user =>
        user.id === userId ? { ...user, status: nextActiveState ? "Active" : "Suspended" } : user
      ));
    } catch (error) {
      toast({
        title: "User update failed",
        description: error instanceof Error ? error.message : "Karen could not update the user status.",
        variant: "destructive",
      });
    }
  };

  const handleDeleteUser = async (userId: string) => {
    try {
      await apiClient.delete(`/api/users/${userId}`);
      setUsers(users.filter(user => user.id !== userId));
    } catch (error) {
      toast({
        title: "User deletion failed",
        description: error instanceof Error ? error.message : "Karen could not delete the user.",
        variant: "destructive",
      });
    }
  };

  const openUserDialog = (user: User, mode: "view" | "edit") => {
    setEditDialogMode(mode);
    setEditingUser(user);
  };

  const handleCreateUser = async () => {
    setIsCreatingUser(true);
    try {
      const response = await apiClient.post<BackendUserResponse>("/api/users", {
        email: createForm.email.trim(),
        password: createForm.password,
        full_name: createForm.name.trim() || null,
        roles: [createForm.role],
      });

      setUsers((current) => [mapBackendUser(response), ...current]);
      setIsCreateDialogOpen(false);
      setCreateForm({
        name: "",
        email: "",
        password: "",
        role: "user",
      });
      toast({
        title: "User created",
        description: `${response.email} was added through Karen's backend user service.`,
      });
    } catch (error) {
      toast({
        title: "User creation failed",
        description: error instanceof Error ? error.message : "Karen could not create the user.",
        variant: "destructive",
      });
    } finally {
      setIsCreatingUser(false);
    }
  };

  const handleSaveUser = async () => {
    if (!editingUser) {
      return;
    }

    setIsUpdatingUser(true);
    try {
      const response = await apiClient.put<BackendUserResponse>(`/api/users/${editingUser.id}`, {
        full_name: editForm.name.trim(),
        roles: [editForm.role.toLowerCase()],
      });

      setUsers((current) => current.map((user) => (user.id === editingUser.id ? mapBackendUser(response) : user)));
      setEditingUser(null);
      toast({
        title: "User updated",
        description: `${response.email} was updated through Karen's backend user service.`,
      });
    } catch (error) {
      toast({
        title: "User update failed",
        description: error instanceof Error ? error.message : "Karen could not update the user.",
        variant: "destructive",
      });
    } finally {
      setIsUpdatingUser(false);
    }
  };

  return (
    <>
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight flex items-center gap-2">
            <Shield className="h-6 w-6 text-primary" />
            Admin Settings
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Manage users, configure fallback models, monitor system health, and review audit logs.
          </p>
        </div>
        <Separator />

        <Tabs defaultValue="users" className="w-full">
          <TabsList className="flex flex-wrap w-full justify-start shrink-0 h-auto">
            <TabsTrigger value="users"><Users className="mr-1.5 h-4 w-4" />Users</TabsTrigger>
            <TabsTrigger value="models"><Bot className="mr-1.5 h-4 w-4" />Fallback Models</TabsTrigger>
            <TabsTrigger value="training"><GraduationCap className="mr-1.5 h-4 w-4" />Training</TabsTrigger>
            <TabsTrigger value="communications"><Bell className="mr-1.5 h-4 w-4" />Communications</TabsTrigger>
            <TabsTrigger value="system"><Activity className="mr-1.5 h-4 w-4" />System</TabsTrigger>
            <TabsTrigger value="database"><Database className="mr-1.5 h-4 w-4" />Database</TabsTrigger>
            <TabsTrigger value="analytics"><BarChart className="mr-1.5 h-4 w-4" />Analytics</TabsTrigger>
            <TabsTrigger value="audit"><FileText className="mr-1.5 h-4 w-4" />Audit Log</TabsTrigger>
          </TabsList>

          {/* ── Users Tab ── */}
          <TabsContent value="users" className="mt-6">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5 mb-6">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Users</CardTitle>
                  <Users className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{users.length}</div>
                  <p className="text-xs text-muted-foreground">All registered users</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Active Users</CardTitle>
                  <Users className="h-4 w-4 text-green-500" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{users.filter(u => u.status === 'Active').length}</div>
                  <p className="text-xs text-muted-foreground">Users currently active</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">User Metrics</CardTitle>
                  <BrainCircuit className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">--</div>
                  <p className="text-xs text-muted-foreground">Per-user token and session metrics are not yet exposed by the backend contract.</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Pending</CardTitle>
                  <UserPlus className="h-4 w-4 text-yellow-500" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{users.filter(u => u.status === 'Pending').length}</div>
                  <p className="text-xs text-muted-foreground">Awaiting activation</p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Suspended</CardTitle>
                  <Users className="h-4 w-4 text-destructive" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{users.filter(u => u.status === 'Suspended').length}</div>
                  <p className="text-xs text-muted-foreground">Suspended access</p>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>User Management</CardTitle>
                <CardDescription>View, manage, and control user accounts and roles through Karen&apos;s backend user service.</CardDescription>
              </CardHeader>
              <CardContent>
                {usersAccessDenied && (
                  <Alert className="mb-6 border-primary/20 bg-primary/5">
                    <Shield className="h-4 w-4 !text-primary" />
                    <AlertTitle>User Access Restricted</AlertTitle>
                    <AlertDescription>
                      The users route is live, but this session is not authorized to list or manage backend user records.
                    </AlertDescription>
                  </Alert>
                )}
                {usersAuthRequired && (
                  <Alert className="mb-6 border-primary/20 bg-primary/5">
                    <Shield className="h-4 w-4 !text-primary" />
                    <AlertTitle>Sign In Required</AlertTitle>
                    <AlertDescription>
                      The users route is live, but this session is not authenticated. Sign in before listing or managing backend user records.
                    </AlertDescription>
                  </Alert>
                )}
                {usersLoadError && (
                  <Alert className="mb-6 border-yellow-500/30 bg-yellow-500/5">
                    <Activity className="h-4 w-4 !text-yellow-600" />
                    <AlertTitle>User Inventory Unavailable</AlertTitle>
                    <AlertDescription>{usersLoadError}</AlertDescription>
                  </Alert>
                )}
                <div className="flex items-center justify-between gap-4 mb-6">
                  <div className="flex-1 relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Search users by name or email..."
                      className="pl-10 max-w-md"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                  </div>
                  <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
                    <DialogTrigger asChild>
                      <Button>
                        <PlusCircle className="mr-2 h-4 w-4" /> Add User
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="sm:max-w-[425px]">
                      <DialogHeader>
                        <DialogTitle>Add New User</DialogTitle>
                        <DialogDescription>Create a new user account and assign them a role.</DialogDescription>
                      </DialogHeader>
                      <div className="grid gap-4 py-4">
                        <div className="grid grid-cols-4 items-center gap-4">
                          <Label htmlFor="name" className="text-right">Name</Label>
                          <Input
                            id="name"
                            placeholder="John Doe"
                            className="col-span-3"
                            value={createForm.name}
                            onChange={(e) => setCreateForm((current) => ({ ...current, name: e.target.value }))}
                          />
                        </div>
                        <div className="grid grid-cols-4 items-center gap-4">
                          <Label htmlFor="email" className="text-right">Email</Label>
                          <Input
                            id="email"
                            type="email"
                            placeholder="john@example.com"
                            className="col-span-3"
                            value={createForm.email}
                            onChange={(e) => setCreateForm((current) => ({ ...current, email: e.target.value }))}
                          />
                        </div>
                        <div className="grid grid-cols-4 items-center gap-4">
                          <Label htmlFor="password" className="text-right">Password</Label>
                          <Input
                            id="password"
                            type="password"
                            placeholder="Temporary password"
                            className="col-span-3"
                            value={createForm.password}
                            onChange={(e) => setCreateForm((current) => ({ ...current, password: e.target.value }))}
                          />
                        </div>
                        <div className="grid grid-cols-4 items-center gap-4">
                          <Label htmlFor="role" className="text-right">Role</Label>
                          <Select value={createForm.role} onValueChange={(value) => setCreateForm((current) => ({ ...current, role: value }))}>
                            <SelectTrigger className="col-span-3"><SelectValue placeholder="Select a role" /></SelectTrigger>
                            <SelectContent>
                              <SelectItem value="user">User</SelectItem>
                              <SelectItem value="editor">Editor</SelectItem>
                              <SelectItem value="admin">Admin</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                      <DialogFooter>
                        <DialogClose asChild><Button variant="outline">Cancel</Button></DialogClose>
                        <Button
                          type="submit"
                          onClick={() => void handleCreateUser()}
                          disabled={isCreatingUser || !createForm.email.trim() || !createForm.password.trim()}
                        >
                          {isCreatingUser ? "Creating..." : "Create and Invite"}
                        </Button>
                      </DialogFooter>
                    </DialogContent>
                  </Dialog>
                </div>

                {usersLoading ? (
                  <div className="flex items-center gap-2 rounded-xl border border-border/70 p-4 text-sm text-muted-foreground">
                    <Activity className="h-4 w-4 animate-pulse" />
                    Loading backend user inventory.
                  </div>
                ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[40px]"><Checkbox /></TableHead>
                      <TableHead>User</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Role</TableHead>
                      <TableHead>Last Login</TableHead>
                      <TableHead>Time Spent</TableHead>
                      <TableHead className="text-right">Token Usage</TableHead>
                      <TableHead>Date Added</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredUsers.map(user => (
                      <TableRow key={user.id}>
                        <TableCell><Checkbox /></TableCell>
                        <TableCell>
                          <div className="flex items-center gap-3">
                            <Avatar><AvatarFallback>{getInitials(user.name)}</AvatarFallback></Avatar>
                            <div>
                              <div className="font-medium">{user.name}</div>
                              <div className="text-sm text-muted-foreground">{user.email}</div>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell><Badge variant={getStatusBadgeVariant(user.status)}>{user.status}</Badge></TableCell>
                        <TableCell><Badge variant={getRoleBadgeVariant(user.role)}>{user.role}</Badge></TableCell>
                        <TableCell>{formatLastLogin(user.lastLogin)}</TableCell>
                        <TableCell>{user.timeSpent || 'Not instrumented'}</TableCell>
                        <TableCell className="text-right">{user.tokenUsage == null ? 'Not instrumented' : formatNumber(user.tokenUsage)}</TableCell>
                        <TableCell>{user.createdAt}</TableCell>
                        <TableCell className="text-right">
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon"><MoreHorizontal className="h-4 w-4" /></Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuLabel>Actions</DropdownMenuLabel>
                              <DropdownMenuItem onClick={() => openUserDialog(user, "view")}>
                                <Eye className="mr-2 h-4 w-4" /> View Details
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => openUserDialog(user, "edit")}>
                                <PenSquare className="mr-2 h-4 w-4" /> Edit User
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => openUserDialog(user, "edit")}>
                                <UserCog className="mr-2 h-4 w-4" /> Change Role
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem onClick={() => handleToggleSuspend(user.id)}>
                                <Ban className="mr-2 h-4 w-4" /> {user.status === 'Active' ? 'Suspend' : 'Unsuspend'}
                              </DropdownMenuItem>
                              <AlertDialog>
                                <AlertDialogTrigger asChild>
                                  <DropdownMenuItem className="text-destructive" onSelect={(e) => e.preventDefault()}>
                                    <Trash2 className="mr-2 h-4 w-4" /> Delete User
                                  </DropdownMenuItem>
                                </AlertDialogTrigger>
                                <AlertDialogContent>
                                  <AlertDialogHeader>
                                    <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
                                    <AlertDialogDescription>
                                      This will permanently delete the account for <span className="font-semibold">{user.name}</span>.
                                    </AlertDialogDescription>
                                  </AlertDialogHeader>
                                  <AlertDialogFooter>
                                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                                    <AlertDialogAction className="bg-destructive hover:bg-destructive/90" onClick={() => handleDeleteUser(user.id)}>Delete</AlertDialogAction>
                                  </AlertDialogFooter>
                                </AlertDialogContent>
                              </AlertDialog>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* ── Fallback Models Tab ── */}
          <TabsContent value="models" className="mt-6">
            <FallbackModelSettings />
          </TabsContent>

          {/* ── Training Tab ── */}
          <TabsContent value="training" className="mt-6">
            <TrainingSettingsPanel />
          </TabsContent>

          {/* ── Communications Tab ── */}
          <TabsContent value="communications" className="mt-6">
            <CommsCenterPage />
          </TabsContent>

          {/* ── System Tab ── */}
          <TabsContent value="system" className="mt-6">
            <SystemConfigPanel />
          </TabsContent>

          {/* ── Database Tab ── */}
          <TabsContent value="database" className="mt-6 space-y-6">
            <AdminDatabasePanel />
          </TabsContent>

          {/* ── Analytics Tab ── */}
          <TabsContent value="analytics" className="mt-6">
            <AdminAnalyticsPanel />
          </TabsContent>

          {/* ── Audit Log Tab ── */}
          <TabsContent value="audit" className="mt-6">
            <AuditLogPanel />
          </TabsContent>
        </Tabs>
      </div>

      {/* Edit User Dialog */}
      <Dialog open={!!editingUser} onOpenChange={(isOpen) => !isOpen && setEditingUser(null)}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>{editDialogMode === "view" ? "User Details" : "Edit User"}: {editingUser?.name}</DialogTitle>
            <DialogDescription>
              {editDialogMode === "view"
                ? "Review backend-derived account details for this user."
                : "Modify the details for this user account."}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="edit-name" className="text-right">Name</Label>
              <Input
                id="edit-name"
                value={editForm.name}
                onChange={(e) => setEditForm((current) => ({ ...current, name: e.target.value }))}
                className="col-span-3"
                disabled={editDialogMode === "view"}
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="edit-email" className="text-right">Email</Label>
              <Input id="edit-email" type="email" value={editForm.email} className="col-span-3" disabled />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="edit-role" className="text-right">Role</Label>
              <Select
                value={editForm.role}
                onValueChange={(value) => setEditForm((current) => ({ ...current, role: value as UserRole }))}
                disabled={editDialogMode === "view"}
              >
                <SelectTrigger className="col-span-3"><SelectValue placeholder="Select a role" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="User">User</SelectItem>
                  <SelectItem value="Editor">Editor</SelectItem>
                  <SelectItem value="Admin">Admin</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="edit-status" className="text-right">Status</Label>
              <Input id="edit-status" value={editingUser?.status || ""} className="col-span-3" disabled />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="edit-last-login" className="text-right">Last Login</Label>
              <Input id="edit-last-login" value={editingUser ? formatLastLogin(editingUser.lastLogin) : ""} className="col-span-3" disabled />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="edit-user-events" className="text-right">Events</Label>
              <Input
                id="edit-user-events"
                value={userMetricsLoading ? "Loading..." : userMetrics ? String(userMetrics.event_count) : userMetricsError ? "Unavailable" : "Not recorded"}
                className="col-span-3"
                disabled
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="edit-user-sessions" className="text-right">Sessions</Label>
              <Input
                id="edit-user-sessions"
                value={userMetricsLoading ? "Loading..." : userMetrics ? String(userMetrics.session_count) : userMetricsError ? "Unavailable" : "Not recorded"}
                className="col-span-3"
                disabled
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="edit-user-session-minutes" className="text-right">Session Minutes</Label>
              <Input
                id="edit-user-session-minutes"
                value={
                  userMetricsLoading
                    ? "Loading..."
                    : userMetrics
                      ? `${userMetrics.total_session_minutes.toFixed(1)} total / ${userMetrics.average_session_minutes.toFixed(1)} avg`
                      : userMetricsError
                        ? "Unavailable"
                        : "Not recorded"
                }
                className="col-span-3"
                disabled
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="edit-user-last-seen" className="text-right">Last Seen</Label>
              <Input
                id="edit-user-last-seen"
                value={
                  userMetricsLoading
                    ? "Loading..."
                    : userMetrics?.last_seen
                      ? formatLastLogin(userMetrics.last_seen)
                      : userMetricsError
                        ? "Unavailable"
                        : "Not recorded"
                }
                className="col-span-3"
                disabled
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="edit-user-token-usage" className="text-right">Token Usage</Label>
              <Input
                id="edit-user-token-usage"
                value={
                  userMetricsLoading
                    ? "Loading..."
                    : userMetrics?.token_usage_supported
                      ? String(userMetrics.token_usage ?? 0)
                      : "Not instrumented"
                }
                className="col-span-3"
                disabled
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditingUser(null)}>Cancel</Button>
            {editDialogMode === "edit" && (
              <Button type="submit" onClick={() => void handleSaveUser()} disabled={isUpdatingUser}>
                {isUpdatingUser ? "Saving..." : "Save Changes"}
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
