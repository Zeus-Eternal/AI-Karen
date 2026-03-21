
"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Database, Info, Folder, FileText, DatabaseZap, Plug, Unplug, Settings, TestTube2, Server, Waves, PlusCircle } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogClose } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";

// Simple inline SVG for Firebase icon
const FirebaseIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" className="h-6 w-6">
    <path d="M96.3 75.2L35.1 11.2c-2-2.7-5.9-3.4-8.6-1.4L4.8 24.3c-2.7 2-3.4 5.9-1.4 8.6l30.8 49.1-32.8 19c-2.5 1.5-3.5 4.8-2.3 7.5l9.2 19.8c1.2 2.7 4.3 4 7 2.8l70.7-41c2.7-1.5 3.5-5 .8-7.9z" fill="#f57c00"></path>
    <path d="M96.4 75.2l-33.5 50.1c-1.7 2.5-5.1 3.5-7.8 2.1l-11.9-6.1c-2.7-1.4-4-4.6-2.9-7.4L71 63l23-14.2c2.4-1.5 5.7-.1 6.8 2.6l4.2 9.2c1.1 2.3.1 5.3-2.6 6.6z" fill="#ffca28"></path>
    <path d="M99.1 59.8L37.8 13.3c-2.4-1.8-5.8-1.1-7.6 1.3L4.8 24.3c-2.7 2-3.4 5.9-1.4 8.6l57.7 91.8c2 2.7 5.9 3.4 8.6 1.4l11.7-8.6c2.7-2 3.4-5.9 1.4-8.6L25.1 20.2l70.7-41c2.7-1.6 3.5-5.1.8-7.9L99.1 59.8z" fillOpacity="0.1" style={{"mixBlendMode": "multiply"}}></path>
    <path d="M99.1 59.8L37.8 13.3c-2.4-1.8-5.8-1.1-7.6 1.3L4.8 24.3c-2.7 2-3.4 5.9-1.4 8.6l57.7 91.8c2 2.7 5.9 3.4 8.6 1.4l11.7-8.6c2.7-2 3.4-5.9 1.4-8.6L25.1 20.2l70.7-41c2.7-1.6 3.5-5.1.8-7.9z" fill="#ffa000"></path>
  </svg>
);

const ElasticsearchIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" className="h-6 w-6">
      <path fill="currentColor" d="M496 240H333.2c-15.3 0-29.2-8.3-36.6-21.7L256 150.4 215.4 218.3c-7.4 13.4-21.3 21.7-36.6 21.7H16c-8.8 0-16 7.2-16 16v.1c0 8.8 7.2 16 16 16h162.8c15.3 0 29.2 8.3 36.6 21.7l40.6 67.9 40.6-67.9c7.4-13.4 21.3 21.7 36.6-21.7H496c8.8 0 16-7.2 16-16v-.1c0-8.8-7.2-16-16-16zM16 32c-8.8 0-16 7.2-16 16v160h106.1c15.3 0 29.2 8.3 36.6 21.7l40.6 67.9L256 150.4 215.4 82.5C208 69.1 194.1 60.8 178.8 60.8H16V32zm480 0v28.8H333.2c-15.3 0-29.2-8.3-36.6-21.7L256 0l-40.6 67.9c-7.4 13.4-21.3 21.7-36.6-21.7H16v132.8h162.8c15.3 0 29.2-8.3 36.6-21.7L256 150.4l40.6, 67.9c7.4, 13.4, 21.3, 21.7, 36.6, 21.7H496V32zM496 464c8.8 0 16-7.2 16-16V288H333.2c-15.3 0-29.2-8.3-36.6-21.7L256 198.4l-40.6 67.9c-7.4 13.4-21.3 21.7-36.6-21.7H16v160h162.8c15.3 0 29.2 8.3 36.6 21.7l40.6 67.9 40.6-67.9c7.4-13.4 21.3-21.7 36.6-21.7H496z"></path>
    </svg>
);
  
const DuckDBIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" className="h-6 w-6">
        <path fill="currentColor" d="M21.75 12.003c0-3.582-2.918-6.5-6.5-6.5s-6.5 2.918-6.5 6.5c0 .355.03.704.086 1.047l-1.037.947c-.5.456-1.202.585-1.84.34l-1.428-.54C4.19 13.62.997 12.68.997 11.39c0-1.808 3.588-3.273 8.02-3.273s8.022 1.465 8.022 3.274c0 .332-.182.64-.49.912a.99.99 0 0 0-.323.75c0 .484.35.89.813.98l.004.001c2.476.544 4.707-1.39 4.707-3.955M7.848 14.18c.24.01.474.08.69.2l.474.264c.64.356 1.038.996 1.038 1.69v.185c0 1.294-1.284 2.34-2.865 2.34-1.583 0-2.866-1.046-2.866-2.34v-.186c0-.693.398-1.333 1.04-1.688l.473-.264c.216-.12.45-.19.69-.2m9.402-1.046c-2.73 0-4.945 2.214-4.945 4.945s2.215 4.945 4.945 4.945c2.73 0 4.945-2.214 4.945-4.945s-2.215-4.945-4.945-4.945"></path>
    </svg>
);

const MilvusIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" className="h-6 w-6">
        <path fill="currentColor" d="M19.922 17.518L12 5.57l-7.922 11.948h15.844M12 2L0 20.036h24L12 2z"></path>
    </svg>
);

const RedisIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" className="h-6 w-6">
        <path fill="currentColor" d="M12.984 3h-2.07L4.95 9.117h2.1l4.05-4.54h.015l.015.015v14.4l-4.05-4.54H5l5.91 5.91h.03L18.9 14.883h-2.07l-3.832 3.848v-9.42l3.832 3.848h2.07L12.984 3z"/>
    </svg>
);


type ConnectionStatus = "Connected" | "Disconnected";
type Connection = {
    name: string;
    icon: React.ReactNode;
    description: string;
    status: ConnectionStatus;
};

/**
 * @file DataConnectorPluginPage.tsx
 * @description Page describing the Data Connector plugin, which allows Karen AI to connect to various data sources.
 * It showcases the live Google Books API connection as a functional example.
 */
export default function DataConnectorPluginPage() {

    const initialConnections: Connection[] = [
        { name: "Firebase", icon: <FirebaseIcon />, description: "Primary Firestore for user data", status: "Connected" },
        { name: "Milvus", icon: <MilvusIcon />, description: "Vector store for semantic search", status: "Connected" },
        { name: "Redis", icon: <RedisIcon />, description: "Cache for session data", status: "Disconnected" },
        { name: "PostgreSQL", icon: <Database className="h-6 w-6"/>, description: "Production analytics database", status: "Disconnected" },
        { name: "Google Drive", icon: <Folder className="h-6 w-6"/>, description: "For reading user documents", status: "Disconnected" },
    ];
    
    const [connections, setConnections] = useState<Connection[]>(initialConnections);
    const { toast } = useToast();

    const handleToggleConnection = (name: string) => {
        setConnections(connections.map(c => {
            if (c.name === name) {
                const newStatus = c.status === 'Connected' ? 'Disconnected' : 'Connected';
                toast({
                    title: `Connection Status Changed (Mock)`,
                    description: `${name} has been ${newStatus.toLowerCase()}.`,
                });
                return { ...c, status: newStatus };
            }
            return c;
        }));
    };

    const handleTestConnection = (name: string) => {
         toast({
            title: `Testing Connection (Mock)`,
            description: `Pinging ${name}... Connection successful!`,
        });
    }

  return (
    <div className="space-y-8">
      <div className="flex items-center space-x-3">
        <Database className="h-8 w-8 text-primary" />
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">Data Connector Plugin</h2>
          <p className="text-sm text-muted-foreground">
            Connect Karen AI to various data sources to extend her knowledge and capabilities.
          </p>
        </div>
      </div>

       <Alert variant="destructive">
        <Info className="h-4 w-4" />
        <AlertTitle>Conceptual Feature</AlertTitle>
        <AlertDescription>
          This entire section is a conceptual placeholder. Connecting to live data sources requires significant backend implementation for authentication, data processing, and security. All UI elements are for demonstration.
        </AlertDescription>
      </Alert>
      
      {/* Categories of Data Sources */}
      <div className="space-y-6">

        <Card>
            <CardHeader>
                <CardTitle>Vector Databases</CardTitle>
                <CardDescription>For semantic search, RAG (Retrieval-Augmented Generation), and long-term memory.</CardDescription>
            </CardHeader>
            <CardContent className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
                <div className="flex items-center gap-3 p-3 border rounded-lg bg-muted/30">
                    <DatabaseZap className="h-6 w-6 text-purple-500" />
                    <div>
                        <p className="font-semibold text-sm">Pinecone</p>
                        <p className="text-xs text-muted-foreground">Managed Vector DB</p>
                    </div>
                </div>
                 <div className="flex items-center gap-3 p-3 border rounded-lg bg-muted/30">
                    <MilvusIcon />
                    <div>
                        <p className="font-semibold text-sm">Milvus</p>
                        <p className="text-xs text-muted-foreground">Open-Source Vector DB</p>
                    </div>
                </div>
                <div className="flex items-center gap-3 p-3 border rounded-lg bg-muted/30">
                    <Waves className="h-6 w-6 text-cyan-500" />
                    <div>
                        <p className="font-semibold text-sm">Weaviate</p>
                        <p className="text-xs text-muted-foreground">Vector Search Engine</p>
                    </div>
                </div>
            </CardContent>
        </Card>
        
        <Card>
            <CardHeader>
                <CardTitle>Document & Search Databases</CardTitle>
                <CardDescription>For storing flexible data structures and enabling powerful text search.</CardDescription>
            </CardHeader>
            <CardContent className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
                <div className="flex items-center gap-3 p-3 border rounded-lg bg-muted/30">
                    <FirebaseIcon />
                    <div>
                        <p className="font-semibold text-sm">Firestore</p>
                        <p className="text-xs text-muted-foreground">NoSQL Document DB</p>
                    </div>
                </div>
                <div className="flex items-center gap-3 p-3 border rounded-lg bg-muted/30">
                    <ElasticsearchIcon />
                    <div>
                        <p className="font-semibold text-sm">Elasticsearch</p>
                        <p className="text-xs text-muted-foreground">Search & Analytics</p>
                    </div>
                </div>
            </CardContent>
        </Card>
        
        <Card>
            <CardHeader>
                <CardTitle>In-Memory Stores</CardTitle>
                <CardDescription>For high-speed caching, session management, and short-term conversational memory.</CardDescription>
            </CardHeader>
            <CardContent className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
                <div className="flex items-center gap-3 p-3 border rounded-lg bg-muted/30">
                    <RedisIcon />
                    <div>
                        <p className="font-semibold text-sm">Redis</p>
                        <p className="text-xs text-muted-foreground">In-Memory Data Store</p>
                    </div>
                </div>
            </CardContent>
        </Card>

        <Card>
            <CardHeader>
                <CardTitle>Relational & Analytical Databases</CardTitle>
                <CardDescription>For structured data, business intelligence, and complex queries.</CardDescription>
            </CardHeader>
            <CardContent className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
                <div className="flex items-center gap-3 p-3 border rounded-lg bg-muted/30">
                    <Database className="h-6 w-6" />
                    <div>
                        <p className="font-semibold text-sm">PostgreSQL</p>
                        <p className="text-xs text-muted-foreground">Relational Database</p>
                    </div>
                </div>
                 <div className="flex items-center gap-3 p-3 border rounded-lg bg-muted/30">
                    <Database className="h-6 w-6" />
                    <div>
                        <p className="font-semibold text-sm">MySQL</p>
                        <p className="text-xs text-muted-foreground">Relational Database</p>
                    </div>
                </div>
                <div className="flex items-center gap-3 p-3 border rounded-lg bg-muted/30">
                    <DuckDBIcon />
                    <div>
                        <p className="font-semibold text-sm">DuckDB</p>
                        <p className="text-xs text-muted-foreground">In-Process Analytical DB</p>
                    </div>
                </div>
            </CardContent>
        </Card>
      </div>


       <Card>
        <CardHeader>
          <CardTitle>Manage Connections</CardTitle>
          <CardDescription>Conceptual interface to connect, disconnect, and configure data sources.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
           {connections.map(conn => (
            <div key={conn.name} className="flex flex-wrap justify-between items-center p-3 border rounded-lg gap-4 bg-muted/20">
                <div className="flex items-center gap-4">
                    <div className="text-primary">{conn.icon}</div>
                    <div>
                        <p className="font-semibold">{conn.name}</p>
                        <p className="text-xs text-muted-foreground">{conn.description}</p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <Badge variant={conn.status === "Connected" ? "default" : "destructive"}>{conn.status}</Badge>
                    {conn.status === "Connected" && (
                        <Button variant="outline" size="sm" onClick={() => handleTestConnection(conn.name)}>
                            <TestTube2 className="mr-2 h-4 w-4" />
                            Test
                        </Button>
                    )}
                    <Button variant="ghost" size="icon" disabled><Settings className="h-4 w-4"/></Button>
                    <Dialog>
                      <DialogTrigger asChild>
                         <Button
                            variant={conn.status === "Connected" ? "secondary" : "default"}
                            size="sm"
                          >
                           {conn.status === "Connected" ? <Unplug className="mr-2 h-4 w-4"/> : <Plug className="mr-2 h-4 w-4"/>}
                           {conn.status === "Connected" ? 'Disconnect' : 'Connect'}
                         </Button>
                      </DialogTrigger>
                      {conn.status === 'Disconnected' && (
                         <DialogContent>
                            <DialogHeader>
                              <DialogTitle>Connect to {conn.name}</DialogTitle>
                              <DialogDescription>Enter the conceptual connection details below.</DialogDescription>
                            </DialogHeader>
                            <div className="grid gap-4 py-4">
                              <div className="grid grid-cols-4 items-center gap-4">
                                <Label htmlFor="host" className="text-right">Host</Label>
                                <Input id="host" placeholder="e.g., localhost" className="col-span-3" />
                              </div>
                              <div className="grid grid-cols-4 items-center gap-4">
                                <Label htmlFor="port" className="text-right">Port</Label>
                                <Input id="port" placeholder="e.g., 5432" className="col-span-3" />
                              </div>
                               <div className="grid grid-cols-4 items-center gap-4">
                                <Label htmlFor="user" className="text-right">Username</Label>
                                <Input id="user" placeholder="e.g., admin" className="col-span-3" />
                              </div>
                               <div className="grid grid-cols-4 items-center gap-4">
                                <Label htmlFor="password" className="text-right">Password</Label>
                                <Input id="password" type="password" className="col-span-3" />
                              </div>
                            </div>
                            <DialogFooter>
                              <DialogClose asChild>
                                <Button variant="outline">Cancel</Button>
                              </DialogClose>
                              <DialogClose asChild>
                                <Button onClick={() => handleToggleConnection(conn.name)}>Connect</Button>
                              </DialogClose>
                            </DialogFooter>
                          </DialogContent>
                      )}
                       {conn.status === 'Connected' && (
                         <DialogContent>
                            <DialogHeader>
                              <DialogTitle>Disconnect from {conn.name}?</DialogTitle>
                              <DialogDescription>Are you sure you want to disconnect from this data source?</DialogDescription>
                            </DialogHeader>
                            <DialogFooter>
                               <DialogClose asChild>
                                <Button variant="outline">Cancel</Button>
                              </DialogClose>
                              <DialogClose asChild>
                                <Button variant="destructive" onClick={() => handleToggleConnection(conn.name)}>Disconnect</Button>
                              </DialogClose>
                            </DialogFooter>
                          </DialogContent>
                       )}
                    </Dialog>
                </div>
            </div>
           ))}
        </CardContent>
         <CardFooter>
            <Dialog>
                <DialogTrigger asChild>
                    <Button>
                        <PlusCircle className="mr-2 h-4 w-4"/>
                        Add New Data Source
                    </Button>
                </DialogTrigger>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Add New Data Source (Conceptual)</DialogTitle>
                        <DialogDescription>Select a new data source to configure and add to your connections list.</DialogDescription>
                    </DialogHeader>
                    <div className="py-4">
                        <p className="text-sm text-muted-foreground text-center">A form to select and configure a new data source would appear here.</p>
                    </div>
                     <DialogFooter>
                        <DialogClose asChild>
                            <Button variant="outline">Cancel</Button>
                        </DialogClose>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
         </CardFooter>
      </Card>
    </div>
  );
}
