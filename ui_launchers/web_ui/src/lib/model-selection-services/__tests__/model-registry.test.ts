/**
 * Unit tests for ModelRegistry service
 */

import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { ModelRegistryService, getModelRegistry, resetModelRegistry } from "../model-registry";
import type { Model } from "../../model-utils";
import { ModelRegistryError } from "../errors/model-selection-errors";

describe("ModelRegistryService", () => {
  let service: ModelRegistryService;
  let mockModels: Model[];

  beforeEach(() => {
    // Reset singleton
    resetModelRegistry();

    // Create fresh service instance
    service = new ModelRegistryService(100); // Short cache timeout for testing

    // Create mock models for testing
    mockModels = [
      {
        id: "model-1",
        name: "GPT-4",
        type: "text",
        provider: "openai",
        status: "available",
        capabilities: ["text-generation", "chat"],
        health: {
          is_healthy: true,
          last_check: new Date().toISOString(),
          issues: [],
        },
        size: 1000,
        description: "GPT-4 model",
        metadata: {},
        last_used: new Date(Date.now() - 1000).toISOString(),
      },
      {
        id: "model-2",
        name: "Claude-3",
        type: "text",
        provider: "anthropic",
        status: "local",
        capabilities: ["text-generation", "analysis"],
        health: {
          is_healthy: true,
          last_check: new Date().toISOString(),
          issues: [],
        },
        size: 800,
        description: "Claude-3 model",
        metadata: {},
        last_used: new Date(Date.now() - 2000).toISOString(),
      },
      {
        id: "model-3",
        name: "DALL-E",
        type: "image",
        provider: "openai",
        status: "available",
        capabilities: ["image-generation"],
        health: {
          is_healthy: false,
          last_check: new Date().toISOString(),
          issues: ["Connection failed"],
        },
        size: 1500,
        description: "DALL-E image generation model",
        metadata: {},
        last_used: new Date(Date.now() - 3000).toISOString(),
      },
      {
        id: "model-4",
        name: "Llama-2",
        type: "text",
        provider: "meta",
        status: "downloading",
        capabilities: ["text-generation"],
        health: {
          is_healthy: true,
          last_check: new Date().toISOString(),
          issues: [],
        },
        size: 1200,
        description: "Llama-2 model",
        metadata: {},
        last_used: new Date(Date.now() - 4000).toISOString(),
      },
    ];

  afterEach(async () => {
    if (service) {
      await service.shutdown();
    }
    resetModelRegistry();

  describe("Constructor and Initialization", () => {
    it("should create service with default configuration", () => {
      expect(service).toBeInstanceOf(ModelRegistryService);

    it("should initialize successfully", async () => {
      await service.initialize();
      expect(service.getRegistryStats().isInitialized).toBe(true);


  describe("updateRegistry", () => {
    it("should update registry with models and categorization", async () => {
      await service.updateRegistry(mockModels);

      const registry = await service.getModelRegistry();
      expect(registry.models).toHaveLength(4);
      expect(registry.categories.byType.text).toHaveLength(3);
      expect(registry.categories.byType.image).toHaveLength(1);
      expect(registry.categories.byProvider.openai).toHaveLength(2);
      expect(registry.categories.byProvider.anthropic).toHaveLength(1);
      expect(registry.categories.byProvider.meta).toHaveLength(1);

    it("should update lastUpdate timestamp", async () => {
      const beforeTime = Date.now();
      await service.updateRegistry(mockModels);
      const afterTime = Date.now();

      const registry = await service.getModelRegistry();
      expect(registry.lastUpdate).toBeGreaterThanOrEqual(beforeTime);
      expect(registry.lastUpdate).toBeLessThanOrEqual(afterTime);

    it("should handle empty model array", async () => {
      await service.updateRegistry([]);

      const registry = await service.getModelRegistry();
      expect(registry.models).toHaveLength(0);
      expect(Object.keys(registry.categories.byType)).toHaveLength(0);

    it("should handle models with missing properties", async () => {
      const incompleteModels: Model[] = [
        {
          id: "incomplete-1",
          name: "Incomplete Model",
          provider: "",
          size: 0,
          description: "",
          capabilities: [],
          status: "available",
          metadata: {},
          // Missing type, provider, etc.
        } as Model,
      ];

      await service.updateRegistry(incompleteModels);

      const registry = await service.getModelRegistry();
      expect(registry.models).toHaveLength(1);
      expect(registry.categories.byType.unknown).toHaveLength(1);
      expect(registry.categories.byProvider.unknown).toHaveLength(1);


  describe("getModelRegistry", () => {
    beforeEach(async () => {
      await service.updateRegistry(mockModels);

    it("should return cached registry", async () => {
      const registry1 = await service.getModelRegistry();
      const registry2 = await service.getModelRegistry();

      expect(registry1).toBe(registry2); // Same object reference

    it("should force refresh when requested", async () => {
      await service.getModelRegistry();

      // Update registry with new data
      const newModels = [
        ...mockModels,
        {
          id: "model-5",
          name: "New Model",
          type: "text",
          provider: "test",
          status: "available",
          size: 500,
          description: "New test model",
          capabilities: ["text-generation"],
          metadata: {},
        } as Model,
      ];

      await service.updateRegistry(newModels);
      const registry2 = await service.getModelRegistry(true);

      expect(registry2.models).toHaveLength(5);

    it("should return empty registry when no data available", async () => {
      const freshService = new ModelRegistryService();
      const registry = await freshService.getModelRegistry();

      expect(registry.models).toHaveLength(0);
      expect(registry.lastUpdate).toBe(0);

      await freshService.shutdown();


  describe("lookupModels", () => {
    beforeEach(async () => {
      await service.updateRegistry(mockModels);

    it("should return all models with no filters", async () => {
      const models = await service.lookupModels();
      expect(models).toHaveLength(4);

    it("should filter by type", async () => {
      const textModels = await service.lookupModels({ type: "text" });
      const imageModels = await service.lookupModels({ type: "image" });

      expect(textModels).toHaveLength(3);
      expect(imageModels).toHaveLength(1);
      expect(textModels.every((m) => m.type === "text")).toBe(true);
      expect(imageModels.every((m) => m.type === "image")).toBe(true);

    it("should filter by provider", async () => {
      const openaiModels = await service.lookupModels({ provider: "openai" });
      const anthropicModels = await service.lookupModels({
        provider: "anthropic",

      expect(openaiModels).toHaveLength(2);
      expect(anthropicModels).toHaveLength(1);
      expect(openaiModels.every((m) => m.provider === "openai")).toBe(true);

    it("should filter by capability", async () => {
      const chatModels = await service.lookupModels({
        capability: "text-generation",

      const imageGenModels = await service.lookupModels({
        capability: "image-generation",

      expect(chatModels).toHaveLength(3);
      expect(imageGenModels).toHaveLength(1);

    it("should filter by status", async () => {
      const availableModels = await service.lookupModels({
        status: "available",

      const localModels = await service.lookupModels({ status: "local" });
      const downloadingModels = await service.lookupModels({
        status: "downloading",

      expect(availableModels).toHaveLength(2);
      expect(localModels).toHaveLength(1);
      expect(downloadingModels).toHaveLength(1);

    it("should filter by health", async () => {
      const healthyModels = await service.lookupModels({ healthyOnly: true });
      expect(healthyModels).toHaveLength(3);
      expect(healthyModels.every((m) => m.health?.is_healthy === true)).toBe(
        true
      );

    it("should apply limit", async () => {
      const limitedModels = await service.lookupModels({ limit: 2 });
      expect(limitedModels).toHaveLength(2);

    it("should sort by name", async () => {
      const sortedModels = await service.lookupModels({ sortBy: "name" });
      expect(sortedModels[0].name).toBe("Claude-3");
      expect(sortedModels[1].name).toBe("DALL-E");
      expect(sortedModels[2].name).toBe("GPT-4");
      expect(sortedModels[3].name).toBe("Llama-2");

    it("should sort by size", async () => {
      const sortedModels = await service.lookupModels({ sortBy: "size" });
      expect(sortedModels[0].size).toBe(800); // Claude-3
      expect(sortedModels[3].size).toBe(1500); // DALL-E

    it("should sort by performance (health)", async () => {
      const sortedModels = await service.lookupModels({
        sortBy: "performance",

      expect(sortedModels[0].health?.is_healthy).toBe(true); // Healthy models first
      expect(sortedModels[sortedModels.length - 1].health?.is_healthy).toBe(
        false
      ); // Unhealthy models last

    it("should sort by recent usage", async () => {
      const sortedModels = await service.lookupModels({ sortBy: "recent" });
      expect(sortedModels[0].id).toBe("model-1"); // Most recent
      expect(sortedModels[3].id).toBe("model-4"); // Least recent

    it("should combine multiple filters", async () => {
      const filteredModels = await service.lookupModels({
        type: "text",
        provider: "openai",
        healthyOnly: true,
        limit: 1,

      expect(filteredModels).toHaveLength(1);
      expect(filteredModels[0].type).toBe("text");
      expect(filteredModels[0].provider).toBe("openai");
      expect(filteredModels[0].health?.is_healthy).toBe(true);


  describe("getModelsByCategory", () => {
    beforeEach(async () => {
      await service.updateRegistry(mockModels);

    it("should get models by type category", async () => {
      const textModels = await service.getModelsByCategory("type", "text");
      const imageModels = await service.getModelsByCategory("type", "image");

      expect(textModels).toHaveLength(3);
      expect(imageModels).toHaveLength(1);

    it("should get models by provider category", async () => {
      const openaiModels = await service.getModelsByCategory(
        "provider",
        "openai"
      );
      expect(openaiModels).toHaveLength(2);

    it("should get models by capability category", async () => {
      const textGenModels = await service.getModelsByCategory(
        "capability",
        "text-generation"
      );
      expect(textGenModels).toHaveLength(3);

    it("should get models by status category", async () => {
      const availableModels = await service.getModelsByCategory(
        "status",
        "available"
      );
      expect(availableModels).toHaveLength(2);

    it("should get models by health category", async () => {
      const healthyModels = await service.getModelsByCategory(
        "health",
        "healthy"
      );
      const unhealthyModels = await service.getModelsByCategory(
        "health",
        "unhealthy"
      );

      expect(healthyModels).toHaveLength(3);
      expect(unhealthyModels).toHaveLength(1);

    it("should return empty array for non-existent category value", async () => {
      const models = await service.getModelsByCategory("type", "nonexistent");
      expect(models).toHaveLength(0);

    it("should throw error for invalid category", async () => {
      await expect(
        service.getModelsByCategory("invalid", "value")
      ).rejects.toThrow(ModelRegistryError);


  describe("getCategorySummary", () => {
    beforeEach(async () => {
      await service.updateRegistry(mockModels);

    it("should return category summary", async () => {
      const summary = await service.getCategorySummary();

      expect(summary.totalModels).toBe(4);
      expect(summary.typeCount.text).toBe(3);
      expect(summary.typeCount.image).toBe(1);
      expect(summary.providerCount.openai).toBe(2);
      expect(summary.providerCount.anthropic).toBe(1);
      expect(summary.providerCount.meta).toBe(1);
      expect(summary.statusCount.available).toBe(2);
      expect(summary.statusCount.local).toBe(1);
      expect(summary.statusCount.downloading).toBe(1);
      expect(summary.healthCount.healthy).toBe(3);
      expect(summary.healthCount.unhealthy).toBe(1);

    it("should return empty summary for empty registry", async () => {
      await service.updateRegistry([]);
      const summary = await service.getCategorySummary();

      expect(summary.totalModels).toBe(0);
      expect(Object.keys(summary.typeCount)).toHaveLength(0);
      expect(Object.keys(summary.providerCount)).toHaveLength(0);


  describe("categorizeModels", () => {
    it("should categorize models correctly", () => {
      const categories = service.categorizeModels(mockModels);

      expect(categories.byType.text).toHaveLength(3);
      expect(categories.byType.image).toHaveLength(1);
      expect(categories.byProvider.openai).toHaveLength(2);
      expect(categories.byCapability["text-generation"]).toHaveLength(3);
      expect(categories.byCapability["image-generation"]).toHaveLength(1);
      expect(categories.byStatus.available).toHaveLength(2);
      expect(categories.byHealth.healthy).toHaveLength(3);
      expect(categories.byHealth.unhealthy).toHaveLength(1);

    it("should handle models with missing properties", () => {
      const incompleteModels: Model[] = [
        {
          id: "1",
          name: "Model 1",
          provider: "",
          size: 0,
          description: "",
          capabilities: [],
          status: "available",
          metadata: {},
        } as Model,
        {
          id: "2",
          name: "Model 2",
          type: "text",
          provider: "test",
          size: 100,
          description: "Test model",
          capabilities: [],
          status: "available",
          metadata: {},
        } as Model,
      ];

      const categories = service.categorizeModels(incompleteModels);

      expect(categories.byType.unknown).toHaveLength(1);
      expect(categories.byType.text).toHaveLength(1);
      expect(categories.byProvider.unknown).toHaveLength(2);
      expect(categories.byStatus.unknown).toHaveLength(2);
      expect(categories.byHealth.unhealthy).toHaveLength(2);

    it("should handle empty model array", () => {
      const categories = service.categorizeModels([]);

      expect(Object.keys(categories.byType)).toHaveLength(0);
      expect(Object.keys(categories.byProvider)).toHaveLength(0);
      expect(Object.keys(categories.byCapability)).toHaveLength(0);
      expect(Object.keys(categories.byStatus)).toHaveLength(0);
      expect(Object.keys(categories.byHealth)).toHaveLength(0);


  describe("clearRegistry", () => {
    it("should clear the registry", async () => {
      await service.updateRegistry(mockModels);

      let stats = service.getRegistryStats();
      expect(stats.hasRegistry).toBe(true);
      expect(stats.totalModels).toBe(4);

      service.clearRegistry();

      stats = service.getRegistryStats();
      expect(stats.hasRegistry).toBe(false);
      expect(stats.totalModels).toBe(0);


  describe("getRegistryStats", () => {
    it("should return service statistics", async () => {
      const stats = service.getRegistryStats();

      expect(stats).toHaveProperty("serviceName", "ModelRegistryService");
      expect(stats).toHaveProperty("isInitialized");
      expect(stats).toHaveProperty("cacheSize");
      expect(stats).toHaveProperty("hasRegistry");
      expect(stats).toHaveProperty("totalModels");
      expect(stats).toHaveProperty("lastUpdate");

    it("should reflect registry state in stats", async () => {
      let stats = service.getRegistryStats();
      expect(stats.hasRegistry).toBe(false);
      expect(stats.totalModels).toBe(0);

      await service.updateRegistry(mockModels);

      stats = service.getRegistryStats();
      expect(stats.hasRegistry).toBe(true);
      expect(stats.totalModels).toBe(4);
      expect(stats.lastUpdate).toBeGreaterThan(0);


  describe("Singleton Management", () => {
    it("should return same instance from getModelRegistry", () => {
      const instance1 = getModelRegistry();
      const instance2 = getModelRegistry();

      expect(instance1).toBe(instance2);

    it("should create new instance after reset", () => {
      const instance1 = getModelRegistry();
      resetModelRegistry();
      const instance2 = getModelRegistry();

      expect(instance1).not.toBe(instance2);


  describe("Error Handling", () => {
    it("should handle errors in updateRegistry gracefully", async () => {
      // Mock a scenario that would cause an error
      const invalidModels = null as any;

      await expect(service.updateRegistry(invalidModels)).rejects.toThrow(
      );

    it("should handle errors in lookupModels gracefully", async () => {
      // Create a scenario where the registry is corrupted
      await service.updateRegistry(mockModels);

      // Manually corrupt the registry to trigger an error
      (service as any).modelRegistry = { models: null };

      await expect(service.lookupModels()).rejects.toThrow(ModelRegistryError);


