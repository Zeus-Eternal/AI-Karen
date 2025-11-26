import React, { useState } from 'react';
import { CopilotMemoryOps, MemoryResult } from '../types/backend';
import { CopilotMessage } from '../types/copilot';

/**
 * MemoryManagement component
 * Provides UI for managing memory tiers (short-term, long-term, persistent)
 */
interface MemoryManagementProps {
  messages: CopilotMessage[];
  memoryOps: CopilotMemoryOps | null;
  onQueryMemory: (query: string) => void;
  onPinMemory: (messageId: string) => void;
  onForgetMemory: (messageId: string) => void;
  securityContext: {
    userRoles: string[];
    securityMode: 'safe' | 'aggressive' | 'evil';
    canAccessSensitive: boolean;
    redactionLevel: 'none' | 'partial' | 'full';
  };
  className?: string;
}

export function MemoryManagement({ 
  messages, 
  memoryOps, 
  onQueryMemory, 
  onPinMemory, 
  onForgetMemory, 
  securityContext,
  className = '' 
}: MemoryManagementProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<MemoryResult[]>([]);
  const [selectedTier, setSelectedTier] = useState<'short-term' | 'long-term' | 'persistent' | 'echo-core'>('short-term');
  const [isSearching, setIsSearching] = useState(false);
  const [pinnedMessages, setPinnedMessages] = useState<string[]>([]);
  

  // Handle memory search
  const handleSearch = async () => {
    if (!query.trim()) return;
    
    setIsSearching(true);
    try {
      onQueryMemory(query);
      // In a real implementation, this would update the results state
      // For now, we'll simulate it with a timeout
      setTimeout(() => {
        setResults([]); // Reset results
        setIsSearching(false);
      }, 1000);
    } catch (error) {
      console.error('Error searching memory:', error);
      setIsSearching(false);
    }
  };

  // Handle pinning a message
  const handlePinMessage = (messageId: string) => {
    if (pinnedMessages.includes(messageId)) {
      setPinnedMessages(pinnedMessages.filter(id => id !== messageId));
    } else {
      setPinnedMessages([...pinnedMessages, messageId]);
    }
    onPinMemory(messageId);
  };

  // Handle forgetting a message
  const handleForgetMessage = (messageId: string) => {
    setPinnedMessages(pinnedMessages.filter(id => id !== messageId));
    onForgetMemory(messageId);
  };

  // Filter messages based on selected tier
  const filteredMessages = messages.filter(() => {
    // This is a simplified filtering logic
    // In a real implementation, messages would have tier information
    return true;
  });

  // Group messages by date for better organization
  const messagesByDate = filteredMessages.reduce((groups, message) => {
    const date = message.timestamp.toDateString();
    if (!groups[date]) {
      groups[date] = [];
    }
    groups[date].push(message);
    return groups;
  }, {} as Record<string, CopilotMessage[]>);

  return (
    <div className={`memory-management ${className}`}>
      <div className="memory-management__header">
        <h2 className="memory-management__title">Memory Management</h2>
        <p className="memory-management__description">
          Manage your conversation memory across different tiers
        </p>
      </div>

      {/* Memory Stats */}
      {memoryOps && (
        <div className="memory-management__stats">
          <h3 className="memory-management__stats-title">Memory Operations</h3>
          <div className="memory-management__stats-grid">
            <div className="memory-management__stat">
              <span className="memory-management__stat-label">Reads:</span>
              <span className="memory-management__stat-value">{memoryOps.reads}</span>
            </div>
            <div className="memory-management__stat">
              <span className="memory-management__stat-label">Writes:</span>
              <span className="memory-management__stat-value">{memoryOps.writes}</span>
            </div>
            <div className="memory-management__stat">
              <span className="memory-management__stat-label">Active Tier:</span>
              <span className="memory-management__stat-value">{memoryOps.tier}</span>
            </div>
          </div>
        </div>
      )}

      {/* Memory Search */}
      <div className="memory-management__search">
        <h3 className="memory-management__search-title">Search Memory</h3>
        <div className="memory-management__search-form">
          <input
            type="text"
            className="memory-management__search-input"
            placeholder="Search your memory..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                handleSearch();
              }
            }}
          />
          <select
            className="memory-management__tier-select"
            value={selectedTier}
            onChange={(e) => setSelectedTier(e.target.value as 'short-term' | 'long-term' | 'persistent' | 'echo-core')}
          >
            <option value="short-term">Short-term</option>
            <option value="long-term">Long-term</option>
            <option value="persistent">Persistent</option>
            {securityContext.securityMode === 'evil' && (
              <option value="echo-core">Echo Core</option>
            )}
          </select>
          <button
            className="memory-management__search-button"
            onClick={handleSearch}
            disabled={isSearching || !query.trim()}
          >
            {isSearching ? 'Searching...' : 'Search'}
          </button>
        </div>
      </div>

      {/* Search Results */}
      {results.length > 0 && (
        <div className="memory-management__results">
          <h3 className="memory-management__results-title">Search Results</h3>
          <div className="memory-management__results-list">
            {results.map((result, index) => (
              <div key={index} className="memory-management__result">
                <div className="memory-management__result-header">
                  <span className="memory-management__result-type">{result.type}</span>
                  <span className="memory-management__result-tier">{result.tier}</span>
                  <span className="memory-management__result-score">
                    Relevance: {Math.round(result.relevanceScore * 100)}%
                  </span>
                </div>
                <div className="memory-management__result-content">
                  {result.content}
                </div>
                <div className="memory-management__result-footer">
                  <span className="memory-management__result-date">
                    {result.timestamp.toLocaleString()}
                  </span>
                  <button
                    className="memory-management__result-pin-button"
                    onClick={() => {
                      // Pin the result
                      const messageId = `result_${index}`;
                      handlePinMessage(messageId);
                    }}
                  >
                    Pin
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Memory Tiers */}
      <div className="memory-management__tiers">
        <h3 className="memory-management__tiers-title">Memory Tiers</h3>
        <div className="memory-management__tier-tabs">
          <button
            className={`memory-management__tier-tab ${selectedTier === 'short-term' ? 'active' : ''}`}
            onClick={() => setSelectedTier('short-term')}
          >
            Short-term
          </button>
          <button
            className={`memory-management__tier-tab ${selectedTier === 'long-term' ? 'active' : ''}`}
            onClick={() => setSelectedTier('long-term')}
          >
            Long-term
          </button>
          <button
            className={`memory-management__tier-tab ${selectedTier === 'persistent' ? 'active' : ''}`}
            onClick={() => setSelectedTier('persistent')}
          >
            Persistent
          </button>
          {securityContext.securityMode === 'evil' && (
            <button
              className={`memory-management__tier-tab ${selectedTier === 'echo-core' ? 'active' : ''}`}
              onClick={() => setSelectedTier('echo-core')}
            >
              Echo Core
            </button>
          )}
        </div>

        <div className="memory-management__tier-description">
          {selectedTier === 'short-term' && (
            <p>
              Short-term memory stores recent conversations and is quickly accessible.
              Items may be automatically removed after a period of inactivity.
            </p>
          )}
          {selectedTier === 'long-term' && (
            <p>
              Long-term memory stores important conversations and insights.
              Items are retained for extended periods and can be retrieved through search.
            </p>
          )}
          {selectedTier === 'persistent' && (
            <p>
              Persistent memory stores critical information that should never be forgotten.
              Items are retained indefinitely and are highly prioritized in search results.
            </p>
          )}
          {selectedTier === 'echo-core' && (
            <p>
              Echo Core memory stores deeply embedded patterns and insights.
              This tier is only available in Evil Mode and contains the most sensitive information.
            </p>
          )}
        </div>
      </div>

      {/* Message History */}
      <div className="memory-management__history">
        <h3 className="memory-management__history-title">Conversation History</h3>
        {Object.entries(messagesByDate).map(([date, dayMessages]) => (
          <div key={date} className="memory-management__date-group">
            <h4 className="memory-management__date-header">{date}</h4>
            <div className="memory-management__date-messages">
              {(dayMessages as CopilotMessage[]).map(message => (
                <div 
                  key={message.id} 
                  className={`memory-management__message memory-management__message--${message.role}`}
                >
                  <div className="memory-management__message-header">
                    <span className="memory-management__message-role">{message.role}</span>
                    <span className="memory-management__message-time">
                      {message.timestamp.toLocaleTimeString()}
                    </span>
                    <div className="memory-management__message-actions">
                      <button
                        className={`memory-management__message-pin ${pinnedMessages.includes(message.id) ? 'pinned' : ''}`}
                        onClick={() => handlePinMessage(message.id)}
                        title={pinnedMessages.includes(message.id) ? 'Unpin' : 'Pin'}
                      >
                        {pinnedMessages.includes(message.id) ? '📌' : '📍'}
                      </button>
                      <button
                        className="memory-management__message-forget"
                        onClick={() => handleForgetMessage(message.id)}
                        title="Forget"
                        disabled={securityContext.redactionLevel === 'full'}
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                  <div className="memory-management__message-content">
                    {message.content}
                  </div>
                  {message.metadata && (
                    <div className="memory-management__message-metadata">
                      {Object.entries(message.metadata).map(([key, value]) => (
                        <div key={key} className="memory-management__metadata-item">
                          <span className="memory-management__metadata-key">{key}:</span>
                          <span className="memory-management__metadata-value">
                            {String(value)}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Pinned Messages */}
      {pinnedMessages.length > 0 && (
        <div className="memory-management__pinned">
          <h3 className="memory-management__pinned-title">Pinned Messages</h3>
          <div className="memory-management__pinned-list">
            {pinnedMessages.map(messageId => {
              const message = messages.find(m => m.id === messageId);
              if (!message) return null;
              
              return (
                <div key={messageId} className="memory-management__pinned-message">
                  <div className="memory-management__pinned-header">
                    <span className="memory-management__pinned-role">{message.role}</span>
                    <span className="memory-management__pinned-time">
                      {message.timestamp.toLocaleString()}
                    </span>
                  </div>
                  <div className="memory-management__pinned-content">
                    {message.content}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}