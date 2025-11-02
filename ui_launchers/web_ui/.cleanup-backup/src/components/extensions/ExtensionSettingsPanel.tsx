"use client";

import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Select, SelectTrigger, SelectContent, SelectItem, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { sanitizeInput } from "@/lib/utils";

const schema = z.object({
  refreshInterval: z.number().min(1).max(60),
  enableLogs: z.boolean(),
  logLevel: z.enum(["info", "debug", "error"]),
  endpoint: z.string().url(),
});

type FormValues = z.infer<typeof schema>;

export default function ExtensionSettingsPanel({ onSave }: { onSave?: (v: FormValues) => void }) {
  const { register, control, handleSubmit, watch, setValue, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { refreshInterval: 5, enableLogs: false, logLevel: "info", endpoint: "http://localhost" },
  });
  const { toast } = useToast();
  const refresh = watch("refreshInterval");

  const submit = handleSubmit((vals) => {
    vals.endpoint = sanitizeInput(vals.endpoint);
    onSave?.(vals);
    toast({ title: "Settings saved" });
  });

  return (
    <form onSubmit={submit} className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Extension Settings</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-sm">
          <div className="space-y-1">
            <label className="text-sm font-medium">Refresh Interval ({refresh}m)</label>
            <Slider min={1} max={60} value={[refresh]} onValueChange={(v) => setValue("refreshInterval", v[0])} />
            {errors.refreshInterval && <p className="text-xs text-destructive">Invalid interval</p>}
          </div>
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium">Enable Logs</label>
            <Switch {...register("enableLogs")} />
          </div>
          <div className="space-y-1">
            <label className="text-sm font-medium">Log Level</label>
            <Select value={watch("logLevel")} onValueChange={(val) => setValue("logLevel", val as any)}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="info">Info</SelectItem>
                <SelectItem value="debug">Debug</SelectItem>
                <SelectItem value="error">Error</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1">
            <label className="text-sm font-medium" htmlFor="endpoint">Endpoint</label>
            <Input id="endpoint" {...register("endpoint")}/>
            {errors.endpoint && <p className="text-xs text-destructive">Enter valid URL</p>}
          </div>
        </CardContent>
        <CardFooter className="flex justify-end">
          <Button size="sm" type="submit">Save</Button>
        </CardFooter>
      </Card>
    </form>
  );
}
