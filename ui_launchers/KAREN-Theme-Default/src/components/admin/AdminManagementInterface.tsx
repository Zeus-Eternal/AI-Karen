"use client";

/**
 * Admin Management Interface Component (Prod-Grade)
 *
 * Manage administrators: invite, promote, demote, activate/deactivate, filter, and search.
 * Dependencies: shadcn/ui (Card, Button, Input, Select, Dialog, Table, Badge), ErrorBoundary, useToast
 * API contracts used (expected):
 *  - GET  /api/admin/admins
 *  - GET  /api/admin/users?role=user
 *  - POST /api/admin/admins/invite          { email, message }
 *  - POST /api/admin/admins/promote/:userId
 *  - POST /api/admin/admins/demote/:adminId
 *  - PATCH /api/admin/admins/:adminId       { isActive: boolean }
 */

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ErrorBoundary } from "@/components/error-handling/ErrorBoundary";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger
} from "@/components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/hooks/use-toast";
import type { User } from "@/types/admin";
import {
  Filter,
  Mail,
  Search as SearchIcon,
  Shield,
  ShieldCheck,
  UserPlus,
  UserX,
  UserCheck
} from "lucide-react";

export type AdminStatusFilter = "all" | "active" | "inactive";

export interface AdminUser extends User {
  lastLogin?: Date;
  invitedAt?: Date;
  invitedBy?: string;
}

export interface InviteAdminForm {
  email: string;
  message: string;
}

export default function AdminManagementInterface() {
  const [admins, setAdmins] = useState<AdminUser[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  const [searchQuery, setSearchQuery] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<AdminStatusFilter>("all");

  const [showInviteDialog, setShowInviteDialog] = useState<boolean>(false);
  const [showPromoteDialog, setShowPromoteDialog] = useState<boolean>(false);

  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);

  const [inviteForm, setInviteForm] = useState<InviteAdminForm>({
    email: "",
    message: ""
  });

  const { toast } = useToast();
  const abortRef = useRef<AbortController | null>(null);

  /* ----------------------------- Data Loaders ----------------------------- */

  const normalizeAdmin = (admin: unknown): AdminUser => {
    const createdAt = admin.created_at ? new Date(admin.created_at) : new Date();
    const updatedAt = admin.updated_at ? new Date(admin.updated_at) : createdAt;
    const lastLogin = admin.last_login_at ? new Date(admin.last_login_at) : undefined;
    const invitedAt = admin.invited_at ? new Date(admin.invited_at) : createdAt;
    return {
      user_id: admin.user_id,
      email: admin.email,
      full_name: admin.full_name ?? "",
      role: admin.role ?? "admin",
      roles: Array.isArray(admin.roles) && admin.roles.length ? admin.roles : [admin.role ?? "admin"],
      tenant_id: admin.tenant_id ?? "default",
      preferences: admin.preferences ?? {},
      is_verified: Boolean(admin.is_verified),
      is_active: Boolean(admin.is_active),
      created_at: createdAt,
      updated_at: updatedAt,
      last_login_at: lastLogin,
      failed_login_attempts: admin.failed_login_attempts ?? 0,
      locked_until: admin.locked_until ? new Date(admin.locked_until) : undefined,
      two_factor_enabled: Boolean(admin.two_factor_enabled),
      created_by: admin.created_by ?? undefined,
      lastLogin,
      invitedAt,
      invitedBy: admin.invited_by ?? admin.created_by ?? undefined
    };
  };

  const loadAdmins = useCallback(async () => {
    setLoading(true);
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const response = await fetch("/api/admin/admins", {
        signal: controller.signal,
        headers: { "Cache-Control": "no-store" }
      });
      if (!response.ok) throw new Error("Failed to load administrators");
      const payload = await response.json();

      const adminsData = Array.isArray(payload?.data?.admins)
        ? payload.data.admins
        : Array.isArray(payload?.admins)
          ? payload.admins
          : Array.isArray(payload)
            ? payload
            : [];

      setAdmins(adminsData.map((a: unknown) => normalizeAdmin(a)));
    } catch (_error: Error) {
      if (error?.name !== "AbortError") {
        toast({
          title: "Error",
          description: "Failed to load administrators",
          variant: "destructive"
        });
      }
    } finally {
      if (!controller.signal.aborted) setLoading(false);
    }
  }, [toast]);

  const loadUsers = useCallback(async () => {
    try {
      const response = await fetch("/api/admin/users?role=user", {
        headers: { "Cache-Control": "no-store" }
      });
      if (!response.ok) return;
      const data = await response.json();
      const arr = Array.isArray(data?.data) ? data.data : Array.isArray(data) ? data : [];
      setUsers(arr);
    } catch {
      /* silent */
    }
  }, []);

  useEffect(() => {
    loadAdmins();
    loadUsers();
    return () => abortRef.current?.abort();
  }, [loadAdmins, loadUsers]);

  /* ------------------------------ Actions -------------------------------- */

  const handleInviteAdmin = async () => {
    if (!inviteForm.email) {
      toast({
        title: "Email required",
        description: "Please enter an email address.",
        variant: "destructive"
      });
      return;
    }

    try {
      const response = await fetch("/api/admin/admins/invite", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(inviteForm)
      });

      if (!response.ok) {
        const error = await safeJson(response);
        throw new Error(error?.message || "Failed to send invitation");
      }

      toast({
        title: "Invitation sent",
        description: `Invite sent to ${inviteForm.email}.`
      });

      setShowInviteDialog(false);
      setInviteForm({ email: "", message: "" });
      loadAdmins();
    } catch (error: unknown) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to send invitation",
        variant: "destructive"
      });
    }
  };

  const handlePromoteUser = async (userId: string) => {
    try {
      const response = await fetch(`/api/admin/admins/promote/${userId}`, {
        method: "POST"
      });

      if (!response.ok) {
        const error = await safeJson(response);
        throw new Error(error?.message || "Failed to promote user");
      }

      toast({ title: "Success", description: "User promoted to administrator." });
      setShowPromoteDialog(false);
      setSelectedUserId(null);
      loadAdmins();
      loadUsers();
    } catch (error: unknown) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to promote user",
        variant: "destructive"
      });
    }
  };

  const handleDemoteAdmin = async (adminId: string) => {
    const ok = window.confirm(
      "Are you sure you want to demote this administrator? They will lose all admin privileges."
    );
    if (!ok) return;

    try {
      const response = await fetch(`/api/admin/admins/demote/${adminId}`, {
        method: "POST"
      });

      if (!response.ok) {
        const error = await safeJson(response);
        throw new Error(error?.message || "Failed to demote administrator");
      }

      toast({ title: "Success", description: "Administrator demoted." });
      loadAdmins();
      loadUsers();
    } catch (error: unknown) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to demote administrator",
        variant: "destructive"
      });
    }
  };

  const handleToggleAdminStatus = async (adminId: string, isActive: boolean) => {
    try {
      const response = await fetch(`/api/admin/admins/${adminId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ isActive: !isActive })
      });

      if (!response.ok) {
        const error = await safeJson(response);
        throw new Error(error?.message || "Failed to update administrator status");
      }

      toast({
        title: "Success",
        description: `Administrator ${!isActive ? "activated" : "deactivated"}.`
      });
      loadAdmins();
    } catch (error: unknown) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to update administrator status",
        variant: "destructive"
      });
    }
  };

  /* ------------------------------- Derived -------------------------------- */

  const filteredAdmins = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    return admins.filter((admin) => {
      const matchesSearch =
        !q ||
        admin.email.toLowerCase().includes(q) ||
        (admin.full_name || "").toLowerCase().includes(q);

      const matchesStatus =
        statusFilter === "all" ||
        (statusFilter === "active" && admin.is_active) ||
        (statusFilter === "inactive" && !admin.is_active);

      return matchesSearch && matchesStatus;
    });
  }, [admins, searchQuery, statusFilter]);

  const selectedUser = useMemo(
    () => users.find((u) => u.user_id === selectedUserId) || null,
    [users, selectedUserId]
  );

  const formatLastLogin = (date?: Date | string | null) => {
    if (!date) return "Never";
    try {
      return new Date(date).toLocaleDateString();
    } catch {
      return "Unknown";
    }
  };

  /* -------------------------------- Render -------------------------------- */

  return (
    <ErrorBoundary>
      <div className="space-y-6">
        {/* Header Actions */}
        <div className="flex flex-col sm:flex-row gap-4 justify-between">
          <div className="flex flex-1 gap-4">
            <div className="relative flex-1 max-w-sm">
              <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 h-4 w-4" />
              <Input
                placeholder="Search administrators..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
                aria-label="Search administrators"
              />
            </div>

            <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v as AdminStatusFilter)}>
              <SelectTrigger className="w-40" aria-label="Filter by status">
                <Filter className="h-4 w-4 mr-2" />
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="inactive">Inactive</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex gap-2">
            {/* Invite Admin */}
            <Dialog open={showInviteDialog} onOpenChange={setShowInviteDialog}>
              <DialogTrigger asChild>
                <Button aria-label="Invite Administrator">
                  <Mail className="mr-2 h-4 w-4" />
                  Invite Admin
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Invite New Administrator</DialogTitle>
                  <DialogDescription>
                    Send an invitation email to create a new administrator account.
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="invite-email">Email Address</Label>
                    <Input
                      id="invite-email"
                      type="email"
                      placeholder="admin@example.com"
                      value={inviteForm.email}
                      onChange={(e) => setInviteForm((p) => ({ ...p, email: e.target.value }))}
                    />
                  </div>
                  <div>
                    <Label htmlFor="invite-message">Custom Message (Optional)</Label>
                    <Textarea
                      id="invite-message"
                      placeholder="Welcome to the admin team..."
                      value={inviteForm.message}
                      onChange={(e) => setInviteForm((p) => ({ ...p, message: e.target.value }))}
                      rows={3}
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setShowInviteDialog(false)}>
                    Cancel
                  </Button>
                  <Button onClick={handleInviteAdmin}>Send Invite</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>

            {/* Promote User */}
            <Dialog open={showPromoteDialog} onOpenChange={setShowPromoteDialog}>
              <DialogTrigger asChild>
                <Button variant="outline" aria-label="Promote user to admin">
                  <UserPlus className="mr-2 h-4 w-4" />
                  Promote User
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Promote User to Administrator</DialogTitle>
                  <DialogDescription>Select a user to promote to administrator role.</DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <Label>Select User</Label>
                    <Select value={selectedUserId ?? ""} onValueChange={(v) => setSelectedUserId(v)}>
                      <SelectTrigger aria-label="Select user to promote">
                        <SelectValue placeholder="Choose a user to promote" />
                      </SelectTrigger>
                      <SelectContent>
                        {users.map((u) => (
                          <SelectItem key={u.user_id} value={u.user_id}>
                            {u.email} {u.full_name ? `(${u.full_name})` : "(No name)"}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {selectedUser && (
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <h4 className="font-medium">Selected User</h4>
                      <p className="text-sm text-gray-600">{selectedUser.email}</p>
                      <p className="text-sm text-gray-600">
                        Name: {selectedUser.full_name || "Not provided"}
                      </p>
                      <p className="text-sm text-gray-600">
                        Joined: {new Date(selectedUser.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  )}
                </div>
                <DialogFooter>
                  <Button
                    variant="outline"
                    onClick={() => {
                      setShowPromoteDialog(false);
                      setSelectedUserId(null);
                    }}
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={() => selectedUserId && handlePromoteUser(selectedUserId)}
                    disabled={!selectedUserId}
                  >
                    Promote
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {/* Administrators Table */}
        <Card>
          <CardHeader>
            <CardTitle>Administrators</CardTitle>
            <CardDescription>Invite, manage roles, and control access.</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
                <span className="ml-2">Loading administrators...</span>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Administrator</TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Last Login</TableHead>
                    <TableHead>Invited</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredAdmins.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-8 text-gray-500">
                        No administrators found.
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredAdmins.map((admin) => (
                      <TableRow key={admin.user_id}>
                        <TableCell>
                          <div>
                            <div className="font-medium">{admin.email}</div>
                            <div className="text-sm text-gray-500">{admin.full_name || "No name"}</div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant={admin.role === "super_admin" ? "default" : "secondary"}>
                            {admin.role === "super_admin" ? (
                              <>
                                <ShieldCheck className="mr-1 h-3 w-3" />
                                Super Admin
                              </>
                            ) : (
                              <>
                                <Shield className="mr-1 h-3 w-3" />
                                Admin
                              </>
                            )}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant={admin.is_active ? "default" : "secondary"}>
                            {admin.is_active ? "Active" : "Inactive"}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-sm text-gray-600">
                          {formatLastLogin(admin.lastLogin ?? admin.last_login_at)}
                        </TableCell>
                        <TableCell className="text-sm text-gray-600">
                          {(admin.invitedAt ?? admin.created_at) ? (
                            <div>
                              <div>{new Date(admin.invitedAt ?? admin.created_at).toLocaleDateString()}</div>
                              {admin.invitedBy && (
                                <div className="text-xs text-gray-500">by {admin.invitedBy}</div>
                              )}
                            </div>
                          ) : (
                            "Direct creation"
                          )}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex items-center justify-end gap-2">
                            {admin.role !== "super_admin" && (
                              <>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => handleToggleAdminStatus(admin.user_id, admin.is_active)}
                                >
                                  {admin.is_active ? (
                                    <>
                                      <UserX className="mr-1 h-3 w-3" />
                                      Deactivate
                                    </>
                                  ) : (
                                    <>
                                      <UserCheck className="mr-1 h-3 w-3" />
                                      Activate
                                    </>
                                  )}
                                </Button>
                                <Button
                                  variant="destructive"
                                  size="sm"
                                  onClick={() => handleDemoteAdmin(admin.user_id)}
                                >
                                  Demote
                                </Button>
                              </>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </ErrorBoundary>
  );
}

/* --------------------------------- Utils --------------------------------- */

async function safeJson(res: Response) {
  try {
    return await res.json();
  } catch {
    return null;
  }
}
