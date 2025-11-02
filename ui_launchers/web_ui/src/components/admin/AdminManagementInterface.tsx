"use client";

/**
 * Admin Management Interface Component
 * 
 * This component provides the interface for managing administrators,
 * including creating, promoting, demoting, and inviting admin users.
 */
import React, { useState, useEffect } from 'react';
import { ErrorBoundary } from '@/components/error-handling/ErrorBoundary';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import { User } from '@/types/admin';

import { } from 'lucide-react';
interface AdminUser extends User {
  lastLogin?: Date;
  invitedAt?: Date;
  invitedBy?: string;
}
interface InviteAdminForm {
  email: string;
  message: string;
}
export default function AdminManagementInterface() {
  const [admins, setAdmins] = useState<AdminUser[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all');
  const [showInviteDialog, setShowInviteDialog] = useState(false);
  const [showPromoteDialog, setShowPromoteDialog] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [inviteForm, setInviteForm] = useState<InviteAdminForm>({
    email: '',
    message: ''

  const { toast } = useToast();
  // Load admins and users
  useEffect(() => {
    loadAdmins();
    loadUsers();
  }, []);
  const normalizeAdmin = (admin: any): AdminUser => {
    const createdAt = admin.created_at ? new Date(admin.created_at) : new Date();
    const updatedAt = admin.updated_at ? new Date(admin.updated_at) : createdAt;
    const lastLogin = admin.last_login_at ? new Date(admin.last_login_at) : undefined;
    const invitedAt = admin.invited_at ? new Date(admin.invited_at) : createdAt;
    return {
      user_id: admin.user_id,
      email: admin.email,
      full_name: admin.full_name ?? '',
      role: admin.role ?? 'admin',
      roles: Array.isArray(admin.roles) && admin.roles.length ? admin.roles : [admin.role ?? 'admin'],
      tenant_id: admin.tenant_id ?? 'default',
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
      lastLogin: lastLogin,
      invitedAt,
      invitedBy: admin.invited_by ?? admin.created_by ?? undefined,
    };
  };
  const loadAdmins = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/admin/admins');
      if (response.ok) {
        const payload = await response.json();
        const adminsData = Array.isArray(payload?.data?.admins)
          ? payload.data.admins
          : Array.isArray(payload?.admins)
            ? payload.admins
            : Array.isArray(payload)
              ? payload
              : [];
        setAdmins(adminsData.map((admin: any) => normalizeAdmin(admin)));
      } else {
        throw new Error('Failed to load administrators');
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load administrators',
        variant: 'destructive'

    } finally {
      setLoading(false);
    }
  };
  const loadUsers = async () => {
    try {
      const response = await fetch('/api/admin/users?role=user');
      if (response.ok) {
        const data = await response.json();
        setUsers(data.data || []);
      }
    } catch (error) {
    }
  };
  const handleInviteAdmin = async () => {
    if (!inviteForm.email) {
      toast({
        title: 'Error',
        description: 'Email is required',
        variant: 'destructive'

      return;
    }
    try {
      const response = await fetch('/api/admin/admins/invite', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(inviteForm)

      if (response.ok) {
        toast({
          title: 'Success',
          description: 'Admin invitation sent successfully'

        setShowInviteDialog(false);
        setInviteForm({ email: '', message: '' });
        loadAdmins();
      } else {
        const error = await response.json();
        throw new Error(error.message || 'Failed to send invitation');
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to send invitation',
        variant: 'destructive'

    }
  };
  const handlePromoteUser = async (userId: string) => {
    try {
      const response = await fetch(`/api/admin/admins/promote/${userId}`, {
        method: 'POST'

      if (response.ok) {
        toast({
          title: 'Success',
          description: 'User promoted to administrator successfully'

        setShowPromoteDialog(false);
        setSelectedUser(null);
        loadAdmins();
        loadUsers();
      } else {
        const error = await response.json();
        throw new Error(error.message || 'Failed to promote user');
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to promote user',
        variant: 'destructive'

    }
  };
  const handleDemoteAdmin = async (adminId: string) => {
    if (!confirm('Are you sure you want to demote this administrator? They will lose all admin privileges.')) {
      return;
    }
    try {
      const response = await fetch(`/api/admin/admins/demote/${adminId}`, {
        method: 'POST'

      if (response.ok) {
        toast({
          title: 'Success',
          description: 'Administrator demoted successfully'

        loadAdmins();
        loadUsers();
      } else {
        const error = await response.json();
        throw new Error(error.message || 'Failed to demote administrator');
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to demote administrator',
        variant: 'destructive'

    }
  };
  const handleToggleAdminStatus = async (adminId: string, isActive: boolean) => {
    try {
      const response = await fetch(`/api/admin/admins/${adminId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ isActive: !isActive })

      if (response.ok) {
        toast({
          title: 'Success',
          description: `Administrator ${!isActive ? 'activated' : 'deactivated'} successfully`

        loadAdmins();
      } else {
        const error = await response.json();
        throw new Error(error.message || 'Failed to update administrator status');
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to update administrator status',
        variant: 'destructive'

    }
  };
  const filteredAdmins = admins.filter(admin => {
    const matchesSearch = admin.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         admin.full_name?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'all' || 
                         (statusFilter === 'active' && admin.is_active) ||
                         (statusFilter === 'inactive' && !admin.is_active);
    return matchesSearch && matchesStatus;

  const formatLastLogin = (date?: Date | string | null) => {
    if (!date) return 'Never';
    return new Date(date).toLocaleDateString();
  };
  return (
    <ErrorBoundary fallback={<div>Something went wrong in AdminManagementInterface</div>}>
      <div className="space-y-6">
      {/* Header Actions */}
      <div className="flex flex-col sm:flex-row gap-4 justify-between">
        <div className="flex flex-1 gap-4">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4 " />
            <input
              placeholder="Search administrators..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          <select value={statusFilter} onValueChange={(value: any) = aria-label="Select option"> setStatusFilter(value)}>
            <selectTrigger className="w-32 " aria-label="Select option">
              <Filter className="h-4 w-4 mr-2 " />
              <selectValue />
            </SelectTrigger>
            <selectContent aria-label="Select option">
              <selectItem value="all" aria-label="Select option">All</SelectItem>
              <selectItem value="active" aria-label="Select option">Active</SelectItem>
              <selectItem value="inactive" aria-label="Select option">Inactive</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="flex gap-2">
          <Dialog open={showInviteDialog} onOpenChange={setShowInviteDialog}>
            <DialogTrigger asChild>
              <button aria-label="Button">
                <Mail className="mr-2 h-4 w-4 " />
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
                  <Label htmlFor="email">Email Address</Label>
                  <input
                    id="email"
                    type="email"
                    placeholder="admin@example.com"
                    value={inviteForm.email}
                    onChange={(e) => setInviteForm(prev => ({ ...prev, email: e.target.value }))}
                  />
                </div>
                <div>
                  <Label htmlFor="message">Custom Message (Optional)</Label>
                  <textarea
                    id="message"
                    placeholder="Welcome to the admin team..."
                    value={inviteForm.message}
                    onChange={(e) => setInviteForm(prev => ({ ...prev, message: e.target.value }))}
                    rows={3}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowInviteDialog(false)}>
                </Button>
                <Button onClick={handleInviteAdmin} >
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
          <Dialog open={showPromoteDialog} onOpenChange={setShowPromoteDialog}>
            <DialogTrigger asChild>
              <Button variant="outline" >
                <UserPlus className="mr-2 h-4 w-4 " />
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Promote User to Administrator</DialogTitle>
                <DialogDescription>
                  Select a user to promote to administrator role.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label>Select User</Label>
                  <select onValueChange={(value) = aria-label="Select option"> {
                    const user = users.find(u => u.user_id === value);
                    setSelectedUser(user || null);
                  }}>
                    <selectTrigger aria-label="Select option">
                      <selectValue placeholder="Choose a user to promote" />
                    </SelectTrigger>
                    <selectContent aria-label="Select option">
                      {users.map(user => (
                        <selectItem key={user.user_id} value={user.user_id} aria-label="Select option">
                          {user.email} ({user.full_name || 'No name'})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                {selectedUser && (
                  <div className="p-4 bg-gray-50 rounded-lg sm:p-4 md:p-6">
                    <h4 className="font-medium">Selected User</h4>
                    <p className="text-sm text-gray-600 md:text-base lg:text-lg">{selectedUser.email}</p>
                    <p className="text-sm text-gray-600 md:text-base lg:text-lg">Name: {selectedUser.full_name || 'Not provided'}</p>
                    <p className="text-sm text-gray-600 md:text-base lg:text-lg">
                      Joined: {new Date(selectedUser.created_at).toLocaleDateString()}
                    </p>
                  </div>
                )}
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => {
                  setShowPromoteDialog(false);
                  setSelectedUser(null);
                }}>
                </Button>
                <Button 
                  onClick={() => selectedUser && handlePromoteUser(selectedUser.user_id)}
                  disabled={!selectedUser}
                >
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
          <CardDescription>
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary "></div>
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
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredAdmins.map((admin) => (
                    <TableRow key={admin.user_id}>
                      <TableCell>
                        <div>
                          <div className="font-medium">{admin.email}</div>
                          <div className="text-sm text-gray-500 md:text-base lg:text-lg">{admin.full_name || 'No name'}</div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={admin.role === 'super_admin' ? 'default' : 'secondary'}>
                          {admin.role === 'super_admin' ? (
                            <>
                              <ShieldCheck className="mr-1 h-3 w-3 " />
                            </>
                          ) : (
                            <>
                              <Shield className="mr-1 h-3 w-3 " />
                            </>
                          )}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={admin.is_active ? 'default' : 'secondary'}>
                          {admin.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm text-gray-500 md:text-base lg:text-lg">
                        {formatLastLogin(admin.lastLogin ?? admin.last_login_at)}
                      </TableCell>
                      <TableCell className="text-sm text-gray-500 md:text-base lg:text-lg">
                        {(admin.invitedAt ?? admin.created_at) ? (
                          <div>
                            <div>{new Date(admin.invitedAt ?? admin.created_at).toLocaleDateString()}</div>
                            {admin.invitedBy && (
                              <div className="text-xs sm:text-sm md:text-base">by {admin.invitedBy}</div>
                            )}
                          </div>
                        ) : (
                          'Direct creation'
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          {admin.role !== 'super_admin' && (
                            <>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleToggleAdminStatus(admin.user_id, admin.is_active)}
                              >
                                {admin.is_active ? (
                                  <>
                                    <UserX className="mr-1 h-3 w-3 " />
                                  </>
                                ) : (
                                  <>
                                    <UserCheck className="mr-1 h-3 w-3 " />
                                  </>
                                )}
                              </Button>
                              <Button
                                variant="destructive"
                                size="sm"
                                onClick={() => handleDemoteAdmin(admin.user_id)}
                              >
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
