import React, { useState } from 'react';
import { CopilotArtifactSummary, SecurityContext } from '../types/backend';
import { useCopilotDismissArtifact } from '../hooks/useCopilot';

/**
 * ArtifactSystem component
 * Provides UI for backend-generated artifacts
 */
interface ArtifactSystemProps {
  artifacts: CopilotArtifactSummary[];
  _onOpenArtifact: (artifact: CopilotArtifactSummary) => void;
  _onDismissArtifact: (artifactId: string) => void;
  securityContext: SecurityContext;
  className?: string;
}

export function ArtifactSystem({
  artifacts,
  _onOpenArtifact,
  _onDismissArtifact,
  securityContext,
  className = ''
}: ArtifactSystemProps) {
  const [selectedArtifact, setSelectedArtifact] = useState<CopilotArtifactSummary | null>(null);
  const [artifactContent, setArtifactContent] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [filterType, setFilterType] = useState<string>('all');
  const [filterRisk, setFilterRisk] = useState<string>('all');
  
  const dismissArtifactHook = useCopilotDismissArtifact();

  // Filter artifacts based on security context and filters
  const filteredArtifacts = artifacts.filter(artifact => {
    // Filter out artifacts that require higher privileges than user has
    if (artifact.riskLevel === 'evil-mode-only' && securityContext.securityMode !== 'evil') {
      return false;
    }
    
    if (artifact.riskLevel === 'privileged' && !securityContext.canAccessSensitive) {
      return false;
    }
    
    // Apply type filter
    if (filterType !== 'all' && artifact.type !== filterType) {
      return false;
    }
    
    // Apply risk filter
    if (filterRisk !== 'all' && artifact.riskLevel !== filterRisk) {
      return false;
    }
    
    return true;
  });

  // Handle opening an artifact
  const handleOpenArtifact = async (artifact: CopilotArtifactSummary) => {
    setIsLoading(true);
    setSelectedArtifact(artifact);
    
    try {
      // In a real implementation, this would fetch the artifact content
      // For now, we'll simulate it with a timeout
      setTimeout(() => {
        setArtifactContent(`Content for artifact "${artifact.title}" (Version ${artifact.version || 1})\n\nThis is a simulated content preview. In a real implementation, this would be the actual content of the artifact.`);
        setIsLoading(false);
      }, 1000);
    } catch (error) {
      console.error('Error opening artifact:', error);
      setArtifactContent(`Error loading artifact: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setIsLoading(false);
    }
  };

  // Handle dismissing an artifact
  const handleDismissArtifact = (artifactId: string) => {
    dismissArtifactHook(artifactId);
    if (selectedArtifact && selectedArtifact.id === artifactId) {
      setSelectedArtifact(null);
      setArtifactContent(null);
    }
  };

  // Group artifacts by type
  const artifactsByType = filteredArtifacts.reduce((groups, artifact) => {
    if (!groups[artifact.type]) {
      groups[artifact.type] = [];
    }
    groups[artifact.type].push(artifact);
    return groups;
  }, {} as Record<string, CopilotArtifactSummary[]>);

  // Get unique artifact types for filter
  const artifactTypes = Array.from(new Set(artifacts.map(a => a.type)));

  return (
    <div className={`artifact-system ${className}`}>
      <div className="artifact-system__header">
        <h2 className="artifact-system__title">Artifact System</h2>
        <p className="artifact-system__description">
          View and manage artifacts generated during your conversations
        </p>
      </div>

      {/* Filters and View Options */}
      <div className="artifact-system__controls">
        <div className="artifact-system__filters">
          <div className="artifact-system__filter-group">
            <label className="artifact-system__filter-label">Type:</label>
            <select
              className="artifact-system__filter-select"
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
            >
              <option value="all">All Types</option>
              {artifactTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>
          
          <div className="artifact-system__filter-group">
            <label className="artifact-system__filter-label">Risk Level:</label>
            <select
              className="artifact-system__filter-select"
              value={filterRisk}
              onChange={(e) => setFilterRisk(e.target.value)}
            >
              <option value="all">All Levels</option>
              <option value="safe">Safe</option>
              <option value="privileged">Privileged</option>
              {securityContext.securityMode === 'evil' && (
                <option value="evil-mode-only">Evil Mode Only</option>
              )}
            </select>
          </div>
        </div>
        
        <div className="artifact-system__view-options">
          <button
            className={`artifact-system__view-button ${viewMode === 'grid' ? 'active' : ''}`}
            onClick={() => setViewMode('grid')}
            title="Grid View"
          >
            ⊞
          </button>
          <button
            className={`artifact-system__view-button ${viewMode === 'list' ? 'active' : ''}`}
            onClick={() => setViewMode('list')}
            title="List View"
          >
            ☰
          </button>
        </div>
      </div>

      {/* Artifact Content Preview */}
      {selectedArtifact && (
        <div className="artifact-system__preview">
          <div className="artifact-system__preview-header">
            <h3 className="artifact-system__preview-title">{selectedArtifact.title}</h3>
            <div className="artifact-system__preview-meta">
              <span className={`artifact-system__preview-type artifact-system__preview-type--${selectedArtifact.type}`}>
                {selectedArtifact.type}
              </span>
              <span className={`artifact-system__preview-risk artifact-system__preview-risk--${selectedArtifact.riskLevel}`}>
                {selectedArtifact.riskLevel}
              </span>
              {selectedArtifact.version && (
                <span className="artifact-system__preview-version">
                  v{selectedArtifact.version}
                </span>
              )}
              <span className="artifact-system__preview-plugin">
                {selectedArtifact.pluginId}
              </span>
            </div>
            <button
              className="artifact-system__preview-close"
              onClick={() => {
                setSelectedArtifact(null);
                setArtifactContent(null);
              }}
            >
              ✕
            </button>
          </div>
          
          <div className="artifact-system__preview-content">
            {isLoading ? (
              <div className="artifact-system__preview-loading">
                Loading artifact content...
              </div>
            ) : (
              <div className="artifact-system__preview-text">
                {artifactContent}
              </div>
            )}
          </div>
          
          <div className="artifact-system__preview-actions">
            <button
              className="artifact-system__preview-download"
              onClick={() => {
                // In a real implementation, this would download the artifact
                alert('Download functionality would be implemented here');
              }}
            >
              Download
            </button>
            <button
              className="artifact-system__preview-share"
              onClick={() => {
                // In a real implementation, this would share the artifact
                alert('Share functionality would be implemented here');
              }}
            >
              Share
            </button>
          </div>
        </div>
      )}

      {/* Artifact Grid/List */}
      {filteredArtifacts.length === 0 ? (
        <div className="artifact-system__empty">
          <p className="artifact-system__empty-message">
            No artifacts found matching your filters.
          </p>
        </div>
      ) : viewMode === 'grid' ? (
        <div className="artifact-system__grid">
          {filteredArtifacts.map(artifact => (
            <ArtifactCard
              key={artifact.id}
              artifact={artifact}
              isSelected={selectedArtifact?.id === artifact.id}
              onSelect={() => setSelectedArtifact(artifact)}
              onOpen={() => handleOpenArtifact(artifact)}
              onDismiss={() => handleDismissArtifact(artifact.id)}
            />
          ))}
        </div>
      ) : (
        <div className="artifact-system__list">
          {filteredArtifacts.map(artifact => (
            <ArtifactListItem
              key={artifact.id}
              artifact={artifact}
              isSelected={selectedArtifact?.id === artifact.id}
              onSelect={() => setSelectedArtifact(artifact)}
              onOpen={() => handleOpenArtifact(artifact)}
              onDismiss={() => handleDismissArtifact(artifact.id)}
            />
          ))}
        </div>
      )}

      {/* Artifact Categories */}
      <div className="artifact-system__categories">
        <h3 className="artifact-system__categories-title">Artifact Categories</h3>
        
        {Object.entries(artifactsByType).map(([type, typeArtifacts]) => (
          <div key={type} className="artifact-system__category">
            <h4 className="artifact-system__category-title">{type}</h4>
            <div className="artifact-system__category-description">
              {type === 'code' && 'Code artifacts include snippets, functions, and full programs'}
              {type === 'documentation' && 'Documentation artifacts include guides, references, and explanations'}
              {type === 'analysis' && 'Analysis artifacts include reports, insights, and summaries'}
              {type === 'test' && 'Test artifacts include unit tests, integration tests, and test cases'}
            </div>
            
            <div className="artifact-system__category-artifacts">
              {typeArtifacts.map(artifact => (
                <div key={artifact.id} className="artifact-system__category-artifact">
                  <div className="artifact-system__category-artifact-header">
                    <h5 className="artifact-system__category-artifact-title">
                      {artifact.title}
                    </h5>
                    <span className={`artifact-system__category-artifact-risk artifact-system__category-artifact-risk--${artifact.riskLevel}`}>
                      {artifact.riskLevel}
                    </span>
                  </div>
                  
                  <p className="artifact-system__category-artifact-description">
                    {artifact.description}
                  </p>
                  
                  <div className="artifact-system__category-artifact-footer">
                    <span className="artifact-system__category-artifact-plugin">
                      {artifact.pluginId}
                    </span>
                    <button
                      className="artifact-system__category-artifact-open"
                      onClick={() => handleOpenArtifact(artifact)}
                    >
                      Open
                    </button>
                    <button
                      className="artifact-system__category-artifact-dismiss"
                      onClick={() => handleDismissArtifact(artifact.id)}
                    >
                      Dismiss
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * ArtifactCard component
 * Represents a single artifact in grid view
 */
interface ArtifactCardProps {
  artifact: CopilotArtifactSummary;
  isSelected: boolean;
  onSelect: () => void;
  onOpen: () => void;
  onDismiss: () => void;
}

function ArtifactCard({ 
  artifact, 
  isSelected, 
  onSelect, 
  onOpen, 
  onDismiss 
}: ArtifactCardProps) {
  return (
    <div 
      className={`artifact-card ${isSelected ? 'artifact-card--selected' : ''} artifact-card--${artifact.type}`}
      onClick={onSelect}
    >
      <div className="artifact-card__header">
        <h4 className="artifact-card__title">{artifact.title}</h4>
        <span className={`artifact-card__risk artifact-card__risk--${artifact.riskLevel}`}>
          {artifact.riskLevel}
        </span>
      </div>
      
      <p className="artifact-card__description">
        {artifact.description}
      </p>
      
      <div className="artifact-card__details">
        <span className={`artifact-card__type artifact-card__type--${artifact.type}`}>
          {artifact.type}
        </span>
        <span className="artifact-card__plugin">
          {artifact.pluginId}
        </span>
        {artifact.version && (
          <span className="artifact-card__version">
            v{artifact.version}
          </span>
        )}
      </div>
      
      {artifact.preview && (
        <div className="artifact-card__preview">
          {artifact.preview}
        </div>
      )}
      
      <div className="artifact-card__actions">
        <button
          className="artifact-card__open-button"
          onClick={(e) => {
            e.stopPropagation();
            onOpen();
          }}
        >
          Open
        </button>
        <button
          className="artifact-card__dismiss-button"
          onClick={(e) => {
            e.stopPropagation();
            onDismiss();
          }}
        >
          Dismiss
        </button>
      </div>
    </div>
  );
}

/**
 * ArtifactListItem component
 * Represents a single artifact in list view
 */
interface ArtifactListItemProps {
  artifact: CopilotArtifactSummary;
  isSelected: boolean;
  onSelect: () => void;
  onOpen: () => void;
  onDismiss: () => void;
}

function ArtifactListItem({ 
  artifact, 
  isSelected, 
  onSelect, 
  onOpen, 
  onDismiss 
}: ArtifactListItemProps) {
  return (
    <div 
      className={`artifact-list-item ${isSelected ? 'artifact-list-item--selected' : ''}`}
      onClick={onSelect}
    >
      <div className="artifact-list-item__main">
        <div className="artifact-list-item__header">
          <h4 className="artifact-list-item__title">{artifact.title}</h4>
          <span className={`artifact-list-item__risk artifact-list-item__risk--${artifact.riskLevel}`}>
            {artifact.riskLevel}
          </span>
        </div>
        
        <p className="artifact-list-item__description">
          {artifact.description}
        </p>
      </div>
      
      <div className="artifact-list-item__meta">
        <span className={`artifact-list-item__type artifact-list-item__type--${artifact.type}`}>
          {artifact.type}
        </span>
        <span className="artifact-list-item__plugin">
          {artifact.pluginId}
        </span>
        {artifact.version && (
          <span className="artifact-list-item__version">
            v{artifact.version}
          </span>
        )}
      </div>
      
      <div className="artifact-list-item__actions">
        <button
          className="artifact-list-item__open-button"
          onClick={(e) => {
            e.stopPropagation();
            onOpen();
          }}
        >
          Open
        </button>
        <button
          className="artifact-list-item__dismiss-button"
          onClick={(e) => {
            e.stopPropagation();
            onDismiss();
          }}
        >
          Dismiss
        </button>
      </div>
    </div>
  );
}