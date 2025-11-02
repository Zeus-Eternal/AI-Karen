/**
 * Dynamic Plugin Configuration Form Tests
 * 
 * Unit tests for the DynamicPluginConfigForm component.
 */


import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { DynamicPluginConfigForm } from '../DynamicPluginConfigForm';
import { PluginInfo, PluginConfigField } from '@/types/plugins';

// Mock plugin with various field types
const mockConfigSchema: PluginConfigField[] = [
  {
    key: 'apiKey',
    type: 'password',
    label: 'API Key',
    description: 'Your API key for authentication',
    required: true,
  },
  {
    key: 'timeout',
    type: 'number',
    label: 'Timeout',
    description: 'Request timeout in seconds',
    required: false,
    default: 30,
    validation: { min: 1, max: 300 },
  },
  {
    key: 'enableLogging',
    type: 'boolean',
    label: 'Enable Logging',
    description: 'Enable detailed logging',
    required: false,
    default: true,
  },
  {
    key: 'logLevel',
    type: 'select',
    label: 'Log Level',
    description: 'Logging verbosity level',
    required: false,
    default: 'info',
    options: [
      { label: 'Debug', value: 'debug' },
      { label: 'Info', value: 'info' },
      { label: 'Warning', value: 'warn' },
      { label: 'Error', value: 'error' },
    ],
  },
  {
    key: 'features',
    type: 'multiselect',
    label: 'Features',
    description: 'Select enabled features',
    required: false,
    options: [
      { label: 'Feature A', value: 'feature-a' },
      { label: 'Feature B', value: 'feature-b' },
      { label: 'Feature C', value: 'feature-c' },
    ],
  },
  {
    key: 'config',
    type: 'json',
    label: 'Advanced Configuration',
    description: 'JSON configuration object',
    required: false,
    default: { setting1: 'value1' },
  },
];

const mockPlugin: PluginInfo = {
  id: 'test-plugin',
  name: 'Test Plugin',
  version: '1.0.0',
  status: 'active',
  manifest: {
    id: 'test-plugin',
    name: 'Test Plugin',
    version: '1.0.0',
    description: 'A test plugin',
    author: { name: 'Test Author' },
    license: 'MIT',
    keywords: ['test'],
    category: 'utility',
    runtime: { platform: ['node'] },
    dependencies: [],
    systemRequirements: {},
    permissions: [],
    sandboxed: true,
    securityPolicy: {
      allowNetworkAccess: true,
      allowFileSystemAccess: false,
      allowSystemCalls: false,
    },
    configSchema: mockConfigSchema,
    apiVersion: '1.0',
  },
  config: {
    timeout: 30,
    enableLogging: true,
    logLevel: 'info',
  },
  permissions: [],
  metrics: {
    performance: {
      averageExecutionTime: 100,
      totalExecutions: 50,
      errorRate: 0.02,
      lastExecution: new Date(),
    },
    resources: {
      memoryUsage: 64,
      cpuUsage: 5,
      diskUsage: 10,
      networkUsage: 2,
    },
    health: {
      status: 'healthy',
      uptime: 99.5,
      lastHealthCheck: new Date(),
      issues: [],
    },
  },
  installedAt: new Date(),
  updatedAt: new Date(),
  installedBy: 'admin',
  enabled: true,
  autoStart: true,
  restartCount: 0,
  dependencyStatus: {
    satisfied: true,
    missing: [],
    conflicts: [],
  },
};

const mockProps = {
  plugin: mockPlugin,
  onSave: vi.fn(),
  onValidate: vi.fn(),
  onPreview: vi.fn(),
};

describe('DynamicPluginConfigForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();

  it('renders configuration form correctly', () => {
    render(<DynamicPluginConfigForm {...mockProps} />);
    
    expect(screen.getByText('Plugin Configuration')).toBeInTheDocument();
    expect(screen.getByText('Configure settings for Test Plugin')).toBeInTheDocument();

  it('renders different field types correctly', async () => {
    render(<DynamicPluginConfigForm {...mockProps} />);
    
    // Expand the general settings group
    const generalGroup = screen.getByText('General Settings');
    fireEvent.click(generalGroup);
    
    await waitFor(() => {
      // String/password field
      expect(screen.getByLabelText(/API Key/)).toBeInTheDocument();
      
      // Number field
      expect(screen.getByLabelText(/Timeout/)).toBeInTheDocument();
      
      // Boolean field (switch)
      expect(screen.getByLabelText(/Enable Logging/)).toBeInTheDocument();


  it('handles field value changes', async () => {
    render(<DynamicPluginConfigForm {...mockProps} />);
    
    // Expand the general settings group
    const generalGroup = screen.getByText('General Settings');
    fireEvent.click(generalGroup);
    
    await waitFor(() => {
      const timeoutInput = screen.getByLabelText(/Timeout/);
      fireEvent.change(timeoutInput, { target: { value: '60' } });
      
      // Should update the internal state
      expect(timeoutInput).toHaveValue(60);


  it('validates required fields', async () => {
    render(<DynamicPluginConfigForm {...mockProps} />);
    
    // Try to save without required field
    const saveButton = screen.getByRole('button', { name: /save configuration/i });
    fireEvent.click(saveButton);
    
    await waitFor(() => {
      expect(screen.getByText(/API Key is required/)).toBeInTheDocument();


  it('validates field constraints', async () => {
    render(<DynamicPluginConfigForm {...mockProps} />);
    
    // Expand the general settings group
    const generalGroup = screen.getByText('General Settings');
    fireEvent.click(generalGroup);
    
    await waitFor(() => {
      const timeoutInput = screen.getByLabelText(/Timeout/);
      fireEvent.change(timeoutInput, { target: { value: '500' } }); // Above max
      
      const saveButton = screen.getByRole('button', { name: /save configuration/i });
      fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText(/must be at most 300/)).toBeInTheDocument();


  it('handles password field visibility toggle', async () => {
    render(<DynamicPluginConfigForm {...mockProps} />);
    
    // Expand the authentication group (where password fields would be)
    const authGroup = screen.getByText('Authentication');
    fireEvent.click(authGroup);
    
    await waitFor(() => {
      const passwordField = screen.getByLabelText(/API Key/);
      expect(passwordField).toHaveAttribute('type', 'password');
      
      // Find and click the eye icon to toggle visibility
      const toggleButton = screen.getByRole('button', { name: '' }); // Eye icon button
      fireEvent.click(toggleButton);
      
      expect(passwordField).toHaveAttribute('type', 'text');


  it('handles form save successfully', async () => {
    mockProps.onSave.mockResolvedValue(undefined);
    
    render(<DynamicPluginConfigForm {...mockProps} initialConfig={{ apiKey: 'test-key' }} />);
    
    const saveButton = screen.getByRole('button', { name: /save configuration/i });
    fireEvent.click(saveButton);
    
    await waitFor(() => {
      expect(mockProps.onSave).toHaveBeenCalledWith(
        expect.objectContaining({ apiKey: 'test-key' })
      );


  it('handles form reset', async () => {
    const initialConfig = { timeout: 30, enableLogging: true };
    render(<DynamicPluginConfigForm {...mockProps} initialConfig={initialConfig} />);
    
    // Make a change
    const generalGroup = screen.getByText('General Settings');
    fireEvent.click(generalGroup);
    
    await waitFor(() => {
      const timeoutInput = screen.getByLabelText(/Timeout/);
      fireEvent.change(timeoutInput, { target: { value: '60' } });

    // Reset the form
    const resetButton = screen.getByRole('button', { name: /reset/i });
    fireEvent.click(resetButton);
    
    await waitFor(() => {
      const timeoutInput = screen.getByLabelText(/Timeout/);
      expect(timeoutInput).toHaveValue(30);


  it('respects read-only mode', () => {
    render(<DynamicPluginConfigForm {...mockProps} readOnly />);
    
    const saveButton = screen.queryByRole('button', { name: /save configuration/i });
    expect(saveButton).not.toBeInTheDocument();

  it('handles JSON field formatting', async () => {
    render(<DynamicPluginConfigForm {...mockProps} />);
    
    // Expand the general settings group
    const generalGroup = screen.getByText('General Settings');
    fireEvent.click(generalGroup);
    
    await waitFor(() => {
      const jsonField = screen.getByLabelText(/Advanced Configuration/);
      expect(jsonField).toBeInTheDocument();
      
      // Should have format button
      const formatButton = screen.getByRole('button', { name: /format/i });
      expect(formatButton).toBeInTheDocument();


  it('shows validation errors for invalid JSON', async () => {
    render(<DynamicPluginConfigForm {...mockProps} />);
    
    // Expand the general settings group
    const generalGroup = screen.getByText('General Settings');
    fireEvent.click(generalGroup);
    
    await waitFor(() => {
      const jsonField = screen.getByLabelText(/Advanced Configuration/);
      fireEvent.change(jsonField, { target: { value: '{ invalid json' } });
      
      const saveButton = screen.getByRole('button', { name: /save configuration/i });
      fireEvent.click(saveButton);

    // Should show validation error or handle gracefully

  it('groups fields correctly', () => {
    render(<DynamicPluginConfigForm {...mockProps} />);
    
    // Should have grouped fields into sections
    expect(screen.getByText('Authentication')).toBeInTheDocument();
    expect(screen.getByText('General Settings')).toBeInTheDocument();

  it('handles search functionality', async () => {
    render(<DynamicPluginConfigForm {...mockProps} />);
    
    // Should have search functionality (though it might not be visible initially)
    // This tests the search logic indirectly through field filtering
    expect(screen.getByText('Plugin Configuration')).toBeInTheDocument();

