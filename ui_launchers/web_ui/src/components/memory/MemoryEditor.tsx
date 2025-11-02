/**
 * CopilotKit-enhanced Memory Editor Component
 * Provides AI-powered suggestions for memory editing and enhancement
 */
import React, { useState, useEffect, useCallback } from 'react';
import { CopilotTextarea } from '@copilotkit/react-textarea';
import { useCopilotAction, useCopilotReadable } from '@copilotkit/react-core';
interface MemoryGridRow {
  id: string;
  content: string;
  type: 'fact' | 'preference' | 'context';
  confidence: number;
  last_accessed: string;
  relevance_score: number;
  semantic_cluster: string;
  relationships: string[];
  timestamp: number;
  user_id: string;
  session_id?: string;
  tenant_id?: string;
}
interface MemoryEditorProps {
  memory: MemoryGridRow | null;
  onSave: (updatedMemory: Partial<MemoryGridRow>) => Promise<void>;
  onCancel: () => void;
  onDelete?: (memoryId: string) => Promise<void>;
  isOpen: boolean;
  userId: string;
  tenantId?: string;
}
interface AISuggestion {
  type: 'enhancement' | 'categorization' | 'relationship' | 'correction';
  content: string;
  confidence: number;
  reasoning: string;
}
export const MemoryEditor: React.FC<MemoryEditorProps> = ({
  memory,
  onSave,
  onCancel,
  onDelete,
  isOpen,
  userId,
  tenantId
}) => {
  const [editedContent, setEditedContent] = useState('');
  const [editedType, setEditedType] = useState<'fact' | 'preference' | 'context'>('context');
  const [editedConfidence, setEditedConfidence] = useState(0.8);
  const [editedCluster, setEditedCluster] = useState('general');
  const [aiSuggestions, setAiSuggestions] = useState<AISuggestion[]>([]);
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Initialize form when memory changes
  useEffect(() => {
    if (memory) {
      setEditedContent(memory.content);
      setEditedType(memory.type);
      setEditedConfidence(memory.confidence);
      setEditedCluster(memory.semantic_cluster);
      setError(null);
    } else {
      // Reset form for new memory
      setEditedContent('');
      setEditedType('context');
      setEditedConfidence(0.8);
      setEditedCluster('general');
      setError(null);
    }
  }, [memory]);
  // Make memory data readable by CopilotKit
  useCopilotReadable({
    description: "Current memory being edited",
    value: memory ? {
      id: memory.id,
      content: memory.content,
      type: memory.type,
      cluster: memory.semantic_cluster,
      relationships: memory.relationships
    } : null

  // CopilotKit action for memory enhancement
  useCopilotAction({
    name: "enhanceMemory",
    description: "Enhance and improve memory content with AI suggestions",
    parameters: [
      {
        name: "content",
        type: "string",
        description: "The memory content to enhance"
      },
      {
        name: "context",
        type: "string", 
        description: "Additional context about the memory"
      }
    ],
    handler: async ({ content, context }) => {
      await generateAISuggestions(content, context);
    }

  // CopilotKit action for memory categorization
  useCopilotAction({
    name: "categorizeMemory",
    description: "Suggest the best category and cluster for a memory",
    parameters: [
      {
        name: "content",
        type: "string",
        description: "The memory content to categorize"
      }
    ],
    handler: async ({ content }) => {
      const suggestions = await getCategorySuggestions(content);
      if (suggestions.type) {
        setEditedType(suggestions.type);
      }
      if (suggestions.cluster) {
        setEditedCluster(suggestions.cluster);
      }
    }

  // Generate AI suggestions for memory enhancement
  const generateAISuggestions = useCallback(async (content?: string, context?: string) => {
    try {
      setIsLoadingSuggestions(true);
      setError(null);
      const response = await fetch('/api/memory/ai-suggestions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: content || editedContent,
          context: context || '',
          memory_id: memory?.id,
          user_id: userId,
          tenant_id: tenantId,
          current_type: editedType,
          current_cluster: editedCluster
        })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setAiSuggestions(data.suggestions || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate AI suggestions');
    } finally {
      setIsLoadingSuggestions(false);
    }
  }, [editedContent, memory?.id, userId, tenantId, editedType, editedCluster]);
  // Get category suggestions from AI
  const getCategorySuggestions = useCallback(async (content: string) => {
    try {
      const response = await fetch('/api/memory/categorize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content,
          user_id: userId,
          tenant_id: tenantId
        })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return {
        type: data.suggested_type,
        cluster: data.suggested_cluster,
        confidence: data.confidence
      };
    } catch (err) {
      return {};
    }
  }, [userId, tenantId]);
  // Apply AI suggestion
  const applySuggestion = useCallback((suggestion: AISuggestion) => {
    switch (suggestion.type) {
      case 'enhancement':
        setEditedContent(suggestion.content);
        break;
      case 'categorization':
        // Parse categorization suggestion
        const lines = suggestion.content.split('\n');
        lines.forEach(line => {
          if (line.startsWith('Type:')) {
            const type = line.split(':')[1].trim().toLowerCase();
            if (['fact', 'preference', 'context'].includes(type)) {
              setEditedType(type as 'fact' | 'preference' | 'context');
            }
          } else if (line.startsWith('Cluster:')) {
            const cluster = line.split(':')[1].trim().toLowerCase();
            setEditedCluster(cluster);
          }

        break;
      case 'correction':
        setEditedContent(suggestion.content);
        break;
    }
  }, []);
  // Handle save
  const handleSave = useCallback(async () => {
    try {
      setIsSaving(true);
      setError(null);
      const updatedMemory: Partial<MemoryGridRow> = {
        content: editedContent,
        type: editedType,
        confidence: editedConfidence,
        semantic_cluster: editedCluster,
        last_accessed: new Date().toISOString()
      };
      await onSave(updatedMemory);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save memory');
    } finally {
      setIsSaving(false);
    }
  }, [editedContent, editedType, editedConfidence, editedCluster, onSave]);
  // Handle delete
  const handleDelete = useCallback(async () => {
    if (!memory || !onDelete) return;
    if (window.confirm('Are you sure you want to delete this memory? This action cannot be undone.')) {
      try {
        await onDelete(memory.id);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to delete memory');
      }
    }
  }, [memory, onDelete]);
  if (!isOpen) return null;
  return (
    <div className="memory-editor-overlay" style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }}>
      <div className="memory-editor-modal" style={{
        backgroundColor: 'white',
        borderRadius: '8px',
        padding: '24px',
        maxWidth: '800px',
        width: '90%',
        maxHeight: '90%',
        overflow: 'auto',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.15)'
      }} role="dialog">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h2 style={{ margin: 0, color: '#333' }}>
            {memory ? 'Edit Memory' : 'Create New Memory'}
          </h2>
          <button
            onClick={onCancel}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '24px',
              cursor: 'pointer',
              color: '#666'
            }}
           aria-label="Button">
            ×
          </button>
        </div>
        {error && (
          <div style={{
            padding: '12px',
            backgroundColor: '#ffebee',
            color: '#c62828',
            borderRadius: '4px',
            marginBottom: '16px',
            border: '1px solid #ffcdd2'
          }}>
            {error}
          </div>
        )}
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
          {/* Main editing area */}
          <div>
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
              </label>
              <CopilotTextarea
                className="memory-content-textarea"
                value={editedContent}
                onChange={(e) => setEditedContent(e.target.value)}
                placeholder="Enter memory content... (AI suggestions will appear as you type)"
                autosuggestionsConfig={{
                  textareaPurpose: "Memory content editing with AI enhancement",
                  chatApiConfigs: {
                    suggestionsApiConfig: {
                      maxTokens: 250,
                      stop: [".", "\n"],
                    },
                  },
                }}
                style={{
                  width: '100%',
                  minHeight: '120px',
                  padding: '12px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  fontSize: '14px',
                  fontFamily: 'inherit',
                  resize: 'vertical'
                }}
              />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px', marginBottom: '16px' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
                </label>
                <select
                  value={editedType}
                  onChange={(e) => setEditedType(e.target.value as 'fact' | 'preference' | 'context')}
                  style={{
                    width: '100%',
                    padding: '8px',
                    border: '1px solid #ddd',
                    borderRadius: '4px'
                  }}
                >
                  <option value="fact">Fact</option>
                  <option value="preference">Preference</option>
                  <option value="context">Context</option>
                </select>
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
                  Confidence ({Math.round(editedConfidence * 100)}%)
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={editedConfidence}
                  onChange={(e) => setEditedConfidence(parseFloat(e.target.value))}
                  style={{ width: '100%' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
                </label>
                <select
                  value={editedCluster}
                  onChange={(e) => setEditedCluster(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px',
                    border: '1px solid #ddd',
                    borderRadius: '4px'
                  }}
                >
                  <option value="technical">Technical</option>
                  <option value="personal">Personal</option>
                  <option value="work">Work</option>
                  <option value="general">General</option>
                </select>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
              <button
                onClick={() => generateAISuggestions()}
                disabled={isLoadingSuggestions || !editedContent.trim()}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#2196F3',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: isLoadingSuggestions ? 'not-allowed' : 'pointer',
                  opacity: isLoadingSuggestions || !editedContent.trim() ? 0.6 : 1
                }}
              >
                {isLoadingSuggestions ? 'Generating...' : 'Get AI Suggestions'}
              </button>
              <button
                onClick={() => getCategorySuggestions(editedContent)}
                disabled={!editedContent.trim()}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#FF9800',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: !editedContent.trim() ? 'not-allowed' : 'pointer',
                  opacity: !editedContent.trim() ? 0.6 : 1
                }}
              >
                Auto-Categorize
              </button>
            </div>
          </div>
          {/* AI Suggestions panel */}
          <div>
            <h3 style={{ marginTop: 0, marginBottom: '16px' }}>AI Suggestions</h3>
            {isLoadingSuggestions ? (
              <div style={{ textAlign: 'center', padding: '20px', color: '#666' }}>
                Generating AI suggestions...
              </div>
            ) : aiSuggestions.length > 0 ? (
              <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                {aiSuggestions.map((suggestion, index) => (
                  <div
                    key={index}
                    style={{
                      padding: '12px',
                      border: '1px solid #ddd',
                      borderRadius: '4px',
                      marginBottom: '8px',
                      backgroundColor: '#f9f9f9'
                    }}
                  >
                    <div style={{ 
                      display: 'flex', 
                      justifyContent: 'space-between', 
                      alignItems: 'center',
                      marginBottom: '8px'
                    }}>
                      <span style={{
                        fontSize: '12px',
                        fontWeight: 'bold',
                        color: '#666',
                        textTransform: 'uppercase'
                      }}>
                        {suggestion.type}
                      </span>
                      <span style={{
                        fontSize: '12px',
                        color: '#666'
                      }}>
                        {Math.round(suggestion.confidence * 100)}% confidence
                      </span>
                    </div>
                    <div style={{ fontSize: '14px', marginBottom: '8px' }}>
                      {suggestion.content}
                    </div>
                    <div style={{ fontSize: '12px', color: '#666', marginBottom: '8px' }}>
                      {suggestion.reasoning}
                    </div>
                    <button
                      onClick={() => applySuggestion(suggestion)}
                      style={{
                        padding: '4px 8px',
                        backgroundColor: '#4CAF50',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        fontSize: '12px',
                        cursor: 'pointer'
                      }}
                    >
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '20px', color: '#666' }}>
                Click "Get AI Suggestions" to see enhancement recommendations
              </div>
            )}
          </div>
        </div>
        {/* Action buttons */}
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          marginTop: '24px',
          paddingTop: '16px',
          borderTop: '1px solid #eee'
        }}>
          <div>
            {memory && onDelete && (
              <button
                onClick={handleDelete}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#f44336',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
               aria-label="Button">
              </button>
            )}
          </div>
          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              onClick={onCancel}
              style={{
                padding: '8px 16px',
                backgroundColor: '#666',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
             aria-label="Button">
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving || !editedContent.trim()}
              style={{
                padding: '8px 16px',
                backgroundColor: '#4CAF50',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: isSaving || !editedContent.trim() ? 'not-allowed' : 'pointer',
                opacity: isSaving || !editedContent.trim() ? 0.6 : 1
              }}
             aria-label="Button">
              {isSaving ? 'Saving...' : 'Save Memory'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
export default MemoryEditor;
