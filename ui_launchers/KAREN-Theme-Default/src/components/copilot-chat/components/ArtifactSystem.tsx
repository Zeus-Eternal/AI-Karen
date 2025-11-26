import React, { useState, useEffect, useCallback } from 'react';
import { useArtifactSystem, useArtifacts, useActiveArtifacts, useSharedArtifacts } from '../core/artifact-hooks';
import { CopilotArtifact } from '../types/copilot';
import { Button } from '../../ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../ui/card';
import { Badge } from '../../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../ui/tabs';
import { Alert, AlertDescription, AlertTitle } from '../../ui/alert';
import { Input } from '../../ui/input';
import { Textarea } from '../../ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../ui/select';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '../../ui/dialog';
import {
  FileText,
  Code,
  TestTube,
  BarChart3,
  Plus,
  Eye,
  Edit,
  Trash2,
  Share,
  History,
  Download,
  Copy,
  Save,
  X
} from 'lucide-react';

/**
 * ArtifactSystem - Provides UI for artifact management
 * Implements Phase 5 of the INNOVATIVE_COPILOT_PLAN.md
 */

interface ArtifactSystemProps {
  className?: string;
}

interface ArtifactCardProps {
  artifact: CopilotArtifact;
  isActive: boolean;
  onView: () => void;
  onEdit: () => void;
  onDelete: () => void;
  onShare: () => void;
  onVersion: () => void;
  onDownload: () => void;
}

/**
 * ArtifactCard component for displaying a single artifact
 */
const ArtifactCard: React.FC<ArtifactCardProps> = ({
  artifact,
  isActive,
  onView,
  onEdit,
  onDelete,
  onShare,
  onVersion,
  onDownload,
}) => {
  const getArtifactIcon = () => {
    switch (artifact.type) {
      case 'code':
        return <Code className="h-5 w-5" />;
      case 'documentation':
        return <FileText className="h-5 w-5" />;
      case 'test':
        return <TestTube className="h-5 w-5" />;
      case 'analysis':
        return <BarChart3 className="h-5 w-5" />;
      default:
        return <FileText className="h-5 w-5" />;
    }
  };

  const getTypeBadgeVariant = () => {
    switch (artifact.type) {
      case 'code':
        return 'default';
      case 'documentation':
        return 'secondary';
      case 'test':
        return 'outline';
      case 'analysis':
        return 'default';
      default:
        return 'outline';
    }
  };

  return (
    <Card className="w-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-sm">
      <CardHeader className="pb-3">
        <div className="flex justify-between items-start">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400">
              {getArtifactIcon()}
            </div>
            <div className="text-left">
              <CardTitle className="text-lg">{artifact.title}</CardTitle>
              <CardDescription className="text-sm">{artifact.description}</CardDescription>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={getTypeBadgeVariant()} className="text-xs">
              {artifact.type}
            </Badge>
            {isActive && (
              <Badge variant="outline" className="text-xs">Active</Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="space-y-4">
          <div className="text-sm text-muted-foreground dark:text-gray-400">
            <p>Language: {artifact.language}</p>
            <p>Created: {artifact.metadata.timestamp ? new Date(artifact.metadata.timestamp as string).toLocaleString() : 'Unknown'}</p>
            {artifact.metadata.sharedWith && Array.isArray(artifact.metadata.sharedWith) && artifact.metadata.sharedWith.length > 0 ? (
              <p>Shared with: {(artifact.metadata.sharedWith as string[]).length} users</p>
            ) : null}
          </div>

          <div className="flex flex-wrap gap-2">
            <Button onClick={onView} size="sm" variant="outline" className="rounded-lg">
              <Eye className="h-4 w-4 mr-1" />
              View
            </Button>
            <Button onClick={onEdit} size="sm" variant="outline" className="rounded-lg">
              <Edit className="h-4 w-4 mr-1" />
              Edit
            </Button>
            <Button onClick={onShare} size="sm" variant="outline" className="rounded-lg">
              <Share className="h-4 w-4 mr-1" />
              Share
            </Button>
            <Button onClick={onVersion} size="sm" variant="outline" className="rounded-lg">
              <History className="h-4 w-4 mr-1" />
              Version
            </Button>
            <Button onClick={onDownload} size="sm" variant="outline" className="rounded-lg">
              <Download className="h-4 w-4 mr-1" />
              Download
            </Button>
            <Button onClick={onDelete} size="sm" variant="outline" className="rounded-lg">
              <Trash2 className="h-4 w-4 mr-1" />
              Delete
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

/**
 * ArtifactPreview component for viewing artifact content
 */
interface ArtifactPreviewProps {
  artifact: CopilotArtifact | null;
  isOpen: boolean;
  onClose: () => void;
  onEdit: (content: string) => void;
}

const ArtifactPreview: React.FC<ArtifactPreviewProps> = ({
  artifact,
  isOpen,
  onClose,
  onEdit,
}) => {
  const [content, setContent] = useState('');
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    if (artifact) {
      setContent(artifact.content);
    }
  }, [artifact]);

  const handleSave = () => {
    if (artifact) {
      onEdit(content);
      setIsEditing(false);
    }
  };

  const handleCancel = () => {
    if (artifact) {
      setContent(artifact.content);
      setIsEditing(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
  };

  if (!artifact) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-sm">
        <DialogHeader className="pb-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex justify-between items-center">
            <div>
              <DialogTitle className="text-xl">{artifact.title}</DialogTitle>
              <DialogDescription className="text-sm">{artifact.description}</DialogDescription>
            </div>
            <Button variant="ghost" size="sm" onClick={onClose} className="rounded-lg">
              <X className="h-4 w-4" />
            </Button>
          </div>
        </DialogHeader>
        
        <div className="space-y-4 pt-4">
          <div className="flex justify-between items-center">
            <div className="flex gap-2">
              <Badge variant="outline" className="text-xs">{artifact.type}</Badge>
              <Badge variant="outline" className="text-xs">{artifact.language}</Badge>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={handleCopy} className="rounded-lg">
                <Copy className="h-4 w-4 mr-1" />
                Copy
              </Button>
              {isEditing ? (
                <>
                  <Button variant="outline" size="sm" onClick={handleCancel} className="rounded-lg">
                    Cancel
                  </Button>
                  <Button size="sm" onClick={handleSave} className="rounded-lg">
                    <Save className="h-4 w-4 mr-1" />
                    Save
                  </Button>
                </>
              ) : (
                <Button variant="outline" size="sm" onClick={() => setIsEditing(true)} className="rounded-lg">
                  <Edit className="h-4 w-4 mr-1" />
                  Edit
                </Button>
              )}
            </div>
          </div>

          {isEditing ? (
            <Textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              className="min-h-[400px] font-mono text-sm bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg"
            />
          ) : (
            <pre className="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg overflow-x-auto text-sm border border-gray-200 dark:border-gray-700">
              <code>{content}</code>
            </pre>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

/**
 * ArtifactSystem component
 */
export const ArtifactSystem: React.FC<ArtifactSystemProps> = ({ className }) => {
  const {
    createArtifact,
    updateArtifact,
    deleteArtifact,
    viewArtifact,
    generateArtifact,
    error,
    clearError,
  } = useArtifactSystem();

  const artifacts = useArtifacts();
  const activeArtifacts = useActiveArtifacts();
  const sharedArtifacts = useSharedArtifacts();

  const [selectedArtifact, setSelectedArtifact] = useState<CopilotArtifact | null>(null);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isGenerateDialogOpen, setIsGenerateDialogOpen] = useState(false);
  const [newArtifact, setNewArtifact] = useState({
    title: '',
    description: '',
    type: 'code' as CopilotArtifact['type'],
    content: '',
    language: 'javascript',
  });
  const [generatePrompt, setGeneratePrompt] = useState('');
  const [generateType, setGenerateType] = useState<CopilotArtifact['type']>('code');

  const handleViewArtifact = useCallback((artifact: CopilotArtifact) => {
    setSelectedArtifact(artifact);
    setIsPreviewOpen(true);
    viewArtifact(artifact.id);
  }, [viewArtifact]);

  const handleEditArtifact = useCallback((artifact: CopilotArtifact) => {
    setSelectedArtifact(artifact);
    setIsPreviewOpen(true);
  }, []);

  const handleSaveArtifact = useCallback(async (content: string) => {
    if (selectedArtifact) {
      await updateArtifact(selectedArtifact.id, { content });
      setSelectedArtifact({
        ...selectedArtifact,
        content,
      });
    }
  }, [selectedArtifact, updateArtifact]);

  const handleDeleteArtifact = useCallback(async (artifact: CopilotArtifact) => {
    await deleteArtifact(artifact.id);
  }, [deleteArtifact]);

  const handleShareArtifact = useCallback(async (artifact: CopilotArtifact) => {
    // In a real implementation, this would open a dialog to select users to share with
    // For now, we'll just simulate sharing with a dummy user
    await updateArtifact(artifact.id, {
      metadata: {
        ...artifact.metadata,
        sharedWith: [...(artifact.metadata.sharedWith as string[] || []), 'user1'],
      },
    });
  }, [updateArtifact]);

  const handleVersionArtifact = useCallback(async (artifact: CopilotArtifact) => {
    // In a real implementation, this would open a version history dialog
    // For now, we'll just create a new version
    await updateArtifact(artifact.id, {
      metadata: {
        ...artifact.metadata,
        versionedAt: new Date().toISOString(),
      },
    });
  }, [updateArtifact]);

  const handleDownloadArtifact = useCallback((artifact: CopilotArtifact) => {
    // Create a blob with the artifact content
    const blob = new Blob([artifact.content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    
    // Create a temporary link to download the file
    const a = document.createElement('a');
    a.href = url;
    a.download = `${artifact.title}.${getFileExtension(artifact.type)}`;
    document.body.appendChild(a);
    a.click();
    
    // Clean up
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, []);

  const getFileExtension = (type: CopilotArtifact['type']): string => {
    switch (type) {
      case 'code':
        return 'js';
      case 'documentation':
        return 'md';
      case 'test':
        return 'test.js';
      case 'analysis':
        return 'md';
      default:
        return 'txt';
    }
  };

  const handleCreateArtifact = useCallback(async () => {
    await createArtifact({
      ...newArtifact,
      metadata: {
        createdAt: new Date().toISOString(),
      },
    });
    setNewArtifact({
      title: '',
      description: '',
      type: 'code',
      content: '',
      language: 'javascript',
    });
    setIsCreateDialogOpen(false);
  }, [createArtifact, newArtifact]);

  const handleGenerateArtifact = useCallback(async () => {
    await generateArtifact(generateType, generatePrompt);
    setGeneratePrompt('');
    setIsGenerateDialogOpen(false);
  }, [generateArtifact, generatePrompt, generateType]);

  // Group artifacts by type
  const codeArtifacts = artifacts.filter(a => a.type === 'code');
  const documentationArtifacts = artifacts.filter(a => a.type === 'documentation');
  const testArtifacts = artifacts.filter(a => a.type === 'test');
  const analysisArtifacts = artifacts.filter(a => a.type === 'analysis');

  return (
    <div className={`p-4 ${className}`}>
      {error && (
        <Alert variant="destructive" className="mb-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <X className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
          <Button variant="outline" size="sm" onClick={clearError} className="mt-2 rounded-lg">
            Dismiss
          </Button>
        </Alert>
      )}

      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Artifact System</h1>
        <div className="flex gap-2">
          <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" className="rounded-lg">
                <Plus className="h-4 w-4 mr-1" />
                Create Artifact
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-sm">
              <DialogHeader className="pb-4 border-b border-gray-200 dark:border-gray-700">
                <DialogTitle className="text-xl">Create New Artifact</DialogTitle>
                <DialogDescription className="text-sm">
                  Create a new artifact from scratch
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 pt-4">
                <div>
                  <label className="text-sm font-medium">Title</label>
                  <Input
                    value={newArtifact.title}
                    onChange={(e) => setNewArtifact({...newArtifact, title: e.target.value})}
                    placeholder="Enter artifact title"
                    className="rounded-lg"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Description</label>
                  <Textarea
                    value={newArtifact.description}
                    onChange={(e) => setNewArtifact({...newArtifact, description: e.target.value})}
                    placeholder="Enter artifact description"
                    className="rounded-lg"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Type</label>
                  <Select
                    value={newArtifact.type}
                    onValueChange={(value: CopilotArtifact['type']) =>
                      setNewArtifact({...newArtifact, type: value})
                    }
                  >
                    <SelectTrigger className="rounded-lg">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="code">Code</SelectItem>
                      <SelectItem value="documentation">Documentation</SelectItem>
                      <SelectItem value="test">Test</SelectItem>
                      <SelectItem value="analysis">Analysis</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm font-medium">Language</label>
                  <Input
                    value={newArtifact.language}
                    onChange={(e) => setNewArtifact({...newArtifact, language: e.target.value})}
                    placeholder="Enter programming language"
                    className="rounded-lg"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Content</label>
                  <Textarea
                    value={newArtifact.content}
                    onChange={(e) => setNewArtifact({...newArtifact, content: e.target.value})}
                    placeholder="Enter artifact content"
                    className="min-h-[200px] rounded-lg"
                  />
                </div>
                <div className="flex justify-end gap-2">
                  <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)} className="rounded-lg">
                    Cancel
                  </Button>
                  <Button onClick={handleCreateArtifact} className="rounded-lg">
                    Create
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>

          <Dialog open={isGenerateDialogOpen} onOpenChange={setIsGenerateDialogOpen}>
            <DialogTrigger asChild>
              <Button className="rounded-lg">
                <Plus className="h-4 w-4 mr-1" />
                Generate Artifact
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-sm">
              <DialogHeader className="pb-4 border-b border-gray-200 dark:border-gray-700">
                <DialogTitle className="text-xl">Generate Artifact</DialogTitle>
                <DialogDescription className="text-sm">
                  Generate an artifact using AI
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 pt-4">
                <div>
                  <label className="text-sm font-medium">Type</label>
                  <Select
                    value={generateType}
                    onValueChange={(value: CopilotArtifact['type']) => setGenerateType(value)}
                  >
                    <SelectTrigger className="rounded-lg">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="code">Code</SelectItem>
                      <SelectItem value="documentation">Documentation</SelectItem>
                      <SelectItem value="test">Test</SelectItem>
                      <SelectItem value="analysis">Analysis</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm font-medium">Prompt</label>
                  <Textarea
                    value={generatePrompt}
                    onChange={(e) => setGeneratePrompt(e.target.value)}
                    placeholder="Describe what you want to generate"
                    className="min-h-[200px] rounded-lg"
                  />
                </div>
                <div className="flex justify-end gap-2">
                  <Button variant="outline" onClick={() => setIsGenerateDialogOpen(false)} className="rounded-lg">
                    Cancel
                  </Button>
                  <Button onClick={handleGenerateArtifact} className="rounded-lg">
                    Generate
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <Tabs defaultValue="all" className="w-full">
        <TabsList className="grid w-full grid-cols-6 bg-white dark:bg-gray-800 p-1 rounded-xl shadow-sm mb-4">
          <TabsTrigger value="all" className="rounded-lg data-[state=active]:bg-gray-100 dark:data-[state=active]:bg-gray-700">All</TabsTrigger>
          <TabsTrigger value="code" className="rounded-lg data-[state=active]:bg-gray-100 dark:data-[state=active]:bg-gray-700">Code</TabsTrigger>
          <TabsTrigger value="documentation" className="rounded-lg data-[state=active]:bg-gray-100 dark:data-[state=active]:bg-gray-700">Documentation</TabsTrigger>
          <TabsTrigger value="test" className="rounded-lg data-[state=active]:bg-gray-100 dark:data-[state=active]:bg-gray-700">Tests</TabsTrigger>
          <TabsTrigger value="analysis" className="rounded-lg data-[state=active]:bg-gray-100 dark:data-[state=active]:bg-gray-700">Analysis</TabsTrigger>
          <TabsTrigger value="shared" className="rounded-lg data-[state=active]:bg-gray-100 dark:data-[state=active]:bg-gray-700">Shared</TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {artifacts.map(artifact => (
              <ArtifactCard
                key={artifact.id}
                artifact={artifact}
                isActive={activeArtifacts.some(aId => aId === artifact.id)}
                onView={() => handleViewArtifact(artifact)}
                onEdit={() => handleEditArtifact(artifact)}
                onDelete={() => handleDeleteArtifact(artifact)}
                onShare={() => handleShareArtifact(artifact)}
                onVersion={() => handleVersionArtifact(artifact)}
                onDownload={() => handleDownloadArtifact(artifact)}
              />
            ))}
          </div>
        </TabsContent>

        <TabsContent value="code" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {codeArtifacts.map(artifact => (
              <ArtifactCard
                key={artifact.id}
                artifact={artifact}
                isActive={activeArtifacts.some(aId => aId === artifact.id)}
                onView={() => handleViewArtifact(artifact)}
                onEdit={() => handleEditArtifact(artifact)}
                onDelete={() => handleDeleteArtifact(artifact)}
                onShare={() => handleShareArtifact(artifact)}
                onVersion={() => handleVersionArtifact(artifact)}
                onDownload={() => handleDownloadArtifact(artifact)}
              />
            ))}
          </div>
        </TabsContent>

        <TabsContent value="documentation" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {documentationArtifacts.map(artifact => (
              <ArtifactCard
                key={artifact.id}
                artifact={artifact}
                isActive={activeArtifacts.some(aId => aId === artifact.id)}
                onView={() => handleViewArtifact(artifact)}
                onEdit={() => handleEditArtifact(artifact)}
                onDelete={() => handleDeleteArtifact(artifact)}
                onShare={() => handleShareArtifact(artifact)}
                onVersion={() => handleVersionArtifact(artifact)}
                onDownload={() => handleDownloadArtifact(artifact)}
              />
            ))}
          </div>
        </TabsContent>

        <TabsContent value="test" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {testArtifacts.map(artifact => (
              <ArtifactCard
                key={artifact.id}
                artifact={artifact}
                isActive={activeArtifacts.some(aId => aId === artifact.id)}
                onView={() => handleViewArtifact(artifact)}
                onEdit={() => handleEditArtifact(artifact)}
                onDelete={() => handleDeleteArtifact(artifact)}
                onShare={() => handleShareArtifact(artifact)}
                onVersion={() => handleVersionArtifact(artifact)}
                onDownload={() => handleDownloadArtifact(artifact)}
              />
            ))}
          </div>
        </TabsContent>

        <TabsContent value="analysis" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {analysisArtifacts.map(artifact => (
              <ArtifactCard
                key={artifact.id}
                artifact={artifact}
                isActive={activeArtifacts.some(aId => aId === artifact.id)}
                onView={() => handleViewArtifact(artifact)}
                onEdit={() => handleEditArtifact(artifact)}
                onDelete={() => handleDeleteArtifact(artifact)}
                onShare={() => handleShareArtifact(artifact)}
                onVersion={() => handleVersionArtifact(artifact)}
                onDownload={() => handleDownloadArtifact(artifact)}
              />
            ))}
          </div>
        </TabsContent>

        <TabsContent value="shared" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {sharedArtifacts.map(artifact => (
              <ArtifactCard
                key={artifact.id}
                artifact={artifact}
                isActive={activeArtifacts.some(aId => aId === artifact.id)}
                onView={() => handleViewArtifact(artifact)}
                onEdit={() => handleEditArtifact(artifact)}
                onDelete={() => handleDeleteArtifact(artifact)}
                onShare={() => handleShareArtifact(artifact)}
                onVersion={() => handleVersionArtifact(artifact)}
                onDownload={() => handleDownloadArtifact(artifact)}
              />
            ))}
          </div>
        </TabsContent>
      </Tabs>

      <ArtifactPreview
        artifact={selectedArtifact}
        isOpen={isPreviewOpen}
        onClose={() => setIsPreviewOpen(false)}
        onEdit={handleSaveArtifact}
      />
    </div>
  );
};

export default ArtifactSystem;