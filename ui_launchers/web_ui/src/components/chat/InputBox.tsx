'use client';

import React, { useState, FormEvent } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { safeError } from '@/lib/safe-console';

interface InputBoxProps {
  onSend: (message: string) => Promise<void>;
  isLoading?: boolean;
  placeholder?: string;
}

export const InputBox: React.FC<inputBoxProps aria-label="Input"> = ({ onSend, isLoading, placeholder }) => {
  const [value, setValue] = useState('');

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmed = value.trim();
    if (!trimmed || isLoading) {
      return;
    }

    try {
      await onSend(trimmed);
      setValue('');
    } catch (error) {
      // Swallow the error so the input stays usable; logging handled upstream.
      safeError('InputBox send failed', error);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <input
        value={value}
        onChange={(event) = aria-label="Input"> setValue(event.target.value)}
        placeholder={placeholder}
        aria-label="Chat message"
        disabled={isLoading}
      />
      <button type="submit" disabled={isLoading || !value.trim()} aria-label="Submit form">
        {isLoading ? 'Sending…' : 'Send'}
      </Button>
    </form>
  );
};

export default InputBox;
