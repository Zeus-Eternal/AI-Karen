/**
 * Multi-Modal Service
 *
 * Handles various multi-modal AI providers including:
 * - Image generation (Stable Diffusion, DALL·E, Midjourney)
 * - Image analysis/vision (GPT-4V, Claude Vision)
 * - Audio generation (ElevenLabs, OpenAI TTS)
 * - Video generation (RunwayML, Pika Labs)
 *
 * Features: Karen's intelligent prompt enhancement and provider routing.
 * SSR-safe, production-grade.
 */

import { getKarenBackend } from "./karen-backend";

// ---------------------- Types ----------------------

export type ProviderType =
  | "image-generation"
  | "image-analysis"
  | "audio-generation"
  | "video-generation"
  | "text-to-speech"
  | "speech-to-text";

export interface MultiModalProvider {
  id: string;
  name: string;
  type: ProviderType;
  capabilities: string[];
  status: "available" | "unavailable" | "local" | "api-key-required";
  pricing?: {
    model: "free" | "credits" | "subscription" | "pay-per-use";
    cost?: string;
  };
  limits?: {
    maxResolution?: string;
    maxDuration?: number;
    dailyLimit?: number;
  };
  config?: Record<string, any>;
  health?: {
    lastChecked?: string;
    healthy?: boolean;
    reason?: string;
  };
}

export interface GenerationRequest {
  prompt: string;
  provider?: string;
  type: ProviderType;
  parameters?: {
    // Image generation
    width?: number;
    height?: number;
    steps?: number;
    guidance_scale?: number;
    negative_prompt?: string;
    style?: string;

    // Audio generation
    voice?: string;
    speed?: number;
    pitch?: number;

    // Video generation
    duration?: number;
    fps?: number;

    // General
    quality?: "draft" | "standard" | "high" | "ultra";
    seed?: number;
  };
  enhancePrompt?: boolean;
  timeoutMs?: number;
}

export interface GenerationResult {
  id: string;
  status: "pending" | "processing" | "completed" | "failed";
  provider: string;
  type: ProviderType;
  originalPrompt: string;
  enhancedPrompt?: string;
  result?: {
    url?: string;
    urls?: string[];
    data?: string; // base64 for small files
    metadata?: Record<string, any>;
  };
  error?: string;
  progress?: number;
  estimatedTime?: number;
  createdAt: Date;
  completedAt?: Date;
}

export interface KarenPromptEnhancement {
  originalPrompt: string;
  enhancedPrompt: string;
  improvements: string[];
  confidence: number;
  suggestedProvider?: string;
  suggestedParameters?: Record<string, any>;
}

// Optional telemetry hooks (no-op friendly)
export type Telemetry = {
  track?: (event: string, payload?: Record<string, any>) => void;
};

// ---------------------- Service ----------------------

class MultiModalService {
  private providers: Map<string, MultiModalProvider> = new Map();
  private activeGenerations: Map<string, GenerationResult> = new Map();

  // optional, attach your telemetry later
  private telemetry: Telemetry | null = null;

  private karenPersonality = {
    imageGeneration: {
      stylePreferences: ["cinematic", "detailed", "professional", "artistic"],
      qualityEnhancements: ["high resolution", "8k", "masterpiece", "best quality"],
      technicalTerms: ["depth of field", "perfect lighting", "sharp focus"],
    },
    promptPatterns: {
      photography:
        "professional photography, {prompt}, shot with {camera}, {lighting}, {composition}",
      art: "digital art, {prompt}, {style}, highly detailed, {quality}",
      character:
        "character portrait, {prompt}, {expression}, {background}, {style}",
      landscape:
        "landscape photography, {prompt}, {time_of_day}, {weather}, {composition}",
    },
  };

  constructor() {
    this.initializeProviders();
  }

  // ---------------- Provider Registry ----------------

  private initializeProviders() {
    // Local Stable Diffusion
    this.providers.set("stable-diffusion-local", {
      id: "stable-diffusion-local",
      name: "Stable Diffusion (Local)",
      type: "image-generation",
      capabilities: ["text-to-image", "img2img", "inpainting"],
      status: "local",
      pricing: { model: "free" },
      limits: { maxResolution: "1024x1024" },
    });

    // OpenAI DALL·E 3
    this.providers.set("dalle-3", {
      id: "dalle-3",
      name: "DALL·E 3",
      type: "image-generation",
      capabilities: ["text-to-image", "high-quality"],
      status: "api-key-required",
      pricing: { model: "pay-per-use", cost: "$0.04–0.08 per image" },
      limits: { maxResolution: "1024x1024", dailyLimit: 50 },
    });

    // Midjourney (via API)
    this.providers.set("midjourney", {
      id: "midjourney",
      name: "Midjourney",
      type: "image-generation",
      capabilities: ["text-to-image", "artistic", "high-quality"],
      status: "api-key-required",
      pricing: { model: "subscription" },
      limits: { dailyLimit: 200 },
    });

    // GPT-4 Vision
    this.providers.set("gpt4-vision", {
      id: "gpt4-vision",
      name: "GPT-4 Vision",
      type: "image-analysis",
      capabilities: ["image-to-text", "image-analysis", "ocr"],
      status: "api-key-required",
      pricing: { model: "pay-per-use" },
    });

    // ElevenLabs TTS
    this.providers.set("elevenlabs-tts", {
      id: "elevenlabs-tts",
      name: "ElevenLabs TTS",
      type: "text-to-speech",
      capabilities: ["text-to-speech", "voice-cloning", "multilingual"],
      status: "api-key-required",
      pricing: { model: "credits" },
    });

    // RunwayML Gen-2 Video
    this.providers.set("runway-video", {
      id: "runway-video",
      name: "RunwayML Gen-2",
      type: "video-generation",
      capabilities: ["text-to-video", "img2video"],
      status: "api-key-required",
      pricing: { model: "credits" },
      limits: { maxDuration: 4, maxResolution: "1280x768" },
    });
  }

  registerProvider(provider: MultiModalProvider) {
    this.providers.set(provider.id, provider);
  }

  removeProvider(id: string) {
    this.providers.delete(id);
  }

  updateProvider(id: string, patch: Partial<MultiModalProvider>) {
    const p = this.providers.get(id);
    if (p) this.providers.set(id, { ...p, ...patch });
  }

  getProvider(id: string): MultiModalProvider | undefined {
    return this.providers.get(id);
  }

  getProviders(type?: ProviderType): MultiModalProvider[] {
    const all = Array.from(this.providers.values());
    return type ? all.filter((p) => p.type === type) : all;
  }

  // ---------------- Provider Routing ----------------

  async getBestProvider(request: { prompt: string; type: ProviderType }): Promise<string> {
    const availableProviders = this.getProviders(request.type).filter(
      (p) => p.status === "available" || p.status === "local"
    );

    if (availableProviders.length === 0) {
      throw new Error(`No available providers for ${request.type}`);
    }

    if (request.type === "image-generation") {
      // prefer local first
      const local = availableProviders.find((p) => p.id === "stable-diffusion-local");
      if (local) return local.id;

      if (this.isArtisticPrompt(request.prompt)) {
        const mj = availableProviders.find((p) => p.id === "midjourney");
        if (mj) return mj.id;
      }

      if (this.isPhotorealisticPrompt(request.prompt)) {
        const de = availableProviders.find((p) => p.id === "dalle-3");
        if (de) return de.id;
      }
    }

    return availableProviders[0].id;
  }

  // ---------------- Prompt Enhancement ----------------

  async enhancePrompt(
    prompt: string,
    type: ProviderType,
    provider?: string
  ): Promise<KarenPromptEnhancement> {
    try {
      const karenBackend = getKarenBackend();
      const response = await karenBackend.makeRequestPublic<KarenPromptEnhancement>(
        "/api/ai/enhance-prompt",
        {
          method: "POST",
          body: JSON.stringify({
            prompt,
            type,
            provider,
            personality: "karen",
            enhancements: {
              technical: true,
              artistic: type === "image-generation",
              professional: true,
              detailed: true,
            },
          }),
        }
      );
      this.telemetry?.track?.("prompt_enhanced", {
        type,
        provider,
        confidence: response.confidence,
      });
      return response;
    } catch {
      const local = this.localPromptEnhancement(prompt, type);
      this.telemetry?.track?.("prompt_enhanced_local_fallback", { type, provider });
      return local;
    }
  }

  private localPromptEnhancement(
    prompt: string,
    type: ProviderType
  ): KarenPromptEnhancement {
    let enhancedPrompt = prompt;
    const improvements: string[] = [];

    if (type === "image-generation") {
      const category = this.detectPromptCategory(prompt);
      if (category && this.karenPersonality.promptPatterns[category]) {
        const pattern = this.karenPersonality.promptPatterns[category];
        enhancedPrompt = this.applyPromptPattern(prompt, pattern);
        improvements.push(`Applied ${category} pattern`);
      }

      const qualityTerms = this.karenPersonality.imageGeneration.qualityEnhancements;
      const hasQuality = qualityTerms.some((term) =>
        prompt.toLowerCase().includes(term.toLowerCase())
      );
      if (!hasQuality) {
        enhancedPrompt += ", " + qualityTerms.slice(0, 2).join(", ");
        improvements.push("Added quality enhancers");
      }

      if (
        !/lighting/i.test(prompt) &&
        !/focus/i.test(prompt)
      ) {
        enhancedPrompt += ", perfect lighting, sharp focus";
        improvements.push("Added technical improvements");
      }
    }

    return {
      originalPrompt: prompt,
      enhancedPrompt,
      improvements,
      confidence: 0.8,
      suggestedProvider: this.getSuggestedProvider(prompt, type),
    };
  }

  // ---------------- Generation Orchestration ----------------

  async generate(request: GenerationRequest): Promise<GenerationResult> {
    const generationId = this.generateId();

    // Enhance prompt (default true)
    let finalPrompt = request.prompt;
    let enhancement: KarenPromptEnhancement | undefined;

    if (request.enhancePrompt !== false) {
      enhancement = await this.enhancePrompt(request.prompt, request.type, request.provider);
      finalPrompt = enhancement.enhancedPrompt;
    }

    // Provider selection
    const providerId = request.provider || (await this.getBestProvider({ prompt: finalPrompt, type: request.type }));
    const provider = this.providers.get(providerId);
    if (!provider) throw new Error(`Provider ${providerId} not found`);

    const result: GenerationResult = {
      id: generationId,
      status: "pending",
      provider: providerId,
      type: request.type,
      originalPrompt: request.prompt,
      enhancedPrompt: enhancement?.enhancedPrompt,
      createdAt: new Date(),
    };
    this.activeGenerations.set(generationId, result);

    // fire-and-forget processing (caller can poll via getGeneration)
    this.processGeneration(result, finalPrompt, request.parameters || {}, request.timeoutMs).catch(() => {});

    return result;
  }

  private async processGeneration(
    result: GenerationResult,
    prompt: string,
    parameters: Record<string, any>,
    timeoutMs?: number
  ) {
    const karenBackend = getKarenBackend();
    const controller = typeof AbortController !== "undefined" ? new AbortController() : undefined;
    const timer = timeoutMs
      ? setTimeout(() => controller?.abort(), timeoutMs)
      : undefined;

    try {
      result.status = "processing";
      this.activeGenerations.set(result.id, result);

      const response = await karenBackend.makeRequestPublic<GenerationResult>(
        "/api/multimodal/generate",
        {
          method: "POST",
          body: JSON.stringify({
            provider: result.provider,
            type: result.type,
            prompt,
            parameters,
          }),
          signal: controller?.signal,
        }
      );

      if (response && typeof response === "object" && "status" in response) {
        if (response.status === "completed") {
          result.status = "completed";
          result.result = response.result;
          result.progress = 100;
          result.completedAt = new Date();
          this.telemetry?.track?.("generation_completed", {
            id: result.id,
            provider: result.provider,
            type: result.type,
          });
        } else {
          result.status = "failed";
          result.error = (response as any).error || "Generation failed";
          this.telemetry?.track?.("generation_failed", {
            id: result.id,
            provider: result.provider,
            type: result.type,
            error: result.error,
          });
        }
      } else {
        result.status = "failed";
        result.error = "Invalid response from server";
      }
    } catch (error: unknown) {
      result.status = "failed";
      const errorObj = error as { name?: string };
      result.error =
        errorObj?.name === "AbortError" ? "Generation timed out" :
        error instanceof Error ? error.message : "Unknown error";
      this.telemetry?.track?.("generation_failed_exception", {
        id: result.id,
        provider: result.provider,
        type: result.type,
        error: result.error,
      });
    } finally {
      if (timer) clearTimeout(timer);
      this.activeGenerations.set(result.id, result);
    }
  }

  getGeneration(id: string): GenerationResult | undefined {
    return this.activeGenerations.get(id);
  }

  getActiveGenerations(): GenerationResult[] {
    return Array.from(this.activeGenerations.values());
  }

  async cancelGeneration(id: string): Promise<boolean> {
    const generation = this.activeGenerations.get(id);
    if (!generation || generation.status === "completed" || generation.status === "failed") {
      return false;
    }
    try {
      const karenBackend = getKarenBackend();
      await karenBackend.makeRequestPublic(`/api/multimodal/cancel/${id}`, {
        method: "POST",
      });
      generation.status = "failed";
      generation.error = "Cancelled by user";
      this.activeGenerations.set(id, generation);
      this.telemetry?.track?.("generation_cancelled", { id });
      return true;
    } catch {
      return false;
    }
  }

  // ---------------- Helpers ----------------

  setTelemetry(telemetry: Telemetry) {
    this.telemetry = telemetry;
  }

  private generateId(): string {
    return `gen_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
  }

  private isArtisticPrompt(prompt: string): boolean {
    const artisticKeywords = [
      "art",
      "painting",
      "drawing",
      "artistic",
      "creative",
      "abstract",
      "style",
      "illustration",
    ];
    return artisticKeywords.some((k) => prompt.toLowerCase().includes(k));
  }

  private isPhotorealisticPrompt(prompt: string): boolean {
    const photoKeywords = [
      "photo",
      "realistic",
      "photograph",
      "real",
      "portrait",
      "landscape",
      "candid",
    ];
    return photoKeywords.some((k) => prompt.toLowerCase().includes(k));
  }

  private detectPromptCategory(
    prompt: string
  ): keyof typeof this.karenPersonality.promptPatterns | null {
    const lower = prompt.toLowerCase();

    if (lower.includes("photo") || lower.includes("shot") || lower.includes("camera")) {
      return "photography";
    }
    if (lower.includes("character") || lower.includes("person") || lower.includes("portrait")) {
      return "character";
    }
    if (lower.includes("landscape") || lower.includes("scenery") || lower.includes("environment")) {
      return "landscape";
    }
    if (lower.includes("art") || lower.includes("painting") || lower.includes("drawing")) {
      return "art";
    }
    return null;
    }

  private applyPromptPattern(prompt: string, pattern: string): string {
    return pattern
      .replace("{prompt}", prompt)
      .replace("{camera}", "professional DSLR")
      .replace("{lighting}", "natural lighting")
      .replace("{composition}", "rule of thirds")
      .replace("{style}", "modern digital art")
      .replace("{quality}", "ultra high quality")
      .replace("{expression}", "confident expression")
      .replace("{background}", "blurred background")
      .replace("{time_of_day}", "golden hour")
      .replace("{weather}", "clear weather");
  }

  private getSuggestedProvider(prompt: string, type: ProviderType): string | undefined {
    if (type === "image-generation") {
      if (this.isArtisticPrompt(prompt)) return "midjourney";
      if (this.isPhotorealisticPrompt(prompt)) return "dalle-3";
      return "stable-diffusion-local";
    }
    return undefined;
  }
}

// ---------------- Exports ----------------

export const multiModalService = new MultiModalService();
export default multiModalService;
