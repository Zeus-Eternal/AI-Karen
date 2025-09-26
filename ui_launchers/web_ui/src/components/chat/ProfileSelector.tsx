"use client";

import React, { useEffect, useState } from "react";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { getKarenBackend } from "@/lib/karen-backend";

type ProfileSummary = { id: string; name: string; is_active: boolean; assignments_count: number; fallback_chain: string[] };

export const ProfileSelector: React.FC = () => {
  const { toast } = useToast();
  const backend = getKarenBackend();
  const [profiles, setProfiles] = useState<ProfileSummary[]>([]);
  const [active, setActive] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [validating, setValidating] = useState(false);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);

  const loadProfiles = async () => {
    setLoading(true);
    try {
      const res = await backend.makeRequestPublic<{ status: string; output: any }>("/api/copilot/start", {
        method: "POST",
        body: JSON.stringify({ action: "routing.profile.list", payload: {} }),
      });
      const out = (res as any)?.output || {};
      setProfiles(out.profiles || []);
      setActive(out.active_profile || "");
    } catch (e) {
      toast({ variant: "destructive", title: "Failed to load profiles" });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProfiles();
  }, []);

  const onChangeProfile = async (pid: string) => {
    try {
      const res = await backend.makeRequestPublic<{ status: string; output: any }>("/api/copilot/start", {
        method: "POST",
        body: JSON.stringify({ action: "routing.profile.set", payload: { profile_id: pid } }),
      });
      const out = (res as any)?.output || {};
      if (out.ok) {
        setActive(pid);
        toast({ title: "Profile switched", description: pid });
        validateProfile(pid);
      } else {
        throw new Error(out.error || "Profile switch failed");
      }
    } catch (e: any) {
      toast({ variant: "destructive", title: "Profile switch failed", description: e?.message });
    }
  };

  const validateProfile = async (pid?: string) => {
    setValidating(true);
    setValidationErrors([]);
    try {
      const res = await backend.makeRequestPublic<{ status: string; output: any }>("/api/copilot/start", {
        method: "POST",
        body: JSON.stringify({ action: "routing.profile.validate", payload: { profile_id: pid } }),
      });
      const out = (res as any)?.output || {};
      if (out.ok) {
        toast({ title: "Profile valid" });
      } else {
        setValidationErrors(out.errors || ["Invalid profile"]);
        toast({ variant: "destructive", title: "Profile validation failed" });
      }
    } catch (e) {
      toast({ variant: "destructive", title: "Validation error" });
    } finally {
      setValidating(false);
    }
  };

  const exportProfiles = async () => {
    try {
      const res = await backend.makeRequestPublic<{ status: string; output: any }>("/api/copilot/start", {
        method: "POST",
        body: JSON.stringify({ action: "routing.profile.export", payload: {} }),
      });
      const out = (res as any)?.output || {};
      const blob = new Blob([JSON.stringify(out.data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `profiles-${new Date().toISOString().split("T")[0]}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      toast({ variant: "destructive", title: "Export failed" });
    }
  };

  const importProfiles = async (file: File) => {
    try {
      const text = await file.text();
      const data = JSON.parse(text);
      const res = await backend.makeRequestPublic<{ status: string; output: any }>("/api/copilot/start", {
        method: "POST",
        body: JSON.stringify({ action: "routing.profile.import", payload: { data } }),
      });
      const out = (res as any)?.output || {};
      if (out.ok) {
        toast({ title: "Profiles imported" });
        loadProfiles();
      } else {
        throw new Error(out.error || "Import failed");
      }
    } catch (e: any) {
      toast({ variant: "destructive", title: "Import failed", description: e?.message });
    }
  };

  return (
    <div className="flex items-center gap-2 flex-wrap">
      <div className="flex items-center gap-2">
        <span className="text-xs text-muted-foreground">Profile</span>
        <Select value={active} onValueChange={onChangeProfile} disabled={loading}>
          <SelectTrigger className="h-8 w-56">
            <SelectValue placeholder={loading ? "Loading..." : active || "Select profile"} />
          </SelectTrigger>
          <SelectContent>
            {profiles.map((p) => (
              <SelectItem key={p.id} value={p.id}>
                <div className="flex items-center gap-2">
                  <span>{p.name}</span>
                  {p.is_active && <Badge variant="secondary">active</Badge>}
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button size="sm" variant="outline" onClick={() => validateProfile(active || undefined)} disabled={validating}>
          Validate
        </Button>
      </div>
      <div className="flex items-center gap-2">
        <Button size="sm" variant="ghost" onClick={exportProfiles}>Export</Button>
        <label className="text-xs cursor-pointer">
          <input type="file" accept="application/json" className="hidden" onChange={(e) => e.target.files && e.target.files[0] && importProfiles(e.target.files[0])} />
          <span className="underline">Import</span>
        </label>
      </div>
      {validationErrors.length > 0 && (
        <div className="text-xs text-red-500">
          {validationErrors.join("; ")}
        </div>
      )}
    </div>
  );
};

export default ProfileSelector;
