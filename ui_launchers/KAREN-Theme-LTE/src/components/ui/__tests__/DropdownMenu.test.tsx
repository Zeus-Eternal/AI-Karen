import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import userEvent from '@testing-library/user-event';
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuCheckboxItem,
  DropdownMenuRadioItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuShortcut,
  DropdownMenuGroup,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuRadioGroup,
} from '../dropdown-menu';
import { Button } from '../button';
import { render as customRender } from '@/lib/__tests__/test-utils';

describe('DropdownMenu', () => {
  const mockOnClick = vi.fn();
  const mockOnSelect = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('Basic DropdownMenu', () => {
    it('renders dropdown menu with trigger and content', async () => {
      const user = userEvent.setup();
      
      customRender(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button>Open Menu</Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem onSelect={mockOnSelect}>Item 1</DropdownMenuItem>
            <DropdownMenuItem onSelect={mockOnSelect}>Item 2</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      );

      const trigger = screen.getByRole('button', { name: /open menu/i });
      expect(trigger).toBeInTheDocument();
      
      // Menu should not be visible initially
      expect(screen.queryByText('Item 1')).not.toBeInTheDocument();
      
      // Click to open menu
      await user.click(trigger);
      
      // Menu should be visible now
      await waitFor(() => {
        expect(screen.getByText('Item 1')).toBeInTheDocument();
        expect(screen.getByText('Item 2')).toBeInTheDocument();
      });
    });

    it('handles item selection', async () => {
      const user = userEvent.setup();
      
      customRender(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button>Open Menu</Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem onSelect={mockOnSelect}>Selectable Item</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      );

      const trigger = screen.getByRole('button', { name: /open menu/i });
      await user.click(trigger);
      
      const menuItem = screen.getByText('Selectable Item');
      await user.click(menuItem);
      
      expect(mockOnSelect).toHaveBeenCalledTimes(1);
    });

    it('closes menu after item selection', async () => {
      const user = userEvent.setup();
      
      customRender(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button>Open Menu</Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem onSelect={mockOnSelect}>Item 1</DropdownMenuItem>
            <DropdownMenuItem onSelect={mockOnSelect}>Item 2</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      );

      const trigger = screen.getByRole('button', { name: /open menu/i });
      await user.click(trigger);
      
      const menuItem = screen.getByText('Item 1');
      await user.click(menuItem);
      
      // Menu should close after selection
      await waitFor(() => {
        expect(screen.queryByText('Item 1')).not.toBeInTheDocument();
      });
    });
  });

  describe('DropdownMenuCheckboxItem', () => {
    it('renders checkbox item with checked state', async () => {
      const user = userEvent.setup();
      
      customRender(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button>Open Menu</Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuCheckboxItem checked={true} onCheckedChange={vi.fn()}>
              Checked Item
            </DropdownMenuCheckboxItem>
            <DropdownMenuCheckboxItem checked={false} onCheckedChange={vi.fn()}>
              Unchecked Item
            </DropdownMenuCheckboxItem>
          </DropdownMenuContent>
        </DropdownMenu>
      );

      await user.click(screen.getByRole('button', { name: /open menu/i }));
      
      // Check that items are rendered
      expect(screen.getByText('Checked Item')).toBeInTheDocument();
      expect(screen.getByText('Unchecked Item')).toBeInTheDocument();
      
      // The checked indicator should be present for the checked item
      const checkedItem = screen.getByText('Checked Item');
      expect(checkedItem.closest('[role="menuitemcheckbox"]')).toHaveAttribute('aria-checked', 'true');
      
      const uncheckedItem = screen.getByText('Unchecked Item');
      expect(uncheckedItem.closest('[role="menuitemcheckbox"]')).toHaveAttribute('aria-checked', 'false');
    });

    it('handles checkbox state changes', async () => {
      const mockOnCheckedChange = vi.fn();
      const user = userEvent.setup();
      
      customRender(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button>Open Menu</Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuCheckboxItem checked={false} onCheckedChange={mockOnCheckedChange}>
              Toggle Item
            </DropdownMenuCheckboxItem>
          </DropdownMenuContent>
        </DropdownMenu>
      );

      await user.click(screen.getByRole('button', { name: /open menu/i }));
      
      const checkboxItem = screen.getByText('Toggle Item');
      await user.click(checkboxItem);
      
      expect(mockOnCheckedChange).toHaveBeenCalledWith(true);
    });
  });

  describe('DropdownMenuRadioItem', () => {
    it('renders radio item with selected state', async () => {
      const user = userEvent.setup();
      
      customRender(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button>Open Menu</Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuRadioGroup value="option1">
              <DropdownMenuRadioItem value="option1">Option 1</DropdownMenuRadioItem>
              <DropdownMenuRadioItem value="option2">Option 2</DropdownMenuRadioItem>
            </DropdownMenuRadioGroup>
          </DropdownMenuContent>
        </DropdownMenu>
      );

      await user.click(screen.getByRole('button', { name: /open menu/i }));
      
      const option1 = screen.getByText('Option 1');
      const option2 = screen.getByText('Option 2');
      
      expect(option1.closest('[role="menuitemradio"]')).toHaveAttribute('aria-checked', 'true');
      expect(option2.closest('[role="menuitemradio"]')).toHaveAttribute('aria-checked', 'false');
    });

    it('handles radio selection changes', async () => {
      const mockOnValueChange = vi.fn();
      const user = userEvent.setup();
      
      customRender(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button>Open Menu</Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuRadioGroup value="option1" onValueChange={mockOnValueChange}>
              <DropdownMenuRadioItem value="option1">Option 1</DropdownMenuRadioItem>
              <DropdownMenuRadioItem value="option2">Option 2</DropdownMenuRadioItem>
            </DropdownMenuRadioGroup>
          </DropdownMenuContent>
        </DropdownMenu>
      );

      await user.click(screen.getByRole('button', { name: /open menu/i }));
      
      const option2 = screen.getByText('Option 2');
      await user.click(option2);
      
      expect(mockOnValueChange).toHaveBeenCalledWith('option2');
    });
  });

  describe('DropdownMenuLabel and Separator', () => {
    it('renders labels and separators correctly', async () => {
      const user = userEvent.setup();
      
      customRender(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button>Open Menu</Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuLabel>Section 1</DropdownMenuLabel>
            <DropdownMenuItem>Item 1</DropdownMenuItem>
            <DropdownMenuItem>Item 2</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuLabel>Section 2</DropdownMenuLabel>
            <DropdownMenuItem>Item 3</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      );

      await user.click(screen.getByRole('button', { name: /open menu/i }));
      
      expect(screen.getByText('Section 1')).toBeInTheDocument();
      expect(screen.getByText('Section 2')).toBeInTheDocument();
      expect(screen.getByText('Item 1')).toBeInTheDocument();
      expect(screen.getByText('Item 2')).toBeInTheDocument();
      expect(screen.getByText('Item 3')).toBeInTheDocument();
      
      // Check for separator (it should have a specific class)
      const separator = document.querySelector('[role="separator"]');
      expect(separator).toBeInTheDocument();
    });
  });

  describe('DropdownMenuShortcut', () => {
    it('renders shortcut text', async () => {
      const user = userEvent.setup();
      
      customRender(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button>Open Menu</Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>
              Copy
              <DropdownMenuShortcut>⌘C</DropdownMenuShortcut>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      );

      await user.click(screen.getByRole('button', { name: /open menu/i }));
      
      expect(screen.getByText('Copy')).toBeInTheDocument();
      expect(screen.getByText('⌘C')).toBeInTheDocument();
    });
  });

  describe('DropdownMenuGroup', () => {
    it('renders grouped items', async () => {
      const user = userEvent.setup();
      
      customRender(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button>Open Menu</Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuGroup>
              <DropdownMenuItem>Group Item 1</DropdownMenuItem>
              <DropdownMenuItem>Group Item 2</DropdownMenuItem>
            </DropdownMenuGroup>
          </DropdownMenuContent>
        </DropdownMenu>
      );

      await user.click(screen.getByRole('button', { name: /open menu/i }));
      
      expect(screen.getByText('Group Item 1')).toBeInTheDocument();
      expect(screen.getByText('Group Item 2')).toBeInTheDocument();
    });
  });

  describe('DropdownMenuSub', () => {
    it('renders submenu with trigger and content', async () => {
      const user = userEvent.setup();
      
      customRender(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button>Open Menu</Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuSub>
              <DropdownMenuSubTrigger>Submenu</DropdownMenuSubTrigger>
              <DropdownMenuSubContent>
                <DropdownMenuItem>Sub Item 1</DropdownMenuItem>
                <DropdownMenuItem>Sub Item 2</DropdownMenuItem>
              </DropdownMenuSubContent>
            </DropdownMenuSub>
          </DropdownMenuContent>
        </DropdownMenu>
      );

      await user.click(screen.getByRole('button', { name: /open menu/i }));
      
      const submenuTrigger = screen.getByText('Submenu');
      expect(submenuTrigger).toBeInTheDocument();
      
      // Hover over submenu trigger to show submenu
      await user.hover(submenuTrigger);
      
      await waitFor(() => {
        expect(screen.getByText('Sub Item 1')).toBeInTheDocument();
        expect(screen.getByText('Sub Item 2')).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA attributes', async () => {
      const user = userEvent.setup();
      
      customRender(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button>Open Menu</Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem>Item 1</DropdownMenuItem>
            <DropdownMenuCheckboxItem checked={true}>Checkbox Item</DropdownMenuCheckboxItem>
            <DropdownMenuRadioGroup value="option1">
              <DropdownMenuRadioItem value="option1">Radio Item</DropdownMenuRadioItem>
            </DropdownMenuRadioGroup>
          </DropdownMenuContent>
        </DropdownMenu>
      );

      const trigger = screen.getByRole('button', { name: /open menu/i });
      expect(trigger).toHaveAttribute('aria-haspopup', 'menu');
      expect(trigger).toHaveAttribute('aria-expanded', 'false');
      
      await user.click(trigger);
      
      // After opening, aria-expanded should be true
      expect(trigger).toHaveAttribute('aria-expanded', 'true');
      
      // Check menu items have proper roles
      await waitFor(() => {
        const menuItem = screen.getByText('Item 1');
        expect(menuItem.closest('[role="menuitem"]')).toBeInTheDocument();
        
        const checkboxItem = screen.getByText('Checkbox Item');
        expect(checkboxItem.closest('[role="menuitemcheckbox"]')).toBeInTheDocument();
        
        const radioItem = screen.getByText('Radio Item');
        expect(radioItem.closest('[role="menuitemradio"]')).toBeInTheDocument();
      });
    });

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup();
      
      customRender(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button>Open Menu</Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem onSelect={mockOnSelect}>Item 1</DropdownMenuItem>
            <DropdownMenuItem onSelect={mockOnSelect}>Item 2</DropdownMenuItem>
            <DropdownMenuItem onSelect={mockOnSelect}>Item 3</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      );

      const trigger = screen.getByRole('button', { name: /open menu/i });
      trigger.focus();
      
      // Open menu with Enter key
      await user.keyboard('{Enter}');
      
      await waitFor(() => {
        expect(screen.getByText('Item 1')).toBeInTheDocument();
      });
      
      // Navigate with arrow keys
      await user.keyboard('{ArrowDown}');
      await user.keyboard('{ArrowDown}');
      
      // Select with Enter
      await user.keyboard('{Enter}');
      
      expect(mockOnSelect).toHaveBeenCalledTimes(1);
    });
  });

  describe('Edge Cases', () => {
    it('handles empty dropdown menu', async () => {
      const user = userEvent.setup();
      
      customRender(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button>Empty Menu</Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            {/* No items */}
          </DropdownMenuContent>
        </DropdownMenu>
      );

      const trigger = screen.getByRole('button', { name: /empty menu/i });
      await user.click(trigger);
      
      // Should not throw error
      expect(trigger).toHaveAttribute('aria-expanded', 'true');
    });

    it('handles disabled items', async () => {
      const user = userEvent.setup();
      
      customRender(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button>Menu</Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem onSelect={mockOnSelect}>Enabled Item</DropdownMenuItem>
            <DropdownMenuItem disabled onSelect={mockOnSelect}>
              Disabled Item
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      );

      await user.click(screen.getByRole('button', { name: /menu/i }));
      
      const enabledItem = screen.getByText('Enabled Item');
      const disabledItem = screen.getByText('Disabled Item');
      
      // Check that items have the correct disabled state
      expect(enabledItem).not.toHaveAttribute('aria-disabled', 'true');
      expect(disabledItem).toHaveAttribute('data-disabled', '');
      
      // Click enabled item
      await user.click(enabledItem);
      expect(mockOnSelect).toHaveBeenCalledTimes(1);
      
      // Try to click disabled item
      await user.click(disabledItem);
      expect(mockOnSelect).toHaveBeenCalledTimes(1); // Still only called once
    });

    it('handles custom className', async () => {
      const user = userEvent.setup();
      
      customRender(
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button>Menu</Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="custom-dropdown">
            <DropdownMenuItem className="custom-item">Custom Item</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      );

      await user.click(screen.getByRole('button', { name: /menu/i }));
      
      const content = document.querySelector('.custom-dropdown');
      const item = document.querySelector('.custom-item');
      
      expect(content).toBeInTheDocument();
      expect(item).toBeInTheDocument();
    });
  });
});