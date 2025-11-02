/**
 * Email Template Engine Tests
 * 
 * Tests for template rendering, validation, and management functionality.
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { TemplateEngine, EmailTemplateManager } from '../template-engine';
import { EmailTemplate, EmailTemplateVariables } from '../types';

describe('TemplateEngine', () => {
  describe('render', () => {
    it('should replace simple variables', () => {
      const template = 'Hello {{name}}, welcome to {{system}}!';
      const variables: EmailTemplateVariables = {
        name: 'John Doe',
        system: 'AI Karen',
      };

      const result = TemplateEngine.render(template, variables);
      expect(result).toBe('Hello John Doe, welcome to AI Karen!');

    it('should handle conditional blocks', () => {
      const template = 'Hello {{name}}{{#if urgent}}, this is urgent!{{/if}}';
      
      const withCondition: EmailTemplateVariables = {
        name: 'John',
        urgent: true,
      };
      
      const withoutCondition: EmailTemplateVariables = {
        name: 'John',
        urgent: false,
      };

      expect(TemplateEngine.render(template, withCondition)).toBe('Hello John, this is urgent!');
      expect(TemplateEngine.render(template, withoutCondition)).toBe('Hello John');

    it('should clean up unused template syntax', () => {
      const template = 'Hello {{name}}, {{unknown_variable}}';
      const variables: EmailTemplateVariables = {
        name: 'John',
      };

      const result = TemplateEngine.render(template, variables);
      expect(result).toBe('Hello John, ');

    it('should handle missing variables gracefully', () => {
      const template = 'Hello {{name}}, your role is {{role}}';
      const variables: EmailTemplateVariables = {
        name: 'John',
      };

      const result = TemplateEngine.render(template, variables);
      expect(result).toBe('Hello John, your role is ');


  describe('extractVariables', () => {
    it('should extract simple variables', () => {
      const template = 'Hello {{name}}, welcome to {{system}}!';
      const variables = TemplateEngine.extractVariables(template);
      
      expect(variables).toEqual(['name', 'system']);

    it('should extract variables from conditional blocks', () => {
      const template = 'Hello {{name}}{{#if urgent}}, urgent message{{/if}}';
      const variables = TemplateEngine.extractVariables(template);
      
      expect(variables).toEqual(['name', 'urgent']);

    it('should handle duplicate variables', () => {
      const template = 'Hello {{name}}, {{name}} is your name';
      const variables = TemplateEngine.extractVariables(template);
      
      expect(variables).toEqual(['name']);


  describe('validateTemplate', () => {
    let mockTemplate: EmailTemplate;

    beforeEach(() => {
      mockTemplate = {
        id: 'test-template',
        name: 'Test Template',
        subject: 'Hello {{name}}',
        html_content: '<p>Hello {{name}}, welcome to {{system}}!</p>',
        text_content: 'Hello {{name}}, welcome to {{system}}!',
        template_type: 'user_welcome',
        variables: ['name', 'system'],
        is_active: true,
        created_at: new Date(),
        updated_at: new Date(),
        created_by: 'test-user',
      };

    it('should validate a correct template', () => {
      const validation = TemplateEngine.validateTemplate(mockTemplate);
      
      expect(validation.is_valid).toBe(true);
      expect(validation.errors).toHaveLength(0);
      expect(validation.missing_variables).toHaveLength(0);
      expect(validation.unused_variables).toHaveLength(0);

    it('should detect missing variable declarations', () => {
      mockTemplate.html_content = '<p>Hello {{name}}, your email is {{email}}!</p>';
      
      const validation = TemplateEngine.validateTemplate(mockTemplate);
      
      expect(validation.is_valid).toBe(false);
      expect(validation.missing_variables).toContain('email');

    it('should detect unused variable declarations', () => {
      mockTemplate.variables = ['name', 'system', 'unused_var'];
      
      const validation = TemplateEngine.validateTemplate(mockTemplate);
      
      expect(validation.is_valid).toBe(true);
      expect(validation.unused_variables).toContain('unused_var');
      expect(validation.warnings.length).toBeGreaterThan(0);

    it('should validate with provided variables', () => {
      const variables: EmailTemplateVariables = {
        name: 'John',
        system: 'AI Karen',
      };
      
      const validation = TemplateEngine.validateTemplate(mockTemplate, variables);
      
      expect(validation.is_valid).toBe(true);

    it('should detect empty subject', () => {
      mockTemplate.subject = '';
      
      const validation = TemplateEngine.validateTemplate(mockTemplate);
      
      expect(validation.is_valid).toBe(false);
      expect(validation.errors).toContain('Subject is required');



describe('EmailTemplateManager', () => {
  describe('createDefaultTemplates', () => {
    it('should create all default templates', async () => {
      const templates = await EmailTemplateManager.createDefaultTemplates('test-user');
      
      expect(templates).toHaveLength(3);
      expect(templates.map(t => t.template_type)).toEqual([
        'admin_invitation',
        'user_welcome',
        'security_alert'
      ]);

    it('should set correct metadata for default templates', async () => {
      const templates = await EmailTemplateManager.createDefaultTemplates('test-user');
      
      templates.forEach(template => {
        expect(template.id).toMatch(/^default_/);
        expect(template.is_active).toBe(true);
        expect(template.created_by).toBe('test-user');
        expect(template.created_at).toBeInstanceOf(Date);
        expect(template.updated_at).toBeInstanceOf(Date);



  describe('createTemplate', () => {
    it('should create a new template with correct properties', () => {
      const request = {
        name: 'Test Template',
        subject: 'Test Subject {{name}}',
        html_content: '<p>Test content {{name}}</p>',
        text_content: 'Test content {{name}}',
        template_type: 'user_welcome' as const,
        variables: ['name'],
      };

      const template = EmailTemplateManager.createTemplate(request, 'test-user');

      expect(template.name).toBe(request.name);
      expect(template.subject).toBe(request.subject);
      expect(template.html_content).toBe(request.html_content);
      expect(template.text_content).toBe(request.text_content);
      expect(template.template_type).toBe(request.template_type);
      expect(template.variables).toEqual(request.variables);
      expect(template.is_active).toBe(true);
      expect(template.created_by).toBe('test-user');
      expect(template.id).toMatch(/^template_/);


  describe('updateTemplate', () => {
    let existingTemplate: EmailTemplate;

    beforeEach(() => {
      existingTemplate = {
        id: 'test-template',
        name: 'Original Name',
        subject: 'Original Subject',
        html_content: '<p>Original content</p>',
        text_content: 'Original content',
        template_type: 'user_welcome',
        variables: ['name'],
        is_active: true,
        created_at: new Date('2023-01-01'),
        updated_at: new Date('2023-01-01'),
        created_by: 'original-user',
      };

    it('should update specified fields only', () => {
      const updateRequest = {
        name: 'Updated Name',
        subject: 'Updated Subject',
      };

      const updatedTemplate = EmailTemplateManager.updateTemplate(existingTemplate, updateRequest);

      expect(updatedTemplate.name).toBe('Updated Name');
      expect(updatedTemplate.subject).toBe('Updated Subject');
      expect(updatedTemplate.html_content).toBe(existingTemplate.html_content);
      expect(updatedTemplate.text_content).toBe(existingTemplate.text_content);
      expect(updatedTemplate.updated_at).not.toEqual(existingTemplate.updated_at);

    it('should preserve original fields when not updated', () => {
      const updateRequest = {
        name: 'Updated Name',
      };

      const updatedTemplate = EmailTemplateManager.updateTemplate(existingTemplate, updateRequest);

      expect(updatedTemplate.id).toBe(existingTemplate.id);
      expect(updatedTemplate.created_at).toEqual(existingTemplate.created_at);
      expect(updatedTemplate.created_by).toBe(existingTemplate.created_by);


  describe('generatePreview', () => {
    let mockTemplate: EmailTemplate;

    beforeEach(() => {
      mockTemplate = {
        id: 'test-template',
        name: 'Test Template',
        subject: 'Hello {{name}}',
        html_content: '<p>Hello {{name}}, welcome to {{system}}!</p>',
        text_content: 'Hello {{name}}, welcome to {{system}}!',
        template_type: 'user_welcome',
        variables: ['name', 'system'],
        is_active: true,
        created_at: new Date(),
        updated_at: new Date(),
        created_by: 'test-user',
      };

    it('should generate preview with sample variables', () => {
      const preview = EmailTemplateManager.generatePreview(mockTemplate);

      expect(preview.subject).toContain('John Doe');
      expect(preview.html).toContain('John Doe');
      expect(preview.html).toContain('AI Karen Admin System');
      expect(preview.text).toContain('John Doe');
      expect(preview.text).toContain('AI Karen Admin System');

    it('should generate preview with custom variables', () => {
      const customVariables: EmailTemplateVariables = {
        name: 'Jane Smith',
        system: 'Custom System',
      };

      const preview = EmailTemplateManager.generatePreview(mockTemplate, customVariables);

      expect(preview.subject).toBe('Hello Jane Smith');
      expect(preview.html).toBe('<p>Hello Jane Smith, welcome to Custom System!</p>');
      expect(preview.text).toBe('Hello Jane Smith, welcome to Custom System!');


  describe('getTemplateByType', () => {
    let mockTemplates: EmailTemplate[];

    beforeEach(async () => {
      mockTemplates = await EmailTemplateManager.createDefaultTemplates('test-user');

    it('should find template by type', () => {
      const template = EmailTemplateManager.getTemplateByType(mockTemplates, 'admin_invitation');
      
      expect(template).toBeDefined();
      expect(template?.template_type).toBe('admin_invitation');

    it('should return undefined for non-existent type', () => {
      const template = EmailTemplateManager.getTemplateByType(mockTemplates, 'non_existent' as any);
      
      expect(template).toBeUndefined();

    it('should only return active templates', () => {
      // Mark a template as inactive
      mockTemplates[0].is_active = false;
      
      const template = EmailTemplateManager.getTemplateByType(mockTemplates, mockTemplates[0].template_type);
      
      expect(template).toBeUndefined();


  describe('cloneTemplate', () => {
    let originalTemplate: EmailTemplate;

    beforeEach(() => {
      originalTemplate = {
        id: 'original-template',
        name: 'Original Template',
        subject: 'Original Subject',
        html_content: '<p>Original content</p>',
        text_content: 'Original content',
        template_type: 'user_welcome',
        variables: ['name'],
        is_active: true,
        created_at: new Date('2023-01-01'),
        updated_at: new Date('2023-01-01'),
        created_by: 'original-user',
      };

    it('should create a clone with new ID and metadata', () => {
      const clonedTemplate = EmailTemplateManager.cloneTemplate(
        originalTemplate,
        'Cloned Template',
        'clone-user'
      );

      expect(clonedTemplate.id).not.toBe(originalTemplate.id);
      expect(clonedTemplate.name).toBe('Cloned Template');
      expect(clonedTemplate.created_by).toBe('clone-user');
      expect(clonedTemplate.created_at).not.toEqual(originalTemplate.created_at);
      expect(clonedTemplate.updated_at).not.toEqual(originalTemplate.updated_at);

    it('should preserve template content and configuration', () => {
      const clonedTemplate = EmailTemplateManager.cloneTemplate(
        originalTemplate,
        'Cloned Template',
        'clone-user'
      );

      expect(clonedTemplate.subject).toBe(originalTemplate.subject);
      expect(clonedTemplate.html_content).toBe(originalTemplate.html_content);
      expect(clonedTemplate.text_content).toBe(originalTemplate.text_content);
      expect(clonedTemplate.template_type).toBe(originalTemplate.template_type);
      expect(clonedTemplate.variables).toEqual(originalTemplate.variables);
      expect(clonedTemplate.is_active).toBe(originalTemplate.is_active);


