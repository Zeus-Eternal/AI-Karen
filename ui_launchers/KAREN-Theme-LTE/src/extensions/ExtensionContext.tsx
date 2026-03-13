import React, { createContext, useState, useCallback, ReactNode } from 'react';

export interface Extension {
  id: string;
  name: string;
  version: string;
  description: string;
  enabled: boolean;
  permissions: string[];
  config?: Record<string, unknown>;
}

export interface ExtensionContextType {
  extensions: Extension[];
  activeExtensions: Extension[];
  addExtension: (extension: Extension) => void;
  removeExtension: (extensionId: string) => void;
  enableExtension: (extensionId: string) => void;
  disableExtension: (extensionId: string) => void;
  updateExtension: (extensionId: string, updates: Partial<Extension>) => void;
  isExtensionEnabled: (extensionId: string) => boolean;
  getExtensionById: (extensionId: string) => Extension | undefined;
}

const ExtensionContext = createContext<ExtensionContextType | undefined>(undefined);

export interface ExtensionProviderProps {
  children: ReactNode;
}

export const ExtensionProvider: React.FC<ExtensionProviderProps> = ({ children }) => {
  const [extensions, setExtensions] = useState<Extension[]>([]);

  const addExtension = useCallback((extension: Extension) => {
    setExtensions(prev => [...prev, extension]);
  }, []);

  const removeExtension = useCallback((extensionId: string) => {
    setExtensions(prev => prev.filter(ext => ext.id !== extensionId));
  }, []);

  const enableExtension = useCallback((extensionId: string) => {
    setExtensions(prev => prev.map(ext => 
      ext.id === extensionId ? { ...ext, enabled: true } : ext
    ));
  }, []);

  const disableExtension = useCallback((extensionId: string) => {
    setExtensions(prev => prev.map(ext => 
      ext.id === extensionId ? { ...ext, enabled: false } : ext
    ));
  }, []);

  const updateExtension = useCallback((extensionId: string, updates: Partial<Extension>) => {
    setExtensions(prev => prev.map(ext => 
      ext.id === extensionId ? { ...ext, ...updates } : ext
    ));
  }, []);

  const isExtensionEnabled = useCallback((extensionId: string) => {
    const extension = extensions.find(ext => ext.id === extensionId);
    return extension?.enabled ?? false;
  }, [extensions]);

  const getExtensionById = useCallback((extensionId: string) => {
    return extensions.find(ext => ext.id === extensionId);
  }, [extensions]);

  const activeExtensions = extensions.filter(ext => ext.enabled);

  const contextValue: ExtensionContextType = {
    extensions,
    activeExtensions,
    addExtension,
    removeExtension,
    enableExtension,
    disableExtension,
    updateExtension,
    isExtensionEnabled,
    getExtensionById,
  };

  return (
    <ExtensionContext.Provider value={contextValue}>
      {children}
    </ExtensionContext.Provider>
  );
};

export { ExtensionContext };
