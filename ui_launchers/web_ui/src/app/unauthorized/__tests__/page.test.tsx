
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import UnauthorizedPage from '../page';

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}));

// Mock auth context
jest.mock('@/contexts/AuthContext', () => ({
  useAuth: jest.fn(),
}));

const mockPush = jest.fn();
const mockBack = jest.fn();
const mockReplace = jest.fn();

beforeEach(() => {
  (useRouter as jest.Mock).mockReturnValue({
    push: mockPush,
    back: mockBack,
    replace: mockReplace,

  jest.clearAllMocks();

describe('UnauthorizedPage', () => {
  it('renders correctly for unauthenticated users', () => {
    (useAuth as jest.Mock).mockReturnValue({
      isAuthenticated: false,
      user: null,

    render(<UnauthorizedPage />);

    expect(screen.getByText('Access Denied')).toBeInTheDocument();
    expect(screen.getByText('You need to be logged in to access this page.')).toBeInTheDocument();
    expect(screen.getByText('Sign In')).toBeInTheDocument();

  it('renders correctly for authenticated users without permission', () => {
    (useAuth as jest.Mock).mockReturnValue({
      isAuthenticated: true,
      user: { role: 'user' },

    render(<UnauthorizedPage />);

    expect(screen.getByText('Access Denied')).toBeInTheDocument();
    expect(screen.getByText(/Your current role \(user\) doesn't have access/)).toBeInTheDocument();
    expect(screen.getByText('Go to Dashboard')).toBeInTheDocument();

  it('handles go back button click', async () => {
    (useAuth as jest.Mock).mockReturnValue({
      isAuthenticated: true,
      user: { role: 'user' },

    render(<UnauthorizedPage />);

    const goBackButton = screen.getByText('Go Back');
    fireEvent.click(goBackButton);

    await waitFor(() => {
      expect(mockBack).toHaveBeenCalledTimes(1);


  it('redirects to correct dashboard for super admin', () => {
    (useAuth as jest.Mock).mockReturnValue({
      isAuthenticated: true,
      user: { role: 'super_admin' },

    render(<UnauthorizedPage />);

    const dashboardLink = screen.getByText('Go to Dashboard').closest('a');
    expect(dashboardLink).toHaveAttribute('href', '/admin/super-admin');

  it('redirects to correct dashboard for admin', () => {
    (useAuth as jest.Mock).mockReturnValue({
      isAuthenticated: true,
      user: { role: 'admin' },

    render(<UnauthorizedPage />);

    const dashboardLink = screen.getByText('Go to Dashboard').closest('a');
    expect(dashboardLink).toHaveAttribute('href', '/admin');

  it('redirects to correct dashboard for regular user', () => {
    (useAuth as jest.Mock).mockReturnValue({
      isAuthenticated: true,
      user: { role: 'user' },

    render(<UnauthorizedPage />);

    const dashboardLink = screen.getByText('Go to Dashboard').closest('a');
    expect(dashboardLink).toHaveAttribute('href', '/chat');

  it('redirects to login for unauthenticated users', () => {
    (useAuth as jest.Mock).mockReturnValue({
      isAuthenticated: false,
      user: null,

    render(<UnauthorizedPage />);

    const signInLink = screen.getByText('Sign In').closest('a');
    expect(signInLink).toHaveAttribute('href', '/login');

