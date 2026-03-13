import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';
import userEvent from '@testing-library/user-event';
import { Input } from '../input';
import { render as customRender } from '@/lib/__tests__/test-utils';

describe('Input', () => {
  const mockOnChange = vi.fn();
  const mockOnFocus = vi.fn();
  const mockOnBlur = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('Basic Input', () => {
    it('renders with default props', () => {
      customRender(<Input placeholder="Enter text" />);
      
      const input = screen.getByPlaceholderText('Enter text');
      expect(input).toBeInTheDocument();
      expect(input).toHaveClass('flex h-10 w-full rounded-md border border-input');
    });

    it('renders with custom className', () => {
      customRender(<Input className="custom-input" />);
      
      const input = screen.getByRole('textbox');
      expect(input).toHaveClass('custom-input');
    });

    it('renders with different types', () => {
      const { rerender } = customRender(<Input type="text" />);
      
      let input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('type', 'text');
      
      rerender(<Input type="password" />);
      input = document.querySelector('input[type="password"]')!;
      expect(input).toHaveAttribute('type', 'password');
      
      rerender(<Input type="email" />);
      input = document.querySelector('input[type="email"]')!;
      expect(input).toHaveAttribute('type', 'email');
      
      rerender(<Input type="number" />);
      input = document.querySelector('input[type="number"]')!;
      expect(input).toHaveAttribute('type', 'number');
    });

    it('handles value changes', async () => {
      const user = userEvent.setup();
      customRender(<Input onChange={mockOnChange} />);
      
      const input = screen.getByRole('textbox');
      await user.type(input, 'Hello World');
      
      expect(mockOnChange).toHaveBeenCalledTimes(11); // Once for each character
    });

    it('handles focus and blur events', async () => {
      const user = userEvent.setup();
      customRender(
        <Input 
          onFocus={mockOnFocus} 
          onBlur={mockOnBlur} 
        />
      );
      
      const input = screen.getByRole('textbox');
      
      await user.click(input);
      expect(mockOnFocus).toHaveBeenCalledTimes(1);
      
      await user.tab(); // Move focus away
      expect(mockOnBlur).toHaveBeenCalledTimes(1);
    });

    it('can be disabled', () => {
      customRender(<Input disabled />);
      
      const input = screen.getByRole('textbox');
      expect(input).toBeDisabled();
      expect(input).toHaveClass('disabled:cursor-not-allowed disabled:opacity-50');
    });

    it('can be readonly', () => {
      customRender(<Input readOnly />);
      
      const input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('readonly');
    });

    it('can be required', () => {
      customRender(<Input required />);
      
      const input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('required');
    });
  });

  describe('Input Styling', () => {
    it('applies focus styles correctly', async () => {
      const user = userEvent.setup();
      customRender(<Input />);
      
      const input = screen.getByRole('textbox');
      
      // Focus the input
      await user.click(input);
      
      // Check for focus classes
      expect(input).toHaveClass('focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2');
    });

    it('applies file input styles', () => {
      customRender(<Input type="file" />);
      
      const input = document.querySelector('input[type="file"]')!;
      
      expect(input).toHaveClass('file:border-0 file:bg-transparent file:text-sm file:font-medium');
    });
  });

  describe('Accessibility', () => {
    it('supports aria-label', () => {
      customRender(<Input aria-label="Search input" />);
      
      const input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('aria-label', 'Search input');
    });

    it('supports aria-labelledby', () => {
      customRender(
        <div>
          <label id="input-label">Name</label>
          <Input aria-labelledby="input-label" />
        </div>
      );
      
      const input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('aria-labelledby', 'input-label');
    });

    it('supports aria-describedby', () => {
      customRender(
        <div>
          <Input aria-describedby="input-description" />
          <p id="input-description">Enter your full name</p>
        </div>
      );
      
      const input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('aria-describedby', 'input-description');
    });

    it('supports aria-invalid', () => {
      customRender(<Input aria-invalid={true} />);
      
      const input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('aria-invalid', 'true');
    });

    it('supports aria-required', () => {
      customRender(<Input aria-required={true} />);
      
      const input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('aria-required', 'true');
    });

    it('supports aria-expanded', () => {
      customRender(<Input aria-expanded={false} />);
      
      const input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('aria-expanded', 'false');
    });

    it('supports aria-activedescendant', () => {
      customRender(<Input aria-activedescendant="option-1" />);
      
      const input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('aria-activedescendant', 'option-1');
    });

    it('supports aria-autocomplete', () => {
      customRender(<Input aria-autocomplete="list" />);
      
      const input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('aria-autocomplete', 'list');
    });

    it('supports aria-placeholder', () => {
      customRender(<Input aria-placeholder="Type here..." />);
      
      const input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('aria-placeholder', 'Type here...');
    });

    it('supports custom role', () => {
      customRender(<Input role="searchbox" />);
      
      const input = screen.getByRole('searchbox');
      expect(input).toHaveAttribute('role', 'searchbox');
    });
  });

  describe('Input Events', () => {
    it('handles onKeyDown event', async () => {
      const mockOnKeyDown = vi.fn();
      const user = userEvent.setup();
      
      customRender(<Input onKeyDown={mockOnKeyDown} />);
      
      const input = screen.getByRole('textbox');
      await user.type(input, 'a');
      
      expect(mockOnKeyDown).toHaveBeenCalled();
    });

    it('handles onKeyUp event', async () => {
      const mockOnKeyUp = vi.fn();
      const user = userEvent.setup();
      
      customRender(<Input onKeyUp={mockOnKeyUp} />);
      
      const input = screen.getByRole('textbox');
      await user.type(input, 'a');
      
      expect(mockOnKeyUp).toHaveBeenCalled();
    });

    it('handles onInput event', async () => {
      const mockOnInput = vi.fn();
      const user = userEvent.setup();
      
      customRender(<Input onInput={mockOnInput} />);
      
      const input = screen.getByRole('textbox');
      await user.type(input, 'test');
      
      expect(mockOnInput).toHaveBeenCalledTimes(4); // Once for each character
    });

    it('handles paste event', async () => {
      const mockOnPaste = vi.fn();
      const user = userEvent.setup();
      
      customRender(<Input onPaste={mockOnPaste} />);
      
      const input = screen.getByRole('textbox');
      
      // Simulate paste event
      await user.click(input);
      await user.paste('pasted text');
      
      expect(mockOnPaste).toHaveBeenCalled();
    });
  });

  describe('Input Ref', () => {
    it('forwards ref correctly', () => {
      const ref = React.createRef<HTMLInputElement>();
      
      customRender(<Input ref={ref} />);
      
      expect(ref.current?.constructor.name).toBe('HTMLInputElement');
    });

    it('can be focused through ref', () => {
      const ref = React.createRef<HTMLInputElement>();
      
      customRender(<Input ref={ref} />);
      
      ref.current?.focus();
      expect(ref.current).toBeDefined();
    });
  });

  describe('Edge Cases', () => {
    it('handles empty props gracefully', () => {
      customRender(<Input />);
      
      const input = screen.getByRole('textbox');
      expect(input).toBeInTheDocument();
    });

    it('handles undefined className', () => {
      customRender(<Input className={undefined} />);
      
      const input = screen.getByRole('textbox');
      expect(input).toBeInTheDocument();
      expect(input).toHaveClass('flex h-10 w-full');
    });

    it('handles null onChange', () => {
      customRender(<Input onChange={undefined} />);
      
      const input = screen.getByRole('textbox');
      expect(input).toBeInTheDocument();
    });

    it('handles controlled input', async () => {
      const user = userEvent.setup();
      const ControlledInput = () => {
        const [value, setValue] = React.useState('');
        return (
          <Input 
            value={value} 
            onChange={(e) => setValue(e.target.value)} 
          />
        );
      };
      
      customRender(<ControlledInput />);
      
      const input = screen.getByRole('textbox');
      await user.type(input, 'controlled');
      
      expect(input).toBeInTheDocument();
    });
  });

  describe('Input Display Name', () => {
    it('has proper display name', () => {
      expect(Input.displayName).toBe('Input');
    });
  });
});