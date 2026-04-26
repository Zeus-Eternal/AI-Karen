import { useState, useEffect, useMemo } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Label } from '@/components/ui/label';
import { Bot, Loader2 } from 'lucide-react';
import { getRuntimeDisplayName, getRuntimeGroupLabel } from '@/lib/chat-response';
import type { ProviderDetails } from '../types';

export type { ProviderDetails };

export const ProviderSettingsModal = ({
  selectableProviders,
  selectedProvider,
  selectedModel,
  applyModelSelection,
  isUpdatingModelSelection
}: {
  selectableProviders: ProviderDetails[];
  selectedProvider: string;
  selectedModel: string;
  applyModelSelection: (providerId: string, modelId: string) => Promise<void>;
  isUpdatingModelSelection: boolean;
}) => {
    const [isOpen, setIsOpen] = useState(false);
    const [localProvider, setLocalProvider] = useState(selectedProvider);
    const [localModel, setLocalModel] = useState(selectedModel);
    
    // Sync local state when modal opens
    useEffect(() => {
      if (isOpen) {
        setLocalProvider(selectedProvider);
        setLocalModel(selectedModel);
      }
    }, [isOpen]);

    const activeProviderDetails = selectableProviders.find(p => p.id === localProvider);
    const providerModels = activeProviderDetails?.models || [];
    const groupedProviders = useMemo(() => {
      const builtInProviders = selectableProviders.filter((provider) => provider.id === 'builtin_vllm');
      const localProviders = selectableProviders.filter((provider) => getRuntimeGroupLabel(provider.id) === 'Local Runtime');
      const thirdPartyProviders = selectableProviders.filter((provider) => getRuntimeGroupLabel(provider.id) === 'External Endpoint');
      const customProviders = selectableProviders.filter((provider) => getRuntimeGroupLabel(provider.id) === 'Custom');
      return { builtInProviders, localProviders, thirdPartyProviders, customProviders };
    }, [selectableProviders]);

    useEffect(() => {
      if (!isOpen || !activeProviderDetails) {
        return;
      }

      setLocalModel(activeProviderDetails.selected_model || activeProviderDetails.models[0]?.id || '');
    }, [isOpen, activeProviderDetails]);

    const handleApply = async () => {
      await applyModelSelection(localProvider, localModel);
      setIsOpen(false);
    };

    return (
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogTrigger asChild>
            <Button
              variant="outline"
              className="flex items-center gap-2 h-9 px-3 border border-input bg-background hover:bg-accent hover:text-accent-foreground font-medium"
            >
              <Bot className="h-4 w-4" />
            MODELS
            </Button>
          </DialogTrigger>
        <DialogContent className="sm:max-w-[850px] gap-0 p-0 overflow-hidden">
          <DialogHeader className="sr-only">
            <DialogTitle>AI Provider Settings</DialogTitle>
            <DialogDescription>
              Configure AI providers, models, and connection settings for Karen.
            </DialogDescription>
          </DialogHeader>
          <div className="flex h-[600px]">
            {/* Sidebar: Provider Selection */}
            <div className="w-[180px] bg-muted/30 border-r border-border p-3 flex flex-col gap-1 overflow-y-auto">
              <div className="text-[10px] uppercase tracking-wider font-bold text-muted-foreground mb-2 px-2">Runtime Providers</div>
              <div className="space-y-2">
                {groupedProviders.builtInProviders.length > 0 && (
                  <div className="space-y-1">
                    <div className="px-2 text-[9px] uppercase tracking-[0.2em] text-muted-foreground">Built-in Runtime</div>
                    {groupedProviders.builtInProviders.map((p) => (
                      <button
                        key={p.id}
                        onClick={() => {
                          setLocalProvider(p.id);
                        }}
                        className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-colors text-left w-full ${
                          localProvider === p.id
                            ? 'bg-primary text-primary-foreground font-medium'
                            : 'hover:bg-muted text-muted-foreground hover:text-foreground'
                        }`}
                      >
                        <Bot className={`h-4 w-4 ${localProvider === p.id ? 'opacity-100' : 'opacity-60'}`} />
                        <span className="truncate">{getRuntimeDisplayName(p.id, p.display_name)}</span>
                      </button>
                    ))}
                  </div>
                )}
                {groupedProviders.localProviders.length > 0 && (
                  <div className="space-y-1">
                    <div className="px-2 text-[9px] uppercase tracking-[0.2em] text-muted-foreground">Local Providers</div>
                    {groupedProviders.localProviders.map((p) => (
                      <button
                        key={p.id}
                        onClick={() => {
                          setLocalProvider(p.id);
                        }}
                        className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-colors text-left w-full ${
                          localProvider === p.id
                            ? 'bg-primary text-primary-foreground font-medium'
                            : 'hover:bg-muted text-muted-foreground hover:text-foreground'
                        }`}
                      >
                        <Bot className={`h-4 w-4 ${localProvider === p.id ? 'opacity-100' : 'opacity-60'}`} />
                        <span className="truncate">{getRuntimeDisplayName(p.id, p.display_name)}</span>
                      </button>
                    ))}
                  </div>
                )}
                {groupedProviders.thirdPartyProviders.length > 0 && (
                  <div className="space-y-1">
                    <div className="px-2 text-[9px] uppercase tracking-[0.2em] text-muted-foreground">Third-Party Providers</div>
                    {groupedProviders.thirdPartyProviders.map((p) => (
                      <button
                        key={p.id}
                        onClick={() => {
                          setLocalProvider(p.id);
                        }}
                        className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-colors text-left w-full ${
                          localProvider === p.id
                            ? 'bg-primary text-primary-foreground font-medium'
                            : 'hover:bg-muted text-muted-foreground hover:text-foreground'
                        }`}
                      >
                        <Bot className={`h-4 w-4 ${localProvider === p.id ? 'opacity-100' : 'opacity-60'}`} />
                        <span className="truncate">{getRuntimeDisplayName(p.id, p.display_name)}</span>
                      </button>
                    ))}
                  </div>
                )}
                {groupedProviders.customProviders.length > 0 && (
                  <div className="space-y-1">
                    <div className="px-2 text-[9px] uppercase tracking-[0.2em] text-muted-foreground">Custom Integrations</div>
                    {groupedProviders.customProviders.map((p) => (
                      <button
                        key={p.id}
                        onClick={() => {
                          setLocalProvider(p.id);
                        }}
                        className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-colors text-left w-full ${
                          localProvider === p.id
                            ? 'bg-primary text-primary-foreground font-medium'
                            : 'hover:bg-muted text-muted-foreground hover:text-foreground'
                        }`}
                      >
                        <Bot className={`h-4 w-4 ${localProvider === p.id ? 'opacity-100' : 'opacity-60'}`} />
                        <span className="truncate">{getRuntimeDisplayName(p.id, p.display_name)}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col min-w-0">
              <DialogHeader className="p-6 pb-2">
                <DialogTitle className="flex items-center gap-2">
                  {getRuntimeDisplayName(activeProviderDetails?.id || '', activeProviderDetails?.display_name || '') || 'Select Runtime'} Models
                </DialogTitle>
                <DialogDescription className="text-xs">
                  Choose from the providers and models already configured in settings.
                </DialogDescription>
              </DialogHeader>

              <ScrollArea className="flex-1 p-6 pt-2">
                <div className="space-y-3">
                  <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Available Models</Label>
                  <div className="grid grid-cols-2 gap-2">
                    {providerModels.map((m) => (
                      <button
                        key={m.id}
                        onClick={() => setLocalModel(m.id)}
                        className={`p-3 rounded-lg border text-left transition-all ${
                          localModel === m.id 
                            ? 'bg-primary/5 border-primary ring-1 ring-primary' 
                            : 'border-border hover:bg-muted/50 hover:border-muted-foreground/30'
                        }`}
                      >
                        <div className="text-sm font-medium leading-tight truncate">{m.name}</div>
                        <div className="text-[10px] text-muted-foreground mt-1 truncate">{m.id}</div>
                      </button>
                    ))}
                    {providerModels.length === 0 && (
                      <div className="col-span-2 py-8 text-center border border-dashed rounded-lg text-muted-foreground text-sm">
                        No configured models found for this provider. Use Application Settings to configure one.
                      </div>
                    )}
                  </div>
                </div>
              </ScrollArea>

              <div className="p-6 pt-4 border-t border-border bg-muted/10 flex justify-end gap-3">
                <Button variant="ghost" onClick={() => setIsOpen(false)} className="h-9">
                  Cancel
                </Button>
                <Button 
                  onClick={handleApply} 
                  disabled={isUpdatingModelSelection || !localModel}
                  className="h-9 min-w-[120px]"
                >
                  {isUpdatingModelSelection ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                  Apply Changes
                </Button>
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    );
  };
