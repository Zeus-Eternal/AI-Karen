import React, { useMemo } from 'react';
import { ExtensionUIComponent, ExtensionUIComponentType, ExtensionUIComponentPosition } from '../../types/extension';
import { useExtensionUI } from '../../hooks/useExtensionUI';

interface ExtensionUIRendererProps {
  /** Position to render components for */
  position: ExtensionUIComponentPosition;
  
  /** Additional props to pass to components */
  additionalProps?: Record<string, any>;
  
  /** CSS class name for container */
  className?: string;
  
  /** Style for container */
  style?: React.CSSProperties;
}

/**
 * Merged props interface for extension UI components
 */
interface MergedExtensionProps {
  key: string;
  'data-extension-component-id': string;
  className?: string;
  label?: string;
  children?: React.ReactNode;
  items?: any[];
  title?: string;
  content?: React.ReactNode;
  footer?: React.ReactNode;
  options?: any[];
  component?: any;
  [key: string]: any;
}

/**
 * Component for rendering extension UI components at a specific position
 */
const ExtensionUIRenderer: React.FC<ExtensionUIRendererProps> = ({
  position,
  additionalProps = {},
  className = '',
  style = {}
}) => {
  const { getComponentsByPosition } = useExtensionUI({
    componentPosition: position
  });
  
  // Get components for this position
  const components = useMemo(() => {
    return getComponentsByPosition(position);
  }, [getComponentsByPosition, position]);
  
  // Render a single component
  const renderComponent = (component: ExtensionUIComponent) => {
    const { id, type, props, visible } = component;
    
    // Skip invisible components
    if (!visible) {
      return null;
    }
    
    // Merge component props with additional props
    const mergedProps: MergedExtensionProps = {
      ...props,
      ...additionalProps,
      key: id,
      'data-extension-component-id': id
    };
    
    // Helper function to filter out custom extension props
    const filterHTMLProps = (props: MergedExtensionProps): any => {
      const { key, 'data-extension-component-id': dataId, items, content, footer, options, component: comp, ...htmlProps } = props;
      return htmlProps;
    };
    
    // Render based on component type
    switch (type) {
      case ExtensionUIComponentType.BUTTON:
        return (
          <button {...filterHTMLProps(mergedProps)} className={`extension-button ${mergedProps.className || ''}`}>
            {mergedProps.label || mergedProps.children || 'Button'}
          </button>
        );
        
      case ExtensionUIComponentType.MENU:
        return (
          <div {...filterHTMLProps(mergedProps)} className={`extension-menu ${mergedProps.className || ''}`}>
            {mergedProps.items?.map((item: any, index: number) => (
              <div key={index} className="extension-menu-item">
                {item.label}
              </div>
            ))}
          </div>
        );
        
      case ExtensionUIComponentType.PANEL:
        return (
          <div {...filterHTMLProps(mergedProps)} className={`extension-panel ${mergedProps.className || ''}`}>
            {mergedProps.title && <div className="extension-panel-title">{mergedProps.title}</div>}
            <div className="extension-panel-content">
              {mergedProps.content || mergedProps.children}
            </div>
          </div>
        );
        
      case ExtensionUIComponentType.MODAL:
        return (
          <div {...filterHTMLProps(mergedProps)} className={`extension-modal ${mergedProps.className || ''}`}>
            <div className="extension-modal-content">
              {mergedProps.title && <div className="extension-modal-title">{mergedProps.title}</div>}
              <div className="extension-modal-body">
                {mergedProps.content || mergedProps.children}
              </div>
              <div className="extension-modal-footer">
                {mergedProps.footer}
              </div>
            </div>
          </div>
        );
        
      case ExtensionUIComponentType.INPUT:
        return (
          <input {...filterHTMLProps(mergedProps)} className={`extension-input ${mergedProps.className || ''}`} />
        );
        
      case ExtensionUIComponentType.SELECT:
        return (
          <select {...filterHTMLProps(mergedProps)} className={`extension-select ${mergedProps.className || ''}`}>
            {mergedProps.options?.map((option: any, index: number) => (
              <option key={index} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        );
        
      case ExtensionUIComponentType.REACT_COMPONENT:
        if (mergedProps.component) {
          const Component = mergedProps.component;
          return <Component {...mergedProps} />;
        }
        return null;
        
      default:
        console.warn(`Unknown extension UI component type: ${type}`);
        return null;
    }
  };
  
  return (
    <div className={`extension-ui-renderer ${className}`} style={style}>
      {components.map(renderComponent)}
    </div>
  );
};

export default ExtensionUIRenderer;
