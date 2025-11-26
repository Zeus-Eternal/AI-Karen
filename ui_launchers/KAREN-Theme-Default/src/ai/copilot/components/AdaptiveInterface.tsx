import React, { useState, useEffect } from 'react';
import { UIAdaptationPolicy, UserExpertiseLevel } from '../types/copilot';
import { useCopilotContext } from '../hooks/useCopilot';

/**
 * AdaptiveInterface component
 * Creates an interface that adapts based on backend suggestions
 */
interface AdaptiveInterfaceProps {
  children: React.ReactNode;
  adaptationPolicy?: UIAdaptationPolicy;
  expertiseLevel?: UserExpertiseLevel;
  className?: string;
}

export function AdaptiveInterface({ 
  children, 
  adaptationPolicy,
  expertiseLevel = 'intermediate',
  className = '' 
}: AdaptiveInterfaceProps) {
  const { state, updateUIConfig } = useCopilotContext();
  const [adaptedUI, setAdaptedUI] = useState<React.ReactNode>(children);
  const [currentPolicy, setCurrentPolicy] = useState<UIAdaptationPolicy | null>(adaptationPolicy || null);
  const [suggestion, setSuggestion] = useState<string | null>(null);
  const [isEngineReady, setIsEngineReady] = useState(false);

  // Apply adaptation policy
  useEffect(() => {
    if (!adaptationPolicy) {
      setAdaptedUI(children);
      return;
    }

    // Apply adaptations based on policy and expertise level
    const adaptedChildren = applyAdaptations(children, adaptationPolicy, expertiseLevel);
    setAdaptedUI(adaptedChildren);
  }, [children, adaptationPolicy, expertiseLevel]);

  // Initialize adaptation policy on mount and when expertise level changes
  useEffect(() => {
    if (!adaptationPolicy) {
      const policy = generateAdaptationPolicy(expertiseLevel);
      setCurrentPolicy(policy);
      
      // Generate a suggestion based on expertise level
      const suggestions = {
        beginner: "Try using the guided mode for step-by-step assistance.",
        intermediate: "You can customize the interface using the settings panel.",
        advanced: "Advanced features and shortcuts are now available.",
        expert: "All advanced features and developer tools are enabled."
      };
      
      setSuggestion(suggestions[expertiseLevel]);
    }
  }, [expertiseLevel, adaptationPolicy]);

  // Handle policy change
  const handlePolicyChange = (newPolicy: UIAdaptationPolicy) => {
    setCurrentPolicy(newPolicy);
  };

  // Check if engine is ready
  useEffect(() => {
    // Try to access a property to check if engine is initialized
    try {
      if (state && state.uiConfig) {
        setIsEngineReady(true);
      }
    } catch (error) {
      // Engine is not ready yet
      console.debug('Engine not ready:', error);
      setIsEngineReady(false);
    }
  }, [state]);

  // Update UI config when policy changes, but only if it's different from current config and engine is ready
  useEffect(() => {
    if (currentPolicy && state && isEngineReady) {
      const configChanged =
        currentPolicy.showDebugInfo !== state.uiConfig.showDebugInfo ||
        currentPolicy.showMemoryOps !== state.uiConfig.showMemoryOps ||
        currentPolicy.maxMessageHistory !== state.uiConfig.maxMessageHistory;
        
      if (configChanged) {
        try {
          updateUIConfig({
            ...state.uiConfig,
            // Update UI config based on policy
            showDebugInfo: currentPolicy.showDebugInfo,
            showMemoryOps: currentPolicy.showMemoryOps,
            maxMessageHistory: currentPolicy.maxMessageHistory
          });
        } catch (err) {
          console.warn('Failed to update UI config:', err);
          // Check if the error is because the engine is not initialized
          if (err instanceof Error && err.message === 'Copilot engine is not initialized yet') {
            setIsEngineReady(false);
            // Try again after a delay
            const timer = setTimeout(() => {
              setIsEngineReady(true);
            }, 1000);
            return () => clearTimeout(timer);
          }
        }
      }
    }
  }, [currentPolicy, state, updateUIConfig, isEngineReady]);

  // Handle expertise level change
  const handleExpertiseChange = (level: UserExpertiseLevel) => {
    const policy = generateAdaptationPolicy(level);
    handlePolicyChange(policy);
  };

  return (
    <div className={`adaptive-interface ${className}`}>
      {/* Adaptation Controls */}
      <div className="adaptive-interface__controls">
        <div className="adaptive-interface__expertise">
          <label className="adaptive-interface__expertise-label">
            Expertise Level:
          </label>
          <select
            className="adaptive-interface__expertise-select"
            value={expertiseLevel}
            onChange={(e) => handleExpertiseChange(e.target.value as UserExpertiseLevel)}
          >
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
            <option value="expert">Expert</option>
          </select>
        </div>
        
        <div className="adaptive-interface__policy-info">
          <span className="adaptive-interface__policy-title">
            Current Policy: {currentPolicy?.name || 'Default'}
          </span>
          <span className="adaptive-interface__policy-description">
            {currentPolicy?.description || 'Standard interface behavior'}
          </span>
        </div>
      </div>

      {/* Adaptation Suggestion */}
      {suggestion && (
        <div className="adaptive-interface__suggestion">
          <div className="adaptive-interface__suggestion-icon">💡</div>
          <div className="adaptive-interface__suggestion-text">
            {suggestion}
          </div>
          <button
            className="adaptive-interface__suggestion-dismiss"
            onClick={() => setSuggestion(null)}
          >
            ✕
          </button>
        </div>
      )}

      {/* Adapted Content */}
      <div className="adaptive-interface__content">
        {adaptedUI}
      </div>

      {/* Adaptation Details */}
      {currentPolicy && (
        <div className="adaptive-interface__details">
          <h3 className="adaptive-interface__details-title">
            Adaptation Details
          </h3>
          
          <div className="adaptive-interface__details-grid">
            <div className="adaptive-interface__detail-item">
              <span className="adaptive-interface__detail-label">
                Simplified UI:
              </span>
              <span className="adaptive-interface__detail-value">
                {currentPolicy.simplifiedUI ? 'Yes' : 'No'}
              </span>
            </div>
            
            <div className="adaptive-interface__detail-item">
              <span className="adaptive-interface__detail-label">
                Guided Mode:
              </span>
              <span className="adaptive-interface__detail-value">
                {currentPolicy.guidedMode ? 'Yes' : 'No'}
              </span>
            </div>
            
            <div className="adaptive-interface__detail-item">
              <span className="adaptive-interface__detail-label">
                Show Advanced:
              </span>
              <span className="adaptive-interface__detail-value">
                {currentPolicy.showAdvancedFeatures ? 'Yes' : 'No'}
              </span>
            </div>
            
            <div className="adaptive-interface__detail-item">
              <span className="adaptive-interface__detail-label">
                Show Debug:
              </span>
              <span className="adaptive-interface__detail-value">
                {currentPolicy.showDebugInfo ? 'Yes' : 'No'}
              </span>
            </div>
            
            <div className="adaptive-interface__detail-item">
              <span className="adaptive-interface__detail-label">
                Show Memory:
              </span>
              <span className="adaptive-interface__detail-value">
                {currentPolicy.showMemoryOps ? 'Yes' : 'No'}
              </span>
            </div>
            
            <div className="adaptive-interface__detail-item">
              <span className="adaptive-interface__detail-label">
                Max History:
              </span>
              <span className="adaptive-interface__detail-value">
                {currentPolicy.maxMessageHistory}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Generate adaptation policy based on expertise level
 */
function generateAdaptationPolicy(expertiseLevel: UserExpertiseLevel): UIAdaptationPolicy {
  const policies: Record<UserExpertiseLevel, UIAdaptationPolicy> = {
    beginner: {
      name: 'Beginner Friendly',
      description: 'Simplified interface with guided assistance',
      simplifiedUI: true,
      guidedMode: true,
      showAdvancedFeatures: false,
      showDebugInfo: false,
      showMemoryOps: false,
      maxMessageHistory: 10,
      enableAnimations: true,
      enableSoundEffects: true,
      enableKeyboardShortcuts: false,
      autoScroll: true,
      markdownSupport: true,
      codeHighlighting: false,
      imagePreview: true
    },
    intermediate: {
      name: 'Standard',
      description: 'Balanced interface with common features',
      simplifiedUI: false,
      guidedMode: false,
      showAdvancedFeatures: false,
      showDebugInfo: false,
      showMemoryOps: true,
      maxMessageHistory: 25,
      enableAnimations: true,
      enableSoundEffects: false,
      enableKeyboardShortcuts: true,
      autoScroll: true,
      markdownSupport: true,
      codeHighlighting: true,
      imagePreview: true
    },
    advanced: {
      name: 'Advanced',
      description: 'Full-featured interface with advanced tools',
      simplifiedUI: false,
      guidedMode: false,
      showAdvancedFeatures: true,
      showDebugInfo: true,
      showMemoryOps: true,
      maxMessageHistory: 50,
      enableAnimations: false,
      enableSoundEffects: false,
      enableKeyboardShortcuts: true,
      autoScroll: false,
      markdownSupport: true,
      codeHighlighting: true,
      imagePreview: true
    },
    expert: {
      name: 'Expert',
      description: 'Power-user interface with all features enabled',
      simplifiedUI: false,
      guidedMode: false,
      showAdvancedFeatures: true,
      showDebugInfo: true,
      showMemoryOps: true,
      maxMessageHistory: 100,
      enableAnimations: false,
      enableSoundEffects: false,
      enableKeyboardShortcuts: true,
      autoScroll: false,
      markdownSupport: true,
      codeHighlighting: true,
      imagePreview: true
    }
  };

  return policies[expertiseLevel];
}

/**
 * Apply adaptations to children based on policy and expertise level
 */
function applyAdaptations(
  children: React.ReactNode,
  _policy: UIAdaptationPolicy,
  _expertiseLevel: UserExpertiseLevel
): React.ReactNode {
  // In a real implementation, this would apply actual transformations to the children
  // For now, we'll just return the children as-is
  
  // This is where you would:
  // 1. Simplify complex UI components if policy.simplifiedUI is true
  // 2. Add guided tooltips if policy.guidedMode is true
  // 3. Hide advanced features if policy.showAdvancedFeatures is false
  // 4. Show/hide debug information based on policy.showDebugInfo
  // 5. Show/hide memory operations based on policy.showMemoryOps
  // 6. Limit message history based on policy.maxMessageHistory
  // 7. Enable/disable animations, sounds, shortcuts, etc.
  
  return children;
}