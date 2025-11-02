/**
 * Memory Management Tools Component
 * Provides CRUD operations, batch operations, validation, and backup/restore functionality
 */
import React, { useState, useCallback, useMemo, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Checkbox } from '@/components/ui/checkbox';

import { } from 'lucide-react';
import { getMemoryService } from '@/services/memoryService';
import type {  MemoryEntry, MemoryValidationResult, ValidationIssue, MemoryBatchOperation, MemoryBatchResult, MemoryBackup, MemoryRestoreOptions, MemoryEditorProps } from '@/types/memory';
interface BatchOperationConfig {
  type: 'delete' | 'update' | 'merge' | 'tag' | 'cluster';
  parameters: Record<string, any>;
  confirmationRequired: boolean;
}
interface ValidationConfig {
  checkDuplicates: boolean;
  checkInconsistencies: boolean;
  checkCorruption: boolean;
  checkLowQuality: boolean;
  checkOrphaned: boolean;
  minConfidenceThreshold: number;
  maxContentLength: number;
}
export const MemoryManagementTools: React.FC<MemoryEditorProps> = ({
  memory,
  onSave,
  onCancel,
  onDelete,
  isOpen,
  userId,
  tenantId
}) => {
  const [selectedMemories, setSelectedMemories] = useState<Set<string>>(new Set());
  const [memories, setMemories] = useState<MemoryEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationResults, setValidationResults] = useState<MemoryValidationResult | null>(null);
  const [backups, setBackups] = useState<MemoryBackup[]>([]);
  const [activeTab, setActiveTab] = useState('editor');
  const [searchQuery, setSearchQuery] = useState('');
  const [batchOperation, setBatchOperation] = useState<BatchOperationConfig | null>(null);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [validationConfig, setValidationConfig] = useState<ValidationConfig>({
    checkDuplicates: true,
    checkInconsistencies: true,
    checkCorruption: true,
    checkLowQuality: false,
    checkOrphaned: true,
    minConfidenceThreshold: 0.3,
    maxContentLength: 10000

  const [editForm, setEditForm] = useState({
    content: '',
    type: 'context' as 'fact' | 'preference' | 'context',
    confidence: 0.8,
    tags: [] as string[],
    cluster: 'general'

  const memoryService = useMemo(() => getMemoryService(), []);
  // Initialize form when memory changes
  useEffect(() => {
    if (memory) {
      setEditForm({
        content: memory.content,
        type: memory.type || 'context',
        confidence: memory.confidence || 0.8,
        tags: memory.tags || [],
        cluster: memory.metadata?.cluster || 'general'

    } else {
      setEditForm({
        content: '',
        type: 'context',
        confidence: 0.8,
        tags: [],
        cluster: 'general'

    }
  }, [memory]);
  // Load memories for batch operations
  const loadMemories = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await memoryService.searchMemories('', {
        userId,
        maxResults: 100

      setMemories(result.memories);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load memories';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [userId, tenantId, memoryService]);
  // Load backups
  const loadBackups = useCallback(async () => {
    try {
      // Mock backup data - in real implementation, this would fetch from backend
      const mockBackups: MemoryBackup[] = [
        {
          id: 'backup-1',
          name: 'Daily Backup - 2024-01-15',
          description: 'Automated daily backup',
          userId,
          createdAt: new Date(Date.now() - 86400000),
          memoryCount: 150,
          size: 2048000,
          version: '1.0',
          metadata: { type: 'automatic' }
        },
        {
          id: 'backup-2',
          name: 'Manual Backup - Before Cleanup',
          description: 'Manual backup before memory cleanup',
          userId,
          createdAt: new Date(Date.now() - 172800000),
          memoryCount: 200,
          size: 2560000,
          version: '1.0',
          metadata: { type: 'manual' }
        }
      ];
      setBackups(mockBackups);
    } catch (err) {
    }
  }, [userId]);
  // Load data when component opens
  useEffect(() => {
    if (isOpen) {
      loadMemories();
      loadBackups();
    }
  }, [isOpen, loadMemories, loadBackups]);
  // Validate memories
  const validateMemories = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      // Mock validation logic - in real implementation, this would call backend
      const issues: ValidationIssue[] = [];
      const memoriesToCheck = selectedMemories.size > 0 
        ? memories.filter(m => selectedMemories.has(m.id))
        : memories;
      // Check for duplicates
      if (validationConfig.checkDuplicates) {
        const contentMap = new Map<string, string[]>();
        memoriesToCheck.forEach(memory => {
          const normalizedContent = memory.content.toLowerCase().trim();
          if (!contentMap.has(normalizedContent)) {
            contentMap.set(normalizedContent, []);
          }
          contentMap.get(normalizedContent)!.push(memory.id);

        contentMap.forEach((ids, content) => {
          if (ids.length > 1) {
            issues.push({
              type: 'duplicate',
              severity: 'medium',
              description: `Found ${ids.length} memories with identical content`,
              affectedMemories: ids,
              suggestedAction: 'Merge duplicate memories or remove redundant ones'

          }

      }
      // Check for low quality memories
      if (validationConfig.checkLowQuality) {
        memoriesToCheck.forEach(memory => {
          if ((memory.confidence || 0) < validationConfig.minConfidenceThreshold) {
            issues.push({
              type: 'low_quality',
              severity: 'low',
              description: `Memory has low confidence score: ${((memory.confidence || 0) * 100).toFixed(0)}%`,
              affectedMemories: [memory.id],
              suggestedAction: 'Review and improve memory content or remove if not useful'

          }
          if (memory.content.length > validationConfig.maxContentLength) {
            issues.push({
              type: 'low_quality',
              severity: 'low',
              description: `Memory content is too long: ${memory.content.length} characters`,
              affectedMemories: [memory.id],
              suggestedAction: 'Split into smaller memories or summarize content'

          }

      }
      // Check for inconsistencies
      if (validationConfig.checkInconsistencies) {
        memoriesToCheck.forEach(memory => {
          if (!memory.tags || memory.tags.length === 0) {
            issues.push({
              type: 'inconsistency',
              severity: 'low',
              description: 'Memory has no tags',
              affectedMemories: [memory.id],
              suggestedAction: 'Add relevant tags to improve searchability'

          }
          if (!memory.type) {
            issues.push({
              type: 'inconsistency',
              severity: 'medium',
              description: 'Memory has no type classification',
              affectedMemories: [memory.id],
              suggestedAction: 'Classify memory as fact, preference, or context'

          }

      }
      // Check for orphaned memories
      if (validationConfig.checkOrphaned) {
        memoriesToCheck.forEach(memory => {
          if (!memory.relationships || memory.relationships.length === 0) {
            issues.push({
              type: 'orphaned',
              severity: 'low',
              description: 'Memory has no relationships to other memories',
              affectedMemories: [memory.id],
              suggestedAction: 'Consider linking to related memories or removing if isolated'

          }

      }
      const validationResult: MemoryValidationResult = {
        isValid: issues.length === 0,
        issues,
        suggestions: [
          'Regular validation helps maintain memory quality',
          'Consider setting up automated cleanup rules',
          'Review and update memory tags periodically'
        ],
        confidence: Math.max(0, 1 - (issues.length / memoriesToCheck.length))
      };
      setValidationResults(validationResult);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Validation failed';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [memories, selectedMemories, validationConfig]);
  // Handle batch operations
  const executeBatchOperation = useCallback(async (operation: BatchOperationConfig) => {
    if (selectedMemories.size === 0) {
      setError('No memories selected for batch operation');
      return;
    }
    try {
      setLoading(true);
      setError(null);
      const batchOp: MemoryBatchOperation = {
        type: operation.type,
        memoryIds: Array.from(selectedMemories),
        parameters: operation.parameters,
        userId,
        timestamp: new Date()
      };
      // Mock batch operation - in real implementation, this would call backend
      const result: MemoryBatchResult = {
        operationId: `batch-${Date.now()}`,
        success: true,
        processedCount: selectedMemories.size,
        failedCount: 0,
        errors: [],
        warnings: [],
        duration: Math.random() * 1000 + 500
      };
      // Update local state based on operation
      switch (operation.type) {
        case 'delete':
          setMemories(prev => prev.filter(m => !selectedMemories.has(m.id)));
          break;
        case 'tag':
          const newTags = operation.parameters.tags || [];
          setMemories(prev => prev.map(m => 
            selectedMemories.has(m.id) 
              ? { ...m, tags: [...new Set([...m.tags, ...newTags])] }
              : m
          ));
          break;
        case 'cluster':
          const newCluster = operation.parameters.cluster;
          setMemories(prev => prev.map(m => 
            selectedMemories.has(m.id) 
              ? { ...m, metadata: { ...m.metadata, cluster: newCluster } }
              : m
          ));
          break;
      }
      setSelectedMemories(new Set());
      setBatchOperation(null);
      setShowConfirmation(false);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Batch operation failed';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [selectedMemories, userId]);
  // Handle memory save
  const handleSave = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const updatedMemory: Partial<MemoryEntry> = {
        content: editForm.content,
        type: editForm.type,
        confidence: editForm.confidence,
        tags: editForm.tags,
        metadata: {
          ...memory?.metadata,
          cluster: editForm.cluster
        }
      };
      await onSave(updatedMemory);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save memory';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [editForm, memory, onSave]);
  // Handle backup creation
  const createBackup = useCallback(async (name: string, description?: string) => {
    try {
      setLoading(true);
      setError(null);
      // Mock backup creation
      const backup: MemoryBackup = {
        id: `backup-${Date.now()}`,
        name,
        description,
        userId,
        createdAt: new Date(),
        memoryCount: memories.length,
        size: memories.reduce((sum, m) => sum + m.content.length, 0),
        version: '1.0',
        metadata: { type: 'manual' }
      };
      setBackups(prev => [backup, ...prev]);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create backup';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [memories, userId]);
  // Handle backup restore
  const restoreBackup = useCallback(async (backup: MemoryBackup, options: MemoryRestoreOptions) => {
    try {
      setLoading(true);
      setError(null);
      // Mock restore operation
      // In real implementation, this would restore memories from backup
      await new Promise(resolve => setTimeout(resolve, 2000));
      // Reload memories after restore
      await loadMemories();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to restore backup';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [loadMemories]);
  // Filter memories based on search
  const filteredMemories = useMemo(() => {
    if (!searchQuery) return memories;
    const query = searchQuery.toLowerCase();
    return memories.filter(memory => 
      memory.content.toLowerCase().includes(query) ||
      memory.tags.some(tag => tag.toLowerCase().includes(query)) ||
      (memory.type && memory.type.toLowerCase().includes(query))
    );
  }, [memories, searchQuery]);
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden ">
        <div className="flex items-center justify-between p-6 border-b sm:p-4 md:p-6">
          <h2 className="text-xl font-semibold">
            {memory ? 'Edit Memory' : 'Memory Management Tools'}
          </h2>
          <Button variant="ghost" onClick={onCancel} >
            <XCircle className="w-5 h-5 " />
          </Button>
        </div>
        {error && (
          <div className="p-4 bg-red-50 border-b border-red-200 sm:p-4 md:p-6">
            <div className="flex items-center space-x-2 text-red-700">
              <AlertTriangle className="w-4 h-4 " />
              <span>{error}</span>
            </div>
          </div>
        )}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="editor">Editor</TabsTrigger>
            <TabsTrigger value="batch">Batch Operations</TabsTrigger>
            <TabsTrigger value="validation">Validation</TabsTrigger>
            <TabsTrigger value="backup">Backup & Restore</TabsTrigger>
            <TabsTrigger value="settings">Settings</TabsTrigger>
          </TabsList>
          <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)] sm:p-4 md:p-6">
            <TabsContent value="editor" className="space-y-4">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2 md:text-base lg:text-lg">Content</label>
                    <textarea
                      value={editForm.content}
                      onChange={(e) => setEditForm(prev => ({ ...prev, content: e.target.value }))}
                      placeholder="Enter memory content..."
                      className="w-full h-32 p-3 border rounded-md resize-vertical sm:p-4 md:p-6"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-2 md:text-base lg:text-lg">Type</label>
                      <select
                        value={editForm.type}
                        onChange={(e) => setEditForm(prev => ({ 
                          ...prev, 
                          type: e.target.value as any 
                        }))}
                        className="w-full p-2 border rounded-md sm:p-4 md:p-6"
                      >
                        <option value="fact">Fact</option>
                        <option value="preference">Preference</option>
                        <option value="context">Context</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2 md:text-base lg:text-lg">Cluster</label>
                      <select
                        value={editForm.cluster}
                        onChange={(e) => setEditForm(prev => ({ ...prev, cluster: e.target.value }))}
                        className="w-full p-2 border rounded-md sm:p-4 md:p-6"
                      >
                        <option value="technical">Technical</option>
                        <option value="personal">Personal</option>
                        <option value="work">Work</option>
                        <option value="general">General</option>
                      </select>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2 md:text-base lg:text-lg">
                      Confidence ({Math.round(editForm.confidence * 100)}%)
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.1"
                      value={editForm.confidence}
                      onChange={(e) => setEditForm(prev => ({ 
                        ...prev, 
                        confidence: parseFloat(e.target.value) 
                      }))}
                      className="w-full"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2 md:text-base lg:text-lg">Tags</label>
                    <input
                      type="text"
                      placeholder="Enter tags separated by commas"
                      value={editForm.tags.join(', ')}
                      onChange={(e) => setEditForm(prev => ({ 
                        ...prev, 
                        tags: e.target.value.split(',').map(tag => tag.trim()).filter(Boolean)
                      }))}
                    />
                    <div className="flex flex-wrap gap-1 mt-2">
                      {editForm.tags.map(tag => (
                        <Badge key={tag} variant="secondary" className="text-xs sm:text-sm md:text-base">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
                <div className="space-y-4">
                  <Card className="p-4 sm:p-4 md:p-6">
                    <h3 className="font-medium mb-3">Memory Preview</h3>
                    <div className="space-y-2 text-sm md:text-base lg:text-lg">
                      <div><strong>Type:</strong> {editForm.type}</div>
                      <div><strong>Cluster:</strong> {editForm.cluster}</div>
                      <div><strong>Confidence:</strong> {Math.round(editForm.confidence * 100)}%</div>
                      <div><strong>Tags:</strong> {editForm.tags.length} tags</div>
                      <div><strong>Content Length:</strong> {editForm.content.length} characters</div>
                    </div>
                  </Card>
                  <Card className="p-4 sm:p-4 md:p-6">
                    <h3 className="font-medium mb-3">Actions</h3>
                    <div className="space-y-2">
                      <Button 
                        onClick={handleSave} 
                        disabled={loading || !editForm.content.trim()}
                        className="w-full"
                       >
                        {loading ? 'Saving...' : 'Save Memory'}
                      </Button>
                      {memory && onDelete && (
                        <Button 
                          variant="destructive" 
                          onClick={() => onDelete(memory.id)}
                          className="w-full"
                        >
                        </Button>
                      )}
                      <Button variant="outline" onClick={onCancel} className="w-full" >
                      </Button>
                    </div>
                  </Card>
                </div>
              </div>
            </TabsContent>
            <TabsContent value="batch" className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium">Batch Operations</h3>
                <div className="flex items-center space-x-2">
                  <input
                    type="text"
                    placeholder="Search memories..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-64 "
                  />
                  <Button onClick={loadMemories} variant="outline" size="sm" >
                    <RefreshCw className="w-4 h-4 " />
                  </Button>
                </div>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded sm:p-4 md:p-6">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    checked={selectedMemories.size === filteredMemories.length && filteredMemories.length > 0}
                    onCheckedChange={(checked) => {
                      if (checked) {
                        setSelectedMemories(new Set(filteredMemories.map(m => m.id)));
                      } else {
                        setSelectedMemories(new Set());
                      }
                    }}
                  />
                  <span className="text-sm md:text-base lg:text-lg">
                    {selectedMemories.size} of {filteredMemories.length} selected
                  </span>
                </div>
                <div className="flex space-x-2">
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={selectedMemories.size === 0}
                    onClick={() => setBatchOperation({
                      type: 'tag',
                      parameters: { tags: ['batch-tagged'] },
                      confirmationRequired: false
                    })}
                  >
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={selectedMemories.size === 0}
                    onClick={() => setBatchOperation({
                      type: 'cluster',
                      parameters: { cluster: 'general' },
                      confirmationRequired: false
                    })}
                  >
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    disabled={selectedMemories.size === 0}
                    onClick={() => {
                      setBatchOperation({
                        type: 'delete',
                        parameters: {},
                        confirmationRequired: true

                      setShowConfirmation(true);
                    }}
                  >
                  </Button>
                </div>
              </div>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {filteredMemories.map(memory => (
                  <Card key={memory.id} className="p-3 sm:p-4 md:p-6">
                    <div className="flex items-start space-x-3">
                      <Checkbox
                        checked={selectedMemories.has(memory.id)}
                        onCheckedChange={(checked) => {
                          const newSelected = new Set(selectedMemories);
                          if (checked) {
                            newSelected.add(memory.id);
                          } else {
                            newSelected.delete(memory.id);
                          }
                          setSelectedMemories(newSelected);
                        }}
                      />
                      <div className="flex-1 min-w-0 ">
                        <div className="flex items-center space-x-2 mb-1">
                          <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                            {memory.type || 'unknown'}
                          </Badge>
                          {memory.confidence && (
                            <Badge variant="secondary" className="text-xs sm:text-sm md:text-base">
                              {Math.round(memory.confidence * 100)}%
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm line-clamp-2 md:text-base lg:text-lg">{memory.content}</p>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {memory.tags.slice(0, 3).map(tag => (
                            <Badge key={tag} variant="outline" className="text-xs sm:text-sm md:text-base">
                              {tag}
                            </Badge>
                          ))}
                          {memory.tags.length > 3 && (
                            <Badge variant="outline" className="text-xs sm:text-sm md:text-base">
                              +{memory.tags.length - 3}
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </TabsContent>
            <TabsContent value="validation" className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium">Memory Validation</h3>
                <button onClick={validateMemories} disabled={loading} aria-label="Button">
                  {loading ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin " />
                      Validating...
                    </>
                  ) : (
                    <>
                      <Shield className="w-4 h-4 mr-2 " />
                    </>
                  )}
                </Button>
              </div>
              <Card className="p-4 sm:p-4 md:p-6">
                <h4 className="font-medium mb-3">Validation Settings</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="flex items-center space-x-2">
                      <Checkbox
                        checked={validationConfig.checkDuplicates}
                        onCheckedChange={(checked) => setValidationConfig(prev => ({
                          ...prev,
                          checkDuplicates: !!checked
                        }))}
                      />
                      <span className="text-sm md:text-base lg:text-lg">Check for duplicates</span>
                    </label>
                    <label className="flex items-center space-x-2">
                      <Checkbox
                        checked={validationConfig.checkInconsistencies}
                        onCheckedChange={(checked) => setValidationConfig(prev => ({
                          ...prev,
                          checkInconsistencies: !!checked
                        }))}
                      />
                      <span className="text-sm md:text-base lg:text-lg">Check for inconsistencies</span>
                    </label>
                    <label className="flex items-center space-x-2">
                      <Checkbox
                        checked={validationConfig.checkLowQuality}
                        onCheckedChange={(checked) => setValidationConfig(prev => ({
                          ...prev,
                          checkLowQuality: !!checked
                        }))}
                      />
                      <span className="text-sm md:text-base lg:text-lg">Check for low quality</span>
                    </label>
                  </div>
                  <div className="space-y-2">
                    <label className="flex items-center space-x-2">
                      <Checkbox
                        checked={validationConfig.checkCorruption}
                        onCheckedChange={(checked) => setValidationConfig(prev => ({
                          ...prev,
                          checkCorruption: !!checked
                        }))}
                      />
                      <span className="text-sm md:text-base lg:text-lg">Check for corruption</span>
                    </label>
                    <label className="flex items-center space-x-2">
                      <Checkbox
                        checked={validationConfig.checkOrphaned}
                        onCheckedChange={(checked) => setValidationConfig(prev => ({
                          ...prev,
                          checkOrphaned: !!checked
                        }))}
                      />
                      <span className="text-sm md:text-base lg:text-lg">Check for orphaned memories</span>
                    </label>
                  </div>
                </div>
              </Card>
              {validationResults && (
                <Card className="p-4 sm:p-4 md:p-6">
                  <div className="flex items-center space-x-2 mb-3">
                    {validationResults.isValid ? (
                      <CheckCircle className="w-5 h-5 text-green-500 " />
                    ) : (
                      <AlertTriangle className="w-5 h-5 text-yellow-500 " />
                    )}
                    <h4 className="font-medium">
                      Validation Results ({validationResults.issues.length} issues found)
                    </h4>
                  </div>
                  {validationResults.issues.length > 0 && (
                    <div className="space-y-2">
                      {validationResults.issues.map((issue, index) => (
                        <div key={index} className="p-3 border rounded-md sm:p-4 md:p-6">
                          <div className="flex items-center justify-between mb-2">
                            <Badge 
                              variant={issue.severity === 'critical' ? 'destructive' : 
                                     issue.severity === 'high' ? 'destructive' :
                                     issue.severity === 'medium' ? 'default' : 'secondary'}
                            >
                              {issue.type} - {issue.severity}
                            </Badge>
                            <span className="text-xs text-gray-500 sm:text-sm md:text-base">
                              {issue.affectedMemories.length} memories affected
                            </span>
                          </div>
                          <p className="text-sm mb-2 md:text-base lg:text-lg">{issue.description}</p>
                          <p className="text-xs text-gray-600 sm:text-sm md:text-base">{issue.suggestedAction}</p>
                        </div>
                      ))}
                    </div>
                  )}
                  <div className="mt-4 p-3 bg-blue-50 rounded-md sm:p-4 md:p-6">
                    <h5 className="font-medium text-sm mb-2 md:text-base lg:text-lg">Suggestions:</h5>
                    <ul className="text-xs space-y-1 sm:text-sm md:text-base">
                      {validationResults.suggestions.map((suggestion, index) => (
                        <li key={index}>• {suggestion}</li>
                      ))}
                    </ul>
                  </div>
                </Card>
              )}
            </TabsContent>
            <TabsContent value="backup" className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium">Backup & Restore</h3>
                <button
                  onClick={() => {
                    const name = prompt('Enter backup name:');
                    if (name) {
                      const description = prompt('Enter backup description (optional):');
                      createBackup(name, description || undefined);
                    }
                  }}
                >
                  <Archive className="w-4 h-4 mr-2 " />
                </Button>
              </div>
              <div className="space-y-3">
                {backups.map(backup => (
                  <Card key={backup.id} className="p-4 sm:p-4 md:p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-medium">{backup.name}</h4>
                        {backup.description && (
                          <p className="text-sm text-gray-600 md:text-base lg:text-lg">{backup.description}</p>
                        )}
                        <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500 sm:text-sm md:text-base">
                          <span>{backup.memoryCount} memories</span>
                          <span>{(backup.size / 1024 / 1024).toFixed(1)} MB</span>
                          <span>{backup.createdAt.toLocaleDateString()}</span>
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            if (confirm(`Restore backup "${backup.name}"? This will overwrite current memories.`)) {
                              restoreBackup(backup, {
                                backupId: backup.id,
                                overwriteExisting: true,
                                preserveIds: false

                            }
                          }}
                        >
                          <Upload className="w-4 h-4 mr-1 " />
                        </Button>
                        <Button size="sm" variant="outline" >
                          <Download className="w-4 h-4 mr-1 " />
                        </Button>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </TabsContent>
            <TabsContent value="settings" className="space-y-4">
              <h3 className="text-lg font-medium">Management Settings</h3>
              <Card className="p-4 sm:p-4 md:p-6">
                <h4 className="font-medium mb-3">Validation Thresholds</h4>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2 md:text-base lg:text-lg">
                      Minimum Confidence Threshold ({validationConfig.minConfidenceThreshold})
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.1"
                      value={validationConfig.minConfidenceThreshold}
                      onChange={(e) => setValidationConfig(prev => ({
                        ...prev,
                        minConfidenceThreshold: parseFloat(e.target.value)
                      }))}
                      className="w-full"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2 md:text-base lg:text-lg">
                    </label>
                    <input
                      type="number"
                      value={validationConfig.maxContentLength}
                      onChange={(e) => setValidationConfig(prev => ({
                        ...prev,
                        maxContentLength: parseInt(e.target.value) || 10000
                      }))}
                    />
                  </div>
                </div>
              </Card>
              <Card className="p-4 sm:p-4 md:p-6">
                <h4 className="font-medium mb-3">Batch Operation Settings</h4>
                <div className="space-y-2">
                  <label className="flex items-center space-x-2">
                    <Checkbox defaultChecked />
                    <span className="text-sm md:text-base lg:text-lg">Require confirmation for destructive operations</span>
                  </label>
                  <label className="flex items-center space-x-2">
                    <Checkbox defaultChecked />
                    <span className="text-sm md:text-base lg:text-lg">Create backup before batch operations</span>
                  </label>
                  <label className="flex items-center space-x-2">
                    <Checkbox />
                    <span className="text-sm md:text-base lg:text-lg">Enable undo for batch operations</span>
                  </label>
                </div>
              </Card>
            </TabsContent>
          </div>
        </Tabs>
        {/* Confirmation Dialog */}
        {showConfirmation && batchOperation && (
          <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center">
            <Card className="p-6 max-w-md sm:p-4 md:p-6">
              <h3 className="font-medium mb-3">Confirm Batch Operation</h3>
              <p className="text-sm text-gray-600 mb-4 md:text-base lg:text-lg">
                Are you sure you want to {batchOperation.type} {selectedMemories.size} memories?
                This action cannot be undone.
              </p>
              <div className="flex space-x-2">
                <Button
                  variant="destructive"
                  onClick={() => executeBatchOperation(batchOperation)}
                  disabled={loading}
                >
                  {loading ? 'Processing...' : 'Confirm'}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowConfirmation(false);
                    setBatchOperation(null);
                  }}
                >
                </Button>
              </div>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
};
export default MemoryManagementTools;
