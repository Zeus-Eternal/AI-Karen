
import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AgentDashboard } from '../AgentDashboard';
import { Agent } from '@/types/workflows';

const mockAgents: Agent[] = [
  {
    id: 'agent-1',
    name: 'Test Agent 1',
    description: 'A test agent for unit testing',
    type: 'workflow',
    status: 'running',
    config: {
      maxConcurrentTasks: 5,
      timeout: 30000,
      retryAttempts: 3,
      resources: { cpu: 0.5, memory: 1024 },
      permissions: ['read', 'write'],
      environment: { NODE_ENV: 'test' }
    },
    metrics: {
      tasksCompleted: 100,
      tasksInProgress: 2,
      tasksFailed: 5,
      averageExecutionTime: 1500,
      successRate: 0.95,
      resourceUsage: { cpu: 0.3, memory: 0.6 },
      uptime: 7200
    },
    taskQueue: [
      {
        id: 'task-1',
        type: 'test-task',
        priority: 'normal',
        status: 'running',
        payload: { test: true },
        createdAt: new Date(),
        startedAt: new Date()
      }
    ],
    lastActivity: new Date(),
    health: {
      status: 'healthy',
      lastCheck: new Date(),
      checks: [
        {
          name: 'connectivity',
          status: 'pass',
          timestamp: new Date(),
          duration: 50
        }
      ],
      issues: []
    }
  },
  {
    id: 'agent-2',
    name: 'Test Agent 2',
    description: 'Another test agent',
    type: 'autonomous',
    status: 'error',
    config: {
      maxConcurrentTasks: 3,
      timeout: 15000,
      retryAttempts: 2,
      resources: { cpu: 0.3, memory: 512 },
      permissions: ['read'],
      environment: {}
    },
    metrics: {
      tasksCompleted: 50,
      tasksInProgress: 0,
      tasksFailed: 10,
      averageExecutionTime: 2000,
      successRate: 0.83,
      resourceUsage: { cpu: 0.1, memory: 0.2 },
      uptime: 3600
    },
    taskQueue: [],
    lastActivity: new Date(),
    health: {
      status: 'critical',
      lastCheck: new Date(),
      checks: [
        {
          name: 'connectivity',
          status: 'fail',
          message: 'Connection timeout',
          timestamp: new Date(),
          duration: 5000
        }
      ],
      issues: [
        {
          id: 'issue-1',
          type: 'connectivity',
          severity: 'critical',
          message: 'Unable to connect to service',
          timestamp: new Date(),
          resolved: false
        }
      ]
    }
  }
];

describe('AgentDashboard', () => {
  const mockHandlers = {
    onStartAgent: vi.fn(),
    onStopAgent: vi.fn(),
    onRestartAgent: vi.fn(),
    onConfigureAgent: vi.fn(),
    onDeleteAgent: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();

  describe('rendering', () => {
    it('should render dashboard header and stats', () => {
      render(<AgentDashboard agents={mockAgents} {...mockHandlers} />);

      expect(screen.getByText('Agent Management')).toBeInTheDocument();
      expect(screen.getByText('Monitor and control your AI agents')).toBeInTheDocument();
      expect(screen.getByText('Total Agents')).toBeInTheDocument();
      expect(screen.getByText('2')).toBeInTheDocument(); // Total agents count

    it('should display agent statistics correctly', () => {
      render(<AgentDashboard agents={mockAgents} {...mockHandlers} />);

      expect(screen.getByText('Running')).toBeInTheDocument();
      expect(screen.getByText('1')).toBeInTheDocument(); // 1 running agent
      expect(screen.getByText('Tasks Completed')).toBeInTheDocument();
      expect(screen.getByText('150')).toBeInTheDocument(); // 100 + 50 completed tasks

    it('should render agent cards with correct information', () => {
      render(<AgentDashboard agents={mockAgents} {...mockHandlers} />);

      expect(screen.getByText('Test Agent 1')).toBeInTheDocument();
      expect(screen.getByText('Test Agent 2')).toBeInTheDocument();
      expect(screen.getByText('A test agent for unit testing')).toBeInTheDocument();
      expect(screen.getByText('Another test agent')).toBeInTheDocument();


  describe('search and filtering', () => {
    it('should filter agents by search term', async () => {
      render(<AgentDashboard agents={mockAgents} {...mockHandlers} />);

      const searchInput = screen.getByPlaceholderText('Search agents...');
      fireEvent.change(searchInput, { target: { value: 'Agent 1' } });

      await waitFor(() => {
        expect(screen.getByText('Test Agent 1')).toBeInTheDocument();
        expect(screen.queryByText('Test Agent 2')).not.toBeInTheDocument();


    it('should filter agents by status', async () => {
      render(<AgentDashboard agents={mockAgents} {...mockHandlers} />);

      const statusFilter = screen.getByDisplayValue('All Status');
      fireEvent.change(statusFilter, { target: { value: 'running' } });

      await waitFor(() => {
        expect(screen.getByText('Test Agent 1')).toBeInTheDocument();
        expect(screen.queryByText('Test Agent 2')).not.toBeInTheDocument();


    it('should show no results message when no agents match', async () => {
      render(<AgentDashboard agents={mockAgents} {...mockHandlers} />);

      const searchInput = screen.getByPlaceholderText('Search agents...');
      fireEvent.change(searchInput, { target: { value: 'nonexistent' } });

      await waitFor(() => {
        expect(screen.getByText('No agents found matching your criteria.')).toBeInTheDocument();



  describe('agent actions', () => {
    it('should call onStartAgent when start button is clicked', async () => {
      render(<AgentDashboard agents={mockAgents} {...mockHandlers} />);

      // Find the stopped/idle agent and click start
      const startButtons = screen.getAllByText('Start');
      if (startButtons.length > 0) {
        fireEvent.click(startButtons[0]);
        await waitFor(() => {
          expect(mockHandlers.onStartAgent).toHaveBeenCalled();

      }

    it('should call onStopAgent when stop button is clicked', async () => {
      render(<AgentDashboard agents={mockAgents} {...mockHandlers} />);

      const stopButtons = screen.getAllByText('Stop');
      if (stopButtons.length > 0) {
        fireEvent.click(stopButtons[0]);
        await waitFor(() => {
          expect(mockHandlers.onStopAgent).toHaveBeenCalled();

      }

    it('should call onRestartAgent when restart button is clicked', async () => {
      render(<AgentDashboard agents={mockAgents} {...mockHandlers} />);

      const restartButtons = screen.getAllByText('Restart');
      fireEvent.click(restartButtons[0]);

      await waitFor(() => {
        expect(mockHandlers.onRestartAgent).toHaveBeenCalledWith('agent-1');


    it('should call onConfigureAgent when config button is clicked', async () => {
      render(<AgentDashboard agents={mockAgents} {...mockHandlers} />);

      const configButtons = screen.getAllByText('Config');
      fireEvent.click(configButtons[0]);

      await waitFor(() => {
        expect(mockHandlers.onConfigureAgent).toHaveBeenCalledWith('agent-1');



  describe('agent selection and details', () => {
    it('should show agent details when agent is selected', async () => {
      render(<AgentDashboard agents={mockAgents} {...mockHandlers} />);

      const agentCard = screen.getByText('Test Agent 1').closest('div[role="button"], div');
      if (agentCard) {
        fireEvent.click(agentCard);

        await waitFor(() => {
          expect(screen.getByText('Overview')).toBeInTheDocument();
          expect(screen.getByText('Tasks')).toBeInTheDocument();
          expect(screen.getByText('Health')).toBeInTheDocument();

      }

    it('should show select agent message when no agent is selected', () => {
      render(<AgentDashboard agents={mockAgents} {...mockHandlers} />);

      expect(screen.getByText('Select an agent to view details')).toBeInTheDocument();


  describe('resource usage display', () => {
    it('should display CPU and memory usage correctly', () => {
      render(<AgentDashboard agents={mockAgents} {...mockHandlers} />);

      expect(screen.getByText('CPU')).toBeInTheDocument();
      expect(screen.getByText('Memory')).toBeInTheDocument();
      expect(screen.getByText('30.0%')).toBeInTheDocument(); // CPU usage for agent 1
      expect(screen.getByText('60.0%')).toBeInTheDocument(); // Memory usage for agent 1


  describe('health status display', () => {
    it('should display health status icons correctly', () => {
      render(<AgentDashboard agents={mockAgents} {...mockHandlers} />);

      // Should have health icons for both agents
      const healthyIcons = screen.getAllByTestId('check-circle') || [];
      const criticalIcons = screen.getAllByTestId('alert-circle') || [];
      
      // At least one of each type should be present based on mock data
      expect(healthyIcons.length + criticalIcons.length).toBeGreaterThan(0);


  describe('empty state', () => {
    it('should show empty state when no agents are provided', () => {
      render(<AgentDashboard agents={[]} {...mockHandlers} />);

      expect(screen.getByText('No agents found matching your criteria.')).toBeInTheDocument();
      expect(screen.getByText('0')).toBeInTheDocument(); // Total agents count


  describe('loading states', () => {
    it('should disable buttons during loading', async () => {
      const slowHandler = vi.fn(() => new Promise(resolve => setTimeout(resolve, 100)));
      render(<AgentDashboard agents={mockAgents} onRestartAgent={slowHandler} />);

      const restartButton = screen.getAllByText('Restart')[0];
      fireEvent.click(restartButton);

      // Button should be disabled during loading
      expect(restartButton).toBeDisabled();


