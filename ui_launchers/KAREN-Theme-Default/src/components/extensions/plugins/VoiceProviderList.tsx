"use client";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Volume2 } from "lucide-react";

interface VoiceProvider {
  id: string;
  name: string;
  previewText?: string;
}

const DEFAULT_VOICE_PROVIDERS: VoiceProvider[] = [
  { id: "system", name: "System Voices", previewText: "Hello from your system" },
];

export default function VoiceProviderList() {
  const providers = DEFAULT_VOICE_PROVIDERS;

  const handlePreview = (text?: string) => {
    if (!text) return;

    if (typeof window === "undefined" || !window.speechSynthesis) {
      return;
    }

    const utterance = new SpeechSynthesisUtterance(text);
    setPreviewing(text);
    utterance.onend = () => setPreviewing(null);
    window.speechSynthesis.speak(utterance);
  };

  return (
    <div className="space-y-4">
      {providers.map((p) => (
        <Card key={p.id}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm flex items-center gap-1 md:text-base lg:text-lg">
              <Volume2 className="h-4 w-4 " /> {p.name}
            </CardTitle>
          </CardHeader>
          {p.previewText && (
            <CardContent>
              <Button
                size="sm"
                variant="outline"
                onClick={() => handlePreview(p.previewText)}
                className="flex items-center gap-1"
                disabled={previewing === p.previewText}
              >
                {previewing === p.previewText ? "Playing" : "Preview"}
              </Button>
            </CardContent>
          )}
        </Card>
      ))}
    </div>
  );
}
