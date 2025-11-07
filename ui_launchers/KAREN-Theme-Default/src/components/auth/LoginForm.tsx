"use client";

import React from 'react';

export interface LoginFormProps {
  onSuccess?: () => void;
}

export default function LoginForm({ onSuccess }: LoginFormProps) {
  return (
    <div>
      <h1>Login Form</h1>
      <p>Temporarily disabled for build</p>
    </div>
  );
}