/**
 * Email Template Engine
 * 
 * Template rendering, validation, and management system for email templates.
 * Supports variable substitution, conditional content, and template validation.
 */
import { 
  EmailTemplate, 
  EmailTemplateVariables, 
  EmailTemplateValidation,
  CreateEmailTemplateRequest,
  UpdateEmailTemplateRequest 
} from './types';
import { DEFAULT_TEMPLATES } from './config';
/**
 * Simple template variable replacement
 * Supports {{variable}} syntax with basic conditional blocks
 */
export class TemplateEngine {
  /**
   * Render template content with variables
   */
  static render(template: string, variables: EmailTemplateVariables): string {
    let rendered = template;
    // Replace simple variables {{variable}}
    Object.entries(variables).forEach(([key, value]) => {
      const regex = new RegExp(`{{\\s*${key}\\s*}}`, 'g');
      rendered = rendered.replace(regex, String(value));
    });
    // Handle conditional blocks {{#if variable}}...{{/if}}
    rendered = this.renderConditionals(rendered, variables);
    // Clean up any remaining template syntax
    rendered = this.cleanupTemplate(rendered);
    return rendered;
  }
  /**
   * Render conditional blocks
   */
  private static renderConditionals(template: string, variables: EmailTemplateVariables): string {
    const conditionalRegex = /{{#if\s+(\w+)}}([\s\S]*?){{\/if}}/g;
    return template.replace(conditionalRegex, (match, variable, content) => {
      const value = variables[variable];
      return value ? content : '';
    });
  }
  /**
   * Clean up remaining template syntax
   */
  private static cleanupTemplate(template: string): string {
    // Remove any remaining template variables
    return template.replace(/{{[^}]*}}/g, '');
  }
  /**
   * Extract variables from template content
   */
  static extractVariables(template: string): string[] {
    const variables = new Set<string>();
    const regex = /{{(?:#if\s+)?(\w+)(?:\s*}}|[^}]*}})/g;
    let match;
    while ((match = regex.exec(template)) !== null) {
      variables.add(match[1]);
    }
    return Array.from(variables);
  }
  /**
   * Validate template syntax and variables
   */
  static validateTemplate(template: EmailTemplate, variables?: EmailTemplateVariables): EmailTemplateValidation {
    const errors: string[] = [];
    const warnings: string[] = [];
    const htmlIssues: string[] = [];
    const textIssues: string[] = [];
    // Extract variables from content
    const htmlVariables = this.extractVariables(template.html_content);
    const textVariables = this.extractVariables(template.text_content);
    const subjectVariables = this.extractVariables(template.subject);
    const allTemplateVariables = new Set([...htmlVariables, ...textVariables, ...subjectVariables]);
    const declaredVariables = new Set(template.variables);
    // Check for missing variable declarations
    const missingVariables = Array.from(allTemplateVariables).filter(v => !declaredVariables.has(v));
    const unusedVariables = template.variables.filter(v => !allTemplateVariables.has(v));
    if (missingVariables.length > 0) {
      errors.push(`Missing variable declarations: ${missingVariables.join(', ')}`);
    }
    if (unusedVariables.length > 0) {
      warnings.push(`Unused declared variables: ${unusedVariables.join(', ')}`);
    }
    // Validate HTML content
    if (template.html_content) {
      const htmlValidation = this.validateHtmlContent(template.html_content);
      htmlIssues.push(...htmlValidation);
    }
    // Validate text content
    if (!template.text_content.trim()) {
      warnings.push('Text content is empty - consider adding plain text version');
    }
    // Validate subject
    if (!template.subject.trim()) {
      errors.push('Subject is required');
    }
    // If variables provided, test rendering
    if (variables) {
      try {
        this.render(template.html_content, variables);
        this.render(template.text_content, variables);
        this.render(template.subject, variables);
      } catch (error) {
        errors.push(`Template rendering failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    }
    return {
      template_id: template.id,
      is_valid: errors.length === 0,
      errors,
      warnings,
      missing_variables: missingVariables,
      unused_variables: unusedVariables,
      html_issues: htmlIssues,
      text_issues: textIssues,
      validated_at: new Date(),
    };
  }
  /**
   * Basic HTML validation
   */
  private static validateHtmlContent(html: string): string[] {
    const issues: string[] = [];
    // Check for basic HTML structure
    if (!html.includes('<html>') && !html.includes('<div>') && !html.includes('<p>')) {
      issues.push('HTML content appears to lack proper structure');
    }
    // Check for unclosed tags (basic check)
    const openTags = html.match(/<[^/][^>]*>/g) || [];
    const closeTags = html.match(/<\/[^>]*>/g) || [];
    if (openTags.length !== closeTags.length) {
      issues.push('Possible unclosed HTML tags detected');
    }
    // Check for inline styles (recommended for email)
    if (html.includes('<style>') || html.includes('class=')) {
      issues.push('Consider using inline styles instead of CSS classes for better email client compatibility');
    }
    return issues;
  }
}
/**
 * Email Template Manager
 */
export class EmailTemplateManager {
  /**
   * Create default templates
   */
  static async createDefaultTemplates(createdBy: string): Promise<EmailTemplate[]> {
    const templates: EmailTemplate[] = [];
    for (const [type, defaultTemplate] of Object.entries(DEFAULT_TEMPLATES)) {
      const template: EmailTemplate = {
        id: `default_${type}`,
        name: defaultTemplate.name,
        subject: defaultTemplate.subject,
        html_content: defaultTemplate.html_content,
        text_content: defaultTemplate.text_content,
        template_type: type as EmailTemplate['template_type'],
        variables: [...defaultTemplate.variables],
        is_active: true,
        created_at: new Date(),
        updated_at: new Date(),
        created_by: createdBy,
      };
      templates.push(template);
    }
    return templates;
  }
  /**
   * Create new template
   */
  static createTemplate(request: CreateEmailTemplateRequest, createdBy: string): EmailTemplate {
    const template: EmailTemplate = {
      id: `template_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      name: request.name,
      subject: request.subject,
      html_content: request.html_content,
      text_content: request.text_content,
      template_type: request.template_type,
      variables: request.variables,
      is_active: true,
      created_at: new Date(),
      updated_at: new Date(),
      created_by: createdBy,
    };
    return template;
  }
  /**
   * Update existing template
   */
  static updateTemplate(
    existingTemplate: EmailTemplate, 
    request: UpdateEmailTemplateRequest
  ): EmailTemplate {
    return {
      ...existingTemplate,
      name: request.name ?? existingTemplate.name,
      subject: request.subject ?? existingTemplate.subject,
      html_content: request.html_content ?? existingTemplate.html_content,
      text_content: request.text_content ?? existingTemplate.text_content,
      variables: request.variables ?? existingTemplate.variables,
      is_active: request.is_active ?? existingTemplate.is_active,
      updated_at: new Date(),
    };
  }
  /**
   * Generate template preview
   */
  static generatePreview(
    template: EmailTemplate, 
    sampleVariables?: EmailTemplateVariables
  ): { html: string; text: string; subject: string } {
    const variables = sampleVariables || this.generateSampleVariables(template.variables);
    return {
      html: TemplateEngine.render(template.html_content, variables),
      text: TemplateEngine.render(template.text_content, variables),
      subject: TemplateEngine.render(template.subject, variables),
    };
  }
  /**
   * Generate sample variables for preview
   */
  private static generateSampleVariables(variableNames: string[]): EmailTemplateVariables {
    const : Record<string, any> = {
      name: 'John Doe',
      full_name: 'John Doe',
      email: 'john.doe@example.com',
      system_name: 'AI Karen Admin System',
      system: 'AI Karen Admin System',
      invited_by_name: 'Admin User',
      created_by_name: 'System Administrator',
      role: 'Admin',
      invitation_link: 'https://example.com/accept-invitation?token=sample',
      setup_link: 'https://example.com/setup-password?token=sample',
      expiry_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toLocaleDateString(),
      created_date: new Date().toLocaleDateString(),
      alert_type: 'Failed Login Attempt',
      alert_time: new Date().toLocaleString(),
      user_email: 'user@example.com',
      ip_address: '192.168.1.100',
      alert_description: 'Multiple failed login attempts detected from this IP address.',
      action_required: 'Please verify this activity and consider changing your password.',
    };
    const variables: EmailTemplateVariables = {};
    variableNames.forEach(name => {
      variables[name] = [name] || `[${name}]`;
    });
    return variables;
  }
  /**
   * Validate all templates
   */
  static async validateAllTemplates(templates: EmailTemplate[]): Promise<EmailTemplateValidation[]> {
    return templates.map(template => TemplateEngine.validateTemplate(template));
  }
  /**
   * Get template by type
   */
  static getTemplateByType(
    templates: EmailTemplate[], 
    type: EmailTemplate['template_type']
  ): EmailTemplate | undefined {
    return templates.find(t => t.template_type === type && t.is_active);
  }
  /**
   * Clone template
   */
  static cloneTemplate(template: EmailTemplate, newName: string, createdBy: string): EmailTemplate {
    return {
      ...template,
      id: `template_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      name: newName,
      created_at: new Date(),
      updated_at: new Date(),
      created_by: createdBy,
    };
  }
}
/**
 * Template variable helpers
 */
export class TemplateVariableHelpers {
  /**
   * Get common admin variables
   */
  static getAdminInvitationVariables(data: {
    fullName: string;
    invitedByName: string;
    invitationLink: string;
    expiryDate: Date;
  }): EmailTemplateVariables {
    return {
      full_name: data.fullName,
      system_name: 'AI Karen Admin System',
      invited_by_name: data.invitedByName,
      invitation_link: data.invitationLink,
      expiry_date: data.expiryDate.toLocaleDateString(),
    };
  }
  /**
   * Get user welcome variables
   */
  static getUserWelcomeVariables(data: {
    fullName: string;
    email: string;
    role: string;
    createdByName: string;
    setupLink: string;
  }): EmailTemplateVariables {
    return {
      full_name: data.fullName,
      system_name: 'AI Karen Admin System',
      email: data.email,
      role: data.role,
      created_by_name: data.createdByName,
      created_date: new Date().toLocaleDateString(),
      setup_link: data.setupLink,
    };
  }
  /**
   * Get security alert variables
   */
  static getSecurityAlertVariables(data: {
    alertType: string;
    userEmail: string;
    ipAddress: string;
    alertDescription: string;
    actionRequired?: string;
  }): EmailTemplateVariables {
    return {
      alert_type: data.alertType,
      alert_time: new Date().toLocaleString(),
      user_email: data.userEmail,
      ip_address: data.ipAddress,
      alert_description: data.alertDescription,
      action_required: data.actionRequired || '',
      system_name: 'AI Karen Admin System',
    };
  }
}
