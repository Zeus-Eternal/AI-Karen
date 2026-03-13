import React, { useState, useEffect } from 'react';
import { Agent, AgentFilter, AgentStatus, AgentType, Theme, AgentCustomizationOptions } from './types';
import { useTheme } from '../chat/ThemeProvider';
import AgentService from '../../services/AgentService';

interface AgentSelectionComponentProps {
  className?: string;
  theme?: Partial<Theme>;
  onAgentSelect?: (agent: Agent) => void;
  onAgentCustomize?: (agentId: string, options: AgentCustomizationOptions) => void;
  showCustomization?: boolean;
  multiSelect?: boolean;
  selectedAgentIds?: string[];
}

export const AgentSelectionComponent: React.FC<AgentSelectionComponentProps> = ({
  className = '',
  theme: customTheme,
  onAgentSelect,
  onAgentCustomize,
  showCustomization = true,
  multiSelect = false,
  selectedAgentIds = []
}) => {
  const { theme } = useTheme();
  const agentService = AgentService.getInstance();
  
  // State
  const [agents, setAgents] = useState<Agent[]>([]);
  const [filteredAgents, setFilteredAgents] = useState<Agent[]>([]);
  const [selectedAgents, setSelectedAgents] = useState<Agent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<AgentStatus[]>([]);
  const [typeFilter, setTypeFilter] = useState<AgentType[]>([]);
  const [showCustomizationModal, setShowCustomizationModal] = useState(false);
  const [agentToCustomize, setAgentToCustomize] = useState<Agent | null>(null);

  // Load agents
  useEffect(() => {
    const loadAgents = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        const agentData = await agentService.getAgents();
        setAgents(agentData);
        setFilteredAgents(agentData);
      } catch (err) {
        console.error('Failed to load agents:', err);
        setError('Failed to load agents');
      } finally {
        setIsLoading(false);
      }
    };
    
    loadAgents();
  }, []);

  // Apply filters
  useEffect(() => {
    let result = [...agents];
    
    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(agent => 
        agent.name.toLowerCase().includes(query) ||
        agent.persona.description.toLowerCase().includes(query) ||
        agent.persona.expertise.some(expertise => 
          expertise.toLowerCase().includes(query)
        )
      );
    }
    
    // Apply status filter
    if (statusFilter.length > 0) {
      result = result.filter(agent => statusFilter.includes(agent.status));
    }
    
    // Apply type filter
    if (typeFilter.length > 0) {
      result = result.filter(agent => typeFilter.includes(agent.type));
    }
    
    setFilteredAgents(result);
  }, [agents, searchQuery, statusFilter, typeFilter]);

  // Handle agent selection
  const handleAgentSelect = (agent: Agent) => {
    if (multiSelect) {
      const isSelected = selectedAgents.some(a => a.id === agent.id);
      if (isSelected) {
        setSelectedAgents(selectedAgents.filter(a => a.id !== agent.id));
      } else {
        setSelectedAgents([...selectedAgents, agent]);
      }
    } else {
      setSelectedAgents([agent]);
      if (onAgentSelect) {
        onAgentSelect(agent);
      }
    }
  };

  // Handle agent customization
  const handleCustomizeAgent = (agent: Agent) => {
    setAgentToCustomize(agent);
    setShowCustomizationModal(true);
  };

  // Handle customization save
  const handleSaveCustomization = async (options: AgentCustomizationOptions) => {
    if (!agentToCustomize) return;
    
    try {
      // Update agent persona
      if (options.persona) {
        await agentService.updateAgentPersona(agentToCustomize.id, options.persona);
      }
      
      // Update agent capabilities
      if (options.capabilities) {
        const capabilityUpdates = Object.entries(options.capabilities)
          .filter(([_, enabled]) => enabled !== undefined)
          .map(([capability, enabled]) => ({
            capability: capability as any,
            enabled: enabled as boolean
          }));
        
        if (capabilityUpdates.length > 0) {
          await agentService.updateAgentCapabilities(agentToCustomize.id, capabilityUpdates);
        }
      }
      
      // Refresh agents
      const updatedAgents = await agentService.getAgents();
      setAgents(updatedAgents);
      
      if (onAgentCustomize) {
        onAgentCustomize(agentToCustomize.id, options);
      }
      
      setShowCustomizationModal(false);
      setAgentToCustomize(null);
    } catch (err) {
      console.error('Failed to customize agent:', err);
      setError('Failed to customize agent');
    }
  };

  // Toggle status filter
  const toggleStatusFilter = (status: AgentStatus) => {
    if (statusFilter.includes(status)) {
      setStatusFilter(statusFilter.filter(s => s !== status));
    } else {
      setStatusFilter([...statusFilter, status]);
    }
  };

  // Toggle type filter
  const toggleTypeFilter = (type: AgentType) => {
    if (typeFilter.includes(type)) {
      setTypeFilter(typeFilter.filter(t => t !== type));
    } else {
      setTypeFilter([...typeFilter, type]);
    }
  };

  // Clear all filters
  const clearFilters = () => {
    setSearchQuery('');
    setStatusFilter([]);
    setTypeFilter([]);
  };

  // Get status color
  const getStatusColor = (status: AgentStatus): string => {
    switch (status) {
      case AgentStatus.AVAILABLE:
        return theme.colors.success;
      case AgentStatus.BUSY:
        return theme.colors.warning;
      case AgentStatus.OFFLINE:
        return theme.colors.textSecondary;
      case AgentStatus.MAINTENANCE:
        return theme.colors.error;
      default:
        return theme.colors.textSecondary;
    }
  };

  // Get status text
  const getStatusText = (status: AgentStatus): string => {
    switch (status) {
      case AgentStatus.AVAILABLE:
        return 'Available';
      case AgentStatus.BUSY:
        return 'Busy';
      case AgentStatus.OFFLINE:
        return 'Offline';
      case AgentStatus.MAINTENANCE:
        return 'Maintenance';
      default:
        return 'Unknown';
    }
  };

  // Get type text
  const getTypeText = (type: AgentType): string => {
    switch (type) {
      case AgentType.GENERAL:
        return 'General';
      case AgentType.SPECIALIST:
        return 'Specialist';
      case AgentType.CREATIVE:
        return 'Creative';
      case AgentType.ANALYTICAL:
        return 'Analytical';
      case AgentType.RESEARCH:
        return 'Research';
      default:
        return 'Unknown';
    }
  };

  // Container style
  const containerStyle: React.CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    width: '100%',
    backgroundColor: theme.colors.background,
    color: theme.colors.text,
    fontFamily: theme.typography.fontFamily,
    borderRadius: theme.borderRadius,
    overflow: 'hidden'
  };

  // Header style
  const headerStyle: React.CSSProperties = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: `${theme.spacing.md} ${theme.spacing.lg}`,
    borderBottom: `1px solid ${theme.colors.border}`,
    backgroundColor: theme.colors.surface
  };

  // Title style
  const titleStyle: React.CSSProperties = {
    margin: 0,
    fontSize: theme.typography.fontSize.xl,
    fontWeight: theme.typography.fontWeight.semibold,
    color: theme.colors.text
  };

  // Content style
  const contentStyle: React.CSSProperties = {
    flex: 1,
    overflowY: 'auto',
    padding: theme.spacing.lg
  };

  // Search container style
  const searchContainerStyle: React.CSSProperties = {
    marginBottom: theme.spacing.lg
  };

  // Search input style
  const searchInputStyle: React.CSSProperties = {
    width: '100%',
    padding: theme.spacing.md,
    border: `1px solid ${theme.colors.border}`,
    borderRadius: theme.borderRadius,
    backgroundColor: theme.colors.surface,
    color: theme.colors.text,
    fontFamily: theme.typography.fontFamily,
    fontSize: theme.typography.fontSize.base
  };

  // Filters container style
  const filtersContainerStyle: React.CSSProperties = {
    display: 'flex',
    flexWrap: 'wrap',
    gap: theme.spacing.sm,
    marginBottom: theme.spacing.lg
  };

  // Filter button style
  const filterButtonStyle = (isActive: boolean): React.CSSProperties => ({
    padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
    borderRadius: theme.borderRadius,
    border: `1px solid ${isActive ? theme.colors.primary : theme.colors.border}`,
    backgroundColor: isActive ? theme.colors.primary + '20' : theme.colors.surface,
    color: isActive ? theme.colors.primary : theme.colors.text,
    cursor: 'pointer',
    fontSize: theme.typography.fontSize.sm,
    transition: 'all 0.2s ease'
  });

  // Agent card style
  const agentCardStyle = (agent: Agent): React.CSSProperties => {
    const isSelected = selectedAgents.some(a => a.id === agent.id);
    return {
      display: 'flex',
      flexDirection: 'column',
      padding: theme.spacing.lg,
      marginBottom: theme.spacing.md,
      border: `1px solid ${isSelected ? theme.colors.primary : theme.colors.border}`,
      borderRadius: theme.borderRadius,
      backgroundColor: isSelected ? theme.colors.primary + '10' : theme.colors.surface,
      cursor: 'pointer',
      transition: 'all 0.2s ease',
      position: 'relative'
    };
  };

  // Agent header style
  const agentHeaderStyle: React.CSSProperties = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: theme.spacing.md
  };

  // Agent name style
  const agentNameStyle: React.CSSProperties = {
    margin: 0,
    fontSize: theme.typography.fontSize.lg,
    fontWeight: theme.typography.fontWeight.semibold,
    color: theme.colors.text
  };

  // Agent status style
  const agentStatusStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: theme.spacing.xs
  };

  // Status indicator style
  const statusIndicatorStyle = (color: string): React.CSSProperties => ({
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    backgroundColor: color
  });

  // Agent description style
  const agentDescriptionStyle: React.CSSProperties = {
    margin: `0 0 ${theme.spacing.md} 0`,
    fontSize: theme.typography.fontSize.base,
    color: theme.colors.textSecondary
  };

  // Agent capabilities style
  const agentCapabilitiesStyle: React.CSSProperties = {
    display: 'flex',
    flexWrap: 'wrap',
    gap: theme.spacing.xs,
    marginBottom: theme.spacing.md
  };

  // Capability tag style
  const capabilityTagStyle: React.CSSProperties = {
    padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
    borderRadius: theme.borderRadius,
    backgroundColor: theme.colors.surface,
    border: `1px solid ${theme.colors.border}`,
    fontSize: theme.typography.fontSize.xs,
    color: theme.colors.textSecondary
  };

  // Agent actions style
  const agentActionsStyle: React.CSSProperties = {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: theme.spacing.sm
  };

  // Button style
  const buttonStyle: React.CSSProperties = {
    padding: `${theme.spacing.sm} ${theme.spacing.md}`,
    borderRadius: theme.borderRadius,
    border: 'none',
    cursor: 'pointer',
    fontFamily: theme.typography.fontFamily,
    fontSize: theme.typography.fontSize.sm,
    fontWeight: theme.typography.fontWeight.medium,
    transition: 'all 0.2s ease'
  };

  // Primary button style
  const primaryButtonStyle: React.CSSProperties = {
    ...buttonStyle,
    backgroundColor: theme.colors.primary,
    color: 'white'
  };

  // Secondary button style
  const secondaryButtonStyle: React.CSSProperties = {
    ...buttonStyle,
    backgroundColor: 'transparent',
    color: theme.colors.primary,
    border: `1px solid ${theme.colors.primary}`
  };

  // Empty state style
  const emptyStateStyle: React.CSSProperties = {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    color: theme.colors.textSecondary,
    textAlign: 'center',
    padding: theme.spacing.xl
  };

  // Loading spinner style
  const loadingSpinnerStyle: React.CSSProperties = {
    width: '40px',
    height: '40px',
    border: `3px solid ${theme.colors.border}`,
    borderTop: `3px solid ${theme.colors.primary}`,
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
    marginBottom: theme.spacing.md
  };

  return (
    <div className={`copilot-agent-selection ${className}`} style={containerStyle}>
      {/* Header */}
      <header className="copilot-header" style={headerStyle}>
        <h1 style={titleStyle}>Agent Selection</h1>
        <div style={{ display: 'flex', gap: theme.spacing.sm }}>
          {(statusFilter.length > 0 || typeFilter.length > 0 || searchQuery) && (
            <button
              onClick={clearFilters}
              style={secondaryButtonStyle}
            >
              Clear Filters
            </button>
          )}
        </div>
      </header>

      {/* Content */}
      <main className="copilot-content" style={contentStyle}>
        {/* Search */}
        <div className="copilot-search-container" style={searchContainerStyle}>
          <input
            type="text"
            placeholder="Search agents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={searchInputStyle}
            aria-label="Search agents"
          />
        </div>

        {/* Filters */}
        <div className="copilot-filters-container" style={filtersContainerStyle}>
          <div style={{ fontWeight: theme.typography.fontWeight.medium, marginRight: theme.spacing.sm }}>
            Status:
          </div>
          {Object.values(AgentStatus).map(status => (
            <button
              key={status}
              onClick={() => toggleStatusFilter(status)}
              style={filterButtonStyle(statusFilter.includes(status))}
              aria-pressed={statusFilter.includes(status)}
            >
              {getStatusText(status)}
            </button>
          ))}
          
          <div style={{ fontWeight: theme.typography.fontWeight.medium, marginRight: theme.spacing.sm, marginLeft: theme.spacing.lg }}>
            Type:
          </div>
          {Object.values(AgentType).map(type => (
            <button
              key={type}
              onClick={() => toggleTypeFilter(type)}
              style={filterButtonStyle(typeFilter.includes(type))}
              aria-pressed={typeFilter.includes(type)}
            >
              {getTypeText(type)}
            </button>
          ))}
        </div>

        {/* Agent List */}
        {isLoading ? (
          <div style={emptyStateStyle}>
            <div style={loadingSpinnerStyle} />
            <p>Loading agents...</p>
          </div>
        ) : error ? (
          <div style={emptyStateStyle}>
            <div style={{ fontSize: '3rem', marginBottom: theme.spacing.md }} aria-hidden="true">⚠️</div>
            <h2 style={{ margin: `0 0 ${theme.spacing.md} 0` }}>Error</h2>
            <p>{error}</p>
          </div>
        ) : filteredAgents.length === 0 ? (
          <div style={emptyStateStyle}>
            <div style={{ fontSize: '3rem', marginBottom: theme.spacing.md }} aria-hidden="true">🤖</div>
            <h2 style={{ margin: `0 0 ${theme.spacing.md} 0` }}>No agents found</h2>
            <p>Try adjusting your search or filters</p>
          </div>
        ) : (
          <div className="copilot-agent-list">
            {filteredAgents.map(agent => (
              <div 
                key={agent.id}
                className="copilot-agent-card"
                style={agentCardStyle(agent)}
                onClick={() => handleAgentSelect(agent)}
                role="button"
                tabIndex={0}
                aria-label={`Select agent ${agent.name}`}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    handleAgentSelect(agent);
                  }
                }}
              >
                {/* Agent Header */}
                <div className="copilot-agent-header" style={agentHeaderStyle}>
                  <h3 style={agentNameStyle}>{agent.name}</h3>
                  <div className="copilot-agent-status" style={agentStatusStyle}>
                    <div style={statusIndicatorStyle(getStatusColor(agent.status))} aria-hidden="true" />
                    <span>{getStatusText(agent.status)}</span>
                  </div>
                </div>

                {/* Agent Description */}
                <p className="copilot-agent-description" style={agentDescriptionStyle}>
                  {agent.persona.description}
                </p>

                {/* Agent Capabilities */}
                <div className="copilot-agent-capabilities" style={agentCapabilitiesStyle}>
                  {agent.capabilities
                    .filter(cap => cap.enabled)
                    .slice(0, 4) // Show only first 4 capabilities
                    .map(cap => (
                      <span key={cap.capability} style={capabilityTagStyle}>
                        {cap.name}
                      </span>
                    ))}
                  {agent.capabilities.filter(cap => cap.enabled).length > 4 && (
                    <span style={capabilityTagStyle}>
                      +{agent.capabilities.filter(cap => cap.enabled).length - 4} more
                    </span>
                  )}
                </div>

                {/* Agent Actions */}
                <div className="copilot-agent-actions" style={agentActionsStyle}>
                  {showCustomization && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleCustomizeAgent(agent);
                      }}
                      style={secondaryButtonStyle}
                      aria-label={`Customize ${agent.name}`}
                    >
                      Customize
                    </button>
                  )}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleAgentSelect(agent);
                    }}
                    style={primaryButtonStyle}
                    aria-label={`Select ${agent.name}`}
                  >
                    Select
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Customization Modal */}
      {showCustomizationModal && agentToCustomize && (
        <AgentCustomizationModal
          agent={agentToCustomize}
          theme={theme}
          onSave={handleSaveCustomization}
          onClose={() => {
            setShowCustomizationModal(false);
            setAgentToCustomize(null);
          }}
        />
      )}

      <style jsx>{`
        @keyframes spin {
          0% {
            transform: rotate(0deg);
          }
          100% {
            transform: rotate(360deg);
          }
        }
        
        /* Responsive styles */
        @media (max-width: 768px) {
          .copilot-agent-selection {
            height: 100vh;
            width: 100vw;
            border-radius: 0;
          }
          
          .copilot-header {
            padding: 12px 16px;
          }
          
          .copilot-content {
            padding: 16px;
          }
          
          .copilot-filters-container {
            flex-direction: column;
            align-items: flex-start;
          }
          
          .copilot-agent-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 8px;
          }
          
          .copilot-agent-actions {
            width: 100%;
            justify-content: space-between;
          }
        }
        
        @media (max-width: 480px) {
          .copilot-agent-card {
            padding: 16px;
          }
          
          .copilot-agent-capabilities {
            justify-content: center;
          }
        }
      `}</style>
    </div>
  );
};

// Agent Customization Modal Component
interface AgentCustomizationModalProps {
  agent: Agent;
  theme: Theme;
  onSave: (options: AgentCustomizationOptions) => void;
  onClose: () => void;
}

const AgentCustomizationModal: React.FC<AgentCustomizationModalProps> = ({
  agent,
  theme,
  onSave,
  onClose
}) => {
  const [persona, setPersona] = useState({
    name: agent.persona.name,
    description: agent.persona.description,
    personality: agent.persona.personality,
    communicationStyle: agent.persona.communicationStyle,
    expertise: agent.persona.expertise.join(', '),
    tone: agent.persona.tone
  });
  
  const [capabilities, setCapabilities] = useState<Record<string, boolean>>(
    agent.capabilities.reduce((acc, cap) => {
      acc[cap.capability] = cap.enabled;
      return acc;
    }, {} as Record<string, boolean>)
  );
  
  const [settings, setSettings] = useState({
    responseLength: 'normal' as 'concise' | 'normal' | 'detailed',
    creativityLevel: 3,
    formalityLevel: 3
  });

  const handleSave = () => {
    const options: AgentCustomizationOptions = {
      persona: {
        name: persona.name,
        description: persona.description,
        personality: persona.personality,
        communicationStyle: persona.communicationStyle,
        expertise: persona.expertise.split(',').map(e => e.trim()).filter(e => e),
        tone: persona.tone
      },
      capabilities,
      settings
    };
    
    onSave(options);
  };

  // Modal overlay style
  const modalOverlayStyle: React.CSSProperties = {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 20
  };

  // Modal content style
  const modalContentStyle: React.CSSProperties = {
    backgroundColor: theme.colors.surface,
    borderRadius: theme.borderRadius,
    boxShadow: theme.shadows.lg,
    maxWidth: '90vw',
    maxHeight: '90vh',
    overflow: 'auto',
    position: 'relative',
    width: '600px'
  };

  // Modal header style
  const modalHeaderStyle: React.CSSProperties = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: `${theme.spacing.md} ${theme.spacing.lg}`,
    borderBottom: `1px solid ${theme.colors.border}`
  };

  // Modal title style
  const modalTitleStyle: React.CSSProperties = {
    margin: 0,
    fontSize: theme.typography.fontSize.xl,
    fontWeight: theme.typography.fontWeight.semibold,
    color: theme.colors.text
  };

  // Modal body style
  const modalBodyStyle: React.CSSProperties = {
    padding: theme.spacing.lg
  };

  // Form group style
  const formGroupStyle: React.CSSProperties = {
    marginBottom: theme.spacing.lg
  };

  // Form label style
  const formLabelStyle: React.CSSProperties = {
    display: 'block',
    marginBottom: theme.spacing.sm,
    fontWeight: theme.typography.fontWeight.medium,
    color: theme.colors.text
  };

  // Form input style
  const formInputStyle: React.CSSProperties = {
    width: '100%',
    padding: theme.spacing.md,
    border: `1px solid ${theme.colors.border}`,
    borderRadius: theme.borderRadius,
    backgroundColor: theme.colors.background,
    color: theme.colors.text,
    fontFamily: theme.typography.fontFamily,
    fontSize: theme.typography.fontSize.base
  };

  // Form textarea style
  const formTextareaStyle: React.CSSProperties = {
    ...formInputStyle,
    minHeight: '100px',
    resize: 'vertical'
  };

  // Form select style
  const formSelectStyle: React.CSSProperties = {
    ...formInputStyle
  };

  // Checkbox container style
  const checkboxContainerStyle: React.CSSProperties = {
    display: 'flex',
    flexWrap: 'wrap',
    gap: theme.spacing.md,
    marginBottom: theme.spacing.md
  };

  // Checkbox label style
  const checkboxLabelStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: theme.spacing.sm,
    cursor: 'pointer'
  };

  // Range container style
  const rangeContainerStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: theme.spacing.md
  };

  // Range input style
  const rangeInputStyle: React.CSSProperties = {
    flex: 1
  };

  // Modal footer style
  const modalFooterStyle: React.CSSProperties = {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: theme.spacing.sm,
    padding: `${theme.spacing.md} ${theme.spacing.lg}`,
    borderTop: `1px solid ${theme.colors.border}`
  };

  // Button style
  const buttonStyle: React.CSSProperties = {
    padding: `${theme.spacing.sm} ${theme.spacing.md}`,
    borderRadius: theme.borderRadius,
    border: 'none',
    cursor: 'pointer',
    fontFamily: theme.typography.fontFamily,
    fontSize: theme.typography.fontSize.base,
    fontWeight: theme.typography.fontWeight.medium,
    transition: 'all 0.2s ease'
  };

  // Primary button style
  const primaryButtonStyle: React.CSSProperties = {
    ...buttonStyle,
    backgroundColor: theme.colors.primary,
    color: 'white'
  };

  // Secondary button style
  const secondaryButtonStyle: React.CSSProperties = {
    ...buttonStyle,
    backgroundColor: 'transparent',
    color: theme.colors.text,
    border: `1px solid ${theme.colors.border}`
  };

  // Close button style
  const closeButtonStyle: React.CSSProperties = {
    position: 'absolute',
    top: theme.spacing.md,
    right: theme.spacing.md,
    background: 'none',
    border: 'none',
    fontSize: theme.typography.fontSize.lg,
    cursor: 'pointer',
    color: theme.colors.textSecondary,
    padding: 0,
    width: '24px',
    height: '24px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center'
  };

  return (
    <div 
      style={modalOverlayStyle} 
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="customization-title"
    >
      <div 
        style={modalContentStyle} 
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          style={closeButtonStyle}
          aria-label="Close dialog"
        >
          ×
        </button>
        
        <div style={modalHeaderStyle}>
          <h2 id="customization-title" style={modalTitleStyle}>
            Customize {agent.name}
          </h2>
        </div>
        
        <div style={modalBodyStyle}>
          {/* Persona Section */}
          <div style={formGroupStyle}>
            <h3 style={{ margin: `0 0 ${theme.spacing.md} 0` }}>Persona</h3>
            
            <div style={formGroupStyle}>
              <label style={formLabelStyle} htmlFor="agent-name">
                Name
              </label>
              <input
                id="agent-name"
                type="text"
                value={persona.name}
                onChange={(e) => setPersona({...persona, name: e.target.value})}
                style={formInputStyle}
              />
            </div>
            
            <div style={formGroupStyle}>
              <label style={formLabelStyle} htmlFor="agent-description">
                Description
              </label>
              <textarea
                id="agent-description"
                value={persona.description}
                onChange={(e) => setPersona({...persona, description: e.target.value})}
                style={formTextareaStyle}
              />
            </div>
            
            <div style={formGroupStyle}>
              <label style={formLabelStyle} htmlFor="agent-personality">
                Personality
              </label>
              <textarea
                id="agent-personality"
                value={persona.personality}
                onChange={(e) => setPersona({...persona, personality: e.target.value})}
                style={formTextareaStyle}
              />
            </div>
            
            <div style={formGroupStyle}>
              <label style={formLabelStyle} htmlFor="agent-communication">
                Communication Style
              </label>
              <input
                id="agent-communication"
                type="text"
                value={persona.communicationStyle}
                onChange={(e) => setPersona({...persona, communicationStyle: e.target.value})}
                style={formInputStyle}
              />
            </div>
            
            <div style={formGroupStyle}>
              <label style={formLabelStyle} htmlFor="agent-expertise">
                Expertise (comma-separated)
              </label>
              <input
                id="agent-expertise"
                type="text"
                value={persona.expertise}
                onChange={(e) => setPersona({...persona, expertise: e.target.value})}
                style={formInputStyle}
              />
            </div>
            
            <div style={formGroupStyle}>
              <label style={formLabelStyle} htmlFor="agent-tone">
                Tone
              </label>
              <select
                id="agent-tone"
                value={persona.tone}
                onChange={(e) => setPersona({...persona, tone: e.target.value as any})}
                style={formSelectStyle}
              >
                <option value="formal">Formal</option>
                <option value="casual">Casual</option>
                <option value="friendly">Friendly</option>
                <option value="professional">Professional</option>
              </select>
            </div>
          </div>
          
          {/* Capabilities Section */}
          <div style={formGroupStyle}>
            <h3 style={{ margin: `0 0 ${theme.spacing.md} 0` }}>Capabilities</h3>
            <div style={checkboxContainerStyle}>
              {agent.capabilities.map(cap => (
                <label key={cap.capability} style={checkboxLabelStyle}>
                  <input
                    type="checkbox"
                    checked={capabilities[cap.capability] || false}
                    onChange={(e) => setCapabilities({
                      ...capabilities,
                      [cap.capability]: e.target.checked
                    })}
                  />
                  {cap.name}
                </label>
              ))}
            </div>
          </div>
          
          {/* Settings Section */}
          <div style={formGroupStyle}>
            <h3 style={{ margin: `0 0 ${theme.spacing.md} 0` }}>Settings</h3>
            
            <div style={formGroupStyle}>
              <label style={formLabelStyle} htmlFor="response-length">
                Response Length
              </label>
              <select
                id="response-length"
                value={settings.responseLength}
                onChange={(e) => setSettings({
                  ...settings,
                  responseLength: e.target.value as any
                })}
                style={formSelectStyle}
              >
                <option value="concise">Concise</option>
                <option value="normal">Normal</option>
                <option value="detailed">Detailed</option>
              </select>
            </div>
            
            <div style={formGroupStyle}>
              <label style={formLabelStyle} htmlFor="creativity-level">
                Creativity Level: {settings.creativityLevel}
              </label>
              <div style={rangeContainerStyle}>
                <span>1</span>
                <input
                  id="creativity-level"
                  type="range"
                  min="1"
                  max="5"
                  value={settings.creativityLevel}
                  onChange={(e) => setSettings({
                    ...settings,
                    creativityLevel: parseInt(e.target.value)
                  })}
                  style={rangeInputStyle}
                />
                <span>5</span>
              </div>
            </div>
            
            <div style={formGroupStyle}>
              <label style={formLabelStyle} htmlFor="formality-level">
                Formality Level: {settings.formalityLevel}
              </label>
              <div style={rangeContainerStyle}>
                <span>1</span>
                <input
                  id="formality-level"
                  type="range"
                  min="1"
                  max="5"
                  value={settings.formalityLevel}
                  onChange={(e) => setSettings({
                    ...settings,
                    formalityLevel: parseInt(e.target.value)
                  })}
                  style={rangeInputStyle}
                />
                <span>5</span>
              </div>
            </div>
          </div>
        </div>
        
        <div style={modalFooterStyle}>
          <button
            onClick={onClose}
            style={secondaryButtonStyle}
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            style={primaryButtonStyle}
          >
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
};

export default AgentSelectionComponent;