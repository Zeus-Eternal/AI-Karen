/**
 * @vitest-environment jsdom
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { I18nManager } from '../index';
import type { TranslationResources } from '../index';

const mockResources: TranslationResources = {
  en: {
    common: {
      hello: 'Hello',
      welcome: 'Welcome {{name}}',
      items: {
        zero: 'No items',
        one: '{{count}} item',
        other: '{{count}} items',
      },
      nested: {
        deep: {
          value: 'Deep nested value',
        },
      },
    },
  },
  es: {
    common: {
      hello: 'Hola',
      welcome: 'Bienvenido {{name}}',
      items: {
        zero: 'Sin elementos',
        one: '{{count}} elemento',
        other: '{{count}} elementos',
      },
    },
  },
};

describe('I18nManager', () => {
  let i18n: I18nManager;

  beforeEach(() => {
    i18n = new I18nManager({
      defaultLocale: 'en',
      locales: ['en', 'es'],
      fallbackLocale: 'en',

    // Mock localStorage
    const localStorageMock = {
      getItem: vi.fn().mockReturnValue(null), // No saved locale
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
    };
    Object.defineProperty(window, 'localStorage', {
      value: localStorageMock,
      writable: true,

    // Mock navigator.language to return English
    Object.defineProperty(window.navigator, 'language', {
      value: 'en-US',
      writable: true,


  describe('initialization', () => {
    it('should initialize with default locale', async () => {
      await i18n.init(mockResources);
      expect(i18n.getCurrentLocale()).toBe('en');

    it('should detect browser locale', async () => {
      Object.defineProperty(window.navigator, 'language', {
        value: 'es-ES',
        writable: true,

      await i18n.init(mockResources);
      expect(i18n.getCurrentLocale()).toBe('es');

    it('should load saved locale from storage', async () => {
      vi.mocked(localStorage.getItem).mockReturnValue('es');
      
      await i18n.init(mockResources);
      expect(i18n.getCurrentLocale()).toBe('es');


  describe('locale management', () => {
    beforeEach(async () => {
      await i18n.init(mockResources);

    it('should change locale', () => {
      i18n.changeLocale('es');
      expect(i18n.getCurrentLocale()).toBe('es');

    it('should store locale in localStorage', () => {
      i18n.changeLocale('es');
      expect(localStorage.setItem).toHaveBeenCalledWith('i18n-locale', 'es');

    it('should warn for unsupported locale', () => {
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
      
      i18n.changeLocale('fr');
      expect(consoleSpy).toHaveBeenCalledWith("Locale 'fr' is not supported");
      expect(i18n.getCurrentLocale()).toBe('en');
      
      consoleSpy.mockRestore();

    it('should notify listeners on locale change', () => {
      const listener = vi.fn();
      const unsubscribe = i18n.onLocaleChange(listener);
      
      i18n.changeLocale('es');
      expect(listener).toHaveBeenCalledWith('es');
      
      unsubscribe();
      i18n.changeLocale('en');
      expect(listener).toHaveBeenCalledTimes(1);

    it('should get available locales', () => {
      const locales = i18n.getAvailableLocales();
      expect(locales).toEqual(['en', 'es']);


  describe('translation', () => {
    beforeEach(async () => {
      await i18n.init(mockResources);

    it('should translate simple keys', () => {
      expect(i18n.t('hello')).toBe('Hello');

    it('should translate with interpolation', () => {
      expect(i18n.t('welcome', { name: 'John' })).toBe('Welcome John');

    it('should translate nested keys', () => {
      expect(i18n.t('nested.deep.value')).toBe('Deep nested value');

    it('should handle pluralization', () => {
      expect(i18n.t('items', { count: 0 })).toBe('No items');
      expect(i18n.t('items', { count: 1 })).toBe('1 item');
      expect(i18n.t('items', { count: 5 })).toBe('5 items');

    it('should use namespace', () => {
      expect(i18n.t('hello', { ns: 'common' })).toBe('Hello');

    it('should fallback to fallback locale', () => {
      i18n.changeLocale('es');
      expect(i18n.t('nested.deep.value')).toBe('Deep nested value'); // Falls back to English

    it('should return key if translation not found', () => {
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
      
      expect(i18n.t('nonexistent.key')).toBe('nonexistent.key');
      expect(consoleSpy).toHaveBeenCalledWith('Translation missing for key: nonexistent.key (locale: en)');
      
      consoleSpy.mockRestore();

    it('should translate in different locale', () => {
      i18n.changeLocale('es');
      expect(i18n.t('hello')).toBe('Hola');
      expect(i18n.t('welcome', { name: 'Juan' })).toBe('Bienvenido Juan');


  describe('formatting', () => {
    beforeEach(async () => {
      await i18n.init(mockResources);

    it('should format numbers', () => {
      const result = i18n.formatNumber(1234.56);
      expect(typeof result).toBe('string');
      expect(result).toContain('1');

    it('should format currency', () => {
      const result = i18n.formatNumber(1234.56, { 
        numberStyle: 'currency', 
        currency: 'USD' 

      expect(typeof result).toBe('string');
      expect(result).toContain('1');

    it('should format dates', () => {
      const date = new Date('2023-01-01T12:00:00Z');
      const result = i18n.formatDate(date, { dateStyle: 'short' });
      expect(typeof result).toBe('string');

    it('should format relative time', () => {
      const result = i18n.formatRelativeTime(-1, 'hour');
      expect(typeof result).toBe('string');

    it('should handle formatting errors gracefully', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      // Invalid currency should fallback to string
      const result = i18n.formatNumber(123, { 
        numberStyle: 'currency', 
        currency: 'INVALID' 

      expect(result).toBe('123');
      
      consoleSpy.mockRestore();


  describe('text direction', () => {
    beforeEach(async () => {
      await i18n.init(mockResources);

    it('should return ltr for English', () => {
      expect(i18n.getTextDirection()).toBe('ltr');

    it('should return rtl for Arabic', () => {
      const arabicI18n = new I18nManager({
        defaultLocale: 'ar',
        locales: ['ar'],

      expect(arabicI18n.getTextDirection()).toBe('rtl');


  describe('locale info', () => {
    beforeEach(async () => {
      await i18n.init(mockResources);

    it('should get locale info for current locale', () => {
      const info = i18n.getLocaleInfo();
      expect(info).toEqual({
        code: 'en',
        name: 'English',
        nativeName: 'English',
        direction: 'ltr',


    it('should get locale info for specific locale', () => {
      const info = i18n.getLocaleInfo('es');
      expect(info).toEqual({
        code: 'es',
        name: 'Spanish',
        nativeName: 'Español',
        direction: 'ltr',



  describe('resource management', () => {
    beforeEach(async () => {
      await i18n.init(mockResources);

    it('should add additional resources', () => {
      i18n.addResources('en', 'common', {
        newKey: 'New value',

      expect(i18n.t('newKey')).toBe('New value');

    it('should merge with existing resources', () => {
      i18n.addResources('en', 'common', {
        hello: 'Hi', // Override existing
        newKey: 'New value', // Add new

      expect(i18n.t('hello')).toBe('Hi');
      expect(i18n.t('newKey')).toBe('New value');
      expect(i18n.t('welcome', { name: 'Test' })).toBe('Welcome Test'); // Existing should remain


