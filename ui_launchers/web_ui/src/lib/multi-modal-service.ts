/**
 * Multi-Modal Service
 *
 * Handles various multi-modal AI providers including:
 * - Image generation (Stable Diffusion, DALL-E, Midjourney, etc.)
 * - Image analysis/vision (GPT-4V, Claude Vision, etc.)
 * - Audio generation (ElevenLabs, OpenAI TTS, etc.)
 * - Video generation (RunwayML, Pika Labs, etc.)
 *
 * Features Karen's intelligent prompt enhancement and provider routing.
 */

import { getKarenBackend } from "./karen-backend";

// Provider types
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

class MultiModalService {
  private providers: Map<string, MultiModalProvider> = new Map();
  private activeGenerations: Map<string, GenerationResult> = new Map();
  private karenPersonality = {
    imageGeneration: {
      stylePreferences: ["cinematic", "detailed", "professional", "artistic"],
      qualityEnhancements: [
        "high resolution",
        "8k",
        "masterpiece",
        "best quality",
      ],
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

    // OpenAI DALL-E
    this.providers.set("dalle-3", {
      id: "dalle-3",
      name: "DALL-E 3",
      type: "image-generation",
      capabilities: ["text-to-image", "high-quality"],
      status: "api-key-required",
      pricing: { model: "pay-per-use", cost: "$0.04-0.08 per image" },
      limits: { maxResolution: "1024x1024", dailyLimit: 50 },

    // Midjourney (via API)
    this.providers.set("midjourney", {
      id: "midjourney",
      name: "Midjourney",
      type: "image-generation",
      capabilities: ["text-to-image", "artistic", "high-quality"],
      status: "api-key-required",
      pricing: { model: "subscription" },
      limits: { dailyLimit: 200 },

    // GPT-4 Vision
    this.providers.set("gpt4-vision", {
      id: "gpt4-vision",
      name: "GPT-4 Vision",
      type: "image-analysis",
      capabilities: ["image-to-text", "image-analysis", "ocr"],
      status: "api-key-required",
      pricing: { model: "pay-per-use" },

    // ElevenLabs TTS
    this.providers.set("elevenlabs-tts", {
      id: "elevenlabs-tts",
      name: "ElevenLabs TTS",
      type: "text-to-speech",
      capabilities: ["text-to-speech", "voice-cloning", "multilingual"],
      status: "api-key-required",
      pricing: { model: "credits" },

    // RunwayML Video
    this.providers.set("runway-video", {
      id: "runway-video",
      name: "RunwayML Gen-2",
      type: "video-generation",
      capabilities: ["text-to-video", "img2video"],
      status: "api-key-required",
      pricing: { model: "credits" },
      limits: { maxDuration: 4, maxResolution: "1280x768" },

  }

  /**
   * Get available providers by type
   */
  getProviders(type?: ProviderType): MultiModalProvider[] {
    const allProviders = Array.from(this.providers.values());
    return type ? allProviders.filter((p) => p.type === type) : allProviders;
  }

  /**
   * Get the best provider for a request using Karen's intelligence
   */
  async getBestProvider(request: {
    prompt: string;
    type: ProviderType;
  }): Promise<string> {
    const availableProviders = this.getProviders(request.type).filter(
      (p) => p.status === "available" || p.status === "local"
    );

    if (availableProviders.length === 0) {
      throw new Error(`No available providers for ${request.type}`);
    }

    // Karen's provider selection logic
    if (request.type === "image-generation") {
      // Prefer local for privacy and speed
      const localSD = availableProviders.find(
        (p) => p.id === "stable-diffusion-local"
      );
      if (localSD) return localSD.id;

      // For artistic prompts, prefer Midjourney
      if (this.isArtisticPrompt(request.prompt)) {
        const midjourney = availableProviders.find(
          (p) => p.id === "midjourney"
        );
        if (midjourney) return midjourney.id;
      }

      // For photorealistic, prefer DALL-E 3
      if (this.isPhotorealisticPrompt(request.prompt)) {
        const dalle = availableProviders.find((p) => p.id === "dalle-3");
        if (dalle) return dalle.id;
      }
    }

    // Default to first available
    return availableProviders[0].id;
  }

  /**
   * Karen's intelligent prompt enhancement
   */
  async enhancePrompt(
    prompt: string,
    type: ProviderType,
    provider?: string
  ): Promise<KarenPromptEnhancement> {
    try {
      // Use Karen's backend for sophisticated prompt enhancement
      const karenBackend = getKarenBackend();
      const response =
        await karenBackend.makeRequestPublic<KarenPromptEnhancement>(
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

      return response;
    } catch (error) {
      // Fallback to local enhancement
      return this.localPromptEnhancement(prompt, type);
    }
  }

  /**
   * Local prompt enhancement fallback
   */
  private localPromptEnhancement(
    prompt: string,
    type: ProviderType
  ): KarenPromptEnhancement {
    let enhancedPrompt = prompt;
    const improvements: string[] = [];

    if (type === "image-generation") {
      // Detect prompt category
      const category = this.detectPromptCategory(prompt);

      // Apply Karen's enhancements
      if (category && this.karenPersonality.promptPatterns[category]) {
        const pattern = this.karenPersonality.promptPatterns[category];
        enhancedPrompt = this.applyPromptPattern(prompt, pattern);
        improvements.push(`Applied ${category} pattern`);
      }

      // Add quality enhancers
      const qualityTerms =
        this.karenPersonality.imageGeneration.qualityEnhancements;
      const hasQuality = qualityTerms.some((term) =>
        prompt.toLowerCase().includes(term.toLowerCase())
      );

      if (!hasQuality) {
        enhancedPrompt += ", " + qualityTerms.slice(0, 2).join(", ");
        improvements.push("Added quality enhancers");
      }

      // Add technical improvements
      if (!prompt.includes("lighting") && !prompt.includes("focus")) {
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

  /**
   * Generate content using the selected provider
   */
  async generate(request: GenerationRequest): Promise<GenerationResult> {
    const generationId = this.generateId();

    // Enhance prompt if requested
    let finalPrompt = request.prompt;
    let enhancement: KarenPromptEnhancement | undefined;

    if (request.enhancePrompt !== false) {
      enhancement = await this.enhancePrompt(
        request.prompt,
        request.type,
        request.provider
      );
      finalPrompt = enhancement.enhancedPrompt;
    }

    // Select provider
    const providerId =
      request.provider || (await this.getBestProvider(request));
    const provider = this.providers.get(providerId);

    if (!provider) {
      throw new Error(`Provider ${providerId} not found`);
    }

    // Create generation result
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

    // Start generation
    this.processGeneration(result, finalPrompt, request.parameters || {});

    return result;
  }

  /**
   * Process the actual generation
   */
  private async processGeneration(
    result: GenerationResult,
    prompt: string,
    parameters: any
  ) {
    try {
      result.status = "processing";

      const karenBackend = getKarenBackend();
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
        }
      );

      if (response && typeof response === "object" && "status" in response) {
        const genResponse = response as GenerationResult;
        if (genResponse.status === "completed") {
          result.status = "completed";
          result.result = genResponse.result;
          result.completedAt = new Date();
        } else {
          result.status = "failed";
          result.error = genResponse.error || "Generation failed";
        }
      } else {
        result.status = "failed";
        result.error = "Invalid response from server";
      }
    } catch (error) {
      result.status = "failed";
      result.error = error instanceof Error ? error.message : "Unknown error";
    }

    this.activeGenerations.set(result.id, result);
  }

  /**
   * Get generation status
   */
  getGeneration(id: string): GenerationResult | undefined {
    return this.activeGenerations.get(id);
  }

  /**
   * Get all active generations
   */
  getActiveGenerations(): GenerationResult[] {
    return Array.from(this.activeGenerations.values());
  }

  /**
   * Cancel a generation
   */
  async cancelGeneration(id: string): Promise<boolean> {
    const generation = this.activeGenerations.get(id);
    if (
      !generation ||
      generation.status === "completed" ||
      generation.status === "failed"
    ) {
      return false;
    }

    try {
      const karenBackend = getKarenBackend();
      await karenBackend.makeRequestPublic(`/api/multimodal/cancel/${id}`, {
        method: "POST",

      generation.status = "failed";
      generation.error = "Cancelled by user";
      return true;
    } catch (error) {
      return false;
    }
  }

  // Helper methods
  private generateId(): string {
    return `gen_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
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
    return artisticKeywords.some((keyword) =>
      prompt.toLowerCase().includes(keyword)
    );
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
    return photoKeywords.some((keyword) =>
      prompt.toLowerCase().includes(keyword)
    );
  }

  private detectPromptCategory(
    prompt: string
  ): keyof typeof this.karenPersonality.promptPatterns | null {
    const lower = prompt.toLowerCase();

    if (
      lower.includes("photo") ||
      lower.includes("shot") ||
      lower.includes("camera")
    ) {
      return "photography";
    }
    if (
      lower.includes("character") ||
      lower.includes("person") ||
      lower.includes("portrait")
    ) {
      return "character";
    }
    if (
      lower.includes("landscape") ||
      lower.includes("scenery") ||
      lower.includes("environment")
    ) {
      return "landscape";
    }
    if (
      lower.includes("art") ||
      lower.includes("painting") ||
      lower.includes("drawing")
    ) {
      return "art";
    }

    return null;
  }

  private applyPromptPattern(prompt: string, pattern: string): string {
    // Simple pattern replacement - in a real implementation, this would be more sophisticated
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

  private getSuggestedProvider(
    prompt: string,
    type: ProviderType
  ): string | undefined {
    if (type === "image-generation") {
      if (this.isArtisticPrompt(prompt)) return "midjourney";
      if (this.isPhotorealisticPrompt(prompt)) return "dalle-3";
      return "stable-diffusion-local";
    }
    return undefined;
  }
}

// Export singleton instance
export const multiModalService = new MultiModalService();
export default multiModalService;
