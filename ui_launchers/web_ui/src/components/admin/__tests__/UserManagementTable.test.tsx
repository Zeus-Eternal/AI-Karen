/**
 * UserManagementTable Component Tests
 * 
 * Tests for the user management table including sorting, filtering,
 * pagination, and user operations.
 */


import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { jest } from '@jest/globals';
import { UserManagementTable } from '../UserManagementTable';
import { useRole } from '@/hooks/useRole';
import type { User } from '@/types/admin';

// Mock the useRole hook
jest.mock('@/hooks/useRole');
const mockUseRole = useRole as jest.MockedFunction<typeof useRole>;

// Mock child components
jest.mock('../UserEditModal', () => ({
  UserEditModal: ({ user, onClose, onUserUpdated }: any) => (
    <div data-testid="user-edit-modal">
      <span>Editing: {user.email}</span>
      <Button onClick={onUserUpdated} aria-label="Button">Update</Button>
      <Button onClick={onClose} aria-label="Button">Close</Button>
    </div>
  )
}));

jest.mock('../UserSearchFilters', () => ({
  UserSearchFilters: ({ filters, onFiltersChange, onRefresh }: any) => (
    <div data-testid="user-search-filters">
      <input
        data-testid="search-input"
        value={filters.search || ''}
        onChange={(e) => onFiltersChange({ ...filters, search: e.target.value })}
      />
      <Button onClick={onRefresh} aria-label="Button">Refresh</Button>
    </div>
  )
}));

// Mock fetch
global.fetch = jest.fn();
const mockFetch = fetch as jest.MockedFunction<typeof fetch>;

const mockUsers: User[] = [
  {
    user_id: 'user1',
    email: 'user1@test.com',
    full_name: 'User One',
    role: 'user',
    roles: ['user'],
    tenant_id: 'default',
    preferences: {},
    is_verified: true,
    is_active: true,
    created_at: new Date('2024-01-01'),
    updated_at: new Date('2024-01-01'),
    last_login_at: new Date('2024-01-15'),
    failed_login_attempts: 0,
    two_factor_enabled: false
  },
  {
    user_id: 'user2',
    email: 'admin@test.com',
    full_name: 'Admin User',
    role: 'admin',
    roles: ['admin'],
    tenant_id: 'default',
    preferences: {},
    is_verified: true,
    is_active: true,
    created_at: new Date('2024-01-02'),
    updated_at: new Date('2024-01-02'),
    last_login_at: new Date('2024-01-16'),
    failed_login_attempts: 0,
    two_factor_enabled: true
  }
];

describe('UserManagementTable', () => {
  const mockProps = {
    selectedUsers: [],
    onSelectionChange: jest.fn(),
    onUserUpdated: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    
    mockUseRole.mockReturnValue({
      hasRole: jest.fn((role: string) => role === 'admin'),
      hasPermission: jest.fn(() => true),
      user: {
        user_id: 'admin1',
        email: 'admin@test.com',
        role: 'admin'
      } as any,
      loading: false

    // Mock successful API response
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        success: true,
        data: {
          data: mockUsers,
          pagination: {
            page: 1,
            limit: 20,
            total: 2,
            total_pages: 1,
            has_next: false,
            has_prev: false
          }
        }
      })
    } as any);

  it('renders user management table', async () => {
    render(<UserManagementTable {...mockProps} />);
    
    await waitFor(() => {
      expect(screen.getByText('user1@test.com')).toBeInTheDocument();
      expect(screen.getByText('admin@test.com')).toBeInTheDocument();
      expect(screen.getByText('User One')).toBeInTheDocument();
      expect(screen.getByText('Admin User')).toBeInTheDocument();


  it('displays user roles with proper styling', async () => {
    render(<UserManagementTable {...mockProps} />);
    
    await waitFor(() => {
      expect(screen.getByText('user')).toBeInTheDocument();
      expect(screen.getByText('admin')).toBeInTheDocument();


  it('displays user status correctly', async () => {
    render(<UserManagementTable {...mockProps} />);
    
    await waitFor(() => {
      const activeStatuses = screen.getAllByText('Active');
      expect(activeStatuses).toHaveLength(2);
      
      const verifiedStatuses = screen.getAllByText('Verified');
      expect(verifiedStatuses).toHaveLength(2);


  it('handles user selection', async () => {
    render(<UserManagementTable {...mockProps} />);
    
    await waitFor(() => {
      const checkboxes = screen.getAllByRole('checkbox');
      fireEvent.click(checkboxes[1]); // First user checkbox (index 0 is select all)

    expect(mockProps.onSelectionChange).toHaveBeenCalledWith(['user1']);

  it('handles select all functionality', async () => {
    render(<UserManagementTable {...mockProps} />);
    
    await waitFor(() => {
      const selectAllCheckbox = screen.getAllByRole('checkbox')[0];
      fireEvent.click(selectAllCheckbox);

    expect(mockProps.onSelectionChange).toHaveBeenCalledWith(['user1', 'user2']);

  it('handles sorting by columns', async () => {
    render(<UserManagementTable {...mockProps} />);
    
    await waitFor(() => {
      const emailHeader = screen.getByText('Email');
      fireEvent.click(emailHeader);

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('sort_by=email&sort_order=asc')
    );

  it('handles pagination', async () => {
    // Mock response with multiple pages
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        success: true,
        data: {
          data: mockUsers,
          pagination: {
            page: 1,
            limit: 20,
            total: 50,
            total_pages: 3,
            has_next: true,
            has_prev: false
          }
        }
      })
    } as any);

    render(<UserManagementTable {...mockProps} />);
    
    await waitFor(() => {
      expect(screen.getByText('Next')).toBeInTheDocument();
      expect(screen.getByText('Showing 1 to 2 of 50 results')).toBeInTheDocument();

    // Click next page
    fireEvent.click(screen.getByText('Next'));
    
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('page=2')
    );

  it('handles filtering', async () => {
    render(<UserManagementTable {...mockProps} />);
    
    await waitFor(() => {
      const searchInput = screen.getByTestId('search-input');
      fireEvent.change(searchInput, { target: { value: 'admin' } });

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('search=admin')
    );

  it('opens edit modal when edit button is clicked', async () => {
    render(<UserManagementTable {...mockProps} />);
    
    await waitFor(() => {
      const editButtons = screen.getAllByText('Edit');
      fireEvent.click(editButtons[0]);

    expect(screen.getByTestId('user-edit-modal')).toBeInTheDocument();
    expect(screen.getByText('Editing: user1@test.com')).toBeInTheDocument();

  it('handles user status toggle', async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({
          success: true,
          data: { data: mockUsers, pagination: { total: 2 } }
        })
      } as any)
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true })
      } as any);

    render(<UserManagementTable {...mockProps} />);
    
    await waitFor(() => {
      const deactivateButtons = screen.getAllByText('Deactivate');
      fireEvent.click(deactivateButtons[0]);

    expect(mockFetch).toHaveBeenCalledWith(
      '/api/admin/users/user1',
      expect.objectContaining({
        method: 'PATCH',
        body: JSON.stringify({ is_active: false })
      })
    );

  it('shows permission-based edit buttons', async () => {
    // Mock as regular admin (can only edit users)
    mockUseRole.mockReturnValue({
      hasRole: jest.fn((role: string) => role === 'admin'),
      hasPermission: jest.fn(() => true),
      user: { user_id: 'admin1', email: 'admin@test.com', role: 'admin' } as any,
      loading: false

    render(<UserManagementTable {...mockProps} />);
    
    await waitFor(() => {
      const editButtons = screen.getAllByText('Edit');
      // Should only show edit button for regular user, not admin user
      expect(editButtons).toHaveLength(1);


  it('handles API errors gracefully', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      json: () => Promise.resolve({
        success: false,
        error: { message: 'Failed to load users' }
      })
    } as any);

    render(<UserManagementTable {...mockProps} />);
    
    await waitFor(() => {
      expect(screen.getByText('Failed to load users')).toBeInTheDocument();
      expect(screen.getByText('Try again')).toBeInTheDocument();


  it('shows loading state initially', () => {
    render(<UserManagementTable {...mockProps} />);
    
    expect(screen.getByRole('status')).toBeInTheDocument(); // Loading spinner

  it('shows empty state when no users found', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        success: true,
        data: {
          data: [],
          pagination: { total: 0, total_pages: 0 }
        }
      })
    } as any);

    render(<UserManagementTable {...mockProps} />);
    
    await waitFor(() => {
      expect(screen.getByText('No users found matching your criteria.')).toBeInTheDocument();


  it('handles user edit modal close', async () => {
    render(<UserManagementTable {...mockProps} />);
    
    await waitFor(() => {
      const editButtons = screen.getAllByText('Edit');
      fireEvent.click(editButtons[0]);

    expect(screen.getByTestId('user-edit-modal')).toBeInTheDocument();
    
    // Close modal
    fireEvent.click(screen.getByText('Close'));
    
    expect(screen.queryByTestId('user-edit-modal')).not.toBeInTheDocument();

  it('refreshes data after user update', async () => {
    render(<UserManagementTable {...mockProps} />);
    
    await waitFor(() => {
      const editButtons = screen.getAllByText('Edit');
      fireEvent.click(editButtons[0]);

    // Update user
    fireEvent.click(screen.getByText('Update'));
    
    expect(mockProps.onUserUpdated).toHaveBeenCalled();
    expect(mockFetch).toHaveBeenCalledTimes(2); // Initial load + refresh

  it('formats dates correctly', async () => {
    render(<UserManagementTable {...mockProps} />);
    
    await waitFor(() => {
      // Check that dates are formatted (exact format may vary by locale)
      expect(screen.getByText(/1\/1\/2024/)).toBeInTheDocument();
      expect(screen.getByText(/1\/15\/2024/)).toBeInTheDocument();


  it('handles page size changes', async () => {
    render(<UserManagementTable {...mockProps} />);
    
    await waitFor(() => {
      const pageSizeSelect = screen.getByDisplayValue('20 per page');
      fireEvent.change(pageSizeSelect, { target: { value: '50' } });

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('limit=50')
    );

