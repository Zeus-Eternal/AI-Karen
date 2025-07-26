"use client";

import { useForm } from "react-hook-form";
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Slider } from "@/components/ui/slider";
import { Textarea } from "@/components/ui/textarea";

export interface LLMModelConfig {
  temperature: number;
  maxTokens: number;
  systemPrompt: string;
  apiKey: string;
}

export default function LLMModelConfigPanel({ onSave }: { onSave?: (cfg: LLMModelConfig) => void }) {
  const { register, handleSubmit, watch, setValue } = useForm<LLMModelConfig>({
    defaultValues: { temperature: 0.7, maxTokens: 2048, systemPrompt: "", apiKey: "" },
  });

  const temp = watch("temperature");

  return (
    <form onSubmit={handleSubmit((data) => onSave?.(data))} className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Model Configuration</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-1">
            <Label>Temperature ({temp.toFixed(2)})</Label>
            <Slider
              min={0}
              max={1}
              step={0.01}
              value={[temp]}
              onValueChange={(val) => setValue("temperature", val[0])}
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="maxTokens">Max Tokens</Label>
            <Input id="maxTokens" type="number" {...register("maxTokens", { valueAsNumber: true })} />
          </div>
          <div className="space-y-1">
            <Label htmlFor="systemPrompt">System Prompt</Label>
            <Textarea id="systemPrompt" rows={3} {...register("systemPrompt")} />
          </div>
          <div className="space-y-1">
            <Label htmlFor="apiKey">API Key</Label>
            <Input id="apiKey" type="password" {...register("apiKey")} />
          </div>
        </CardContent>
        <CardFooter className="flex justify-end">
          <Button size="sm" type="submit">Save</Button>
        </CardFooter>
      </Card>
    </form>
  );
}
