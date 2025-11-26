/**
 * Permission Registry
 * 
 * This class manages the registration and retrieval of permissions in the RBAC system.
 * It provides a centralized way to register, validate, and retrieve permissions.
 */

import { Permission, PermissionCategory } from '../types';
import {
  PermissionNotFoundError,
  InvalidPermissionError
} from '../utils/errors';

/**
 * The PermissionRegistry class manages permission definitions and provides methods to register,
 * validate, and retrieve permissions.
 */
export class PermissionRegistry {
  private permissions: Set<Permission> = new Set();
  private categories: Map<string, PermissionCategory> = new Map();
  private isInitialized = false;

  /**
   * Initialize the permission registry with default permissions
   */
  public initialize(): void {
    if (this.isInitialized) {
      return;
    }

    // Clear any existing permissions and categories
    this.permissions.clear();
    this.categories.clear();

    this.isInitialized = true;
  }

  /**
   * Register a new permission
   * @param permission The permission to register
   * @throws InvalidPermissionError if the permission is invalid
   */
  public registerPermission(permission: Permission): void {
    this.validatePermission(permission);
    this.permissions.add(permission);
  }

  /**
   * Register multiple permissions at once
   * @param permissions An array of permissions to register
   * @throws InvalidPermissionError if any permission is invalid
   */
  public registerPermissions(permissions: Permission[]): void {
    // First validate all permissions
    for (const permission of permissions) {
      this.validatePermission(permission);
    }

    // Then register all permissions
    for (const permission of permissions) {
      this.permissions.add(permission);
    }
  }

  /**
   * Get a permission by name
   * @param permission The name of the permission
   * @returns The permission
   * @throws PermissionNotFoundError if the permission is not found
   */
  public getPermission(permission: Permission): Permission {
    if (!this.permissions.has(permission)) {
      throw new PermissionNotFoundError(permission);
    }
    return permission;
  }

  /**
   * Check if a permission exists
   * @param permission The name of the permission
   * @returns True if the permission exists, false otherwise
   */
  public hasPermission(permission: Permission): boolean {
    return this.permissions.has(permission);
  }

  /**
   * Get all registered permissions
   * @returns An array of all permissions
   */
  public getAllPermissions(): Permission[] {
    return Array.from(this.permissions);
  }

  /**
   * Remove a permission from the registry
   * @param permission The permission to remove
   * @throws PermissionNotFoundError if the permission is not found
   */
  public removePermission(permission: Permission): void {
    if (!this.permissions.has(permission)) {
      throw new PermissionNotFoundError(permission);
    }
    this.permissions.delete(permission);
  }

  /**
   * Clear all permissions from the registry
   */
  public clear(): void {
    this.permissions.clear();
    this.categories.clear();
    this.isInitialized = false;
  }

  /**
   * Get the number of registered permissions
   * @returns The number of registered permissions
   */
  public size(): number {
    return this.permissions.size;
  }

  /**
   * Check if the registry is initialized
   * @returns True if the registry is initialized, false otherwise
   */
  public initialized(): boolean {
    return this.isInitialized;
  }

  /**
   * Register a permission category
   * @param category The permission category to register
   * @throws InvalidPermissionError if the category is invalid
   */
  public registerCategory(category: PermissionCategory): void {
    this.validateCategory(category);
    this.categories.set(category.name, category);
    
    // Also register all permissions in the category
    this.registerPermissions(category.permissions);
  }

  /**
   * Register multiple permission categories at once
   * @param categories An array of permission categories to register
   * @throws InvalidPermissionError if any category is invalid
   */
  public registerCategories(categories: PermissionCategory[]): void {
    // First validate all categories
    for (const category of categories) {
      this.validateCategory(category);
    }

    // Then register all categories and their permissions
    for (const category of categories) {
      this.categories.set(category.name, category);
      this.registerPermissions(category.permissions);
    }
  }

  /**
   * Get a permission category by name
   * @param name The name of the category
   * @returns The permission category
   * @throws InvalidPermissionError if the category is not found
   */
  public getCategory(name: string): PermissionCategory {
    const category = this.categories.get(name);
    if (!category) {
      throw new InvalidPermissionError(name, `Category '${name}' not found`);
    }
    return { ...category }; // Return a copy to prevent mutation
  }

  /**
   * Check if a permission category exists
   * @param name The name of the category
   * @returns True if the category exists, false otherwise
   */
  public hasCategory(name: string): boolean {
    return this.categories.has(name);
  }

  /**
   * Get all registered permission categories
   * @returns An array of all permission categories
   */
  public getAllCategories(): PermissionCategory[] {
    return Array.from(this.categories.values()).map(category => ({ ...category }));
  }

  /**
   * Get the category that contains a specific permission
   * @param permission The permission to find the category for
   * @returns The permission category that contains the permission, or undefined if not found
   */
  public getCategoryForPermission(permission: Permission): PermissionCategory | undefined {
    for (const category of this.categories.values()) {
      if (category.permissions.includes(permission)) {
        return { ...category };
      }
    }
    return undefined;
  }

  /**
   * Get all permissions in a specific category
   * @param categoryName The name of the category
   * @returns An array of permissions in the category
   * @throws InvalidPermissionError if the category is not found
   */
  public getPermissionsInCategory(categoryName: string): Permission[] {
    const category = this.getCategory(categoryName);
    return [...category.permissions];
  }

  /**
   * Remove a permission category
   * @param name The name of the category to remove
   * @throws InvalidPermissionError if the category is not found
   */
  public removeCategory(name: string): void {
    if (!this.categories.has(name)) {
      throw new InvalidPermissionError(name, `Category '${name}' not found`);
    }
    this.categories.delete(name);
  }

  /**
   * Validate a permission
   * @param permission The permission to validate
   * @throws InvalidPermissionError if the permission is invalid
   */
  private validatePermission(permission: Permission): void {
    if (!permission || typeof permission !== 'string') {
      throw new InvalidPermissionError(
        permission as string,
        'Permission must be a non-empty string'
      );
    }

    // Check permission format (e.g., "resource:action")
    const parts = permission.split(':');
    if (parts.length < 2) {
      throw new InvalidPermissionError(
        permission,
        'Permission must be in the format "resource:action"'
      );
    }

    // Check that each part is non-empty
    for (const part of parts) {
      if (!part.trim()) {
        throw new InvalidPermissionError(
          permission,
          'Permission parts must not be empty'
        );
      }
    }
  }

  /**
   * Validate a permission category
   * @param category The permission category to validate
   * @throws InvalidPermissionError if the category is invalid
   */
  private validateCategory(category: PermissionCategory): void {
    if (!category || typeof category !== 'object') {
      throw new InvalidPermissionError(
        'category',
        'Category must be an object'
      );
    }

    if (!category.name || typeof category.name !== 'string') {
      throw new InvalidPermissionError(
        category.name || 'undefined',
        'Category name must be a non-empty string'
      );
    }

    if (!category.description || typeof category.description !== 'string') {
      throw new InvalidPermissionError(
        category.name,
        'Category description must be a non-empty string'
      );
    }

    if (!Array.isArray(category.permissions)) {
      throw new InvalidPermissionError(
        category.name,
        'Category permissions must be an array'
      );
    }

    // Validate all permissions in the category
    for (const permission of category.permissions) {
      this.validatePermission(permission);
    }
  }
}

// Export a singleton instance
export const permissionRegistry = new PermissionRegistry();