"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Mic, Volume2, Settings, Robot, Play, Pause } from "lucide-react";

export default function SpeechInterfacePluginPage() {
  return (
    <div className="space-y-8">
      <div className="flex items-center space-x-3">
        <Mic className="h-8 w-8 text-purple-600" />
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">Speech Interface & Voice Control</h2>
          <p className="text-sm text-muted-foreground">
            Comprehensive speech-to-text, text-to-speech, and voice control capabilities with AI-powered voice understanding
          </p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Features</CardTitle>
          <CardDescription>Available speech capabilities</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-start gap-4 p-4 border rounded-lg">
            <Mic className="h-8 w-8 text-blue-500 mt-1" />
            <div>
              <h4 className="font-semibold">Speech-to-Text (STT)</h4>
              <p className="text-sm text-muted-foreground">
                Convert spoken words into text with high accuracy using advanced speech recognition
              </p>
            </div>
          </div>

          <div className="flex items-start gap-4 p-4 border rounded-lg">
            <Volume2 className="h-8 w-8 text-green-500 mt-1" />
            <div>
              <h4 className="font-semibold">Text-to-Speech (TTS)</h4>
              <p className="text-sm text-muted-foreground">
                Convert text to natural-sounding speech with multiple voices and languages
              </p>
            </div>
          </div>

          <div className="flex items-start gap-4 p-4 border rounded-lg">
            <Robot className="h-8 w-8 text-purple-500 mt-1" />
            <div>
              <h4 className="font-semibold">Voice Control</h4>
              <p className="text-sm text-muted-foreground">
                Control the application and interact with Karen using natural voice commands
              </p>
            </div>
          </div>

          <div className="flex items-start gap-4 p-4 border rounded-lg">
            <Settings className="h-8 w-8 text-gray-500 mt-1" />
            <div>
              <h4 className="font-semibold">AI-Powered Voice Understanding</h4>
              <p className="text-sm text-muted-foreground">
                Intelligent voice processing that understands context, emotion, and intent
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Usage</CardTitle>
          <CardDescription>How to use speech features</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground mb-4">
            You can use speech capabilities by enabling microphone access and speaking to Karen.
          </p>
          <Alert>
            <AlertTitle className="text-sm font-semibold">Example Prompts</AlertTitle>
            <AlertDescription className="text-xs">
              <ul className="list-disc list-inside space-y-1">
                <li>"Read this text aloud: Hello world"</li>
                <li>"Speak to me"</li>
                <li>"Stop speaking"</li>
                <li>"Turn up the volume"</li>
              </ul>
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">System Requirements</CardTitle>
          <CardDescription>Requirements for optimal speech functionality</CardDescription>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li className="flex items-center gap-2">
              <Volume2 className="h-4 w-4" />
              Audio output device (speakers or headphones)
            </li>
            <li className="flex items-center gap-2">
              <Mic className="h-4 w-4" />
              Microphone for voice input
            </li>
            <li className="flex items-center gap-2">
              <Settings className="h-4 w-4" />
              Operating system audio permissions
            </li>
            <li className="flex items-center gap-2">
              <Play className="h-4 w-4" />
              Stable internet connection for AI processing
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}