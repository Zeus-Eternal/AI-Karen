'use client';

/**
 * @file ApiKeyManager.tsx
 * @description Live-backed provider credential manager.
 *
 * Credential ownership:
 * - Backend owns secret storage, encryption, redaction, validation, audit, and RBAC.
 * - UI only submits new secret values and displays backend-provided configured status.
 * - Saved API keys are never fetched back into the browser.
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  AlertCircle,
  CheckCircle2,
  Eye,
  EyeOff,
  KeyRound,
  Loader2,
  RefreshCw,
  Save,
  Trash2,
  XCircle,
} from 'lucide-react';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ApiError, apiClient } from '@/lib/api';

type CredentialProvider = {
  id: string;
  display_name: string;
  description?: string;
  requires_api_key?: boolean;
  api_key_configured?: boolean;
  enabled?: boolean;
  provider_type?: string;
  key_hint?: string | null;
  last_updated?: string | null;
  validation_status?: 'valid' | 'invalid' | 'unknown' | string;
  validation_error?: string | null;
};

type CredentialStatusResponse = {
  providers?: CredentialProvider[];
  credentials?: CredentialProvider[];
  items?: CredentialProvider[];
};

type SecretInputState = Record<string, string>;
type VisibilityState = Record<string, boolean>;
type BusyState = Record<string, boolean>;

const CREDENTIAL_STATUS_ENDPOINT = '/api/settings/credentials';
const CREDENTIAL_SAVE_ENDPOINT = '/api/settings/credentials';
const CREDENTIAL_DELETE_ENDPOINT = '/api/settings/credentials';

const cleanString = (value: unknown): string => {
  return typeof value === 'string' ? value.trim() : '';
};

const getErrorMessage = (
  error: unknown,
  fallback = 'Credential request failed.',
): string => {
  if (error instanceof ApiError && error.message.trim()) {
    return error.message.trim();
  }

  if (error instanceof Error && error.message.trim()) {
    return error.message.trim();
  }

  if (typeof error === 'string' && error.trim()) {
    return error.trim();
  }

  return fallback;
};

const isUnavailableError = (error: unknown): boolean => {
  return (
    error instanceof ApiError &&
    (error.status === 404 || error.status === 405 || error.status === 501)
  );
};

const extractProviders = (response: CredentialStatusResponse | CredentialProvider[]): CredentialProvider[] => {
  if (Array.isArray(response)) {
    return response;
  }

  return response.providers || response.credentials || response.items || [];
};

const getProviderLabel = (provider: CredentialProvider): string => {
  return cleanString(provider.display_name) || cleanString(provider.id) || 'Unknown provider';
};

const getSafeDateLabel = (value: unknown): string => {
  const raw = cleanString(value);

  if (!raw) {
    return '';
  }

  const parsed = new Date(raw);

  if (Number.isNaN(parsed.getTime())) {
    return raw;
  }

  return parsed.toLocaleString();
};

const getValidationBadge = (provider: CredentialProvider) => {
  const status = cleanString(provider.validation_status).toLowerCase();

  if (status === 'valid') {
    return (
      <Badge variant="outline" className="border-green-500/30 bg-green-500/10 text-green-600 dark:text-green-400">
        <CheckCircle2 className="mr-1 h-3 w-3" aria-hidden="true" />
        Valid
      </Badge>
    );
  }

  if (status === 'invalid') {
    return (
      <Badge variant="outline" className="border-red-500/30 bg-red-500/10 text-red-600 dark:text-red-400">
        <XCircle className="mr-1 h-3 w-3" aria-hidden="true" />
        Invalid
      </Badge>
    );
  }

  return (
    <Badge variant="outline" className="border-muted-foreground/20 bg-muted/30 text-muted-foreground">
      Unknown
    </Badge>
  );
};

export default function ApiKeyManager() {
  const [providers, setProviders] = useState<CredentialProvider[]>([]);
  const [secretInputs, setSecretInputs] = useState<SecretInputState>({});
  const [visibleInputs, setVisibleInputs] = useState<VisibilityState>({});
  const [savingProviders, setSavingProviders] = useState<BusyState>({});
  const [clearingProviders, setClearingProviders] = useState<BusyState>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isCredentialApiAvailable, setIsCredentialApiAvailable] = useState(true);
  const [loadError, setLoadError] = useState('');

  const configurableProviders = useMemo(() => {
    return providers.filter((provider) => provider.requires_api_key !== false);
  }, [providers]);

  const loadCredentialStatus = useCallback(async () => {
    setIsLoading(true);
    setLoadError('');

    try {
      const response = await apiClient.get<CredentialStatusResponse | CredentialProvider[]>(
        CREDENTIAL_STATUS_ENDPOINT,
      );

      setProviders(extractProviders(response));
      setIsCredentialApiAvailable(true);
    } catch (error) {
      setProviders([]);

      if (isUnavailableError(error)) {
        setIsCredentialApiAvailable(false);
        setLoadError('Credential management backend is not available yet.');
      } else {
        setIsCredentialApiAvailable(true);
        setLoadError(getErrorMessage(error, 'Karen could not load credential status.'));
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadCredentialStatus();
  }, [loadCredentialStatus]);

  const updateSecretInput = useCallback((providerId: string, value: string) => {
    setSecretInputs((current) => ({
      ...current,
      [providerId]: value,
    }));
  }, []);

  const toggleVisibility = useCallback((providerId: string) => {
    setVisibleInputs((current) => ({
      ...current,
      [providerId]: !current[providerId],
    }));
  }, []);

  const handleSaveCredential = useCallback(
    async (provider: CredentialProvider) => {
      const providerId = cleanString(provider.id);
      const secret = cleanString(secretInputs[providerId]);

      if (!providerId || !secret) {
        return;
      }

      setSavingProviders((current) => ({ ...current, [providerId]: true }));

      try {
        await apiClient.put(`${CREDENTIAL_SAVE_ENDPOINT}/${encodeURIComponent(providerId)}`, {
          api_key: secret,
        });

        setSecretInputs((current) => ({
          ...current,
          [providerId]: '',
        }));

        await loadCredentialStatus();
      } catch (error) {
        setLoadError(getErrorMessage(error, `Could not save key for ${getProviderLabel(provider)}.`));
      } finally {
        setSavingProviders((current) => {
          const next = { ...current };
          delete next[providerId];
          return next;
        });
      }
    },
    [loadCredentialStatus, secretInputs],
  );

  const handleClearCredential = useCallback(
    async (provider: CredentialProvider) => {
      const providerId = cleanString(provider.id);

      if (!providerId) {
        return;
      }

      setClearingProviders((current) => ({ ...current, [providerId]: true }));

      try {
        await apiClient.delete(`${CREDENTIAL_DELETE_ENDPOINT}/${encodeURIComponent(providerId)}`);
        await loadCredentialStatus();
      } catch (error) {
        setLoadError(getErrorMessage(error, `Could not clear key for ${getProviderLabel(provider)}.`));
      } finally {
        setClearingProviders((current) => {
          const next = { ...current };
          delete next[providerId];
          return next;
        });
      }
    },
    [loadCredentialStatus],
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <KeyRound className="h-5 w-5 text-primary" aria-hidden="true" />
          Provider API Keys
        </CardTitle>
        <CardDescription>
          Manage external provider credentials through Karen&apos;s backend. Saved keys are redacted and never returned to the browser.
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-5">
        {!isCredentialApiAvailable && (
          <Alert className="border-amber-500/30 bg-amber-500/10">
            <AlertCircle className="h-4 w-4 !text-amber-600" aria-hidden="true" />
            <AlertTitle>Credential Backend Unavailable</AlertTitle>
            <AlertDescription>
              Karen does not currently expose a live credential management endpoint. No fake key form is being shown.
            </AlertDescription>
          </Alert>
        )}

        {loadError && isCredentialApiAvailable && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" aria-hidden="true" />
            <AlertTitle>Credential Status Error</AlertTitle>
            <AlertDescription>{loadError}</AlertDescription>
          </Alert>
        )}

        <Alert variant="default" className="bg-background">
          <AlertCircle className="h-4 w-4" aria-hidden="true" />
          <AlertTitle className="text-sm font-semibold">Secret Handling</AlertTitle>
          <AlertDescription className="text-xs text-muted-foreground">
            Enter a new key to replace the backend-stored credential. Existing keys are shown only as configured status or backend-provided hints.
          </AlertDescription>
        </Alert>

        <div className="flex justify-end">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => void loadCredentialStatus()}
            disabled={isLoading}
          >
            {isLoading ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />
            ) : (
              <RefreshCw className="mr-2 h-4 w-4" aria-hidden="true" />
            )}
            Refresh Status
          </Button>
        </div>

        {isLoading ? (
          <div className="flex items-center gap-2 rounded-xl border border-border/70 p-4 text-sm text-muted-foreground" role="status" aria-live="polite">
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
            Loading provider credential status.
          </div>
        ) : configurableProviders.length > 0 ? (
          <div className="space-y-4">
            {configurableProviders.map((provider) => {
              const providerId = cleanString(provider.id);
              const label = getProviderLabel(provider);
              const configured = Boolean(provider.api_key_configured);
              const isSaving = Boolean(savingProviders[providerId]);
              const isClearing = Boolean(clearingProviders[providerId]);
              const secretValue = secretInputs[providerId] || '';
              const isVisible = Boolean(visibleInputs[providerId]);
              const updatedLabel = getSafeDateLabel(provider.last_updated);

              return (
                <div
                  key={providerId}
                  className="rounded-xl border border-border/70 p-4"
                >
                  <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                    <div className="space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="font-semibold">{label}</h3>
                        {configured ? (
                          <Badge variant="outline" className="border-green-500/30 bg-green-500/10 text-green-600 dark:text-green-400">
                            Configured
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="border-muted-foreground/20 bg-muted/30 text-muted-foreground">
                            Not configured
                          </Badge>
                        )}
                        {getValidationBadge(provider)}
                      </div>

                      {provider.description && (
                        <p className="text-xs text-muted-foreground">
                          {provider.description}
                        </p>
                      )}

                      {provider.key_hint && (
                        <p className="text-xs text-muted-foreground">
                          Key hint: <span className="font-mono">{provider.key_hint}</span>
                        </p>
                      )}

                      {updatedLabel && (
                        <p className="text-xs text-muted-foreground">
                          Last updated: {updatedLabel}
                        </p>
                      )}

                      {provider.validation_error && (
                        <p className="text-xs text-destructive">
                          {provider.validation_error}
                        </p>
                      )}
                    </div>

                    <div className="w-full space-y-2 md:max-w-md">
                      <Label htmlFor={`api-key-${providerId}`}>
                        New API key
                      </Label>
                      <div className="flex gap-2">
                        <Input
                          id={`api-key-${providerId}`}
                          type={isVisible ? 'text' : 'password'}
                          value={secretValue}
                          onChange={(event) =>
                            updateSecretInput(providerId, event.target.value)
                          }
                          placeholder={configured ? 'Enter replacement key' : 'Enter API key'}
                          autoComplete="off"
                        />

                        <Button
                          type="button"
                          variant="outline"
                          size="icon"
                          onClick={() => toggleVisibility(providerId)}
                          aria-label={isVisible ? 'Hide API key' : 'Show API key'}
                        >
                          {isVisible ? (
                            <EyeOff className="h-4 w-4" aria-hidden="true" />
                          ) : (
                            <Eye className="h-4 w-4" aria-hidden="true" />
                          )}
                        </Button>
                      </div>

                      <div className="flex flex-wrap justify-end gap-2">
                        <Button
                          type="button"
                          onClick={() => void handleSaveCredential(provider)}
                          disabled={!secretValue.trim() || isSaving || isClearing}
                        >
                          {isSaving ? (
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />
                          ) : (
                            <Save className="mr-2 h-4 w-4" aria-hidden="true" />
                          )}
                          Save Key
                        </Button>

                        <Button
                          type="button"
                          variant="outline"
                          onClick={() => void handleClearCredential(provider)}
                          disabled={!configured || isSaving || isClearing}
                        >
                          {isClearing ? (
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />
                          ) : (
                            <Trash2 className="mr-2 h-4 w-4" aria-hidden="true" />
                          )}
                          Clear Key
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : isCredentialApiAvailable ? (
          <div className="rounded-xl border border-border/70 p-4 text-sm text-muted-foreground">
            No API-key-backed providers were returned by the backend credential registry.
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}