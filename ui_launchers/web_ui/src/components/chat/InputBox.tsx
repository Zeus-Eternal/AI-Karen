'use client';

import React, { useState, FormEvent } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

interface InputBoxProps {
  onSend: (message: string) => Promise<void>;
  isLoading?: boolean;
  placeholder?: string;
}

export const InputBox: React.FC<InputBoxProps> = ({ onSend, isLoading, placeholder }) => {
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
      console.error('InputBox send failed', error);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <Input
        value={value}
        onChange={(event) => setValue(event.target.value)}
        placeholder={placeholder}
        aria-label="Chat message"
        disabled={isLoading}
      />
      <Button type="submit" disabled={isLoading || !value.trim()}>
        {isLoading ? 'Sending…' : 'Send'}
      </Button>
    </form>
  );
};

export default InputBox;
