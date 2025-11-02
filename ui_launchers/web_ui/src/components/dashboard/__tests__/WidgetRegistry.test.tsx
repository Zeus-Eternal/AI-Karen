
import React from 'react';
import { render, screen } from '@testing-library/react';
import { vi } from 'vitest';

  widgetRegistry,
  getWidgetComponent,
  getWidgetDefaultConfig,
  getAvailableWidgetTypes,
  getWidgetInfo,
  createWidgetConfig
import { } from '../WidgetRegistry';
import type { WidgetConfig } from '@/types/dashboard';

describe('WidgetRegistry', () => {
  describe('widgetRegistry', () => {
    it('contains all expected widget types', () => {
      const expectedTypes = ['metric', 'status', 'chart', 'log', 'table'];
      const actualTypes = Object.keys(widgetRegistry);
      
      expectedTypes.forEach(type => {
        expect(actualTypes).toContain(type);


    it('has valid structure for each widget type', () => {
      Object.entries(widgetRegistry).forEach(([type, widget]) => {
        expect(widget).toHaveProperty('component');
        expect(widget).toHaveProperty('name');
        expect(widget).toHaveProperty('description');
        expect(widget).toHaveProperty('defaultConfig');
        expect(typeof widget.component).toBe('function');
        expect(typeof widget.name).toBe('string');
        expect(typeof widget.description).toBe('string');
        expect(typeof widget.defaultConfig).toBe('object');



  describe('getWidgetComponent', () => {
    it('returns component for valid widget type', () => {
      const component = getWidgetComponent('metric');
      expect(component).toBeDefined();
      expect(typeof component).toBe('function');

    it('returns null for invalid widget type', () => {
      const component = getWidgetComponent('invalid-type');
      expect(component).toBeNull();


  describe('getWidgetDefaultConfig', () => {
    it('returns default config for valid widget type', () => {
      const config = getWidgetDefaultConfig('metric');
      expect(config).toBeDefined();
      expect(config.type).toBe('metric');
      expect(config.size).toBeDefined();
      expect(config.position).toBeDefined();
      expect(config.enabled).toBe(true);

    it('returns empty object for invalid widget type', () => {
      const config = getWidgetDefaultConfig('invalid-type');
      expect(config).toEqual({});


  describe('getAvailableWidgetTypes', () => {
    it('returns array of widget types', () => {
      const types = getAvailableWidgetTypes();
      expect(Array.isArray(types)).toBe(true);
      expect(types.length).toBeGreaterThan(0);
      expect(types).toContain('metric');
      expect(types).toContain('status');
      expect(types).toContain('chart');


  describe('getWidgetInfo', () => {
    it('returns widget info for valid type', () => {
      const info = getWidgetInfo('metric');
      expect(info).toBeDefined();
      expect(info?.name).toBe('Metric Widget');
      expect(info?.description).toContain('KPIs');
      expect(info?.icon).toBe('TrendingUp');

    it('returns null for invalid type', () => {
      const info = getWidgetInfo('invalid-type');
      expect(info).toBeNull();


  describe('createWidgetConfig', () => {
    it('creates widget config with default values', () => {
      const config = createWidgetConfig('metric');
      
      expect(config.id).toBeDefined();
      expect(config.id).toMatch(/^widget_metric_/);
      expect(config.type).toBe('metric');
      expect(config.title).toBe('Metric Widget');
      expect(config.size).toBeDefined();
      expect(config.position).toBeDefined();
      expect(config.enabled).toBe(true);

    it('applies overrides to default config', () => {
      const overrides = {
        title: 'Custom Title',
        size: 'large' as const,
        config: { customProp: 'value' }
      };
      
      const config = createWidgetConfig('metric', overrides);
      
      expect(config.title).toBe('Custom Title');
      expect(config.size).toBe('large');
      expect(config.config.customProp).toBe('value');

    it('generates unique IDs for multiple widgets', () => {
      const config1 = createWidgetConfig('metric');
      const config2 = createWidgetConfig('metric');
      
      expect(config1.id).not.toBe(config2.id);


  describe('Widget Components', () => {
    it('renders MetricWidget placeholder', () => {
      const MetricWidget = getWidgetComponent('metric');
      const mockConfig: WidgetConfig = {
        id: 'test',
        type: 'metric',
        title: 'Test Metric',
        size: 'small',
        position: { x: 0, y: 0, w: 1, h: 1 },
        config: {},
        refreshInterval: 30000,
        enabled: true
      };

      if (MetricWidget) {
        render(<MetricWidget config={mockConfig} />);
        expect(screen.getByText('Metric Widget')).toBeInTheDocument();
        expect(screen.getByText('Test Metric')).toBeInTheDocument();
      }

    it('renders StatusWidget placeholder', () => {
      const StatusWidget = getWidgetComponent('status');
      const mockConfig: WidgetConfig = {
        id: 'test',
        type: 'status',
        title: 'Test Status',
        size: 'small',
        position: { x: 0, y: 0, w: 1, h: 1 },
        config: {},
        refreshInterval: 15000,
        enabled: true
      };

      if (StatusWidget) {
        render(<StatusWidget config={mockConfig} />);
        expect(screen.getByText('Status Widget')).toBeInTheDocument();
        expect(screen.getByText('Test Status')).toBeInTheDocument();
      }

    it('renders ChartWidget placeholder', () => {
      const ChartWidget = getWidgetComponent('chart');
      const mockConfig: WidgetConfig = {
        id: 'test',
        type: 'chart',
        title: 'Test Chart',
        size: 'medium',
        position: { x: 0, y: 0, w: 2, h: 1 },
        config: {},
        refreshInterval: 60000,
        enabled: true
      };

      if (ChartWidget) {
        render(<ChartWidget config={mockConfig} />);
        expect(screen.getByText('Chart Widget')).toBeInTheDocument();
        expect(screen.getByText('Test Chart')).toBeInTheDocument();
      }

    it('renders LogWidget placeholder', () => {
      const LogWidget = getWidgetComponent('log');
      const mockConfig: WidgetConfig = {
        id: 'test',
        type: 'log',
        title: 'Test Logs',
        size: 'large',
        position: { x: 0, y: 0, w: 2, h: 2 },
        config: {},
        refreshInterval: 5000,
        enabled: true
      };

      if (LogWidget) {
        render(<LogWidget config={mockConfig} />);
        expect(screen.getByText('Log Widget')).toBeInTheDocument();
        expect(screen.getByText('Test Logs')).toBeInTheDocument();
      }

    it('renders TableWidget placeholder', () => {
      const TableWidget = getWidgetComponent('table');
      const mockConfig: WidgetConfig = {
        id: 'test',
        type: 'table',
        title: 'Test Table',
        size: 'medium',
        position: { x: 0, y: 0, w: 2, h: 1 },
        config: {},
        refreshInterval: 30000,
        enabled: true
      };

      if (TableWidget) {
        render(<TableWidget config={mockConfig} />);
        expect(screen.getByText('Table Widget')).toBeInTheDocument();
        expect(screen.getByText('Test Table')).toBeInTheDocument();
      }


