"use client";

import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Volume2 } from "lucide-react";

interface VoiceProvider {
  id: string;
  name: string;
  previewText?: string;
}

export default function VoiceProviderList() {
  const [providers, setProviders] = useState<VoiceProvider[]>([]);

  useEffect(() => {
    // Placeholder providers. Real implementation would detect installed voices or fetch from backend
    setProviders([
      { id: "system", name: "System Voices", previewText: "Hello from your system" },
    ]);
  }, []);

  const handlePreview = (text: string) => {
    if (typeof window !== "undefined" && window.speechSynthesis) {
      const utterance = new SpeechSynthesisUtterance(text);
      window.speechSynthesis.speak(utterance);
    }
  };

  return (
    <div className="space-y-4">
      {providers.map((p) => (
        <Card key={p.id}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm flex items-center gap-1 md:text-base lg:text-lg">
              <Volume2 className="h-4 w-4 sm:w-auto md:w-full" /> {p.name}
            </CardTitle>
          </CardHeader>
          {p.previewText && (
            <CardContent>
              <button size="sm" variant="outline" onClick={() = aria-label="Button"> p.previewText && handlePreview(p.previewText)}>
                Preview Voice
              </Button>
            </CardContent>
          )}
        </Card>
      ))}
    </div>
  );
}
