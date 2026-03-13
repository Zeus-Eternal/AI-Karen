import { 
  ExtensionUIComponent, 
  ExtensionUIComponentType, 
  ExtensionUIComponentPosition 
} from '../types/extension';
import ExtensionService from './ExtensionService';

/**
 * Service for managing UI components from extensions
 */
class ExtensionUIService {
  private static instance: ExtensionUIService;
  private uiComponents: Map<string, ExtensionUIComponent[]> = new Map();
  private componentListeners: Map<string, ComponentEventListener[]> = new Map();

  private constructor() {
    void ExtensionService.getInstance();
  }

  public static getInstance(): ExtensionUIService {
    if (!ExtensionUIService.instance) {
      ExtensionUIService.instance = new ExtensionUIService();
    }
    return ExtensionUIService.instance;
  }

  /**
   * Register a UI component for an extension
   */
  public registerUIComponent(extensionId: string, component: ExtensionUIComponent): boolean {
    try {
      console.log(`Registering UI component ${component.id} for extension ${extensionId}...`);
      
      // Validate component
      if (!this.validateUIComponent(component)) {
        console.error(`Invalid UI component ${component.id} for extension ${extensionId}`);
        return false;
      }
      
      // Get existing components for extension
      const components = this.uiComponents.get(extensionId) || [];
      
      // Check if component already exists
      const existingIndex = components.findIndex(c => c.id === component.id);
      if (existingIndex !== -1) {
        // Update existing component
        components[existingIndex] = component;
      } else {
        // Add new component
        components.push(component);
      }
      
      // Sort components by order
      components.sort((a, b) => a.order - b.order);
      
      // Update components map
      this.uiComponents.set(extensionId, components);
      
      // Emit component registered event
      this.emitComponentEvent('component_registered', {
        extensionId,
        componentId: component.id,
        component
      });
      
      console.log(`UI component ${component.id} registered for extension ${extensionId}`);
      return true;
    } catch (error) {
      console.error(`Failed to register UI component ${component.id} for extension ${extensionId}:`, error);
      return false;
    }
  }

  /**
   * Unregister a UI component for an extension
   */
  public unregisterUIComponent(extensionId: string, componentId: string): boolean {
    try {
      console.log(`Unregistering UI component ${componentId} for extension ${extensionId}...`);
      
      // Get existing components for extension
      const components = this.uiComponents.get(extensionId) || [];
      
      // Find component index
      const index = components.findIndex(c => c.id === componentId);
      if (index === -1) {
        console.warn(`UI component ${componentId} not found for extension ${extensionId}`);
        return true;
      }
      
      // Remove component
      const removedComponent = components.splice(index, 1)[0];
      
      // Update components map
      this.uiComponents.set(extensionId, components);
      
      // Emit component unregistered event
      this.emitComponentEvent('component_unregistered', {
        extensionId,
        componentId,
        component: removedComponent
      });
      
      console.log(`UI component ${componentId} unregistered for extension ${extensionId}`);
      return true;
    } catch (error) {
      console.error(`Failed to unregister UI component ${componentId} for extension ${extensionId}:`, error);
      return false;
    }
  }

  /**
   * Get all UI components for an extension
   */
  public getUIComponents(extensionId: string): ExtensionUIComponent[] {
    return this.uiComponents.get(extensionId) || [];
  }

  /**
   * Get all UI components for a specific position
   */
  public getUIComponentsByPosition(position: ExtensionUIComponentPosition): ExtensionUIComponent[] {
    const result: ExtensionUIComponent[] = [];
    
    for (const components of this.uiComponents.values()) {
      for (const component of components) {
        if (component.position === position && component.visible) {
          result.push(component);
        }
      }
    }
    
    // Sort by order
    result.sort((a, b) => a.order - b.order);
    
    return result;
  }

  /**
   * Get all UI components for a specific type
   */
  public getUIComponentsByType(type: ExtensionUIComponentType): ExtensionUIComponent[] {
    const result: ExtensionUIComponent[] = [];
    
    for (const components of this.uiComponents.values()) {
      for (const component of components) {
        if (component.type === type && component.visible) {
          result.push(component);
        }
      }
    }
    
    // Sort by order
    result.sort((a, b) => a.order - b.order);
    
    return result;
  }

  /**
   * Update a UI component for an extension
   */
  public updateUIComponent(extensionId: string, componentId: string, updates: Partial<ExtensionUIComponent>): boolean {
    try {
      console.log(`Updating UI component ${componentId} for extension ${extensionId}...`);
      
      // Get existing components for extension
      const components = this.uiComponents.get(extensionId) || [];
      
      // Find component index
      const index = components.findIndex(c => c.id === componentId);
      if (index === -1) {
        console.warn(`UI component ${componentId} not found for extension ${extensionId}`);
        return false;
      }
      
      // Update component
      const oldComponent = components[index];
      if (!oldComponent) {
        console.warn(`UI component ${componentId} not found`);
        return false;
      }

      const newComponent = { ...oldComponent, ...updates };
      
      // Validate updated component
      if (!this.validateUIComponent(newComponent)) {
        console.error(`Invalid UI component update for ${componentId}`);
        return false;
      }
      
      // Update component
      components[index] = newComponent;
      
      // Sort components by order
      components.sort((a, b) => a.order - b.order);
      
      // Update components map
      this.uiComponents.set(extensionId, components);
      
      // Emit component updated event
      this.emitComponentEvent('component_updated', {
        extensionId,
        componentId,
        oldComponent,
        newComponent
      });
      
      console.log(`UI component ${componentId} updated for extension ${extensionId}`);
      return true;
    } catch (error) {
      console.error(`Failed to update UI component ${componentId} for extension ${extensionId}:`, error);
      return false;
    }
  }

  /**
   * Set visibility of a UI component
   */
  public setComponentVisibility(extensionId: string, componentId: string, visible: boolean): boolean {
    return this.updateUIComponent(extensionId, componentId, { visible });
  }

  /**
   * Set order of a UI component
   */
  public setComponentOrder(extensionId: string, componentId: string, order: number): boolean {
    return this.updateUIComponent(extensionId, componentId, { order });
  }

  /**
   * Update props of a UI component
   */
  public updateComponentProps(extensionId: string, componentId: string, props: Record<string, unknown>): boolean {
    return this.updateUIComponent(extensionId, componentId, { props });
  }

  /**
   * Add component event listener
   */
  public addComponentEventListener(eventType: string, listener: ComponentEventListener): void {
    if (!this.componentListeners.has(eventType)) {
      this.componentListeners.set(eventType, []);
    }
    this.componentListeners.get(eventType)?.push(listener);
  }

  /**
   * Remove component event listener
   */
  public removeComponentEventListener(eventType: string, listener: ComponentEventListener): void {
    const listeners = this.componentListeners.get(eventType);
    if (listeners) {
      const index = listeners.indexOf(listener);
      if (index !== -1) {
        listeners.splice(index, 1);
      }
    }
  }

  /**
   * Validate a UI component
   */
  private validateUIComponent(component: ExtensionUIComponent): boolean {
    // Check required fields
    if (!component.id || !component.type || !component.position) {
      return false;
    }
    
    // Check if type is valid
    if (!Object.values(ExtensionUIComponentType).includes(component.type)) {
      return false;
    }
    
    // Check if position is valid
    if (!Object.values(ExtensionUIComponentPosition).includes(component.position)) {
      return false;
    }
    
    // Check if order is a number
    if (typeof component.order !== 'number') {
      return false;
    }
    
    // Check if visible is a boolean
    if (typeof component.visible !== 'boolean') {
      return false;
    }
    
    return true;
  }

  /**
   * Emit component event
   */
  private emitComponentEvent(eventType: string, data: ComponentEventPayload): void {
    const listeners = this.componentListeners.get(eventType);
    if (listeners) {
      listeners.forEach(listener => {
        try {
          listener({
            type: eventType,
            timestamp: new Date(),
            ...data
          });
        } catch (error) {
          console.error(`Error in component event listener for ${eventType}:`, error);
        }
      });
    }
  }

  /**
   * Unregister all UI components for an extension
   */
  public unregisterAllUIComponents(extensionId: string): boolean {
    try {
      console.log(`Unregistering all UI components for extension ${extensionId}...`);
      
      // Get existing components for extension
      const components = this.uiComponents.get(extensionId) || [];
      
      // Remove each component
      for (const component of components) {
        this.unregisterUIComponent(extensionId, component.id);
      }
      
      // Clear components map for extension
      this.uiComponents.delete(extensionId);
      
      console.log(`All UI components unregistered for extension ${extensionId}`);
      return true;
    } catch (error) {
      console.error(`Failed to unregister all UI components for extension ${extensionId}:`, error);
      return false;
    }
  }
}

interface ComponentEvent {
  type: string;
  timestamp: Date;
  [key: string]: unknown;
}

type ComponentEventPayload = Record<string, unknown>;
type ComponentEventListener = (event: ComponentEvent) => void;

export default ExtensionUIService;
