"use client";

import { useEffect, useMemo, useState } from "react";
import { apiClient, ApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { useToast } from "@/hooks/use-toast";
import { AlertCircle, FileDown, FileWarning, Info, Loader2, ShieldAlert, ShieldCheck, Trash2 } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "../ui/alert";

type PrivacyHealth = {
  status: string;
  service: string;
  features: Record<string, boolean>;
  timestamp: string;
};

type PrivacyRequestResponse = {
  request_id: string;
  status: string;
  verification_token: string;
  estimated_completion: string;
  next_steps: string;
};

type PrivacyRequestStatusResponse = {
  request_id: string;
  status: string;
  created_at: string;
  completed_at?: string | null;
  progress: Record<string, unknown>;
};

function splitCsv(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof ApiError) {
    return error.message;
  }
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return fallback;
}

export default function PrivacySettings() {
  const { toast } = useToast();
  const [health, setHealth] = useState<PrivacyHealth | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [isLoadingHealth, setIsLoadingHealth] = useState(true);

  const [userId, setUserId] = useState("");
  const [tenantId, setTenantId] = useState("");
  const [dataTypes, setDataTypes] = useState("all");
  const [exportFormat, setExportFormat] = useState("json");
  const [confirmationToken, setConfirmationToken] = useState("");
  const [requestId, setRequestId] = useState("");
  const [verificationToken, setVerificationToken] = useState("");
  const [erasureType, setErasureType] = useState("soft_delete");

  const [isSubmittingExport, setIsSubmittingExport] = useState(false);
  const [isSubmittingErasure, setIsSubmittingErasure] = useState(false);
  const [isLoadingStatus, setIsLoadingStatus] = useState(false);
  const [isProcessingRequest, setIsProcessingRequest] = useState(false);

  const [exportAccessDenied, setExportAccessDenied] = useState(false);
  const [erasureAccessDenied, setErasureAccessDenied] = useState(false);
  const [statusAccessDenied, setStatusAccessDenied] = useState(false);
  const [processAccessDenied, setProcessAccessDenied] = useState(false);
  const [authRequired, setAuthRequired] = useState(false);

  const [lastRequest, setLastRequest] = useState<PrivacyRequestResponse | null>(null);
  const [requestStatus, setRequestStatus] = useState<PrivacyRequestStatusResponse | null>(null);

  useEffect(() => {
    let mounted = true;

    const loadHealth = async () => {
      setIsLoadingHealth(true);
      try {
        const response = await apiClient.get<PrivacyHealth>("/api/privacy/health");
        if (!mounted) {
          return;
        }
        setHealth(response);
        setAuthRequired(false);
        setHealthError(null);
      } catch (error) {
        if (!mounted) {
          return;
        }
        setHealth(null);
        if (error instanceof ApiError && error.status === 401) {
          setAuthRequired(true);
          setHealthError(null);
        } else {
          setAuthRequired(false);
          setHealthError(getErrorMessage(error, "Karen could not load privacy service health."));
        }
      } finally {
        if (mounted) {
          setIsLoadingHealth(false);
        }
      }
    };

    void loadHealth();
    return () => {
      mounted = false;
    };
  }, []);

  const parsedDataTypes = useMemo(() => splitCsv(dataTypes), [dataTypes]);

  const handleRequestExport = async () => {
    setIsSubmittingExport(true);
    setAuthRequired(false);
    setExportAccessDenied(false);
    try {
      const response = await apiClient.post<PrivacyRequestResponse>("/api/privacy/export/request", {
        user_id: userId.trim(),
        tenant_id: tenantId.trim() || null,
        data_types: parsedDataTypes.length > 0 ? parsedDataTypes : ["all"],
        export_format: exportFormat,
        include_pii: false,
      });
      setLastRequest(response);
      setRequestId(response.request_id);
      setVerificationToken(response.verification_token);
      toast({
        title: "Export request created",
        description: `Privacy request ${response.request_id} is now pending backend processing.`,
      });
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        setAuthRequired(true);
        return;
      }
      if (error instanceof ApiError && error.status === 403) {
        setExportAccessDenied(true);
        return;
      }
      toast({
        title: "Export request failed",
        description: getErrorMessage(error, "Karen could not submit the privacy export request."),
        variant: "destructive",
      });
    } finally {
      setIsSubmittingExport(false);
    }
  };

  const handleRequestErasure = async () => {
    setIsSubmittingErasure(true);
    setAuthRequired(false);
    setErasureAccessDenied(false);
    try {
      const response = await apiClient.post<PrivacyRequestResponse>("/api/privacy/erasure/request", {
        user_id: userId.trim(),
        tenant_id: tenantId.trim() || null,
        erasure_type: erasureType,
        data_types: parsedDataTypes.length > 0 ? parsedDataTypes : ["all"],
        confirmation_token: confirmationToken.trim(),
      });
      setLastRequest(response);
      setRequestId(response.request_id);
      setVerificationToken(response.verification_token);
      toast({
        title: "Erasure request created",
        description: `Privacy request ${response.request_id} is awaiting verification and processing.`,
      });
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        setAuthRequired(true);
        return;
      }
      if (error instanceof ApiError && error.status === 403) {
        setErasureAccessDenied(true);
        return;
      }
      toast({
        title: "Erasure request failed",
        description: getErrorMessage(error, "Karen could not submit the privacy erasure request."),
        variant: "destructive",
      });
    } finally {
      setIsSubmittingErasure(false);
    }
  };

  const handleLookupStatus = async () => {
    if (!requestId.trim()) {
      return;
    }
    setIsLoadingStatus(true);
    setAuthRequired(false);
    setStatusAccessDenied(false);
    try {
      const response = await apiClient.get<PrivacyRequestStatusResponse>(`/api/privacy/request/${requestId.trim()}/status`);
      setRequestStatus(response);
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        setAuthRequired(true);
        return;
      }
      if (error instanceof ApiError && error.status === 403) {
        setStatusAccessDenied(true);
        return;
      }
      toast({
        title: "Status lookup failed",
        description: getErrorMessage(error, "Karen could not retrieve the privacy request status."),
        variant: "destructive",
      });
    } finally {
      setIsLoadingStatus(false);
    }
  };

  const handleProcessRequest = async () => {
    if (!requestId.trim() || !verificationToken.trim()) {
      return;
    }
    setIsProcessingRequest(true);
    setAuthRequired(false);
    setProcessAccessDenied(false);
    try {
      await apiClient.post(`/api/privacy/request/${requestId.trim()}/process?verification_token=${encodeURIComponent(verificationToken.trim())}`, {});
      toast({
        title: "Privacy request processed",
        description: `Karen submitted ${requestId.trim()} for backend privacy processing.`,
      });
      await handleLookupStatus();
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        setAuthRequired(true);
        return;
      }
      if (error instanceof ApiError && error.status === 403) {
        setProcessAccessDenied(true);
        return;
      }
      toast({
        title: "Privacy processing failed",
        description: getErrorMessage(error, "Karen could not process the privacy request."),
        variant: "destructive",
      });
    } finally {
      setIsProcessingRequest(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Privacy & Data Control</CardTitle>
        <CardDescription>
          Review local browser storage, check privacy service health, and submit governed export or erasure requests through Karen&apos;s backend.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {authRequired && (
          <Alert className="border-primary/20 bg-primary/5">
            <ShieldAlert className="h-4 w-4 !text-primary" />
            <AlertTitle>Sign In Required</AlertTitle>
            <AlertDescription>
              Karen&apos;s privacy workflows are live, but this session is not authenticated. Sign in before requesting export, erasure, or request processing.
            </AlertDescription>
          </Alert>
        )}
        <Alert variant="default" className="bg-background border-border">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle className="font-semibold text-sm">Local Browser Storage</AlertTitle>
          <AlertDescription className="text-xs text-muted-foreground space-y-1">
            <p>Karen still stores convenience settings in this browser, but privacy export and erasure workflows are now backend-governed.</p>
            <ul className="list-disc list-inside pl-4">
              <li><strong>Local settings:</strong> behavior, persona, facts, voice, alerts, and convenience-filled provider forms.</li>
              <li><strong>Backend privacy controls:</strong> export requests, erasure requests, audit-backed processing, and privacy request status.</li>
            </ul>
          </AlertDescription>
        </Alert>

        <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
          <Card className="border-border/70">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <ShieldCheck className="h-5 w-5 text-primary" />
                Privacy Service Status
              </CardTitle>
              <CardDescription>Backend-derived privacy capabilities for export, erasure, and content sanitization.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {isLoadingHealth ? (
                <div className="flex items-center gap-2 rounded-xl border border-border/70 p-4 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Loading privacy service status.
                </div>
              ) : health ? (
                <>
                  <div className="flex items-center justify-between rounded-xl border border-border/70 p-4">
                    <div>
                      <div className="font-medium">Service</div>
                      <div className="text-sm text-muted-foreground">{health.service}</div>
                    </div>
                    <div className="text-sm font-medium">{health.status}</div>
                  </div>
                  <div className="grid gap-3 md:grid-cols-2">
                    {Object.entries(health.features).map(([feature, enabled]) => (
                      <div key={feature} className="rounded-xl border border-border/70 p-4 text-sm">
                        <div className="font-medium">{feature.replace(/_/g, " ")}</div>
                        <div className="mt-1 text-muted-foreground">{enabled ? "Enabled" : "Disabled"}</div>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <Alert className="border-yellow-500/30 bg-yellow-500/5">
                  <Info className="h-4 w-4 !text-yellow-600" />
                  <AlertTitle>Privacy Service Unavailable</AlertTitle>
                  <AlertDescription>{healthError || "Karen could not confirm the privacy backend state."}</AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>

          <Card className="border-border/70">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Info className="h-5 w-5 text-primary" />
                Request Context
              </CardTitle>
              <CardDescription>Scope the privacy request to the correct user and tenant before calling the backend.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-2">
                <Label htmlFor="privacy-user-id">User ID</Label>
                <Input id="privacy-user-id" value={userId} onChange={(event) => setUserId(event.target.value)} placeholder="user_123" />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="privacy-tenant-id">Tenant ID</Label>
                <Input id="privacy-tenant-id" value={tenantId} onChange={(event) => setTenantId(event.target.value)} placeholder="tenant_abc" />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="privacy-data-types">Data types</Label>
                <Input
                  id="privacy-data-types"
                  value={dataTypes}
                  onChange={(event) => setDataTypes(event.target.value)}
                  placeholder="all or memories,conversations,audit_logs"
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="privacy-export-format">Export format</Label>
                <Input
                  id="privacy-export-format"
                  value={exportFormat}
                  onChange={(event) => setExportFormat(event.target.value)}
                  placeholder="json"
                />
              </div>
            </CardContent>
          </Card>
        </div>

        <Separator />

        <div className="grid gap-6 xl:grid-cols-2">
          <Card className="border-border/70">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <FileDown className="h-5 w-5 text-primary" />
                Data Export Request
              </CardTitle>
              <CardDescription>Create a governed backend export request instead of relying on conceptual UI-only guidance.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {exportAccessDenied && (
                <Alert className="border-primary/20 bg-primary/5">
                  <ShieldAlert className="h-4 w-4 !text-primary" />
                  <AlertTitle>Export Access Restricted</AlertTitle>
                  <AlertDescription>This session does not have permission to create privacy export requests.</AlertDescription>
                </Alert>
              )}
              <Button onClick={() => void handleRequestExport()} disabled={isSubmittingExport || !userId.trim()}>
                {isSubmittingExport ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <FileDown className="mr-2 h-4 w-4" />}
                Request Data Export
              </Button>
            </CardContent>
          </Card>

          <Card className="border-border/70">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Trash2 className="h-5 w-5 text-primary" />
                Data Erasure Request
              </CardTitle>
              <CardDescription>Submit backend erasure requests with explicit erasure mode and confirmation token.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {erasureAccessDenied && (
                <Alert className="border-primary/20 bg-primary/5">
                  <ShieldAlert className="h-4 w-4 !text-primary" />
                  <AlertTitle>Erasure Access Restricted</AlertTitle>
                  <AlertDescription>This session does not have permission to create privacy erasure requests.</AlertDescription>
                </Alert>
              )}
              <div className="grid gap-2">
                <Label htmlFor="erasure-type">Erasure type</Label>
                <Input id="erasure-type" value={erasureType} onChange={(event) => setErasureType(event.target.value)} placeholder="soft_delete" />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="confirmation-token">Confirmation token</Label>
                <Input
                  id="confirmation-token"
                  value={confirmationToken}
                  onChange={(event) => setConfirmationToken(event.target.value)}
                  placeholder="required for erasure requests"
                />
              </div>
              <Button
                variant="outline"
                onClick={() => void handleRequestErasure()}
                disabled={isSubmittingErasure || !userId.trim() || !confirmationToken.trim()}
              >
                {isSubmittingErasure ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <FileWarning className="mr-2 h-4 w-4" />}
                Request Data Erasure
              </Button>
            </CardContent>
          </Card>
        </div>

        {lastRequest && (
          <Card className="border-border/70 bg-muted/20">
            <CardHeader>
              <CardTitle className="text-base">Latest Privacy Request</CardTitle>
              <CardDescription>Backend-issued identifiers and verification data for the most recent request.</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-2 text-sm">
              <div><strong>Request ID:</strong> {lastRequest.request_id}</div>
              <div><strong>Status:</strong> {lastRequest.status}</div>
              <div><strong>Verification token:</strong> {lastRequest.verification_token}</div>
              <div><strong>ETA:</strong> {lastRequest.estimated_completion}</div>
              <div className="text-muted-foreground">{lastRequest.next_steps}</div>
            </CardContent>
          </Card>
        )}

        <Separator />

        <Card className="border-border/70">
          <CardHeader>
            <CardTitle className="text-base">Request Status & Processing</CardTitle>
            <CardDescription>Inspect or process an existing privacy request through the live backend privacy routes.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {(statusAccessDenied || processAccessDenied) && (
              <Alert className="border-primary/20 bg-primary/5">
                <ShieldAlert className="h-4 w-4 !text-primary" />
                <AlertTitle>Privacy Workflow Restricted</AlertTitle>
                <AlertDescription>
                  This session can see the panel, but backend RBAC is restricting privacy request inspection or processing.
                </AlertDescription>
              </Alert>
            )}
            <div className="grid gap-4 md:grid-cols-2">
              <div className="grid gap-2">
                <Label htmlFor="privacy-request-id">Request ID</Label>
                <Input id="privacy-request-id" value={requestId} onChange={(event) => setRequestId(event.target.value)} />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="privacy-verification-token">Verification token</Label>
                <Input
                  id="privacy-verification-token"
                  value={verificationToken}
                  onChange={(event) => setVerificationToken(event.target.value)}
                />
              </div>
            </div>
            <div className="flex flex-wrap gap-3">
              <Button variant="outline" onClick={() => void handleLookupStatus()} disabled={isLoadingStatus || !requestId.trim()}>
                {isLoadingStatus ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Info className="mr-2 h-4 w-4" />}
                Check Request Status
              </Button>
              <Button onClick={() => void handleProcessRequest()} disabled={isProcessingRequest || !requestId.trim() || !verificationToken.trim()}>
                {isProcessingRequest ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <ShieldCheck className="mr-2 h-4 w-4" />}
                Process Verified Request
              </Button>
            </div>
            {requestStatus && (
              <div className="rounded-xl border border-border/70 p-4 text-sm">
                <div><strong>Status:</strong> {requestStatus.status}</div>
                <div><strong>Created:</strong> {new Date(requestStatus.created_at).toLocaleString()}</div>
                <div><strong>Completed:</strong> {requestStatus.completed_at ? new Date(requestStatus.completed_at).toLocaleString() : "Pending"}</div>
                <pre className="mt-3 whitespace-pre-wrap break-words rounded-md bg-muted/40 p-3 text-xs">
{JSON.stringify(requestStatus.progress, null, 2)}
                </pre>
              </div>
            )}
          </CardContent>
        </Card>
      </CardContent>
    </Card>
  );
}
