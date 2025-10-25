/**
 * Tests for ARIA utilities
 */

import { describe, it, expect } from 'vitest';
import {
  generateAriaId,
  createAriaLabel,
  createAriaLive,
  createInteractiveAria,
  createFormAria,
  createGridAria,
  createNavigationAria,
  createModalAria,
  createLoadingAria,
  mergeAriaProps,
  validateAriaProps,
  ARIA_ROLES,
} from '../aria';

describe('ARIA Utilities', () => {
  describe('generateAriaId', () => {
    it('should generate unique IDs', () => {
      const id1 = generateAriaId();
      const id2 = generateAriaId();
      expect(id1).not.toBe(id2);
    });

    it('should use custom prefix', () => {
      const id = generateAriaId('custom');
      expect(id).toMatch(/^custom-/);
    });
  });

  describe('createAriaLabel', () => {
    it('should create aria-label when label provided', () => {
      const result = createAriaLabel('Test label');
      expect(result).toEqual({ 'aria-label': 'Test label' });
    });

    it('should prefer aria-labelledby over aria-label', () => {
      const result = createAriaLabel('Test label', 'label-id');
      expect(result).toEqual({ 'aria-labelledby': 'label-id' });
      expect(result['aria-label']).toBeUndefined();
    });

    it('should include aria-describedby when provided', () => {
      const result = createAriaLabel('Test label', undefined, 'desc-id');
      expect(result).toEqual({
        'aria-label': 'Test label',
        'aria-describedby': 'desc-id'
      });
    });
  });

  describe('createAriaLive', () => {
    it('should create live region attributes with defaults', () => {
      const result = createAriaLive();
      expect(result).toEqual({
        'aria-live': 'polite',
        'aria-atomic': false,
        'aria-relevant': 'additions text'
      });
    });

    it('should accept custom values', () => {
      const result = createAriaLive('assertive', true, 'all');
      expect(result).toEqual({
        'aria-live': 'assertive',
        'aria-atomic': true,
        'aria-relevant': 'all'
      });
    });
  });

  describe('createInteractiveAria', () => {
    it('should create interactive attributes', () => {
      const result = createInteractiveAria(true, false, true, 'page', false);
      expect(result).toEqual({
        'aria-expanded': true,
        'aria-selected': false,
        'aria-pressed': true,
        'aria-current': 'page',
        'aria-disabled': false
      });
    });

    it('should omit undefined values', () => {
      const result = createInteractiveAria(true);
      expect(result).toEqual({
        'aria-expanded': true
      });
    });
  });

  describe('createFormAria', () => {
    it('should create form attributes', () => {
      const result = createFormAria(true, true, 'desc-id', 'error-id');
      expect(result).toEqual({
        'aria-invalid': true,
        'aria-required': true,
        'aria-describedby': 'desc-id error-id'
      });
    });

    it('should handle error-only describedby', () => {
      const result = createFormAria(true, undefined, undefined, 'error-id');
      expect(result).toEqual({
        'aria-invalid': true,
        'aria-describedby': 'error-id'
      });
    });
  });

  describe('createGridAria', () => {
    it('should create grid attributes', () => {
      const result = createGridAria(1, 2, 1, 1, 10, 5);
      expect(result).toEqual({
        'aria-rowindex': 1,
        'aria-colindex': 2,
        'aria-rowspan': 1,
        'aria-colspan': 1,
        'aria-rowcount': 10,
        'aria-colcount': 5
      });
    });
  });

  describe('createNavigationAria', () => {
    it('should create navigation attributes', () => {
      const result = createNavigationAria('page', true, 'menu');
      expect(result).toEqual({
        'aria-current': 'page',
        'aria-expanded': true,
        'aria-haspopup': 'menu'
      });
    });
  });

  describe('createModalAria', () => {
    it('should create modal attributes', () => {
      const result = createModalAria('title-id', 'desc-id', true);
      expect(result).toEqual({
        'aria-labelledby': 'title-id',
        'aria-describedby': 'desc-id',
        'aria-modal': true
      });
    });
  });

  describe('createLoadingAria', () => {
    it('should create loading attributes with defaults', () => {
      const result = createLoadingAria();
      expect(result).toEqual({
        'aria-busy': true,
        'aria-label': 'Loading...',
        'aria-live': 'polite'
      });
    });
  });

  describe('mergeAriaProps', () => {
    it('should merge multiple aria prop objects', () => {
      const props1 = { 'aria-label': 'Label 1', 'aria-expanded': true };
      const props2 = { 'aria-label': 'Label 2', 'aria-selected': false };
      const result = mergeAriaProps(props1, props2);
      
      expect(result).toEqual({
        'aria-label': 'Label 2', // Later props override earlier ones
        'aria-expanded': true,
        'aria-selected': false
      });
    });

    it('should handle undefined props', () => {
      const props1 = { 'aria-label': 'Label 1' };
      const result = mergeAriaProps(props1, undefined, { 'aria-expanded': true });
      
      expect(result).toEqual({
        'aria-label': 'Label 1',
        'aria-expanded': true
      });
    });
  });

  describe('validateAriaProps', () => {
    it('should warn about conflicting label attributes', () => {
      const props = {
        'aria-label': 'Label',
        'aria-labelledby': 'label-id'
      };
      const warnings = validateAriaProps(props);
      expect(warnings).toContain('Both aria-label and aria-labelledby are present. aria-labelledby takes precedence.');
    });

    it('should warn about missing required attributes for tabs', () => {
      const props = { role: 'tab' };
      const warnings = validateAriaProps(props);
      expect(warnings).toContain('Tab role requires aria-selected attribute.');
    });

    it('should warn about missing labelledby for tabpanel', () => {
      const props = { role: 'tabpanel' };
      const warnings = validateAriaProps(props);
      expect(warnings).toContain('Tabpanel role should have aria-labelledby pointing to the associated tab.');
    });

    it('should return no warnings for valid props', () => {
      const props = {
        role: 'tab',
        'aria-selected': true
      };
      const warnings = validateAriaProps(props);
      expect(warnings).toHaveLength(0);
    });
  });

  describe('ARIA_ROLES', () => {
    it('should contain expected role constants', () => {
      expect(ARIA_ROLES.BUTTON).toBe('button');
      expect(ARIA_ROLES.NAVIGATION).toBe('navigation');
      expect(ARIA_ROLES.MAIN).toBe('main');
      expect(ARIA_ROLES.DIALOG).toBe('dialog');
      expect(ARIA_ROLES.TAB).toBe('tab');
      expect(ARIA_ROLES.TABPANEL).toBe('tabpanel');
    });
  });
});