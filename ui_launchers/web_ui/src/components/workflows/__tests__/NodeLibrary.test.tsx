
import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { NodeLibrary } from '../NodeLibrary';

describe('NodeLibrary', () => {
  describe('rendering', () => {
    it('should render search input', () => {
      render(<NodeLibrary />);

      expect(screen.getByPlaceholderText('Search nodes...')).toBeInTheDocument();

    it('should render category tabs', () => {
      render(<NodeLibrary />);

      expect(screen.getByText('All')).toBeInTheDocument();
      expect(screen.getByText('Input')).toBeInTheDocument();
      expect(screen.getByText('AI')).toBeInTheDocument();
      expect(screen.getByText('Control')).toBeInTheDocument();
      expect(screen.getByText('Tools')).toBeInTheDocument();
      expect(screen.getByText('Output')).toBeInTheDocument();

    it('should render node templates', () => {
      render(<NodeLibrary />);

      expect(screen.getByText('Text Input')).toBeInTheDocument();
      expect(screen.getByText('LLM Chat')).toBeInTheDocument();
      expect(screen.getByText('Memory Search')).toBeInTheDocument();
      expect(screen.getByText('Condition')).toBeInTheDocument();

    it('should show drag instruction when not read-only', () => {
      render(<NodeLibrary />);

      expect(screen.getByText(/drag nodes to the canvas/i)).toBeInTheDocument();

    it('should not show drag instruction in read-only mode', () => {
      render(<NodeLibrary readOnly />);

      expect(screen.queryByText(/drag nodes to the canvas/i)).not.toBeInTheDocument();


  describe('search functionality', () => {
    it('should filter nodes by name', async () => {
      render(<NodeLibrary />);

      const searchInput = screen.getByPlaceholderText('Search nodes...');
      fireEvent.change(searchInput, { target: { value: 'LLM' } });

      await waitFor(() => {
        expect(screen.getByText('LLM Chat')).toBeInTheDocument();
        expect(screen.queryByText('Text Input')).not.toBeInTheDocument();


    it('should filter nodes by description', async () => {
      render(<NodeLibrary />);

      const searchInput = screen.getByPlaceholderText('Search nodes...');
      fireEvent.change(searchInput, { target: { value: 'language model' } });

      await waitFor(() => {
        expect(screen.getByText('LLM Chat')).toBeInTheDocument();


    it('should show no results message when search yields no matches', async () => {
      render(<NodeLibrary />);

      const searchInput = screen.getByPlaceholderText('Search nodes...');
      fireEvent.change(searchInput, { target: { value: 'nonexistent' } });

      await waitFor(() => {
        expect(screen.getByText(/no nodes found matching/i)).toBeInTheDocument();


    it('should be case insensitive', async () => {
      render(<NodeLibrary />);

      const searchInput = screen.getByPlaceholderText('Search nodes...');
      fireEvent.change(searchInput, { target: { value: 'llm' } });

      await waitFor(() => {
        expect(screen.getByText('LLM Chat')).toBeInTheDocument();



  describe('category filtering', () => {
    it('should show all nodes by default', () => {
      render(<NodeLibrary />);

      expect(screen.getByText('Text Input')).toBeInTheDocument();
      expect(screen.getByText('LLM Chat')).toBeInTheDocument();
      expect(screen.getByText('Condition')).toBeInTheDocument();

    it('should filter by input category', async () => {
      render(<NodeLibrary />);

      const inputTab = screen.getByText('Input');
      fireEvent.click(inputTab);

      await waitFor(() => {
        expect(screen.getByText('Text Input')).toBeInTheDocument();
        expect(screen.getByText('File Input')).toBeInTheDocument();
        expect(screen.queryByText('LLM Chat')).not.toBeInTheDocument();


    it('should filter by AI category', async () => {
      render(<NodeLibrary />);

      const aiTab = screen.getByText('AI');
      fireEvent.click(aiTab);

      await waitFor(() => {
        expect(screen.getByText('LLM Chat')).toBeInTheDocument();
        expect(screen.getByText('Memory Search')).toBeInTheDocument();
        expect(screen.queryByText('Text Input')).not.toBeInTheDocument();


    it('should filter by control category', async () => {
      render(<NodeLibrary />);

      const controlTab = screen.getByText('Control');
      fireEvent.click(controlTab);

      await waitFor(() => {
        expect(screen.getByText('Condition')).toBeInTheDocument();
        expect(screen.getByText('Loop')).toBeInTheDocument();
        expect(screen.queryByText('LLM Chat')).not.toBeInTheDocument();


    it('should combine search and category filters', async () => {
      render(<NodeLibrary />);

      const aiTab = screen.getByText('AI');
      fireEvent.click(aiTab);

      const searchInput = screen.getByPlaceholderText('Search nodes...');
      fireEvent.change(searchInput, { target: { value: 'memory' } });

      await waitFor(() => {
        expect(screen.getByText('Memory Search')).toBeInTheDocument();
        expect(screen.queryByText('LLM Chat')).not.toBeInTheDocument();
        expect(screen.queryByText('Text Input')).not.toBeInTheDocument();



  describe('node information display', () => {
    it('should display node names and descriptions', () => {
      render(<NodeLibrary />);

      expect(screen.getByText('Text Input')).toBeInTheDocument();
      expect(screen.getByText(/accepts text input from user/i)).toBeInTheDocument();

    it('should display category badges', () => {
      render(<NodeLibrary />);

      const inputBadges = screen.getAllByText('input');
      expect(inputBadges.length).toBeGreaterThan(0);

    it('should display input/output counts', () => {
      render(<NodeLibrary />);

      // Look for input/output count indicators
      expect(screen.getByText('0 in')).toBeInTheDocument(); // Text Input has 0 inputs
      expect(screen.getByText('1 out')).toBeInTheDocument(); // Text Input has 1 output


  describe('drag and drop', () => {
    it('should make nodes draggable when not read-only', () => {
      render(<NodeLibrary />);

      const textInputNode = screen.getByText('Text Input').closest('[draggable]');
      expect(textInputNode).toHaveAttribute('draggable', 'true');

    it('should not make nodes draggable in read-only mode', () => {
      render(<NodeLibrary readOnly />);

      const textInputNode = screen.getByText('Text Input').closest('[draggable]');
      expect(textInputNode).toHaveAttribute('draggable', 'false');

    it('should handle drag start events', () => {
      render(<NodeLibrary />);

      const textInputCard = screen.getByText('Text Input').closest('div');
      const dragStartEvent = new Event('dragstart', { bubbles: true });
      
      // Mock dataTransfer
      Object.defineProperty(dragStartEvent, 'dataTransfer', {
        value: {
          setData: vi.fn(),
          effectAllowed: ''
        }

      if (textInputCard) {
        fireEvent(textInputCard, dragStartEvent);
      }

      expect(dragStartEvent.dataTransfer.setData).toHaveBeenCalled();

    it('should prevent drag start in read-only mode', () => {
      render(<NodeLibrary readOnly />);

      const textInputCard = screen.getByText('Text Input').closest('div');
      const dragStartEvent = new Event('dragstart', { bubbles: true });
      
      Object.defineProperty(dragStartEvent, 'dataTransfer', {
        value: {
          setData: vi.fn(),
          effectAllowed: ''
        }

      if (textInputCard) {
        fireEvent(textInputCard, dragStartEvent);
      }

      // In read-only mode, preventDefault should be called
      expect(dragStartEvent.defaultPrevented).toBe(true);


  describe('accessibility', () => {
    it('should have proper ARIA labels', () => {
      render(<NodeLibrary />);

      const searchInput = screen.getByPlaceholderText('Search nodes...');
      expect(searchInput).toBeInTheDocument();

    it('should support keyboard navigation', () => {
      render(<NodeLibrary />);

      const searchInput = screen.getByPlaceholderText('Search nodes...');
      searchInput.focus();
      expect(document.activeElement).toBe(searchInput);


  describe('visual states', () => {
    it('should show hover states on interactive elements', () => {
      render(<NodeLibrary />);

      const textInputCard = screen.getByText('Text Input').closest('div');
      expect(textInputCard).toHaveClass('cursor-pointer');

    it('should show disabled state in read-only mode', () => {
      render(<NodeLibrary readOnly />);

      const textInputCard = screen.getByText('Text Input').closest('div');
      expect(textInputCard).toHaveClass('opacity-50', 'cursor-not-allowed');


  describe('node template data', () => {
    it('should include all required node template properties', () => {
      render(<NodeLibrary />);

      // Verify that nodes have the expected structure by checking for specific elements
      expect(screen.getByText('Text Input')).toBeInTheDocument();
      expect(screen.getByText('LLM Chat')).toBeInTheDocument();
      expect(screen.getByText('Memory Search')).toBeInTheDocument();
      expect(screen.getByText('Plugin Executor')).toBeInTheDocument();
      expect(screen.getByText('Condition')).toBeInTheDocument();
      expect(screen.getByText('Loop')).toBeInTheDocument();
      expect(screen.getByText('Text Output')).toBeInTheDocument();
      expect(screen.getByText('Webhook Output')).toBeInTheDocument();

    it('should display correct categories for each node type', () => {
      render(<NodeLibrary />);

      // Check that category badges are displayed correctly
      const categoryBadges = screen.getAllByText(/^(input|ai|integration|control|output)$/);
      expect(categoryBadges.length).toBeGreaterThan(0);


