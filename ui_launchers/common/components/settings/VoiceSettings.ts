// Shared Voice Settings Component
// Framework-agnostic voice and TTS configuration interface

import { KarenSettings, Theme } from '../../abstractions/types';

export interface VoiceSettingsOptions {
  enableVoiceSelection?: boolean;
  enableVoicePreview?: boolean;
  showAdvancedOptions?: boolean;
}

export interface VoiceSettingsState {
  selectedVoiceURI: string | null;
  availableVoices: SpeechSynthesisVoice[];
  isPlaying: boolean;
  volume: number;
  rate: number;
  pitch: number;
}

export class SharedVoiceSettings {
  private state: VoiceSettingsState;
  private options: VoiceSettingsOptions;
  private theme: Theme;

  constructor(
    settings: KarenSettings,
    theme: Theme,
    options: VoiceSettingsOptions = {}
  ) {
    this.theme = theme;
    this.options = {
      enableVoiceSelection: true,
      enableVoicePreview: true,
      showAdvancedOptions: false,
      ...options
    };

    this.state = {
      selectedVoiceURI: settings.ttsVoiceURI,
      availableVoices: [],
      isPlaying: false,
      volume: 1.0,
      rate: 1.0,
      pitch: 1.0
    };

    this.loadVoices();
  }

  private loadVoices(): void {
    if ('speechSynthesis' in window) {
      this.state.availableVoices = speechSynthesis.getVoices();
    }
  }

  getRenderData() {
    return {
      state: this.state,
      options: this.options,
      theme: this.theme,
      handlers: {
        onVoiceChange: (voiceURI: string) => this.updateVoice(voiceURI),
        onPreviewVoice: () => this.previewVoice(),
        onVolumeChange: (volume: number) => this.updateVolume(volume),
        onRateChange: (rate: number) => this.updateRate(rate),
        onPitchChange: (pitch: number) => this.updatePitch(pitch)
      }
    };
  }

  private updateVoice(voiceURI: string): void {
    this.state.selectedVoiceURI = voiceURI;
  }

  private previewVoice(): void {
    // Implementation for voice preview
  }

  private updateVolume(volume: number): void {
    this.state.volume = volume;
  }

  private updateRate(rate: number): void {
    this.state.rate = rate;
  }

  private updatePitch(pitch: number): void {
    this.state.pitch = pitch;
  }
}