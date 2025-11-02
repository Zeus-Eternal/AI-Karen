/**
 * Unit tests for PreferencesService
 */

import { describe, it, expect, beforeEach, afterEach, vi, Mock } from "vitest";
import { PreferencesService, getPreferencesService, resetPreferencesService } from "../preferences-service";
import { ModelSelectionPreferences, PreferencesServiceConfig } from "../types";
import { PreferencesError } from "../errors/model-selection-errors";

// Mock the karen-backend module
vi.mock("../../karen-backend", () => ({
  getKarenBackend: vi.fn(() => ({
    makeRequestPublic: vi.fn(),
  })),
}));

// Mock the safe-console module
vi.mock("@/lib/safe-console", () => ({
  safeLog: vi.fn(),
  safeError: vi.fn(),
}));

import { getKarenBackend } from "../../karen-backend";

describe("PreferencesService", () => {
  let service: PreferencesService;
  let mockBackend: { makeRequestPublic: Mock };

  beforeEach(() => {
    // Reset mocks
    vi.clearAllMocks();

    // Setup mock backend
    mockBackend = {
      makeRequestPublic: vi.fn(),
    };
    (getKarenBackend as Mock).mockReturnValue(mockBackend);

    // Reset singleton
    resetPreferencesService();

    // Create fresh service instance with short cache timeout for testing
    service = new PreferencesService({ cacheTimeout: 100 });

  afterEach(async () => {
    if (service) {
      await service.shutdown();
    }
    resetPreferencesService();

  describe("Constructor and Initialization", () => {
    it("should create service with default configuration", () => {
      expect(service).toBeInstanceOf(PreferencesService);

    it("should create service with custom configuration", () => {
      const config: Partial<PreferencesServiceConfig> = {
        cacheTimeout: 60000,
        autoSave: false,
        defaultPreferences: {
          preferLocal: true,
          autoSelectFallback: false,
        },
      };

      const customService = new PreferencesService(config);
      expect(customService).toBeInstanceOf(PreferencesService);

    it("should initialize successfully", async () => {
      mockBackend.makeRequestPublic
        .mockResolvedValueOnce({ lastSelectedModel: "test-model" }) // getUserPreferences
        .mockResolvedValueOnce({ defaultModel: "default-model" }); // getDefaultModelConfig

      await service.initialize();

      expect(mockBackend.makeRequestPublic).toHaveBeenCalledTimes(2);
      expect(mockBackend.makeRequestPublic).toHaveBeenCalledWith(
        "/api/user/preferences/models"
      );
      expect(mockBackend.makeRequestPublic).toHaveBeenCalledWith(
        "/api/system/config/models"
      );

    it("should handle initialization errors gracefully", async () => {
      mockBackend.makeRequestPublic.mockRejectedValue(
        new Error("Backend error")
      );

      // Should not throw, should handle errors gracefully
      await expect(service.initialize()).resolves.not.toThrow();


  describe("getUserPreferences", () => {
    it("should retrieve user preferences from backend", async () => {
      const mockPreferences: ModelSelectionPreferences = {
        lastSelectedModel: "test-model",
        defaultModel: "default-model",
        preferredProviders: ["openai", "anthropic"],
        preferLocal: true,
        autoSelectFallback: false,
      };

      mockBackend.makeRequestPublic.mockResolvedValue(mockPreferences);

      const result = await service.getUserPreferences();

      expect(result).toEqual(mockPreferences);
      expect(mockBackend.makeRequestPublic).toHaveBeenCalledWith(
        "/api/user/preferences/models"
      );

    it("should return defaults when backend returns empty response", async () => {
      mockBackend.makeRequestPublic.mockResolvedValue(null);

      const result = await service.getUserPreferences();

      expect(result).toEqual({
        lastSelectedModel: undefined,
        defaultModel: undefined,
        preferredProviders: [],
        preferLocal: false,
        autoSelectFallback: true,


    it("should return defaults when backend request fails", async () => {
      mockBackend.makeRequestPublic.mockRejectedValue(
        new Error("Network error")
      );

      const result = await service.getUserPreferences();

      expect(result).toEqual({
        lastSelectedModel: undefined,
        defaultModel: undefined,
        preferredProviders: [],
        preferLocal: false,
        autoSelectFallback: true,


    it("should cache preferences and return cached value on subsequent calls", async () => {
      const mockPreferences: ModelSelectionPreferences = {
        lastSelectedModel: "test-model",
        defaultModel: "default-model",
        preferredProviders: ["openai"],
        preferLocal: false,
        autoSelectFallback: true,
      };

      // Create a fresh service to avoid initialization calls
      const freshService = new PreferencesService({ cacheTimeout: 30000 });

      // Clear any previous calls
      vi.clearAllMocks();
      mockBackend.makeRequestPublic.mockResolvedValue(mockPreferences);

      // First call
      const result1 = await freshService.getUserPreferences();
      // Second call (should use cache)
      const result2 = await freshService.getUserPreferences();

      expect(result1).toEqual(mockPreferences);
      expect(result2).toEqual(mockPreferences);
      expect(mockBackend.makeRequestPublic).toHaveBeenCalledTimes(1);

      await freshService.shutdown();


  describe("saveUserPreferences", () => {
    it("should save valid preferences to backend", async () => {
      const preferences: Partial<ModelSelectionPreferences> = {
        lastSelectedModel: "new-model",
        preferLocal: true,
      };

      mockBackend.makeRequestPublic.mockResolvedValue(undefined);

      await service.saveUserPreferences(preferences);

      expect(mockBackend.makeRequestPublic).toHaveBeenCalledWith(
        "/api/user/preferences/models",
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(preferences),
        }
      );

    it("should throw error for invalid preferences", async () => {
      const invalidPreferences = {
        lastSelectedModel: 123, // Should be string
        preferLocal: "yes", // Should be boolean
      } as any;

      await expect(
        service.saveUserPreferences(invalidPreferences)
      ).rejects.toThrow(PreferencesError);

    it("should handle backend save errors", async () => {
      const preferences: Partial<ModelSelectionPreferences> = {
        lastSelectedModel: "test-model",
      };

      mockBackend.makeRequestPublic.mockRejectedValue(new Error("Save failed"));

      await expect(service.saveUserPreferences(preferences)).rejects.toThrow(
      );

    it("should invalidate cache after successful save", async () => {
      const initialPreferences: ModelSelectionPreferences = {
        lastSelectedModel: "old-model",
        defaultModel: undefined,
        preferredProviders: [],
        preferLocal: false,
        autoSelectFallback: true,
      };

      const updatedPreferences: Partial<ModelSelectionPreferences> = {
        lastSelectedModel: "new-model",
      };

      // Create fresh service to avoid initialization calls
      const freshService = new PreferencesService({ cacheTimeout: 30000 });

      // Clear any previous calls
      vi.clearAllMocks();

      // Setup initial cache
      mockBackend.makeRequestPublic.mockResolvedValueOnce(initialPreferences);
      await freshService.getUserPreferences();

      // Save new preferences
      mockBackend.makeRequestPublic.mockResolvedValueOnce(undefined);
      await freshService.saveUserPreferences(updatedPreferences);

      // Verify cache was invalidated by checking if backend is called again
      mockBackend.makeRequestPublic.mockResolvedValueOnce({
        ...initialPreferences,
        ...updatedPreferences,

      const result = await freshService.getUserPreferences();

      expect(result.lastSelectedModel).toBe("new-model");
      expect(mockBackend.makeRequestPublic).toHaveBeenCalledTimes(3); // get, save, get again

      await freshService.shutdown();


  describe("getDefaultModelConfig", () => {
    it("should retrieve default model config from backend", async () => {
      const mockConfig = { defaultModel: "system-default" };

      mockBackend.makeRequestPublic.mockResolvedValue(mockConfig);

      const result = await service.getDefaultModelConfig();

      expect(result).toEqual(mockConfig);
      expect(mockBackend.makeRequestPublic).toHaveBeenCalledWith(
        "/api/system/config/models"
      );

    it("should return empty config when backend request fails", async () => {
      mockBackend.makeRequestPublic.mockRejectedValue(
        new Error("Config error")
      );

      const result = await service.getDefaultModelConfig();

      expect(result).toEqual({});

    it("should cache config and return cached value on subsequent calls", async () => {
      const mockConfig = { defaultModel: "system-default" };

      // Create fresh service to avoid initialization calls
      const freshService = new PreferencesService({ cacheTimeout: 30000 });

      // Clear any previous calls
      vi.clearAllMocks();
      mockBackend.makeRequestPublic.mockResolvedValue(mockConfig);

      // First call
      const result1 = await freshService.getDefaultModelConfig();
      // Second call (should use cache)
      const result2 = await freshService.getDefaultModelConfig();

      expect(result1).toEqual(mockConfig);
      expect(result2).toEqual(mockConfig);
      expect(mockBackend.makeRequestPublic).toHaveBeenCalledTimes(1);

      await freshService.shutdown();


  describe("updateLastSelectedModel", () => {
    it("should update last selected model", async () => {
      const initialPreferences: ModelSelectionPreferences = {
        lastSelectedModel: "old-model",
        defaultModel: undefined,
        preferredProviders: [],
        preferLocal: false,
        autoSelectFallback: true,
      };

      mockBackend.makeRequestPublic
        .mockResolvedValueOnce(initialPreferences) // getUserPreferences
        .mockResolvedValueOnce(undefined); // saveUserPreferences

      await service.updateLastSelectedModel("new-model");

      expect(mockBackend.makeRequestPublic).toHaveBeenCalledWith(
        "/api/user/preferences/models",
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            ...initialPreferences,
            lastSelectedModel: "new-model",
          }),
        }
      );

    it("should throw error for invalid model ID", async () => {
      await expect(service.updateLastSelectedModel("")).rejects.toThrow(
      );

      await expect(
        service.updateLastSelectedModel(null as any)
      ).rejects.toThrow(PreferencesError);

      await expect(service.updateLastSelectedModel(123 as any)).rejects.toThrow(
      );


  describe("setDefaultModel", () => {
    it("should set default model", async () => {
      const initialPreferences: ModelSelectionPreferences = {
        lastSelectedModel: undefined,
        defaultModel: "old-default",
        preferredProviders: [],
        preferLocal: false,
        autoSelectFallback: true,
      };

      mockBackend.makeRequestPublic
        .mockResolvedValueOnce(initialPreferences) // getUserPreferences
        .mockResolvedValueOnce(undefined); // saveUserPreferences

      await service.setDefaultModel("new-default");

      expect(mockBackend.makeRequestPublic).toHaveBeenCalledWith(
        "/api/user/preferences/models",
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            ...initialPreferences,
            defaultModel: "new-default",
          }),
        }
      );

    it("should throw error for invalid model ID", async () => {
      await expect(service.setDefaultModel("")).rejects.toThrow(
      );

      await expect(service.setDefaultModel(null as any)).rejects.toThrow(
      );

      await expect(service.setDefaultModel(123 as any)).rejects.toThrow(
      );


  describe("resetToDefaults", () => {
    it("should reset preferences to defaults", async () => {
      mockBackend.makeRequestPublic.mockResolvedValue(undefined);

      await service.resetToDefaults();

      expect(mockBackend.makeRequestPublic).toHaveBeenCalledWith(
        "/api/user/preferences/models",
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            lastSelectedModel: undefined,
            defaultModel: undefined,
            preferredProviders: [],
            preferLocal: false,
            autoSelectFallback: true,
          }),
        }
      );

    it("should handle reset errors", async () => {
      mockBackend.makeRequestPublic.mockRejectedValue(
        new Error("Reset failed")
      );

      await expect(service.resetToDefaults()).rejects.toThrow(PreferencesError);


  describe("validatePreferences", () => {
    it("should validate correct preferences", () => {
      const validPreferences: Partial<ModelSelectionPreferences> = {
        lastSelectedModel: "test-model",
        defaultModel: "default-model",
        preferredProviders: ["openai", "anthropic"],
        preferLocal: true,
        autoSelectFallback: false,
      };

      expect(service.validatePreferences(validPreferences)).toBe(true);

    it("should reject invalid preferences", () => {
      expect(service.validatePreferences(null as any)).toBe(false);
      expect(service.validatePreferences(undefined as any)).toBe(false);
      expect(service.validatePreferences("string" as any)).toBe(false);
      expect(service.validatePreferences(123 as any)).toBe(false);

    it("should reject preferences with invalid types", () => {
      expect(
        service.validatePreferences({ lastSelectedModel: 123 } as any)
      ).toBe(false);
      expect(service.validatePreferences({ defaultModel: true } as any)).toBe(
        false
      );
      expect(
        service.validatePreferences({ preferredProviders: "string" } as any)
      ).toBe(false);
      expect(
        service.validatePreferences({ preferredProviders: [123] } as any)
      ).toBe(false);
      expect(service.validatePreferences({ preferLocal: "yes" } as any)).toBe(
        false
      );
      expect(
        service.validatePreferences({ autoSelectFallback: "no" } as any)
      ).toBe(false);

    it("should accept partial preferences", () => {
      expect(service.validatePreferences({})).toBe(true);
      expect(service.validatePreferences({ lastSelectedModel: "test" })).toBe(
        true
      );
      expect(service.validatePreferences({ preferLocal: true })).toBe(true);


  describe("mergeWithDefaults", () => {
    it("should merge partial preferences with defaults", () => {
      const partial: Partial<ModelSelectionPreferences> = {
        lastSelectedModel: "test-model",
        preferLocal: true,
      };

      const result = service.mergeWithDefaults(partial);

      expect(result).toEqual({
        lastSelectedModel: "test-model",
        defaultModel: undefined,
        preferredProviders: [],
        preferLocal: true,
        autoSelectFallback: true,


    it("should return defaults for empty preferences", () => {
      const result = service.mergeWithDefaults({});

      expect(result).toEqual({
        lastSelectedModel: undefined,
        defaultModel: undefined,
        preferredProviders: [],
        preferLocal: false,
        autoSelectFallback: true,


    it("should use custom defaults from config", () => {
      const customDefaults: ModelSelectionPreferences = {
        lastSelectedModel: undefined,
        defaultModel: "custom-default",
        preferredProviders: ["custom-provider"],
        preferLocal: true,
        autoSelectFallback: false,
      };

      const customService = new PreferencesService({
        defaultPreferences: customDefaults,

      const result = customService.mergeWithDefaults({});

      expect(result).toEqual(customDefaults);


  describe("Cache Management", () => {
    it("should clear cache", async () => {
      // Load some data into cache
      mockBackend.makeRequestPublic.mockResolvedValue({
        lastSelectedModel: "test",

      await service.getUserPreferences();

      const statsBefore = service.getPreferencesStats();
      expect(statsBefore.cacheSize).toBeGreaterThan(0);

      service.clearCache();

      const statsAfter = service.getPreferencesStats();
      expect(statsAfter.cacheSize).toBe(0);

    it("should provide service statistics", async () => {
      const stats = service.getPreferencesStats();

      expect(stats).toHaveProperty("serviceName", "PreferencesService");
      expect(stats).toHaveProperty("isInitialized");
      expect(stats).toHaveProperty("cacheSize");
      expect(stats).toHaveProperty("config");
      expect(stats).toHaveProperty("hasUserPreferences");
      expect(stats).toHaveProperty("hasDefaultConfig");


  describe("Singleton Management", () => {
    it("should return same instance from getPreferencesService", () => {
      const instance1 = getPreferencesService();
      const instance2 = getPreferencesService();

      expect(instance1).toBe(instance2);

    it("should create new instance after reset", () => {
      const instance1 = getPreferencesService();
      resetPreferencesService();
      const instance2 = getPreferencesService();

      expect(instance1).not.toBe(instance2);


  describe("Error Handling", () => {
    it("should handle timeout errors", async () => {
      // Mock a slow response that times out
      mockBackend.makeRequestPublic.mockImplementation(
        () =>
          new Promise((_, reject) =>
            setTimeout(() => reject(new Error("Timeout")), 100)
          )
      );

      // Create service with very short timeout
      const fastService = new PreferencesService({ cacheTimeout: 1000 });

      // Should return defaults instead of throwing due to error handling
      const result = await fastService.getUserPreferences();
      expect(result).toBeDefined();
      expect(result.autoSelectFallback).toBe(true); // Should have default values

      await fastService.shutdown();

    it("should handle network errors gracefully", async () => {
      mockBackend.makeRequestPublic.mockRejectedValue(
        new Error("Network error")
      );

      // Should not throw, should return defaults
      const result = await service.getUserPreferences();
      expect(result).toBeDefined();


