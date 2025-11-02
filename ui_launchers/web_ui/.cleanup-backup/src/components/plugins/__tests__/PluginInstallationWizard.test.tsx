/**
 * Plugin Installation Wizard Tests
 * 
 * Integration tests for the plugin installation wizard component.
 * Based on requirements: 5.2, 5.5, 9.1
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';

import { PluginInstallationWizard } from '../PluginInstallationWizard';
import { usePluginStore } from '@/store/plugin-store';
import { PluginMarketplaceEntry } from '@/types/plugins';

// Mock the plugin store
vi.mock('@/store/plugin-store');

// Mock file reading
const mockFileReader = {
  readAsText: vi.fn(),
  result: null,
  onload: null,
  onerror: null,
};

Object.defineProperty(window, 'FileReader', {
  writable: true,
  value: vi.fn(() => mockFileReader),
});

// Mock plugin data
const mockPlugin: PluginMarketplaceEntry = {
  id: 'test-plugin',
  name: 'Test Plugin',
  description: 'A test plugin for unit testing',
  version: '1.0.0',
  author: { name: 'Test Author', verified: true },
  category: 'utility',
  tags: ['test', 'utility'],
  downloads: 100,
  rating: 4.5,
  reviewCount: 10,
  featured: false,
  verified: true,
  compatibility: {
    minVersion: '1.0.0',
    platforms: ['node'],
  },
  screenshots: [],
  pricing: { type: 'free' },
  installUrl: 'https://test.com/plugin',
  manifest: {
    id: 'test-plugin',
    name: 'Test Plugin',
    version: '1.0.0',
    description: 'A test plugin for unit testing',
    author: { name: 'Test Author' },
    license: 'MIT',
    keywords: ['test'],
    category: 'utility',
    runtime: { platform: ['node'] },
    dependencies: [
      {
        id: 'test-dep',
        name: 'Test Dependency',
        version: '1.0.0',
        versionConstraint: '^1.0.0',
        optional: false,
        installed: false,
        compatible: true,
      },
    ],
    systemRequirements: {},
    permissions: [
      {
        id: 'test-permission',
        name: 'Test Permission',
        description: 'A test permission',
        category: 'system',
        level: 'read',
        required: true,
      },
      {
        id: 'optional-permission',
        name: 'Optional Permission',
        description: 'An optional permission',
        category: 'data',
        level: 'write',
        required: false,
      },
    ],
    sandboxed: true,
    securityPolicy: {
      allowNetworkAccess: true,
      allowFileSystemAccess: false,
      allowSystemCalls: false,
    },
    configSchema: [
      {
        key: 'apiKey',
        type: 'password',
        label: 'API Key',
        description: 'Your API key',
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
        key: 'enabled',
        type: 'boolean',
        label: 'Enabled',
        description: 'Enable the plugin',
        required: false,
        default: true,
      },
      {
        key: 'mode',
        type: 'select',
        label: 'Mode',
        description: 'Operation mode',
        required: false,
        default: 'production',
        options: [
          { label: 'Development', value: 'development' },
          { label: 'Production', value: 'production' },
        ],
      },
    ],
    apiVersion: '1.0',
  },
};

const mockUsePluginStore = {
  installPlugin: vi.fn(),
};

describe('PluginInstallationWizard', () => {
  const mockOnClose = vi.fn();
  const mockOnComplete = vi.fn();

  beforeEach(() => {
    vi.mocked(usePluginStore).mockReturnValue(mockUsePluginStore as any);
    mockUsePluginStore.installPlugin.mockResolvedValue('install-123');
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Source Selection Step', () => {
    it('renders source selection options', () => {
      render(
        <PluginInstallationWizard
          onClose={mockOnClose}
          onComplete={mockOnComplete}
        />
      );

      expect(screen.getByText('Choose Installation Source')).toBeInTheDocument();
      expect(screen.getByLabelText('Plugin Marketplace')).toBeInTheDocument();
      expect(screen.getByLabelText('Upload Plugin File')).toBeInTheDocument();
      expect(screen.getByLabelText('Download from URL')).toBeInTheDocument();
      expect(screen.getByLabelText('Git Repository')).toBeInTheDocument();
    });

    it('shows file input when file source is selected', async () => {
      const user = userEvent.setup();
      render(
        <PluginInstallationWizard
          onClose={mockOnClose}
          onComplete={mockOnComplete}
        />
      );

      await user.click(screen.getByLabelText('Upload Plugin File'));
      expect(screen.getByLabelText('Plugin File')).toBeInTheDocument();
    });

    it('shows URL input when URL source is selected', async () => {
      const user = userEvent.setup();
      render(
        <PluginInstallationWizard
          onClose={mockOnClose}
          onComplete={mockOnComplete}
        />
      );

      await user.click(screen.getByLabelText('Download from URL'));
      expect(screen.getByLabelText('Plugin URL')).toBeInTheDocument();
    });

    it('shows git inputs when git source is selected', async () => {
      const user = userEvent.setup();
      render(
        <PluginInstallationWizard
          onClose={mockOnClose}
          onComplete={mockOnComplete}
        />
      );

      await user.click(screen.getByLabelText('Git Repository'));
      expect(screen.getByLabelText('Git Repository')).toBeInTheDocument();
      expect(screen.getByLabelText('Branch')).toBeInTheDocument();
    });

    it('enables next button when valid source is selected', async () => {
      const user = userEvent.setup();
      render(
        <PluginInstallationWizard
          onClose={mockOnClose}
          onComplete={mockOnComplete}
        />
      );

      const nextButton = screen.getByRole('button', { name: /next/i });
      expect(nextButton).toBeDisabled();

      await user.click(screen.getByLabelText('Plugin Marketplace'));
      expect(nextButton).toBeEnabled();
    });
  });

  describe('Plugin Selection Step', () => {
    it('shows plugin selection when marketplace is chosen', async () => {
      const user = userEvent.setup();
      render(
        <PluginInstallationWizard
          onClose={mockOnClose}
          onComplete={mockOnComplete}
        />
      );

      await user.click(screen.getByLabelText('Plugin Marketplace'));
      await user.click(screen.getByRole('button', { name: /next/i }));

      expect(screen.getByText('Select Plugin')).toBeInTheDocument();
    });

    it('allows plugin selection from marketplace', async () => {
      const user = userEvent.setup();
      render(
        <PluginInstallationWizard
          onClose={mockOnClose}
          onComplete={mockOnComplete}
        />
      );

      await user.click(screen.getByLabelText('Plugin Marketplace'));
      await user.click(screen.getByRole('button', { name: /next/i }));

      // Mock plugins should be displayed
      const slackPlugin = screen.getByText('Slack Integration');
      expect(slackPlugin).toBeInTheDocument();

      await user.click(slackPlugin.closest('div')!);
      expect(screen.getByRole('button', { name: /next/i })).toBeEnabled();
    });
  });

  describe('Validation Step', () => {
    it('shows validation progress', async () => {
      render(
        <PluginInstallationWizard
          onClose={mockOnClose}
          onComplete={mockOnComplete}
          preselectedPlugin={mockPlugin}
        />
      );

      expect(screen.getByText('Validating Plugin')).toBeInTheDocument();
      expect(screen.getByText('Plugin manifest is valid')).toBeInTheDocument();
      expect(screen.getByText('Compatible with current system version')).toBeInTheDocument();
    });

    it('displays plugin information during validation', async () => {
      render(
        <PluginInstallationWizard
          onClose={mockOnClose}
          onComplete={mockOnComplete}
          preselectedPlugin={mockPlugin}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Plugin Information')).toBeInTheDocument();
      });

      expect(screen.getByText('Test Plugin')).toBeInTheDocument();
      expect(screen.getByText('1.0.0')).toBeInTheDocument();
      expect(screen.getByText('Test Author')).toBeInTheDocument();
    });
  });

  describe('Dependencies Step', () => {
    it('shows dependency resolution progress', async () => {
      render(
        <PluginInstallationWizard
          onClose={mockOnClose}
          onComplete={mockOnComplete}
          preselectedPlugin={mockPlugin}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Resolve Dependencies')).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(screen.getByText('Test Dependency')).toBeInTheDocument();
      });
    });

    it('displays dependency status correctly', async () => {
      render(
        <PluginInstallationWizard
          onClose={mockOnClose}
          onComplete={mockOnComplete}
          preselectedPlugin={mockPlugin}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Test Dependency')).toBeInTheDocument();
      });

      // Should show "Will Install" for uninstalled dependencies
      expect(screen.getByText('Will Install')).toBeInTheDocument();
    });
  });

  describe('Permissions Step', () => {
    it('displays plugin permissions', async () => {
      render(
        <PluginInstallationWizard
          onClose={mockOnClose}
          onComplete={mockOnComplete}
          preselectedPlugin={mockPlugin}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Configure Permissions')).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(screen.getByText('Test Permission')).toBeInTheDocument();
        expect(screen.getByText('Optional Permission')).toBeInTheDocument();
      });
    });

    it('automatically grants required permissions', async () => {
      render(
        <PluginInstallationWizard
          onClose={mockOnClose}
          onComplete={mockOnComplete}
          preselectedPlugin={mockPlugin}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Test Permission')).toBeInTheDocument();
      });

      const requiredPermission = screen.getByLabelText('Test Permission');
      expect(requiredPermission).toBeChecked();
      expect(requiredPermission).toBeDisabled();
    });

    it('allows toggling optional permissions', async () => {
      const user = userEvent.setup();
      render(
        <PluginInstallationWizard
          onClose={mockOnClose}
          onComplete={mockOnComplete}
          preselectedPlugin={mockPlugin}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Optional Permission')).toBeInTheDocument();
      });

      const optionalPermission = screen.getByLabelText('Optional Permission');
      expect(optionalPermission).not.toBeChecked();
      expect(optionalPermission).toBeEnabled();

      await user.click(optionalPermission);
      expect(optionalPermission).toBeChecked();
    });

    it('shows permission details dialog', async () => {
      const user = userEvent.setup();
      render(
        <PluginInstallationWizard
          onClose={mockOnClose}
          onComplete={mockOnComplete}
          preselectedPlugin={mockPlugin}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Test Permission')).toBeInTheDocument();
      });

      // Click the info button for the first permission
      const infoButtons = screen.getAllByRole('button');
      const infoButton = infoButtons.find(button => 
        button.querySelector('svg') && button.getAttribute('aria-label') === null
      );
      
      if (infoButton) {
        await user.click(infoButton);
        expect(screen.getByText('Permission Details')).toBeInTheDocument();
      }
    });
  });

  describe('Configuration Step', () => {
    it('displays configuration form', async () => {
      render(
        <PluginInstallationWizard
          onClose={mockOnClose}
          onComplete={mockOnComplete}
          preselectedPlugin={mockPlugin}
        />
      );

      // Navigate to configuration step
      await waitFor(() => {
        expect(screen.getByText('Configure Permissions')).toBeInTheDocument();
      });

      await waitFor(() => {
        const nextButton = screen.getByRole('button', { name: /next/i });
        fireEvent.click(nextButton);
      });

      await waitFor(() => {
        expect(screen.getByText('Plugin Configuration')).toBeInTheDocument();
      });

      expect(screen.getByLabelText('API Key *')).toBeInTheDocument();
      expect(screen.getByLabelText('Timeout')).toBeInTheDocument();
      expect(screen.getByLabelText('Enabled')).toBeInTheDocument();
      expect(screen.getByLabelText('Mode')).toBeInTheDocument();
    });

    it('handles different field types correctly', async () => {
      const user = userEvent.setup();
      render(
        <PluginInstallationWizard
          onClose={mockOnClose}
          onComplete={mockOnComplete}
          preselectedPlugin={mockPlugin}
        />
      );

      // Navigate to configuration step
      await waitFor(() => {
        expect(screen.getByText('Configure Permissions')).toBeInTheDocument();
      });

      await waitFor(() => {
        const nextButton = screen.getByRole('button', { name: /next/i });
        fireEvent.click(nextButton);
      });

      await waitFor(() => {
        expect(screen.getByText('Plugin Configuration')).toBeInTheDocument();
      });

      // Test password field
      const apiKeyField = screen.getByLabelText('API Key *');
      expect(apiKeyField).toHaveAttribute('type', 'password');

      // Test number field
      const timeoutField = screen.getByLabelText('Timeout');
      expect(timeoutField).toHaveAttribute('type', 'number');

      // Test boolean field
      const enabledField = screen.getByLabelText('Enabled');
      expect(enabledField).toHaveAttribute('type', 'checkbox');

      // Test select field
      expect(screen.getByText('Select an option')).toBeInTheDocument();
    });

    it('validates required fields', async () => {
      const user = userEvent.setup();
      render(
        <PluginInstallationWizard
          onClose={mockOnClose}
          onComplete={mockOnComplete}
          preselectedPlugin={mockPlugin}
        />
      );

      // Navigate to configuration step
      await waitFor(() => {
        expect(screen.getByText('Configure Permissions')).toBeInTheDocument();
      });

      await waitFor(() => {
        const nextButton = screen.getByRole('button', { name: /next/i });
        fireEvent.click(nextButton);
      });

      await waitFor(() => {
        expect(screen.getByText('Plugin Configuration')).toBeInTheDocument();
      });

      // Next button should be disabled without required fields
      const nextButton = screen.getByRole('button', { name: /next/i });
      expect(nextButton).toBeDisabled();

      // Fill required field
      const apiKeyField = screen.getByLabelText('API Key *');
      await user.type(apiKeyField, 'test-api-key');

      expect(nextButton).toBeEnabled();
    });
  });

  describe('Review Step', () => {
    it('displays installation summary', async () => {
      const user = userEvent.setup();
      render(
        <PluginInstallationWizard
          onClose={mockOnClose}
          onComplete={mockOnComplete}
          preselectedPlugin={mockPlugin}
        />
      );

      // Navigate through all steps to review
      await waitFor(() => {
        expect(screen.getByText('Configure Permissions')).toBeInTheDocument();
      });

      // Go to configuration
      await waitFor(() => {
        const nextButton = screen.getByRole('button', { name: /next/i });
        fireEvent.click(nextButton);
      });

      await waitFor(() => {
        expect(screen.getByText('Plugin Configuration')).toBeInTheDocument();
      });

      // Fill required configuration
      const apiKeyField = screen.getByLabelText('API Key *');
      await user.type(apiKeyField, 'test-api-key');

      // Go to review
      const nextButton = screen.getByRole('button', { name: /next/i });
      await user.click(nextButton);

      await waitFor(() => {
        expect(screen.getByText('Review Installation')).toBeInTheDocument();
      });

      expect(screen.getByText('Plugin Information')).toBeInTheDocument();
      expect(screen.getByText('Dependencies')).toBeInTheDocument();
      expect(screen.getByText('Granted Permissions')).toBeInTheDocument();
      expect(screen.getByText('Configuration')).toBeInTheDocument();
    });

    it('shows install button on review step', async () => {
      const user = userEvent.setup();
      render(
        <PluginInstallationWizard
          onClose={mockOnClose}
          onComplete={mockOnComplete}
          preselectedPlugin={mockPlugin}
        />
      );

      // Navigate to review step (simplified for test)
      await waitFor(() => {
        expect(screen.getByText('Configure Permissions')).toBeInTheDocument();
      });

      // Skip to review by mocking the state
      const nextButton = screen.getByRole('button', { name: /next/i });
      fireEvent.click(nextButton);

      await waitFor(() => {
        expect(screen.getByText('Plugin Configuration')).toBeInTheDocument();
      });

      const apiKeyField = screen.getByLabelText('API Key *');
      await user.type(apiKeyField, 'test-api-key');

      await user.click(screen.getByRole('button', { name: /next/i }));

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /install plugin/i })).toBeInTheDocument();
      });
    });
  });

  describe('Installation Step', () => {
    it('shows installation progress', async () => {
      const user = userEvent.setup();
      render(
        <PluginInstallationWizard
          onClose={mockOnClose}
          onComplete={mockOnComplete}
          preselectedPlugin={mockPlugin}
        />
      );

      // Navigate to review and install
      await waitFor(() => {
        expect(screen.getByText('Configure Permissions')).toBeInTheDocument();
      });

      const nextButton = screen.getByRole('button', { name: /next/i });
      fireEvent.click(nextButton);

      await waitFor(() => {
        expect(screen.getByText('Plugin Configuration')).toBeInTheDocument();
      });

      const apiKeyField = screen.getByLabelText('API Key *');
      await user.type(apiKeyField, 'test-api-key');

      await user.click(screen.getByRole('button', { name: /next/i }));

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /install plugin/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /install plugin/i }));

      await waitFor(() => {
        expect(screen.getByText('Installing Plugin')).toBeInTheDocument();
      });

      expect(screen.getByText('Progress')).toBeInTheDocument();
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });

    it('calls installPlugin with correct parameters', async () => {
      const user = userEvent.setup();
      render(
        <PluginInstallationWizard
          onClose={mockOnClose}
          onComplete={mockOnComplete}
          preselectedPlugin={mockPlugin}
        />
      );

      // Navigate to install
      await waitFor(() => {
        expect(screen.getByText('Configure Permissions')).toBeInTheDocument();
      });

      const nextButton = screen.getByRole('button', { name: /next/i });
      fireEvent.click(nextButton);

      await waitFor(() => {
        expect(screen.getByText('Plugin Configuration')).toBeInTheDocument();
      });

      const apiKeyField = screen.getByLabelText('API Key *');
      await user.type(apiKeyField, 'test-api-key');

      await user.click(screen.getByRole('button', { name: /next/i }));

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /install plugin/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /install plugin/i }));

      await waitFor(() => {
        expect(mockUsePluginStore.installPlugin).toHaveBeenCalledWith({
          source: 'marketplace',
          identifier: 'test-plugin',
          version: '1.0.0',
          config: { apiKey: 'test-api-key' },
          permissions: ['test-permission'],
          autoStart: true,
        });
      });
    });
  });

  describe('Complete Step', () => {
    it('shows completion message', async () => {
      const user = userEvent.setup();
      render(
        <PluginInstallationWizard
          onClose={mockOnClose}
          onComplete={mockOnComplete}
          preselectedPlugin={mockPlugin}
        />
      );

      // Navigate through installation
      await waitFor(() => {
        expect(screen.getByText('Configure Permissions')).toBeInTheDocument();
      });

      const nextButton = screen.getByRole('button', { name: /next/i });
      fireEvent.click(nextButton);

      await waitFor(() => {
        expect(screen.getByText('Plugin Configuration')).toBeInTheDocument();
      });

      const apiKeyField = screen.getByLabelText('API Key *');
      await user.type(apiKeyField, 'test-api-key');

      await user.click(screen.getByRole('button', { name: /next/i }));

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /install plugin/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /install plugin/i }));

      // Wait for installation to complete
      await waitFor(() => {
        expect(screen.getByText('Installation Complete')).toBeInTheDocument();
      }, { timeout: 10000 });

      expect(screen.getByText('Test Plugin is now installed!')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /view plugin/i })).toBeInTheDocument();
    });

    it('calls onComplete when view plugin is clicked', async () => {
      const user = userEvent.setup();
      
      // Mock faster installation for testing
      mockUsePluginStore.installPlugin.mockImplementation(async () => {
        await new Promise(resolve => setTimeout(resolve, 100));
        return 'install-123';
      });

      render(
        <PluginInstallationWizard
          onClose={mockOnClose}
          onComplete={mockOnComplete}
          preselectedPlugin={mockPlugin}
        />
      );

      // Wait for permissions step
      await waitFor(() => {
        expect(screen.getByText('Configure Permissions')).toBeInTheDocument();
      }, { timeout: 5000 });

      // Navigate quickly through steps
      fireEvent.click(screen.getByRole('button', { name: /next/i }));

      await waitFor(() => {
        expect(screen.getByText('Plugin Configuration')).toBeInTheDocument();
      });

      const apiKeyField = screen.getByLabelText('API Key *');
      await user.type(apiKeyField, 'test-api-key');

      fireEvent.click(screen.getByRole('button', { name: /next/i }));

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /install plugin/i })).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('button', { name: /install plugin/i }));

      await waitFor(() => {
        expect(screen.getByText('Installation Complete')).toBeInTheDocument();
      }, { timeout: 10000 });

      fireEvent.click(screen.getByRole('button', { name: /view plugin/i }));
      expect(mockOnComplete).toHaveBeenCalled();
    });
  });

  describe('Navigation', () => {
    it('allows going back to previous steps', async () => {
      const user = userEvent.setup();
      render(
        <PluginInstallationWizard
          onClose={mockOnClose}
          onComplete={mockOnComplete}
        />
      );

      // Go to next step
      await user.click(screen.getByLabelText('Plugin Marketplace'));
      await user.click(screen.getByRole('button', { name: /next/i }));

      expect(screen.getAllByText('Select Plugin')[0]).toBeInTheDocument();

      // Go back
      await user.click(screen.getAllByRole('button', { name: /back/i })[1]);
      expect(screen.getByText('Choose Installation Source')).toBeInTheDocument();
    });

    it('calls onClose when back to plugins is clicked', async () => {
      const user = userEvent.setup();
      render(
        <PluginInstallationWizard
          onClose={mockOnClose}
          onComplete={mockOnComplete}
        />
      );

      await user.click(screen.getByRole('button', { name: /back to plugins/i }));
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  describe('Error Handling', () => {
    it('handles installation errors gracefully', async () => {
      const user = userEvent.setup();
      mockUsePluginStore.installPlugin.mockRejectedValue(new Error('Installation failed'));

      render(
        <PluginInstallationWizard
          onClose={mockOnClose}
          onComplete={mockOnComplete}
          preselectedPlugin={mockPlugin}
        />
      );

      // Wait for permissions step
      await waitFor(() => {
        expect(screen.getByText('Configure Permissions')).toBeInTheDocument();
      }, { timeout: 5000 });

      // Navigate through steps quickly
      fireEvent.click(screen.getByRole('button', { name: /next/i }));

      await waitFor(() => {
        expect(screen.getByText('Plugin Configuration')).toBeInTheDocument();
      });

      const apiKeyField = screen.getByLabelText('API Key *');
      await user.type(apiKeyField, 'test-api-key');

      fireEvent.click(screen.getByRole('button', { name: /next/i }));

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /install plugin/i })).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('button', { name: /install plugin/i }));

      await waitFor(() => {
        expect(screen.getByText('Installation failed')).toBeInTheDocument();
      }, { timeout: 5000 });
    });
  });

  describe('Preselected Plugin', () => {
    it('starts at validation step when plugin is preselected', () => {
      render(
        <PluginInstallationWizard
          onClose={mockOnClose}
          onComplete={mockOnComplete}
          preselectedPlugin={mockPlugin}
        />
      );

      expect(screen.getByText('Validating Plugin')).toBeInTheDocument();
    });

    it('disables back button on validation step with preselected plugin', () => {
      render(
        <PluginInstallationWizard
          onClose={mockOnClose}
          onComplete={mockOnComplete}
          preselectedPlugin={mockPlugin}
        />
      );

      const backButtons = screen.getAllByRole('button', { name: /back/i });
      const navigationBackButton = backButtons.find(button => 
        button.textContent?.includes('Back') && !button.textContent?.includes('Plugins')
      );
      expect(navigationBackButton).toBeDisabled();
    });
  });
});