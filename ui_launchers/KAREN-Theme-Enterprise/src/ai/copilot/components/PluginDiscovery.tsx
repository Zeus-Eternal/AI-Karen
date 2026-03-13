import React, { useState } from 'react';
import { PluginManifest, SecurityContext } from '../types/backend';
import { useCopilotTogglePlugin } from '../hooks/useCopilot';

/**
 * PluginDiscovery component
 * Provides UI for plugin discovery and management
 */
interface PluginDiscoveryProps {
  availablePlugins: PluginManifest[];
  _onTogglePlugin: (plugin: PluginManifest, enabled: boolean) => void;
  securityContext: SecurityContext;
  className?: string;
}

interface PluginManifestWithEnabled extends PluginManifest {
  enabled?: boolean;
}

export function PluginDiscovery({
  availablePlugins,
  _onTogglePlugin,
  securityContext,
  className = ''
}: PluginDiscoveryProps) {
  const [selectedPlugin, setSelectedPlugin] = useState<PluginManifest | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterCategory, setFilterCategory] = useState<string>('all');
  const [filterRisk, setFilterRisk] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'name' | 'risk' | 'capability'>('name');
  const [showInstalledOnly, setShowInstalledOnly] = useState(false);
  
  const togglePluginHook = useCopilotTogglePlugin();

  // Get unique plugin categories for filter
  const pluginCategories = Array.from(new Set(
    availablePlugins.flatMap(plugin => plugin.capabilities)
  ));

  // Filter and sort plugins
  const filteredPlugins = availablePlugins
    .filter(plugin => {
      // Filter by search query
      if (searchQuery && !plugin.name.toLowerCase().includes(searchQuery.toLowerCase()) && 
          !plugin.description.toLowerCase().includes(searchQuery.toLowerCase())) {
        return false;
      }
      
      // Filter by category
      if (filterCategory !== 'all' && !plugin.capabilities.includes(filterCategory)) {
        return false;
      }
      
      // Filter by risk level
      if (filterRisk !== 'all' && plugin.riskLevel !== filterRisk as PluginManifest['riskLevel']) {
        return false;
      }
      
      // Filter by installed status
      if (showInstalledOnly && !(plugin as PluginManifestWithEnabled).enabled) {
        return false;
      }
      
      // Filter by security context
      if (plugin.riskLevel === 'evil-mode-only' && securityContext.securityMode !== 'evil') {
        return false;
      }
      
      if (plugin.riskLevel === 'privileged' && !securityContext.canAccessSensitive) {
        return false;
      }
      
      return true;
    })
    .sort((a, b) => {
      const riskOrder = { 'safe': 1, 'privileged': 2, 'evil-mode-only': 3 };
      
      switch (sortBy) {
        case 'name':
          return a.name.localeCompare(b.name);
        case 'risk':
          return riskOrder[a.riskLevel] - riskOrder[b.riskLevel];
        case 'capability':
          return b.capabilities.length - a.capabilities.length;
        default:
          return 0;
      }
    });

  // Group plugins by risk level
  const pluginsByRisk = filteredPlugins.reduce((groups, plugin) => {
    if (!groups[plugin.riskLevel]) {
      groups[plugin.riskLevel] = [];
    }
    groups[plugin.riskLevel].push(plugin);
    return groups;
  }, {} as Record<string, PluginManifest[]>);

  // Handle plugin toggle
  const handleTogglePlugin = (plugin: PluginManifest, enabled: boolean) => {
    togglePluginHook(plugin, enabled);
  };

  // Handle plugin installation (simulated)
  const handleInstallPlugin = (plugin: PluginManifest) => {
    // In a real implementation, this would install the plugin
    alert(`Installation of "${plugin.name}" would be implemented here`);
  };

  return (
    <div className={`plugin-discovery ${className}`}>
      <div className="plugin-discovery__header">
        <h2 className="plugin-discovery__title">Plugin Discovery</h2>
        <p className="plugin-discovery__description">
          Discover, install, and manage plugins to extend Copilot&apos;s capabilities
        </p>
      </div>

      {/* Plugin Search and Filters */}
      <div className="plugin-discovery__controls">
        <div className="plugin-discovery__search">
          <input
            type="text"
            className="plugin-discovery__search-input"
            placeholder="Search plugins..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        
        <div className="plugin-discovery__filters">
          <div className="plugin-discovery__filter-group">
            <label className="plugin-discovery__filter-label">Category:</label>
            <select
              className="plugin-discovery__filter-select"
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
            >
              <option value="all">All Categories</option>
              {pluginCategories.map(category => (
                <option key={category} value={category}>{category}</option>
              ))}
            </select>
          </div>
          
          <div className="plugin-discovery__filter-group">
            <label className="plugin-discovery__filter-label">Risk Level:</label>
            <select
              className="plugin-discovery__filter-select"
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
          
          <div className="plugin-discovery__filter-group">
            <label className="plugin-discovery__filter-label">Sort By:</label>
            <select
              className="plugin-discovery__filter-select"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as 'name' | 'risk' | 'capability')}
            >
              <option value="name">Name</option>
              <option value="risk">Risk Level</option>
              <option value="capability">Capabilities</option>
            </select>
          </div>
          
          <div className="plugin-discovery__filter-group">
            <label className="plugin-discovery__filter-checkbox">
              <input
                type="checkbox"
                checked={showInstalledOnly}
                onChange={(e) => setShowInstalledOnly(e.target.checked)}
              />
              Installed Only
            </label>
          </div>
        </div>
      </div>

      {/* Plugin Categories */}
      <div className="plugin-discovery__categories">
        {/* Safe Plugins */}
        {pluginsByRisk.safe && pluginsByRisk.safe.length > 0 && (
          <div className="plugin-discovery__category">
            <h3 className="plugin-discovery__category-title">Safe Plugins</h3>
            <div className="plugin-discovery__category-description">
              These plugins are safe to use and do not require special permissions
            </div>
            
            <div className="plugin-discovery__plugin-grid">
              {pluginsByRisk.safe.map(plugin => (
                <PluginCard
                  key={plugin.id}
                  plugin={plugin}
                  isSelected={selectedPlugin?.id === plugin.id}
                  onSelect={() => setSelectedPlugin(plugin)}
                  onToggle={handleTogglePlugin}
                  onInstall={handleInstallPlugin}
                />
              ))}
            </div>
          </div>
        )}

        {/* Privileged Plugins */}
        {pluginsByRisk.privileged && pluginsByRisk.privileged.length > 0 && (
          <div className="plugin-discovery__category">
            <h3 className="plugin-discovery__category-title">Privileged Plugins</h3>
            <div className="plugin-discovery__category-description">
              These plugins require elevated permissions and may access sensitive data
            </div>
            
            <div className="plugin-discovery__plugin-grid">
              {pluginsByRisk.privileged.map(plugin => (
                <PluginCard
                  key={plugin.id}
                  plugin={plugin}
                  isSelected={selectedPlugin?.id === plugin.id}
                  onSelect={() => setSelectedPlugin(plugin)}
                  onToggle={handleTogglePlugin}
                  onInstall={handleInstallPlugin}
                  disabled={!securityContext.canAccessSensitive}
                />
              ))}
            </div>
          </div>
        )}

        {/* Evil Mode Plugins */}
        {pluginsByRisk['evil-mode-only'] && pluginsByRisk['evil-mode-only'].length > 0 && (
          <div className="plugin-discovery__category">
            <h3 className="plugin-discovery__category-title">Evil Mode Plugins</h3>
            <div className="plugin-discovery__category-description">
              These plugins are highly dangerous and can cause irreversible changes
            </div>
            
            <div className="plugin-discovery__plugin-grid">
              {pluginsByRisk['evil-mode-only'].map(plugin => (
                <PluginCard
                  key={plugin.id}
                  plugin={plugin}
                  isSelected={selectedPlugin?.id === plugin.id}
                  onSelect={() => setSelectedPlugin(plugin)}
                  onToggle={handleTogglePlugin}
                  onInstall={handleInstallPlugin}
                  disabled={securityContext.securityMode !== 'evil'}
                />
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Plugin Details */}
      {selectedPlugin && (
        <div className="plugin-discovery__details">
          <div className="plugin-discovery__details-header">
            <h3 className="plugin-discovery__details-title">{selectedPlugin.name}</h3>
            <div className="plugin-discovery__details-meta">
              <span className="plugin-discovery__details-version">
                v{selectedPlugin.version}
              </span>
              <span className="plugin-discovery__details-author">
                by {selectedPlugin.author}
              </span>
              <span className={`plugin-discovery__details-risk plugin-discovery__details-risk--${selectedPlugin.riskLevel}`}>
                {selectedPlugin.riskLevel}
              </span>
            </div>
            <button
              className="plugin-discovery__details-close"
              onClick={() => setSelectedPlugin(null)}
            >
              ✕
            </button>
          </div>
          
          <div className="plugin-discovery__details-description">
            {selectedPlugin.description}
          </div>
          
          <div className="plugin-discovery__details-capabilities">
            <h4 className="plugin-discovery__details-capabilities-title">Capabilities</h4>
            <ul className="plugin-discovery__details-capabilities-list">
              {selectedPlugin.capabilities.map((capability, index) => (
                <li key={index} className="plugin-discovery__details-capability">
                  {capability}
                </li>
              ))}
            </ul>
          </div>
          
          {selectedPlugin.config && selectedPlugin.config.parameters.length > 0 && (
            <div className="plugin-discovery__details-config">
              <h4 className="plugin-discovery__details-config-title">Configuration</h4>
              <div className="plugin-discovery__details-parameters">
                {selectedPlugin.config?.parameters.map((param, index) => (
                  <div key={index} className="plugin-discovery__details-parameter">
                    <div className="plugin-discovery__details-parameter-name">
                      {param.name} ({param.type})
                      {param.required && <span className="plugin-discovery__details-parameter-required">*</span>}
                    </div>
                    <div className="plugin-discovery__details-parameter-description">
                      {param.description}
                    </div>
                    {param.defaultValue !== undefined && (
                      <div className="plugin-discovery__details-parameter-default">
                        Default: {String(param.defaultValue)}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
          
          <div className="plugin-discovery__details-actions">
            <button
              className={`plugin-discovery__details-toggle ${(selectedPlugin as PluginManifestWithEnabled).enabled ? 'enabled' : ''}`}
              onClick={() => handleTogglePlugin(selectedPlugin, !(selectedPlugin as PluginManifestWithEnabled).enabled)}
            >
              {(selectedPlugin as PluginManifestWithEnabled).enabled ? 'Disable' : 'Enable'}
            </button>
            <button
              className="plugin-discovery__details-install"
              onClick={() => handleInstallPlugin(selectedPlugin)}
            >
              Install
            </button>
          </div>
        </div>
      )}

      {/* No Plugins Message */}
      {filteredPlugins.length === 0 && (
        <div className="plugin-discovery__empty">
          <p className="plugin-discovery__empty-message">
            No plugins found matching your search criteria.
          </p>
        </div>
      )}
    </div>
  );
}

/**
 * PluginCard component
 * Represents a single plugin in the grid
 */
interface PluginCardProps {
  plugin: PluginManifest;
  isSelected: boolean;
  onSelect: () => void;
  onToggle: (plugin: PluginManifest, enabled: boolean) => void;
  onInstall: (plugin: PluginManifest) => void;
  disabled?: boolean;
}

function PluginCard({
  plugin,
  isSelected,
  onSelect,
  onToggle,
  onInstall,
  disabled = false
}: PluginCardProps) {
  const isEnabled = (plugin as PluginManifestWithEnabled).enabled || false;
  
  return (
    <div 
      className={`plugin-card ${isSelected ? 'plugin-card--selected' : ''} plugin-card--${plugin.riskLevel}`}
      onClick={onSelect}
    >
      <div className="plugin-card__header">
        <h4 className="plugin-card__title">{plugin.name}</h4>
        <span className={`plugin-card__risk plugin-card__risk--${plugin.riskLevel}`}>
          {plugin.riskLevel}
        </span>
      </div>
      
      <p className="plugin-card__description">
        {plugin.description}
      </p>
      
      <div className="plugin-card__details">
        <span className="plugin-card__version">
          v{plugin.version}
        </span>
        <span className="plugin-card__author">
          {plugin.author}
        </span>
        <span className="plugin-card__capabilities">
          {plugin.capabilities.length} capabilities
        </span>
      </div>
      
      <div className="plugin-card__capabilities-preview">
        {plugin.capabilities.slice(0, 3).map((capability, index) => (
          <span key={index} className="plugin-card__capability">
            {capability}
          </span>
        ))}
        {plugin.capabilities.length > 3 && (
          <span className="plugin-card__capability-more">
            +{plugin.capabilities.length - 3} more
          </span>
        )}
      </div>
      
      <div className="plugin-card__actions">
        <button
          className={`plugin-card__toggle ${isEnabled ? 'enabled' : ''}`}
          onClick={(e) => {
            e.stopPropagation();
            onToggle(plugin, !isEnabled);
          }}
          disabled={disabled}
        >
          {isEnabled ? 'Disable' : 'Enable'}
        </button>
        <button
          className="plugin-card__install"
          onClick={(e) => {
            e.stopPropagation();
            onInstall(plugin);
          }}
          disabled={disabled}
        >
          Install
        </button>
      </div>
    </div>
  );
}