import React, { useState, useEffect } from 'react';
import { useExtensions } from '../../hooks/useExtensions';
import { 
  CoPilotExtension, 
  ExtensionStatus, 
  ExtensionHealthStatus,
  ExtensionCategory,
  ExtensionCapability
} from '../../types/extension';
import { Theme } from '../chat/types';

interface ExtensionManagerComponentProps {
  theme: Theme;
  className?: string;
}

/**
 * Component for managing CoPilot extensions
 */
export const ExtensionManagerComponent: React.FC<ExtensionManagerComponentProps> = ({
  theme,
  className = ''
}) => {
  const {
    extensions,
    extensionStatus,
    isLoading,
    error,
    registerExtension,
    unregisterExtension,
    setExtensionEnabled,
    getExtensionUIComponents,
    getExtensionHooks
  } = useExtensions();

  const [selectedExtension, setSelectedExtension] = useState<CoPilotExtension | null>(null);
  const [filter, setFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [showAddExtension, setShowAddExtension] = useState<boolean>(false);

  // Filter extensions based on selected filter and search query
  const filteredExtensions = extensions.filter(extension => {
    // Category filter
    if (filter !== 'all' && extension.category !== filter) {
      return false;
    }

    // Search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        extension.name.toLowerCase().includes(query) ||
        extension.description.toLowerCase().includes(query) ||
        extension.author.toLowerCase().includes(query)
      );
    }

    return true;
  });

  // Get status for an extension
  const getExtensionStatus = (extensionId: string): ExtensionStatus | undefined => {
    return extensionStatus.get(extensionId);
  };

  // Handle extension selection
  const handleExtensionSelect = (extension: CoPilotExtension) => {
    setSelectedExtension(extension);
  };

  // Handle extension enable/disable
  const handleToggleEnabled = async (extensionId: string, enabled: boolean) => {
    await setExtensionEnabled(extensionId, enabled);
  };

  // Handle extension uninstall
  const handleUninstallExtension = async (extensionId: string) => {
    if (window.confirm('Are you sure you want to uninstall this extension?')) {
      await unregisterExtension(extensionId);
      if (selectedExtension?.id === extensionId) {
        setSelectedExtension(null);
      }
    }
  };

  // Render status badge
  const renderStatusBadge = (status: ExtensionStatus | undefined) => {
    if (!status) {
      return null;
    }

    let statusColor = '';
    let statusText = '';

    switch (status.health) {
      case ExtensionHealthStatus.HEALTHY:
        statusColor = theme.colors.success;
        statusText = 'Healthy';
        break;
      case ExtensionHealthStatus.WARNING:
        statusColor = theme.colors.warning;
        statusText = 'Warning';
        break;
      case ExtensionHealthStatus.ERROR:
        statusColor = theme.colors.error;
        statusText = 'Error';
        break;
      case ExtensionHealthStatus.UNRESPONSIVE:
        statusColor = theme.colors.error;
        statusText = 'Unresponsive';
        break;
    }

    return (
      <span
        style={{
          backgroundColor: `${statusColor}20`,
          color: statusColor,
          padding: '2px 8px',
          borderRadius: '12px',
          fontSize: theme.typography.fontSize.xs,
          fontWeight: theme.typography.fontWeight.medium as number
        }}
      >
        {statusText}
      </span>
    );
  };

  // Render capability badges
  const renderCapabilityBadges = (capabilities: ExtensionCapability[]) => {
    return (
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
        {capabilities.map((capability, index) => (
          <span
            key={index}
            style={{
              backgroundColor: `${theme.colors.primary}20`,
              color: theme.colors.primary,
              padding: '2px 6px',
              borderRadius: '8px',
              fontSize: theme.typography.fontSize.xs
            }}
            title={capability}
          >
            {capability.replace('_', ' ')}
          </span>
        ))}
      </div>
    );
  };

  // Render extension details
  const renderExtensionDetails = () => {
    if (!selectedExtension) {
      return (
        <div
          style={{
            padding: theme.spacing.lg,
            textAlign: 'center',
            color: theme.colors.textSecondary
          }}
        >
          <div style={{ fontSize: '3rem', marginBottom: theme.spacing.md }}>📦</div>
          <h3 style={{ margin: 0, marginBottom: theme.spacing.sm }}>Select an Extension</h3>
          <p>Select an extension to view its details and manage its settings.</p>
        </div>
      );
    }

    const status = getExtensionStatus(selectedExtension.id);
    const uiComponents = getExtensionUIComponents(selectedExtension.id);
    const hooks = getExtensionHooks(selectedExtension.id);

    return (
      <div style={{ padding: theme.spacing.md }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: theme.spacing.md }}>
          <div>
            <h2 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: theme.spacing.sm }}>
              {selectedExtension.name}
              {renderStatusBadge(status)}
            </h2>
            <p style={{ margin: '4px 0 0 0', color: theme.colors.textSecondary }}>
              Version {selectedExtension.version} by {selectedExtension.author}
            </p>
          </div>
          <div style={{ display: 'flex', gap: theme.spacing.sm }}>
            <button
              onClick={() => handleToggleEnabled(selectedExtension.id, !status?.enabled)}
              style={{
                padding: '6px 12px',
                backgroundColor: status?.enabled ? theme.colors.warning : theme.colors.success,
                color: 'white',
                border: 'none',
                borderRadius: theme.borderRadius,
                cursor: 'pointer',
                fontSize: theme.typography.fontSize.sm
              }}
            >
              {status?.enabled ? 'Disable' : 'Enable'}
            </button>
            <button
              onClick={() => handleUninstallExtension(selectedExtension.id)}
              style={{
                padding: '6px 12px',
                backgroundColor: theme.colors.error,
                color: 'white',
                border: 'none',
                borderRadius: theme.borderRadius,
                cursor: 'pointer',
                fontSize: theme.typography.fontSize.sm
              }}
            >
              Uninstall
            </button>
          </div>
        </div>

        <div style={{ marginBottom: theme.spacing.lg }}>
          <h3 style={{ margin: '0 0 ' + theme.spacing.sm + ' 0' }}>Description</h3>
          <p style={{ margin: 0, color: theme.colors.textSecondary }}>
            {selectedExtension.description}
          </p>
        </div>

        <div style={{ marginBottom: theme.spacing.lg }}>
          <h3 style={{ margin: '0 0 ' + theme.spacing.sm + ' 0' }}>Category</h3>
          <span
            style={{
              backgroundColor: `${theme.colors.primary}20`,
              color: theme.colors.primary,
              padding: '4px 8px',
              borderRadius: '12px',
              fontSize: theme.typography.fontSize.sm,
              fontWeight: theme.typography.fontWeight.medium as number
            }}
          >
            {selectedExtension.category.replace('_', ' ')}
          </span>
        </div>

        <div style={{ marginBottom: theme.spacing.lg }}>
          <h3 style={{ margin: '0 0 ' + theme.spacing.sm + ' 0' }}>Capabilities</h3>
          {renderCapabilityBadges(selectedExtension.capabilities)}
        </div>

        {status && (
          <div style={{ marginBottom: theme.spacing.lg }}>
            <h3 style={{ margin: '0 0 ' + theme.spacing.sm + ' 0' }}>Status</h3>
            <div style={{ backgroundColor: theme.colors.surface, padding: theme.spacing.md, borderRadius: theme.borderRadius }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: theme.spacing.sm }}>
                <span>Enabled:</span>
                <span style={{ color: status.enabled ? theme.colors.success : theme.colors.error }}>
                  {status.enabled ? 'Yes' : 'No'}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: theme.spacing.sm }}>
                <span>Initialized:</span>
                <span style={{ color: status.initialized ? theme.colors.success : theme.colors.error }}>
                  {status.initialized ? 'Yes' : 'No'}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: theme.spacing.sm }}>
                <span>Health:</span>
                <span>{renderStatusBadge(status)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Requests:</span>
                <span>{status.metrics.requestCount}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Success Rate:</span>
                <span>
                  {status.metrics.requestCount > 0
                    ? `${Math.round((status.metrics.successCount / status.metrics.requestCount) * 100)}%`
                    : '0%'}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>Avg Response Time:</span>
                <span>{status.metrics.averageResponseTime.toFixed(2)}ms</span>
              </div>
            </div>
          </div>
        )}

        {uiComponents.length > 0 && (
          <div style={{ marginBottom: theme.spacing.lg }}>
            <h3 style={{ margin: '0 0 ' + theme.spacing.sm + ' 0' }}>UI Components</h3>
            <div style={{ backgroundColor: theme.colors.surface, padding: theme.spacing.md, borderRadius: theme.borderRadius }}>
              {uiComponents.map((component, index) => (
                <div key={index} style={{ marginBottom: theme.spacing.sm }}>
                  <div style={{ fontWeight: theme.typography.fontWeight.medium as number }}>
                    {component.id} ({component.type})
                  </div>
                  <div style={{ fontSize: theme.typography.fontSize.sm, color: theme.colors.textSecondary }}>
                    Position: {component.position}, Order: {component.order}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {hooks.length > 0 && (
          <div>
            <h3 style={{ margin: '0 0 ' + theme.spacing.sm + ' 0' }}>Hooks</h3>
            <div style={{ backgroundColor: theme.colors.surface, padding: theme.spacing.md, borderRadius: theme.borderRadius }}>
              {hooks.map((hook, index) => (
                <div key={index} style={{ marginBottom: theme.spacing.sm }}>
                  <div style={{ fontWeight: theme.typography.fontWeight.medium as number }}>
                    {hook.name}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  // Render filter controls
  const renderFilterControls = () => {
    const categories = Object.values(ExtensionCategory);

    return (
      <div style={{ marginBottom: theme.spacing.md, display: 'flex', gap: theme.spacing.md, alignItems: 'center' }}>
        <div style={{ flex: 1 }}>
          <input
            type="text"
            placeholder="Search extensions..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              width: '100%',
              padding: '8px 12px',
              border: `1px solid ${theme.colors.border}`,
              borderRadius: theme.borderRadius,
              backgroundColor: theme.colors.surface,
              color: theme.colors.text,
              fontSize: theme.typography.fontSize.sm
            }}
          />
        </div>
        <div>
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            style={{
              padding: '8px 12px',
              border: `1px solid ${theme.colors.border}`,
              borderRadius: theme.borderRadius,
              backgroundColor: theme.colors.surface,
              color: theme.colors.text,
              fontSize: theme.typography.fontSize.sm
            }}
          >
            <option value="all">All Categories</option>
            {categories.map((category) => (
              <option key={category} value={category}>
                {category.replace('_', ' ')}
              </option>
            ))}
          </select>
        </div>
        <button
          onClick={() => setShowAddExtension(true)}
          style={{
            padding: '8px 16px',
            backgroundColor: theme.colors.primary,
            color: 'white',
            border: 'none',
            borderRadius: theme.borderRadius,
            cursor: 'pointer',
            fontSize: theme.typography.fontSize.sm,
            fontWeight: theme.typography.fontWeight.medium as number
          }}
        >
          Add Extension
        </button>
      </div>
    );
  };

  // Render extension list
  const renderExtensionList = () => {
    if (isLoading) {
      return (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: theme.spacing.xl,
            color: theme.colors.textSecondary
          }}
        >
          <div
            style={{
              width: '40px',
              height: '40px',
              border: `3px solid ${theme.colors.border}`,
              borderTop: `3px solid ${theme.colors.primary}`,
              borderRadius: '50%',
              animation: 'spin 1s linear infinite',
              marginBottom: theme.spacing.md
            }}
          />
          <p>Loading extensions...</p>
        </div>
      );
    }

    if (error) {
      return (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: theme.spacing.xl,
            color: theme.colors.error
          }}
        >
          <div style={{ fontSize: '2rem', marginBottom: theme.spacing.md }}>⚠️</div>
          <h3 style={{ margin: '0 0 ' + theme.spacing.sm + ' 0' }}>Error</h3>
          <p>{error}</p>
        </div>
      );
    }

    if (filteredExtensions.length === 0) {
      return (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: theme.spacing.xl,
            color: theme.colors.textSecondary
          }}
        >
          <div style={{ fontSize: '3rem', marginBottom: theme.spacing.md }}>📦</div>
          <h3 style={{ margin: '0 0 ' + theme.spacing.sm + ' 0' }}>No Extensions Found</h3>
          <p>No extensions match your search criteria.</p>
        </div>
      );
    }

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: theme.spacing.sm }}>
        {filteredExtensions.map((extension) => {
          const status = getExtensionStatus(extension.id);
          const isSelected = selectedExtension?.id === extension.id;

          return (
            <div
              key={extension.id}
              onClick={() => handleExtensionSelect(extension)}
              style={{
                padding: theme.spacing.md,
                backgroundColor: isSelected ? `${theme.colors.primary}10` : theme.colors.surface,
                border: `1px solid ${isSelected ? theme.colors.primary : theme.colors.border}`,
                borderRadius: theme.borderRadius,
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: theme.spacing.sm }}>
                  <h3 style={{ margin: 0 }}>{extension.name}</h3>
                  {renderStatusBadge(status)}
                </div>
                <div style={{ color: theme.colors.textSecondary, fontSize: theme.typography.fontSize.sm }}>
                  v{extension.version}
                </div>
              </div>
              <p style={{ margin: '4px 0 0 0', color: theme.colors.textSecondary, fontSize: theme.typography.fontSize.sm }}>
                {extension.description}
              </p>
              <div style={{ marginTop: theme.spacing.sm }}>
                {renderCapabilityBadges(extension.capabilities.slice(0, 3))}
                {extension.capabilities.length > 3 && (
                  <span style={{ marginLeft: '4px', color: theme.colors.textSecondary }}>
                    +{extension.capabilities.length - 3} more
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  // Render add extension dialog
  const renderAddExtensionDialog = () => {
    if (!showAddExtension) {
      return null;
    }

    return (
      <div
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 100
        }}
        onClick={() => setShowAddExtension(false)}
      >
        <div
          style={{
            backgroundColor: theme.colors.background,
            border: `1px solid ${theme.colors.border}`,
            borderRadius: theme.borderRadius,
            boxShadow: theme.shadows.lg,
            width: '500px',
            maxWidth: '90vw',
            padding: theme.spacing.lg
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <h2 style={{ marginTop: 0, marginBottom: theme.spacing.lg }}>Add Extension</h2>
          <p style={{ marginBottom: theme.spacing.lg, color: theme.colors.textSecondary }}>
            This feature is not yet implemented. In the future, you'll be able to add extensions from the marketplace or upload your own.
          </p>
          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button
              onClick={() => setShowAddExtension(false)}
              style={{
                padding: '8px 16px',
                backgroundColor: theme.colors.primary,
                color: 'white',
                border: 'none',
                borderRadius: theme.borderRadius,
                cursor: 'pointer',
                fontSize: theme.typography.fontSize.sm
              }}
            >
              Close
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className={`copilot-extension-manager ${className}`}>
      {renderFilterControls()}
      <div style={{ display: 'flex', height: '600px', border: `1px solid ${theme.colors.border}`, borderRadius: theme.borderRadius, overflow: 'hidden' }}>
        {/* Extension List */}
        <div
          style={{
            width: '350px',
            borderRight: `1px solid ${theme.colors.border}`,
            overflowY: 'auto',
            backgroundColor: theme.colors.background
          }}
        >
          {renderExtensionList()}
        </div>

        {/* Extension Details */}
        <div
          style={{
            flex: 1,
            overflowY: 'auto',
            backgroundColor: theme.colors.background
          }}
        >
          {renderExtensionDetails()}
        </div>
      </div>
      {renderAddExtensionDialog()}

      <style jsx>{`
        @keyframes spin {
          0% {
            transform: rotate(0deg);
          }
          100% {
            transform: rotate(360deg);
          }
        }
      `}</style>
    </div>
  );
};

export default ExtensionManagerComponent;