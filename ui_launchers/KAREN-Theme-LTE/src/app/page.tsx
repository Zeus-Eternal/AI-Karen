"use client";

import { redirect } from 'next/navigation';

/**
 * Homepage - Redirects to chat interface
 * 
 * This consolidates dual-chat architecture by redirecting
 * old homepage to modern /chat interface.
 */
export default function HomePage() {
  // Redirect to chat interface
  redirect('/chat');
}
