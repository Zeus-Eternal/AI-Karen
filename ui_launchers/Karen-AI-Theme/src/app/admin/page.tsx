
"use client";

import { useState } from "react";
import { Brain, Users, Settings, BarChart, Bell, Database, MoreHorizontal, PlusCircle, Search, Trash2, UserPlus, BrainCircuit, Eye, PenSquare, UserCog, Ban, ListTree, FileJson, HardDrive, FileTerminal, ArrowRight, Wrench, RefreshCw, FileSearch, ShieldCheck, History, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuLabel, DropdownMenuSeparator } from "@/components/ui/dropdown-menu";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogClose } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import Link from "next/link";
import SettingsDialog from "@/components/settings/SettingsDialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import apiClient from "@/lib/api";

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
  timeSpent: string;
  tokenUsage: number;
};

const initialUsers: User[] = [
  { id: 'usr_1', name: 'Admin User', email: 'admin@example.com', role: 'Admin', status: 'Active', createdAt: '2023-01-15', lastLogin: '2024-07-30', timeSpent: '12h 30m', tokenUsage: 1250000 },
  { id: 'usr_2', name: 'Demo User', email: 'demo@example.com', role: 'User', status: 'Active', createdAt: '2023-02-20', lastLogin: '2024-07-29', timeSpent: '2h 15m', tokenUsage: 250000 },
  { id: 'usr_3', name: 'John Doe', email: 'john.d@example.com', role: 'User', status: 'Suspended', createdAt: '2023-03-10', lastLogin: '2024-05-10', timeSpent: '5h 45m', tokenUsage: 550000 },
  { id: 'usr_4', name: 'Jane Smith', email: 'jane.s@example.com', role: 'Editor', status: 'Active', createdAt: '2023-04-05', lastLogin: '2024-07-30', timeSpent: '25h 10m', tokenUsage: 2800000 },
  { id: 'usr_5', name: 'Peter Jones', email: 'peter.j@example.com', role: 'User', status: 'Pending', createdAt: '2023-05-21', lastLogin: null, timeSpent: '0h 0m', tokenUsage: 0 },
  { id: 'usr_6', name: 'Mary Johnson', email: 'mary.j@example.com', role: 'Editor', status: 'Active', createdAt: '2023-06-11', lastLogin: '2024-07-28', timeSpent: '8h 5m', tokenUsage: 950000 },
  { id: 'usr_7', name: 'Chris Lee', email: 'chris.l@example.com', role: 'User', status: 'Active', createdAt: '2023-07-01', lastLogin: '2024-07-25', timeSpent: '1h 20m', tokenUsage: 120000 },
];

const dbCollections = [
    { name: 'users', docCount: 7, size: '1.2MB' },
    { name: 'settings', docCount: 1, size: '5KB' },
    { name: 'chat_sessions', docCount: 152, size: '25.6MB' },
    { name: 'automation_tasks', docCount: 12, size: '150KB' },
    { name: 'logs', docCount: 2348, size: '112.8MB' },
];

const dbDocuments = {
    users: initialUsers.map(u => ({ id: u.id, data: { name: u.name, email: u.email, role: u.role } })),
    settings: [{ id: 'global_settings', data: { theme: 'dark', version: '1.2.0', enable_automations: true } }],
    chat_sessions: [
        { id: 'chat_abc', data: { userId: 'usr_2', message_count: 25, start_time: '2024-07-30T10:00:00Z' } },
        { id: 'chat_def', data: { userId: 'usr_4', message_count: 40, start_time: '2024-07-30T11:30:00Z' } },
    ],
    automation_tasks: [
        { id: 'task_123', data: { name: 'Check urgent emails', schedule: '*/15 * * * *', enabled: true } },
        { id: 'task_456', data: { name: 'Generate weekly report', schedule: '0 0 * * 1', enabled: false } },
    ],
    logs: [
        { id: 'log_xyz', data: { level: 'error', message: 'Failed to connect to external API', timestamp: '2024-07-30T12:00:00Z' } }
    ]
};

const getInitials = (name: string) => {
    const names = name.split(' ');
    if (names.length === 1) return names[0].charAt(0).toUpperCase();
    return (names[0].charAt(0) + names[names.length - 1].charAt(0)).toUpperCase();
}

const getStatusBadgeVariant = (status: UserStatus) => {
    switch (status) {
        case 'Active': return 'secondary';
        case 'Suspended': return 'destructive';
        case 'Pending': return 'outline';
        default: return 'secondary';
    }
}

const getRoleBadgeVariant = (role: UserRole) => {
    switch (role) {
        case 'Admin': return 'default';
        case 'Editor': return 'secondary';
        default: return 'outline';
    }
}

const formatNumber = (num: number) => {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

export default function AdminPage() {
    const [users, setUsers] = useState<User[]>(initialUsers);
    const [searchQuery, setSearchQuery] = useState('');
    const [editingUser, setEditingUser] = useState<User | null>(null);

    const [selectedCollection, setSelectedCollection] = useState<keyof typeof dbDocuments>('users');
    
    // Maintenance State
    const [maintenanceReport, setMaintenanceReport] = useState<any>(null);
    const [isCleaning, setIsCleaning] = useState(false);
    const [dryRun, setDryRun] = useState(true);
    const [lastCleanupStatus, setLastCleanupStatus] = useState<{ status: string; last_run: string | null }>({ status: 'ready', last_run: null });

    const filteredUsers = users.filter(user =>
        user.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        user.email.toLowerCase().includes(searchQuery.toLowerCase())
    );
    
    const handleToggleSuspend = (userId: string) => {
        setUsers(users.map(user => 
            user.id === userId ? { ...user, status: user.status === 'Active' ? 'Suspended' : 'Active' } : user
        ));
    };

    const handleDeleteUser = (userId: string) => {
        setUsers(users.filter(user => user.id !== userId));
    };

    const handleRunCleanup = async () => {
        setIsCleaning(true);
        try {
            const report = await apiClient.post<any>(`/api/maintenance/cleanup?dry_run=${dryRun}`);
            setMaintenanceReport(report);
            setLastCleanupStatus({
                status: 'completed',
                last_run: new Date().toISOString()
            });
        } catch (error) {
            console.error("Cleanup failed:", error);
        } finally {
            setIsCleaning(false);
        }
    };


    return (
        <>
        <div className="flex flex-col min-h-screen bg-background text-foreground">
            <header className="p-4 border-b border-border flex items-center justify-between sticky top-0 z-30 bg-background/90 backdrop-blur-md shadow-sm">
                <div className="flex items-center space-x-3">
                    <Brain className="h-8 w-8 text-primary" />
                    <h1 className="text-2xl font-semibold tracking-tight">Karen AI - Admin Dashboard</h1>
                </div>
                 <Button asChild variant="outline">
                    <Link href="/dashboard">Return to App</Link>
                </Button>
            </header>

            <main className="flex-1 p-4 md:p-8">
                <Tabs defaultValue="users" className="w-full">
                    <TabsList className="grid w-full grid-cols-6">
                        <TabsTrigger value="users"><Users className="mr-2 h-4 w-4" />User Management</TabsTrigger>
                        <TabsTrigger value="settings"><Settings className="mr-2 h-4 w-4" />App Settings</TabsTrigger>
                        <TabsTrigger value="database"><Database className="mr-2 h-4 w-4" />Database</TabsTrigger>
                        <TabsTrigger value="maintenance"><Wrench className="mr-2 h-4 w-4" />Maintenance</TabsTrigger>
                        <TabsTrigger value="analytics"><BarChart className="mr-2 h-4 w-4" />Analytics</TabsTrigger>
                        <TabsTrigger value="notifications"><Bell className="mr-2 h-4 w-4" />System Notifications</TabsTrigger>
                    </TabsList>
                    
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
                                    <CardTitle className="text-sm font-medium">Token Usage (Total)</CardTitle>
                                    <BrainCircuit className="h-4 w-4 text-muted-foreground" />
                                </CardHeader>
                                <CardContent>
                                    <div className="text-2xl font-bold">{formatNumber(users.reduce((acc, user) => acc + user.tokenUsage, 0))}</div>
                                    <p className="text-xs text-muted-foreground">Across all users</p>
                                </CardContent>
                            </Card>
                             <Card>
                                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                    <CardTitle className="text-sm font-medium">Pending Invitations</CardTitle>
                                    <UserPlus className="h-4 w-4 text-yellow-500" />
                                </CardHeader>
                                <CardContent>
                                    <div className="text-2xl font-bold">{users.filter(u => u.status === 'Pending').length}</div>
                                    <p className="text-xs text-muted-foreground">Users awaiting activation</p>
                                </CardContent>
                            </Card>
                             <Card>
                                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                    <CardTitle className="text-sm font-medium">Suspended Users</CardTitle>
                                    <Users className="h-4 w-4 text-destructive" />
                                </CardHeader>
                                <CardContent>
                                    <div className="text-2xl font-bold">{users.filter(u => u.status === 'Suspended').length}</div>
                                    <p className="text-xs text-muted-foreground">Users with suspended access</p>
                                </CardContent>
                            </Card>
                        </div>
                        <Card>
                            <CardHeader>
                                <CardTitle>User Management</CardTitle>
                                <CardDescription>View, manage, and control user accounts and roles.</CardDescription>
                            </CardHeader>
                            <CardContent>
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
                                    <div className="flex items-center gap-2">
                                        <Dialog>
                                            <DialogTrigger asChild>
                                                <Button>
                                                    <PlusCircle className="mr-2 h-4 w-4" /> Add User
                                                </Button>
                                            </DialogTrigger>
                                            <DialogContent className="sm:max-w-[425px]">
                                                <DialogHeader>
                                                    <DialogTitle>Add New User</DialogTitle>
                                                    <DialogDescription>
                                                        Create a new user account and assign them a role. An invitation will be sent.
                                                    </DialogDescription>
                                                </DialogHeader>
                                                <div className="grid gap-4 py-4">
                                                    <div className="grid grid-cols-4 items-center gap-4">
                                                        <Label htmlFor="name" className="text-right">Name</Label>
                                                        <Input id="name" placeholder="John Doe" className="col-span-3" />
                                                    </div>
                                                    <div className="grid grid-cols-4 items-center gap-4">
                                                        <Label htmlFor="email" className="text-right">Email</Label>
                                                        <Input id="email" type="email" placeholder="john@example.com" className="col-span-3" />
                                                    </div>
                                                    <div className="grid grid-cols-4 items-center gap-4">
                                                        <Label htmlFor="role" className="text-right">Role</Label>
                                                        <Select>
                                                            <SelectTrigger className="col-span-3">
                                                                <SelectValue placeholder="Select a role" />
                                                            </SelectTrigger>
                                                            <SelectContent>
                                                                <SelectItem value="user">User</SelectItem>
                                                                <SelectItem value="editor">Editor</SelectItem>
                                                                <SelectItem value="admin">Admin</SelectItem>
                                                            </SelectContent>
                                                        </Select>
                                                    </div>
                                                </div>
                                                <DialogFooter>
                                                    <DialogClose asChild>
                                                        <Button variant="outline">Cancel</Button>
                                                    </DialogClose>
                                                     <DialogClose asChild>
                                                        <Button type="submit">Create and Invite</Button>
                                                    </DialogClose>
                                                </DialogFooter>
                                            </DialogContent>
                                        </Dialog>
                                    </div>
                                </div>
                                <Table>
                                    <TableHeader>
                                        <TableRow>
                                            <TableHead className="w-[40px]">
                                                <Checkbox />
                                            </TableHead>
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
                                                <TableCell>
                                                    <Checkbox />
                                                </TableCell>
                                                <TableCell>
                                                    <div className="flex items-center gap-3">
                                                        <Avatar>
                                                            <AvatarFallback>{getInitials(user.name)}</AvatarFallback>
                                                        </Avatar>
                                                        <div>
                                                            <div className="font-medium">{user.name}</div>
                                                            <div className="text-sm text-muted-foreground">{user.email}</div>
                                                        </div>
                                                    </div>
                                                </TableCell>
                                                 <TableCell>
                                                     <Badge variant={getStatusBadgeVariant(user.status)}>
                                                        {user.status}
                                                    </Badge>
                                                </TableCell>
                                                <TableCell>
                                                    <Badge variant={getRoleBadgeVariant(user.role)}>{user.role}</Badge>
                                                </TableCell>
                                                <TableCell>
                                                    {user.lastLogin || 'N/A'}
                                                </TableCell>
                                                <TableCell>
                                                    {user.timeSpent}
                                                </TableCell>
                                                 <TableCell className="text-right">
                                                    {formatNumber(user.tokenUsage)}
                                                </TableCell>
                                                <TableCell>
                                                    {user.createdAt}
                                                </TableCell>
                                                <TableCell className="text-right">
                                                    <DropdownMenu>
                                                        <DropdownMenuTrigger asChild>
                                                            <Button variant="ghost" size="icon">
                                                                <MoreHorizontal className="h-4 w-4" />
                                                            </Button>
                                                        </DropdownMenuTrigger>
                                                        <DropdownMenuContent align="end">
                                                            <DropdownMenuLabel>Actions</DropdownMenuLabel>
                                                            <DropdownMenuItem>
                                                                <Eye className="mr-2 h-4 w-4" /> View Details
                                                            </DropdownMenuItem>
                                                            <DropdownMenuItem onClick={() => setEditingUser(user)}>
                                                                <PenSquare className="mr-2 h-4 w-4" /> Edit User
                                                            </DropdownMenuItem>
                                                            <DropdownMenuItem>
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
                                                                            This action cannot be undone. This will permanently delete the user account for <span className="font-semibold">{user.name}</span>.
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
                            </CardContent>
                        </Card>
                    </TabsContent>

                    <TabsContent value="settings" className="mt-6">
                         <SettingsDialog adminMode />
                    </TabsContent>

                    <TabsContent value="database" className="mt-6 space-y-6">
                        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                             <Card>
                                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                    <CardTitle className="text-sm font-medium">Total Collections</CardTitle>
                                    <ListTree className="h-4 w-4 text-muted-foreground" />
                                </CardHeader>
                                <CardContent>
                                    <div className="text-2xl font-bold">{dbCollections.length}</div>
                                    <p className="text-xs text-muted-foreground">Top-level data collections</p>
                                </CardContent>
                            </Card>
                            <Card>
                                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                    <CardTitle className="text-sm font-medium">Total Documents</CardTitle>
                                    <FileJson className="h-4 w-4 text-muted-foreground" />
                                </CardHeader>
                                <CardContent>
                                    <div className="text-2xl font-bold">{formatNumber(dbCollections.reduce((acc, c) => acc + c.docCount, 0))}</div>
                                    <p className="text-xs text-muted-foreground">Across all collections</p>
                                </CardContent>
                            </Card>
                            <Card>
                                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                    <CardTitle className="text-sm font-medium">Database Size</CardTitle>
                                    <HardDrive className="h-4 w-4 text-muted-foreground" />
                                </CardHeader>
                                <CardContent>
                                    <div className="text-2xl font-bold">140.1 MB</div>
                                    <p className="text-xs text-muted-foreground">Total size of all data</p>
                                </CardContent>
                            </Card>
                            <Card>
                                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                    <CardTitle className="text-sm font-medium">Security Rules</CardTitle>
                                    <FileTerminal className="h-4 w-4 text-muted-foreground" />
                                </CardHeader>
                                <CardContent>
                                    <div className="text-2xl font-bold">Active</div>
                                    <p className="text-xs text-muted-foreground">Last updated: Today</p>
                                </CardContent>
                            </Card>
                        </div>
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                            <div className="lg:col-span-1">
                                <Card>
                                    <CardHeader>
                                        <CardTitle className="flex items-center"><ListTree className="mr-2 h-5 w-5"/> Collections</CardTitle>
                                        <CardDescription>Browse data collections</CardDescription>
                                    </CardHeader>
                                    <CardContent>
                                        <ScrollArea className="h-[480px]">
                                            <div className="space-y-2">
                                                {dbCollections.map(col => (
                                                     <button 
                                                        key={col.name} 
                                                        onClick={() => setSelectedCollection(col.name as keyof typeof dbDocuments)}
                                                        className={`w-full text-left p-3 rounded-lg transition-colors ${selectedCollection === col.name ? 'bg-muted' : 'hover:bg-muted/50'}`}
                                                     >
                                                        <div className="flex justify-between items-center">
                                                            <div className="font-semibold text-sm">{col.name}</div>
                                                            {selectedCollection === col.name && <ArrowRight className="h-4 w-4" />}
                                                        </div>
                                                        <div className="text-xs text-muted-foreground">
                                                            {col.docCount} docs - {col.size}
                                                        </div>
                                                     </button>
                                                ))}
                                            </div>
                                        </ScrollArea>
                                    </CardContent>
                                </Card>
                            </div>
                            <div className="lg:col-span-2 space-y-6">
                                <Card>
                                    <CardHeader>
                                        <CardTitle className="flex items-center"><FileJson className="mr-2 h-5 w-5"/> Documents in <span className="text-primary mx-1">'{selectedCollection}'</span></CardTitle>
                                        <CardDescription>Browse and manage documents within the selected collection.</CardDescription>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="relative mb-4">
                                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                            <Input placeholder="Search document ID..." className="pl-10 w-full" />
                                        </div>
                                        <ScrollArea className="h-[400px] border rounded-md">
                                            <Table>
                                                <TableHeader className="sticky top-0 bg-muted">
                                                    <TableRow>
                                                        <TableHead>Document ID</TableHead>
                                                        <TableHead>Data Preview</TableHead>
                                                        <TableHead className="text-right">Actions</TableHead>
                                                    </TableRow>
                                                </TableHeader>
                                                <TableBody>
                                                     {(dbDocuments[selectedCollection] || []).slice(0, 10).map(doc => (
                                                        <TableRow key={doc.id}>
                                                            <TableCell className="font-mono text-xs">{doc.id}</TableCell>
                                                            <TableCell>
                                                                <pre className="text-xs bg-gray-800 text-gray-200 p-2 rounded-md overflow-x-auto"><code>{JSON.stringify(doc.data, null, 2)}</code></pre>
                                                            </TableCell>
                                                            <TableCell className="text-right">
                                                                <Button variant="ghost" size="sm">View</Button>
                                                                <Button variant="ghost" size="sm" className="text-destructive hover:text-destructive">Delete</Button>
                                                            </TableCell>
                                                        </TableRow>
                                                    ))}
                                                </TableBody>
                                            </Table>
                                        </ScrollArea>
                                    </CardContent>
                                </Card>
                                <Card>
                                    <CardHeader>
                                        <CardTitle className="flex items-center"><FileTerminal className="mr-2 h-5 w-5"/> Query Runner</CardTitle>
                                        <CardDescription>Run a raw query against the database (conceptual).</CardDescription>
                                    </CardHeader>
                                    <CardContent>
                                        <Textarea placeholder="db.collection('users').where('role', '==', 'Admin').get()" className="font-mono text-xs" rows={5} />
                                        <Button className="mt-4">Run Query</Button>
                                    </CardContent>
                                </Card>
                            </div>
                        </div>
                    </TabsContent>

                    <TabsContent value="maintenance" className="mt-6 space-y-6">
                        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                            <Card>
                                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                    <CardTitle className="text-sm font-medium">System Status</CardTitle>
                                    <ShieldCheck className={`h-4 w-4 ${lastCleanupStatus.status === 'ready' ? 'text-green-500' : 'text-blue-500'}`} />
                                </CardHeader>
                                <CardContent>
                                    <div className="text-2xl font-bold uppercase">{lastCleanupStatus.status}</div>
                                    <p className="text-xs text-muted-foreground">System maintenance health</p>
                                </CardContent>
                            </Card>
                            <Card>
                                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                    <CardTitle className="text-sm font-medium">Last Cleanup</CardTitle>
                                    <History className="h-4 w-4 text-muted-foreground" />
                                </CardHeader>
                                <CardContent>
                                    <div className="text-2xl font-bold">{lastCleanupStatus.last_run ? new Date(lastCleanupStatus.last_run).toLocaleDateString() : 'Never'}</div>
                                    <p className="text-xs text-muted-foreground">{lastCleanupStatus.last_run ? new Date(lastCleanupStatus.last_run).toLocaleTimeString() : 'No recent runs'}</p>
                                </CardContent>
                            </Card>
                            <Card>
                                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                    <CardTitle className="text-sm font-medium">Actions (Total)</CardTitle>
                                    <ListTree className="h-4 w-4 text-muted-foreground" />
                                </CardHeader>
                                <CardContent>
                                    <div className="text-2xl font-bold">{maintenanceReport?.total_actions || 0}</div>
                                    <p className="text-xs text-muted-foreground">From last maintenance run</p>
                                </CardContent>
                            </Card>
                            <Card>
                                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                    <CardTitle className="text-sm font-medium">Purged Size</CardTitle>
                                    <Trash2 className="h-4 w-4 text-muted-foreground" />
                                </CardHeader>
                                <CardContent>
                                    <div className="text-2xl font-bold">{(maintenanceReport?.bytes_cleaned / (1024 * 1024)).toFixed(2) || '0.00'} MB</div>
                                    <p className="text-xs text-muted-foreground">Disk space recovered</p>
                                </CardContent>
                            </Card>
                        </div>

                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                            <Card className="lg:col-span-1">
                                <CardHeader>
                                    <CardTitle className="flex items-center"><Wrench className="mr-2 h-5 w-5"/> Maintenance Tools</CardTitle>
                                    <CardDescription>System-wide cleanup and optimization</CardDescription>
                                </CardHeader>
                                <CardContent className="space-y-6">
                                    <div className="flex items-center justify-between space-x-2">
                                        <div className="flex flex-col space-y-1">
                                            <Label htmlFor="dry-run">Dry Run Mode</Label>
                                            <p className="text-xs text-muted-foreground">Simulate cleanup without deleting data</p>
                                        </div>
                                        <Switch 
                                            id="dry-run" 
                                            checked={dryRun}
                                            onCheckedChange={setDryRun}
                                        />
                                    </div>
                                    
                                    <div className="pt-4 border-t">
                                        <Button 
                                            className="w-full" 
                                            size="lg" 
                                            onClick={handleRunCleanup}
                                            disabled={isCleaning}
                                        >
                                            {isCleaning ? (
                                                <>
                                                    <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                                                    Running Maintenance...
                                                </>
                                            ) : (
                                                <>
                                                    {dryRun ? <FileSearch className="mr-2 h-4 w-4" /> : <RefreshCw className="mr-2 h-4 w-4" />}
                                                    {dryRun ? 'Start Dry Run Simulation' : 'Execute Full System Cleanup'}
                                                </>
                                            )}
                                        </Button>
                                    </div>

                                    <div className="rounded-md bg-muted/50 p-4 space-y-2">
                                        <h4 className="text-sm font-semibold flex items-center">
                                            <AlertCircle className="mr-2 h-4 w-4 text-blue-500" />
                                            Active Maintenance Tasks
                                        </h4>
                                        <ul className="text-xs space-y-1 list-disc pl-4 text-muted-foreground">
                                            <li>Orphaned Demo Users purging</li>
                                            <li>Test/Temp file cleanup</li>
                                            <li>Log file rotation & archiving</li>
                                            <li>Expired Session Cache flushing</li>
                                            <li>System Backup validation</li>
                                        </ul>
                                    </div>
                                </CardContent>
                            </Card>

                            <Card className="lg:col-span-2">
                                <CardHeader>
                                    <CardTitle className="flex items-center">
                                        <FileTerminal className="mr-2 h-5 w-5"/> 
                                        Cleanup Report {maintenanceReport?.dry_run && <Badge className="ml-2" variant="secondary">SIMULATION</Badge>}
                                    </CardTitle>
                                    <CardDescription>Results from the {maintenanceReport ? 'last' : 'next'} maintenance operation</CardDescription>
                                </CardHeader>
                                <CardContent>
                                    {maintenanceReport ? (
                                        <ScrollArea className="h-[400px] rounded-md border p-4 bg-muted/20">
                                            <div className="space-y-4">
                                                {maintenanceReport.actions.map((action: any, i: number) => (
                                                    <div key={i} className="flex items-start gap-3 p-3 rounded-lg bg-background border shadow-sm">
                                                        <div className={`mt-1 p-1 rounded-full ${action.action_type.includes('error') ? 'bg-red-500/10 text-red-500' : 'bg-green-500/10 text-green-500'}`}>
                                                            {action.action_type.includes('error') ? <AlertCircle className="h-4 w-4" /> : <ShieldCheck className="h-4 w-4" />}
                                                        </div>
                                                        <div className="flex-1">
                                                            <div className="flex justify-between">
                                                                <span className="font-semibold text-sm capitalize">{action.action_type.replace(/_/g, ' ')}</span>
                                                                <span className="text-[10px] text-muted-foreground">{new Date(action.timestamp).toLocaleTimeString()}</span>
                                                            </div>
                                                            <p className="text-xs text-muted-foreground mt-1">{action.description}</p>
                                                            <div className="mt-2 flex gap-2">
                                                                <Badge variant="outline" className="text-[10px] py-0">{action.target}</Badge>
                                                                {action.size_bytes > 0 && (
                                                                    <Badge variant="secondary" className="text-[10px] py-0">{(action.size_bytes / 1024).toFixed(1)} KB</Badge>
                                                                )}
                                                            </div>
                                                        </div>
                                                    </div>
                                                ))}
                                                {maintenanceReport.actions.length === 0 && (
                                                    <div className="flex flex-col items-center justify-center h-full text-muted-foreground py-10">
                                                        <ShieldCheck className="h-10 w-10 mb-2 opacity-20" />
                                                        <p>No maintenance actions required. System is clean.</p>
                                                    </div>
                                                )}
                                            </div>
                                        </ScrollArea>
                                    ) : (
                                        <div className="flex flex-col items-center justify-center h-[400px] border rounded-md border-dashed border-muted-foreground/30 text-muted-foreground">
                                            <Wrench className="h-12 w-12 mb-4 opacity-10" />
                                            <p className="text-sm">Run maintenance to generate a system report</p>
                                            <p className="text-xs mt-1">Simulated or active cleanup actions will appear here</p>
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        </div>
                    </TabsContent>

                    <TabsContent value="analytics" className="mt-6">
                        <Card>
                            <CardHeader>
                                <CardTitle>Analytics</CardTitle>
                                <CardDescription>Conceptual placeholder for application analytics and usage metrics.</CardDescription>
                            </CardHeader>
                            <CardContent className="flex items-center justify-center h-64 bg-muted/30 rounded-lg">
                                <p className="text-muted-foreground">Analytics Dashboard would be displayed here.</p>
                            </CardContent>
                        </Card>
                    </TabsContent>

                    <TabsContent value="notifications" className="mt-6">
                        <Card>
                            <CardHeader>
                                <CardTitle>System Notifications</CardTitle>
                                <CardDescription>Conceptual placeholder for sending system-wide notifications to users.</CardDescription>
                            </CardHeader>
                            <CardContent className="flex items-center justify-center h-64 bg-muted/30 rounded-lg">
                                 <p className="text-muted-foreground">System Notification Manager would be displayed here.</p>
                            </CardContent>
                        </Card>
                    </TabsContent>
                </Tabs>
            </main>
        </div>
        
        {/* Edit User Dialog */}
        <Dialog open={!!editingUser} onOpenChange={(isOpen) => !isOpen && setEditingUser(null)}>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>Edit User: {editingUser?.name}</DialogTitle>
                    <DialogDescription>
                       Modify the details for this user account.
                    </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                    <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="edit-name" className="text-right">Name</Label>
                        <Input id="edit-name" defaultValue={editingUser?.name} className="col-span-3" />
                    </div>
                    <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="edit-email" className="text-right">Email</Label>
                        <Input id="edit-email" type="email" defaultValue={editingUser?.email} className="col-span-3" />
                    </div>
                    <div className="grid grid-cols-4 items-center gap-4">
                        <Label htmlFor="edit-role" className="text-right">Role</Label>
                        <Select defaultValue={editingUser?.role}>
                            <SelectTrigger className="col-span-3">
                                <SelectValue placeholder="Select a role" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="User">User</SelectItem>
                                <SelectItem value="Editor">Editor</SelectItem>
                                <SelectItem value="Admin">Admin</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                </div>
                <DialogFooter>
                    <Button variant="outline" onClick={() => setEditingUser(null)}>Cancel</Button>
                    <Button type="submit" onClick={() => setEditingUser(null)}>Save Changes</Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    </>
    );
}
