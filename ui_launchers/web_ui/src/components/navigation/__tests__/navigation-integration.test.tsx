import { describe, it, expect } from 'vitest';
import { RoleBasedNavigation } from '../RoleBasedNavigation';
import { AdminBreadcrumbs } from '../AdminBreadcrumbs';
import { NavigationLayout } from '../NavigationLayout';

describe('Navigation Components Integration', () => {
  it('exports navigation components correctly', () => {
    expect(RoleBasedNavigation).toBeDefined();
    expect(AdminBreadcrumbs).toBeDefined();
    expect(NavigationLayout).toBeDefined();

  it('components are functions', () => {
    expect(typeof RoleBasedNavigation).toBe('function');
    expect(typeof AdminBreadcrumbs).toBe('function');
    expect(typeof NavigationLayout).toBe('function');

