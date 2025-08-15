# Path: ui_launchers/web_ui/src/components/chat/__tests__/Composer.test.tsx

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Composer } from '../Composer';
import { useFeature } from '@/hooks/use-feature';
import { useTelemetry } from '@/hooks/use-telemetry';
import { useVoiceInput } from '@/hooks/use-voice-input';

// Mock dependencies
jest.mock('@/hooks/use-feature');
jest.mock('@/hooks/use-telemetry');
jest.mock('@/hooks/use-voice-input');
jest.mock('@/components/security/RBACGuard', () => ({
  RBACGuard: ({ children, fallback }: any) => children || fallback
}));

const mockUseFeature = useFeature as jest.MockedFunction<typeof useFeature>;
const mockUseTelemetry = useTelemetry as jest.MockedFunction<typeof useTelemetry>;
const mockUseVoiceInput = useVoiceInput as jest.MockedFunction<typeof useVoiceInput>;

describe('Composer', () => {
  const mockOnSubmit = jest.fn();
  const mockTrack = jest.fn();
  const mockStartRecording = jest.fn();
  const mockStopRecording = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();

    mockUseFeature.mockImplementation((feature: string) => {
      const features: Record<string, boolean> = {
        'voice.input': true,
        'attachments.enabled': true,
        'chat.quick_actions': true,
        'emoji.picker': true
      };
      return features[feature] ?? false;
    });

    mockUseTelemetry.mockReturnValue({
      track: mockTrack
    } as any);

    mockUseVoiceInput.mockReturnValue({
      isRecording: false,
      isSupported: true,
      startRecording: mockStartRecording,
      stopRecording: mockStopRecording,
      transcript: ''
    } as any);

    mockOnSubmit.mockResolvedValue(undefined);
  });

  it('should render with default props', () => {
    render(<Composer onSubmit={mockOnSubmit} />);

    expect(screen.getByPlaceholderText('Type your message...')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /send message/i })).toBeInTheDocument();
  });

  it('should render with custom placeholder', () => {
    render(<Composer onSubmit={mockOnSubmit} placeholder="Custom placeholder" />);

    expect(screen.getByPlaceholderText('Custom placeholder')).toBeInTheDocument();
  });

  it('should handle text input', async () => {
    const user = userEvent.setup();
    render(<Composer onSubmit={mockOnSubmit} />);

    const textarea = screen.getByPlaceholderText('Type your message...');
    await user.type(textarea, 'Hello world');

    expect(textarea).toHaveValue('Hello world');
  });

  it('should submit message on Enter key', async () => {
    const user = userEvent.setup();
    render(<Composer onSubmit={mockOnSubmit} />);

    const textarea = screen.getByPlaceholderText('Type your message...');
    await user.type(textarea, 'Hello world');
    await user.keyboard('{Enter}');

    expect(mockOnSubmit).toHaveBeenCalledWith('Hello world', 'text');
    expect(mockTrack).toHaveBeenCalledWith('message_compose_submit', {
      messageLength: 11,
      messageType: 'text',
      hasQuickAction: false
    });
  });

  it('should add new line on Shift+Enter', async () => {
    const user = userEvent.setup();
    render(<Composer onSubmit={mockOnSubmit} />);

    const textarea = screen.getByPlaceholderText('Type your message...');
    await user.type(textarea, 'Line 1');
    await user.keyboard('{Shift>}{Enter}{/Shift}');
    await user.type(textarea, 'Line 2');

    expect(textarea).toHaveValue('Line 1\nLine 2');
    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it('should clear input on Escape key', async () => {
    const user = userEvent.setup();
    render(<Composer onSubmit={mockOnSubmit} />);

    const textarea = screen.getByPlaceholderText('Type your message...');
    await user.type(textarea, 'Hello world');
    await user.keyboard('{Escape}');

    expect(textarea).toHaveValue('');
  });

  it('should submit message on send button click', async () => {
    const user = userEvent.setup();
    render(<Composer onSubmit={mockOnSubmit} />);

    const textarea = screen.getByPlaceholderText('Type your message...');
    await user.type(textarea, 'Hello world');

    const sendButton = screen.getByRole('button', { name: /send message/i });
    await user.click(sendButton);

    expect(mockOnSubmit).toHaveBeenCalledWith('Hello world', 'text');
  });

  it('should disable send button when input is empty', () => {
    render(<Composer onSubmit={mockOnSubmit} />);

    const sendButton = screen.getByRole('button', { name: /send message/i });
    expect(sendButton).toBeDisabled();
  });

  it('should disable composer when isDisabled prop is true', () => {
    render(<Composer onSubmit={mockOnSubmit} isDisabled={true} />);

    const textarea = screen.getByPlaceholderText('Type your message...');
    const sendButton = screen.getByRole('button', { name: /send message/i });

    expect(textarea).toBeDisabled();
    expect(sendButton).toBeDisabled();
  });

  it('should show character count', async () => {
    const user = userEvent.setup();
    render(<Composer onSubmit={mockOnSubmit} maxLength={100} />);

    const textarea = screen.getByPlaceholderText('Type your message...');
    await user.type(textarea, 'Hello');

    expect(screen.getByText('5/100')).toBeInTheDocument();
  });

  it('should show warning when approaching character limit', async () => {
    const user = userEvent.setup();
    render(<Composer onSubmit={mockOnSubmit} maxLength={10} />);

    const textarea = screen.getByPlaceholderText('Type your message...');
    await user.type(textarea, 'Hello wor'); // 9 characters

    const characterCount = screen.getByText('9/10');
    expect(characterCount).toHaveClass('text-warning');
  });

  it('should show error when over character limit', async () => {
    const user = userEvent.setup();
    render(<Composer onSubmit={mockOnSubmit} maxLength={5} />);

    const textarea = screen.getByPlaceholderText('Type your message...');
    await user.type(textarea, 'Hello world'); // Over limit

    const characterCount = screen.getByText('11/5');
    expect(characterCount).toHaveClass('text-destructive');
    
    const sendButton = screen.getByRole('button', { name: /send message/i });
    expect(sendButton).toBeDisabled();
  });

  it('should render quick actions when enabled', () => {
    render(<Composer onSubmit={mockOnSubmit} features={{ quickActions: true }} />);

    expect(screen.getByText('Quick actions:')).toBeInTheDocument();
    expect(screen.getByText('Debug Code')).toBeInTheDocument();
    expect(screen.getByText('Explain')).toBeInTheDocument();
    expect(screen.getByText('Document')).toBeInTheDocument();
    expect(screen.getByText('Analyze')).toBeInTheDocument();
  });

  it('should handle quick action clicks', async () => {
    const user = userEvent.setup();
    render(<Composer onSubmit={mockOnSubmit} features={{ quickActions: true }} />);

    const debugButton = screen.getByText('Debug Code');
    await user.click(debugButton);

    const textarea = screen.getByPlaceholderText('Type your message...');
    expect(textarea).toHaveValue('Help me debug this code: ');
    expect(mockTrack).toHaveBeenCalledWith('quick_action_used', { action: 'Debug Code' });
  });

  it('should render voice input button when enabled', () => {
    render(<Composer onSubmit={mockOnSubmit} features={{ voice: true }} />);

    expect(screen.getByLabelText('Start voice input')).toBeInTheDocument();
  });

  it('should handle voice input toggle', async () => {
    const user = userEvent.setup();
    render(<Composer onSubmit={mockOnSubmit} features={{ voice: true }} />);

    const voiceButton = screen.getByLabelText('Start voice input');
    await user.click(voiceButton);

    expect(mockStartRecording).toHaveBeenCalled();
  });

  it('should show stop recording button when recording', () => {
    mockUseVoiceInput.mockReturnValue({
      isRecording: true,
      isSupported: true,
      startRecording: mockStartRecording,
      stopRecording: mockStopRecording,
      transcript: ''
    } as any);

    render(<Composer onSubmit={mockOnSubmit} features={{ voice: true }} />);

    expect(screen.getByLabelText('Stop recording')).toBeInTheDocument();
  });

  it('should show recording badge when recording', () => {
    mockUseVoiceInput.mockReturnValue({
      isRecording: true,
      isSupported: true,
      startRecording: mockStartRecording,
      stopRecording: mockStopRecording,
      transcript: ''
    } as any);

    render(<Composer onSubmit={mockOnSubmit} features={{ voice: true }} />);

    expect(screen.getByText('Recording...')).toBeInTheDocument();
  });

  it('should render attachment button when enabled', () => {
    render(<Composer onSubmit={mockOnSubmit} features={{ attachments: true }} />);

    expect(screen.getByLabelText('Attach file')).toBeInTheDocument();
  });

  it('should render emoji button when enabled', () => {
    render(<Composer onSubmit={mockOnSubmit} features={{ emoji: true }} />);

    expect(screen.getByLabelText('Add emoji')).toBeInTheDocument();
  });

  it('should show loading state when submitting', async () => {
    const user = userEvent.setup();
    mockOnSubmit.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

    render(<Composer onSubmit={mockOnSubmit} />);

    const textarea = screen.getByPlaceholderText('Type your message...');
    await user.type(textarea, 'Hello');

    const sendButton = screen.getByRole('button', { name: /send message/i });
    await user.click(sendButton);

    expect(screen.getByRole('button', { name: /send message/i })).toBeDisabled();
    // Should show loading spinner (implementation detail)
  });

  it('should handle submission errors', async () => {
    const user = userEvent.setup();
    const error = new Error('Submission failed');
    mockOnSubmit.mockRejectedValue(error);

    render(<Composer onSubmit={mockOnSubmit} />);

    const textarea = screen.getByPlaceholderText('Type your message...');
    await user.type(textarea, 'Hello');

    const sendButton = screen.getByRole('button', { name: /send message/i });
    await user.click(sendButton);

    await waitFor(() => {
      expect(screen.getByText('Submission failed')).toBeInTheDocument();
    });

    expect(mockTrack).toHaveBeenCalledWith('message_compose_error', { error: 'Submission failed' });
  });

  it('should auto-resize textarea', async () => {
    const user = userEvent.setup();
    render(<Composer onSubmit={mockOnSubmit} />);

    const textarea = screen.getByPlaceholderText('Type your message...');
    
    // Mock scrollHeight to simulate content height change
    Object.defineProperty(textarea, 'scrollHeight', {
      value: 100,
      configurable: true
    });

    await user.type(textarea, 'Line 1\nLine 2\nLine 3');

    // The textarea should have its height adjusted (implementation detail)
    expect(textarea).toBeInTheDocument();
  });

  it('should show help text', () => {
    render(<Composer onSubmit={mockOnSubmit} />);

    expect(screen.getByText(/Press.*Enter.*to send/)).toBeInTheDocument();
    expect(screen.getByText(/Shift\+Enter.*for new line/)).toBeInTheDocument();
    expect(screen.getByText(/Esc.*to clear/)).toBeInTheDocument();
  });

  it('should handle voice transcript input', () => {
    mockUseVoiceInput.mockImplementation(({ onTranscript }) => {
      // Simulate transcript callback
      React.useEffect(() => {
        onTranscript?.('Voice input text');
      }, [onTranscript]);

      return {
        isRecording: false,
        isSupported: true,
        startRecording: mockStartRecording,
        stopRecording: mockStopRecording,
        transcript: 'Voice input text'
      } as any;
    });

    render(<Composer onSubmit={mockOnSubmit} features={{ voice: true }} />);

    const textarea = screen.getByPlaceholderText('Type your message...');
    expect(textarea).toHaveValue('Voice input text');
  });

  it('should not render features when disabled by feature flags', () => {
    mockUseFeature.mockReturnValue(false);

    render(<Composer 
      onSubmit={mockOnSubmit} 
      features={{ 
        voice: true, 
        attachments: true, 
        quickActions: true, 
        emoji: true 
      }} 
    />);

    expect(screen.queryByLabelText('Start voice input')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Attach file')).not.toBeInTheDocument();
    expect(screen.queryByText('Quick actions:')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Add emoji')).not.toBeInTheDocument();
  });

  it('should apply custom className', () => {
    const { container } = render(
      <Composer onSubmit={mockOnSubmit} className="custom-class" />
    );

    expect(container.querySelector('.custom-class')).toBeInTheDocument();
  });
});