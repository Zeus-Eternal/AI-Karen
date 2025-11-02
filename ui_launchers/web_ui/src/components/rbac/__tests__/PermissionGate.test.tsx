
import React from 'react';
import { render, screen } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { PermissionGate, withPermission, usePermissionGate } from '../PermissionGate';
import { useRBAC } from '@/providers/rbac-provider';
import { Permission } from '@/types/rbac';

// Mock the RBAC provider
vi.mock('@/providers/rbac-provider');

const mockUseRBAC = vi.mocked(useRBAC);

const createMockRBACContext = () => ({
  hasPermission: vi.fn(),
  hasAllPermissions: vi.fn(),
  hasAnyPermission: vi.fn(),
  checkPermission: vi.fn(),
  currentUser: null,
  userRoles: [],
  effectivePermissions: [],
  getUserRoles: vi.fn(),
  assignRole: vi.fn(),
  removeRole: vi.fn(),
  isEvilModeEnabled: false,
  canEnableEvilMode: false,
  enableEvilMode: vi.fn(),
  disableEvilMode: vi.fn(),
  evilModeSession: null,
  rbacConfig: {} as any,
  evilModeConfig: {} as any,
  isLoading: false,
  isError: false,
  error: null

describe('PermissionGate', () => {
  let mockRBACContext: ReturnType<typeof createMockRBACContext>;

  beforeEach(() => {
    mockRBACContext = createMockRBACContext();
    mockUseRBAC.mockReturnValue(mockRBACContext);

  it('renders children when user has permission', () => {
    mockRBACContext.hasPermission.mockReturnValue(true);
    mockRBACContext.checkPermission.mockReturnValue({
      granted: true,
      reason: 'Permission granted',
      appliedRules: [],
      restrictions: []

    render(
      <PermissionGate permission="dashboard:view">
        <div data-testid="protected-content">Protected Content</div>
      </PermissionGate>
    );

    expect(screen.getByTestId('protected-content')).toBeInTheDocument();

  it('does not render children when user lacks permission', () => {
    mockRBACContext.hasPermission.mockReturnValue(false);
    mockRBACContext.checkPermission.mockReturnValue({
      granted: false,
      reason: 'Permission denied',
      appliedRules: [],
      restrictions: []

    render(
      <PermissionGate permission="dashboard:admin" showFallback={false}>
        <div data-testid="protected-content">Protected Content</div>
      </PermissionGate>
    );

    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();

  it('renders default fallback when permission denied and showFallback is true', () => {
    mockRBACContext.hasPermission.mockReturnValue(false);
    mockRBACContext.checkPermission.mockReturnValue({
      granted: false,
      reason: 'Permission denied',
      appliedRules: [],
      restrictions: []

    render(
      <PermissionGate permission="dashboard:admin" showFallback={true}>
        <div data-testid="protected-content">Protected Content</div>
      </PermissionGate>
    );

    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
    expect(screen.getByText('Permission denied')).toBeInTheDocument();

  it('renders custom fallback when provided', () => {
    mockRBACContext.hasPermission.mockReturnValue(false);
    mockRBACContext.checkPermission.mockReturnValue({
      granted: false,
      reason: 'Permission denied',
      appliedRules: [],
      restrictions: []

    render(
      <PermissionGate 
        permission="dashboard:admin" 
        fallback={<div data-testid="custom-fallback">Custom Fallback</div>}
      >
        <div data-testid="protected-content">Protected Content</div>
      </PermissionGate>
    );

    expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument();
    expect(screen.getByTestId('custom-fallback')).toBeInTheDocument();

  it('handles array of permissions with requireAll=true', () => {
    mockRBACContext.hasAllPermissions.mockReturnValue(true);
    mockRBACContext.checkPermission.mockReturnValue({
      granted: true,
      reason: 'Permission granted',
      appliedRules: [],
      restrictions: []

    render(
      <PermissionGate 
        permission={['dashboard:view', 'dashboard:edit']} 
        requireAll={true}
      >
        <div data-testid="protected-content">Protected Content</div>
      </PermissionGate>
    );

    expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    expect(mockRBACContext.hasAllPermissions).toHaveBeenCalledWith(['dashboard:view', 'dashboard:edit']);

  it('handles array of permissions with requireAll=false', () => {
    mockRBACContext.hasAnyPermission.mockReturnValue(true);
    mockRBACContext.checkPermission.mockReturnValue({
      granted: true,
      reason: 'Permission granted',
      appliedRules: [],
      restrictions: []

    render(
      <PermissionGate 
        permission={['dashboard:view', 'dashboard:admin']} 
        requireAll={false}
      >
        <div data-testid="protected-content">Protected Content</div>
      </PermissionGate>
    );

    expect(screen.getByTestId('protected-content')).toBeInTheDocument();
    expect(mockRBACContext.hasAnyPermission).toHaveBeenCalledWith(['dashboard:view', 'dashboard:admin']);

  it('shows elevation required message', () => {
    mockRBACContext.hasPermission.mockReturnValue(false);
    mockRBACContext.checkPermission.mockReturnValue({
      granted: false,
      reason: 'Evil Mode required',
      appliedRules: [],
      restrictions: [],
      requiresElevation: true,
      elevationReason: 'This operation requires Evil Mode activation'

    render(
      <PermissionGate permission="security:evil_mode" showFallback={true}>
        <div data-testid="protected-content">Protected Content</div>
      </PermissionGate>
    );

    expect(screen.getByText('Evil Mode required')).toBeInTheDocument();
    expect(screen.getByText('This operation requires Evil Mode activation')).toBeInTheDocument();

  it('shows restriction message', () => {
    mockRBACContext.hasPermission.mockReturnValue(false);
    mockRBACContext.checkPermission.mockReturnValue({
      granted: false,
      reason: 'Access restricted outside allowed time window',
      appliedRules: [],
      restrictions: [{
        type: 'time_limit',
        description: 'Time-based access restriction',
        config: { startTime: '09:00', endTime: '17:00' },
        active: true
      }]

    render(
      <PermissionGate permission="dashboard:admin" showFallback={true}>
        <div data-testid="protected-content">Protected Content</div>
      </PermissionGate>
    );

    expect(screen.getByText('Access restricted outside allowed time window')).toBeInTheDocument();


describe('withPermission HOC', () => {
  let mockRBACContext: ReturnType<typeof createMockRBACContext>;

  function TestComponent({ message }: { message: string }) {
    return <div data-testid="test-component">{message}</div>;
  }

  function FallbackComponent({ message }: { message: string }) {
    return <div data-testid="fallback-component">Fallback: {message}</div>;
  }

  beforeEach(() => {
    mockRBACContext = createMockRBACContext();
    mockUseRBAC.mockReturnValue(mockRBACContext);

  it('renders wrapped component when permission granted', () => {
    mockRBACContext.hasPermission.mockReturnValue(true);
    mockRBACContext.checkPermission.mockReturnValue({
      granted: true,
      reason: 'Permission granted',
      appliedRules: [],
      restrictions: []

    const WrappedComponent = withPermission(TestComponent, 'dashboard:view');

    render(<WrappedComponent message="Hello World" />);

    expect(screen.getByTestId('test-component')).toBeInTheDocument();
    expect(screen.getByText('Hello World')).toBeInTheDocument();

  it('renders fallback component when permission denied', () => {
    mockRBACContext.hasPermission.mockReturnValue(false);
    mockRBACContext.checkPermission.mockReturnValue({
      granted: false,
      reason: 'Permission denied',
      appliedRules: [],
      restrictions: []

    const WrappedComponent = withPermission(TestComponent, 'dashboard:admin', {
      fallback: FallbackComponent

    render(<WrappedComponent message="Hello World" />);

    expect(screen.queryByTestId('test-component')).not.toBeInTheDocument();
    expect(screen.getByTestId('fallback-component')).toBeInTheDocument();
    expect(screen.getByText('Fallback: Hello World')).toBeInTheDocument();

  it('handles multiple permissions with requireAll option', () => {
    mockRBACContext.hasAllPermissions.mockReturnValue(false);
    mockRBACContext.checkPermission.mockReturnValue({
      granted: false,
      reason: 'Permission denied',
      appliedRules: [],
      restrictions: []

    const WrappedComponent = withPermission(
      ['dashboard:view', 'dashboard:admin'], 
      { requireAll: true, showFallback: false }
    );

    render(<WrappedComponent message="Hello World" />);

    expect(screen.queryByTestId('test-component')).not.toBeInTheDocument();
    expect(mockRBACContext.hasAllPermissions).toHaveBeenCalledWith(['dashboard:view', 'dashboard:admin']);


describe('usePermissionGate hook', () => {
  let mockRBACContext: ReturnType<typeof createMockRBACContext>;

  function TestComponent({ permission }: { permission: Permission }) {
    const { hasAccess, permissionResult, canRender } = usePermissionGate(permission);

    return (
      <div>
        <div data-testid="has-access">{hasAccess.toString()}</div>
        <div data-testid="can-render">{canRender.toString()}</div>
        <div data-testid="permission-reason">{permissionResult.reason}</div>
      </div>
    );
  }

  beforeEach(() => {
    mockRBACContext = createMockRBACContext();
    mockUseRBAC.mockReturnValue(mockRBACContext);

  it('returns correct access status when permission granted', () => {
    mockRBACContext.hasPermission.mockReturnValue(true);
    mockRBACContext.checkPermission.mockReturnValue({
      granted: true,
      reason: 'Permission granted',
      appliedRules: [],
      restrictions: []

    render(<TestComponent permission="dashboard:view" />);

    expect(screen.getByTestId('has-access')).toHaveTextContent('true');
    expect(screen.getByTestId('can-render')).toHaveTextContent('true');
    expect(screen.getByTestId('permission-reason')).toHaveTextContent('Permission granted');

  it('returns correct access status when permission denied', () => {
    mockRBACContext.hasPermission.mockReturnValue(false);
    mockRBACContext.checkPermission.mockReturnValue({
      granted: false,
      reason: 'Permission denied',
      appliedRules: [],
      restrictions: []

    render(<TestComponent permission="dashboard:admin" />);

    expect(screen.getByTestId('has-access')).toHaveTextContent('false');
    expect(screen.getByTestId('can-render')).toHaveTextContent('false');
    expect(screen.getByTestId('permission-reason')).toHaveTextContent('Permission denied');

  it('handles array permissions correctly', () => {
    mockRBACContext.hasAnyPermission.mockReturnValue(true);
    mockRBACContext.checkPermission.mockReturnValue({
      granted: true,
      reason: 'Permission granted',
      appliedRules: [],
      restrictions: []

    function TestComponentWithArray() {
      const { hasAccess } = usePermissionGate(['dashboard:view', 'dashboard:edit'], false);
      return <div data-testid="has-access">{hasAccess.toString()}</div>;
    }

    render(<TestComponentWithArray />);

    expect(screen.getByTestId('has-access')).toHaveTextContent('true');
    expect(mockRBACContext.hasAnyPermission).toHaveBeenCalledWith(['dashboard:view', 'dashboard:edit']);

