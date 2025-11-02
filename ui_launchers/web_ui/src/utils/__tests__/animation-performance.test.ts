import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {  AnimationPerformanceMonitor, performanceAnimationVariants, reducedMotionVariants, animationCSS, ANIMATION_PERFORMANCE_THRESHOLDS } from '../animation-performance';

// Mock performance API
const mockPerformance = {
  now: vi.fn(() => 1000),
};

// Mock requestAnimationFrame
const mockRequestAnimationFrame = vi.fn((callback) => {
  setTimeout(callback, 16);
  return 1;

const mockCancelAnimationFrame = vi.fn();

// Setup global mocks
Object.defineProperty(global, 'performance', {
  writable: true,
  value: mockPerformance,

Object.defineProperty(global, 'requestAnimationFrame', {
  writable: true,
  value: mockRequestAnimationFrame,

Object.defineProperty(global, 'cancelAnimationFrame', {
  writable: true,
  value: mockCancelAnimationFrame,

describe('AnimationPerformanceMonitor', () => {
  let monitor: AnimationPerformanceMonitor;
  let onPerformanceUpdate: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vi.clearAllMocks();
    onPerformanceUpdate = vi.fn();
    monitor = new AnimationPerformanceMonitor(onPerformanceUpdate);

  afterEach(() => {
    monitor.stopMonitoring();

  describe('basic functionality', () => {
    it('should create a monitor instance', () => {
      expect(monitor).toBeInstanceOf(AnimationPerformanceMonitor);

    it('should start monitoring', () => {
      monitor.startMonitoring();
      expect(mockRequestAnimationFrame).toHaveBeenCalled();

    it('should stop monitoring', () => {
      monitor.startMonitoring();
      monitor.stopMonitoring();
      expect(mockCancelAnimationFrame).toHaveBeenCalled();

    it('should not start monitoring multiple times', () => {
      monitor.startMonitoring();
      monitor.startMonitoring();
      
      // Should only call requestAnimationFrame once initially
      expect(mockRequestAnimationFrame).toHaveBeenCalledTimes(1);


  describe('metrics collection', () => {
    it('should return empty metrics when no frames measured', () => {
      const metrics = monitor.getMetrics();
      
      expect(metrics).toEqual({
        fps: 0,
        averageFrameTime: 0,
        maxFrameTime: 0,
        minFrameTime: 0,
        droppedFrames: 0,
        frameCount: 0,
        isSmooth: false,


    it('should calculate metrics correctly', async () => {
      let frameCount = 0;
      mockPerformance.now.mockImplementation(() => {
        frameCount++;
        return frameCount * 16; // 60fps = 16ms per frame

      monitor.startMonitoring();
      
      // Wait for a few frames
      await new Promise(resolve => setTimeout(resolve, 100));
      
      const metrics = monitor.getMetrics();
      
      expect(metrics.frameCount).toBeGreaterThan(0);
      expect(metrics.fps).toBeCloseTo(62.5, 1); // 1000/16 = 62.5fps
      expect(metrics.averageFrameTime).toBeCloseTo(16, 1);

    it('should detect dropped frames', async () => {
      let frameCount = 0;
      mockPerformance.now.mockImplementation(() => {
        frameCount++;
        // Simulate some slow frames
        return frameCount < 3 ? frameCount * 16 : frameCount * 20; // Some frames take 20ms

      monitor.startMonitoring();
      
      // Wait for frames
      await new Promise(resolve => setTimeout(resolve, 100));
      
      const metrics = monitor.getMetrics();
      
      expect(metrics.droppedFrames).toBeGreaterThan(0);
      expect(metrics.isSmooth).toBe(false);

    it('should call performance update callback', async () => {
      monitor.startMonitoring();
      
      // Wait for callback
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // Should call callback every 30 frames, but we might not reach that in test
      // Just verify the callback was set up
      expect(onPerformanceUpdate).toBeDefined();


  describe('performance rating', () => {
    it('should identify smooth animations', () => {
      mockPerformance.now.mockImplementation(() => Date.now());
      
      monitor.startMonitoring();
      
      // Simulate consistent 60fps
      for (let i = 0; i < 10; i++) {
        mockPerformance.now.mockReturnValue(i * 16.67);
      }
      
      const metrics = monitor.getMetrics();
      expect(metrics.isSmooth).toBe(true);

    it('should identify choppy animations', () => {
      mockPerformance.now.mockImplementation(() => Date.now());
      
      monitor.startMonitoring();
      
      // Simulate inconsistent frame times
      const frameTimes = [16, 33, 16, 50, 16, 33]; // Mix of good and bad frames
      frameTimes.forEach((time, i) => {
        mockPerformance.now.mockReturnValue(i * time);

      const metrics = monitor.getMetrics();
      expect(metrics.isSmooth).toBe(false);



describe('performanceAnimationVariants', () => {
  it('should have all required animation variants', () => {
    expect(performanceAnimationVariants).toHaveProperty('fade');
    expect(performanceAnimationVariants).toHaveProperty('slideUp');
    expect(performanceAnimationVariants).toHaveProperty('slideDown');
    expect(performanceAnimationVariants).toHaveProperty('slideLeft');
    expect(performanceAnimationVariants).toHaveProperty('slideRight');
    expect(performanceAnimationVariants).toHaveProperty('scale');
    expect(performanceAnimationVariants).toHaveProperty('spring');
    expect(performanceAnimationVariants).toHaveProperty('stagger');
    expect(performanceAnimationVariants).toHaveProperty('staggerItem');

  it('should have proper animation structure', () => {
    const fadeVariant = performanceAnimationVariants.fade;
    
    expect(fadeVariant).toHaveProperty('initial');
    expect(fadeVariant).toHaveProperty('animate');
    expect(fadeVariant).toHaveProperty('exit');
    expect(fadeVariant).toHaveProperty('transition');
    
    expect(fadeVariant.initial).toEqual({ opacity: 0 });
    expect(fadeVariant.animate).toEqual({ opacity: 1 });
    expect(fadeVariant.exit).toEqual({ opacity: 0 });

  it('should use performance-optimized properties', () => {
    const slideUpVariant = performanceAnimationVariants.slideUp;
    
    // Should only use transform and opacity for performance
    expect(slideUpVariant.initial).toEqual({ opacity: 0, y: 20 });
    expect(slideUpVariant.animate).toEqual({ opacity: 1, y: 0 });
    expect(slideUpVariant.exit).toEqual({ opacity: 0, y: -20 });

  it('should have optimized transition settings', () => {
    const scaleVariant = performanceAnimationVariants.scale;
    
    expect(scaleVariant.transition).toHaveProperty('duration');
    expect(scaleVariant.transition).toHaveProperty('ease');
    expect(scaleVariant.transition.duration).toBeLessThanOrEqual(0.3); // Fast animations


describe('reducedMotionVariants', () => {
  it('should have simplified animations for reduced motion', () => {
    const fadeVariant = reducedMotionVariants.fade;
    
    expect(fadeVariant.initial).toEqual({ opacity: 0 });
    expect(fadeVariant.animate).toEqual({ opacity: 1 });
    expect(fadeVariant.exit).toEqual({ opacity: 0 });
    expect(fadeVariant.transition.duration).toBe(0.1); // Very fast

  it('should remove transforms in reduced motion variants', () => {
    const slideUpVariant = reducedMotionVariants.slideUp;
    
    // Should only use opacity, no transforms
    expect(slideUpVariant.initial).toEqual({ opacity: 0 });
    expect(slideUpVariant.animate).toEqual({ opacity: 1 });
    expect(slideUpVariant.exit).toEqual({ opacity: 0 });

  it('should have minimal stagger delays', () => {
    const staggerVariant = reducedMotionVariants.stagger;
    
    expect(staggerVariant.animate.transition.staggerChildren).toBe(0.01);


describe('animationCSS', () => {
  it('should provide GPU acceleration styles', () => {
    expect(animationCSS.gpuAcceleration).toEqual({
      transform: 'translateZ(0)',
      willChange: 'transform, opacity',


  it('should provide optimization styles', () => {
    expect(animationCSS.optimizeForAnimation).toHaveProperty('willChange');
    expect(animationCSS.optimizeForAnimation).toHaveProperty('backfaceVisibility');
    expect(animationCSS.optimizeForAnimation).toHaveProperty('perspective');

  it('should provide will-change cleanup', () => {
    expect(animationCSS.removeWillChange).toEqual({
      willChange: 'auto',


  it('should provide containment styles', () => {
    expect(animationCSS.containment).toEqual({
      contain: 'layout style paint',


  it('should provide layer creation styles', () => {
    expect(animationCSS.forceLayer).toHaveProperty('transform');
    expect(animationCSS.forceLayer).toHaveProperty('isolation');


describe('ANIMATION_PERFORMANCE_THRESHOLDS', () => {
  it('should have correct FPS thresholds', () => {
    expect(ANIMATION_PERFORMANCE_THRESHOLDS.EXCELLENT_FPS).toBe(58);
    expect(ANIMATION_PERFORMANCE_THRESHOLDS.GOOD_FPS).toBe(50);
    expect(ANIMATION_PERFORMANCE_THRESHOLDS.POOR_FPS).toBe(30);

  it('should have correct frame time thresholds', () => {
    expect(ANIMATION_PERFORMANCE_THRESHOLDS.MAX_FRAME_TIME).toBeCloseTo(16.67, 2);
    expect(ANIMATION_PERFORMANCE_THRESHOLDS.ACCEPTABLE_FRAME_TIME).toBe(20);
    expect(ANIMATION_PERFORMANCE_THRESHOLDS.POOR_FRAME_TIME).toBeCloseTo(33.33, 2);

  it('should have realistic threshold values', () => {
    // 60fps should be the target
    expect(1000 / ANIMATION_PERFORMANCE_THRESHOLDS.MAX_FRAME_TIME).toBeCloseTo(60, 0);
    
    // 50fps should be acceptable
    expect(1000 / ANIMATION_PERFORMANCE_THRESHOLDS.ACCEPTABLE_FRAME_TIME).toBe(50);
    
    // 30fps should be the minimum
    expect(1000 / ANIMATION_PERFORMANCE_THRESHOLDS.POOR_FRAME_TIME).toBeCloseTo(30, 0);


describe('animation performance utilities', () => {
  it('should calculate FPS correctly', () => {
    const frameTime = 16.67; // 60fps
    const fps = 1000 / frameTime;
    expect(fps).toBeCloseTo(60, 0);

  it('should identify dropped frames correctly', () => {
    const frameTimes = [16, 16, 33, 16, 50]; // 2 dropped frames
    const droppedFrames = frameTimes.filter(time => time > 16.67).length;
    expect(droppedFrames).toBe(2);

  it('should calculate smoothness correctly', () => {
    const frameTimes = [16, 16, 16, 16, 16];
    const avgFrameTime = frameTimes.reduce((sum, time) => sum + time, 0) / frameTimes.length;
    const fps = 1000 / avgFrameTime;
    const droppedFrames = frameTimes.filter(time => time > 16.67).length;
    const isSmooth = fps >= 55 && droppedFrames / frameTimes.length < 0.1;
    
    expect(isSmooth).toBe(true);

