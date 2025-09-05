/**
 * Professional Drum Machine Engine with Tone.js
 * Comprehensive 16-step sequencer with advanced features
 */

import * as Tone from 'tone';

export type DrumVoice = 'kick' | 'snare' | 'hat';
export type SampleKit = 'CR78' | '808' | '909' | 'Synth';

export interface DrumStep {
  active: boolean;
  velocity: number; // 0-1
  probability: number; // 0-1 
  ratchet: number; // 1-4 subdivisions
}

export interface DrumPattern {
  kick: DrumStep[];
  snare: DrumStep[];
  hat: DrumStep[];
}

export interface DrumSettings {
  swing: number; // 0-1
  humanize: number; // 0-1
  tempo: number; // BPM
  kit: SampleKit;
  reverb: {
    kick: number; // 0-1 send level
    snare: number;
    hat: number;
  };
  sidechain: {
    enabled: boolean;
    amount: number; // 0-1
  };
}

export class DrumsPro {
  private voices: Record<DrumVoice, Tone.Synth | Tone.NoiseSynth | Tone.MembraneSynth>;
  private reverb: Tone.Reverb;
  private compressor: Tone.Compressor;
  private sidechainCompressor: Tone.Compressor;
  private kickBus: Tone.Gain;
  private nonKickBus: Tone.Gain;
  private mainBus: Tone.Gain;
  private sequence: Tone.Sequence | null = null;
  
  public patterns: { A: DrumPattern; B: DrumPattern };
  public currentPattern: 'A' | 'B' = 'A';
  public settings: DrumSettings;
  public isPlaying = false;
  public currentStep = 0;

  constructor() {
    this.initializeAudioChain();
    this.initializeVoices();
    this.initializePatterns();
    this.initializeSettings();
  }

  private initializeAudioChain(): void {
    // Main audio chain setup
    this.reverb = new Tone.Reverb({
      roomSize: 0.7,
      dampening: 3000,
      wet: 0.3
    });

    this.compressor = new Tone.Compressor({
      threshold: -12,
      ratio: 3,
      attack: 0.003,
      release: 0.1
    });

    this.sidechainCompressor = new Tone.Compressor({
      threshold: -20,
      ratio: 6,
      attack: 0.003,
      release: 0.1
    });

    // Bus routing
    this.kickBus = new Tone.Gain(0.8);
    this.nonKickBus = new Tone.Gain(0.7);
    this.mainBus = new Tone.Gain(0.9);

    // Connect audio chain
    this.kickBus.connect(this.mainBus);
    this.nonKickBus.connect(this.sidechainCompressor);
    this.sidechainCompressor.connect(this.mainBus);
    this.mainBus.connect(this.compressor);
    this.compressor.connect(this.reverb);
    this.reverb.toDestination();
  }

  private initializeVoices(): void {
    this.voices = {
      kick: new Tone.MembraneSynth({
        pitchDecay: 0.05,
        octaves: 10,
        oscillator: { type: "sine" },
        envelope: { attack: 0.001, decay: 0.4, sustain: 0.01, release: 1.4 }
      }),
      snare: new Tone.NoiseSynth({
        noise: { type: "white" },
        envelope: { attack: 0.005, decay: 0.1, sustain: 0.0, release: 0.4 }
      }),
      hat: new Tone.NoiseSynth({
        noise: { type: "white" },
        envelope: { attack: 0.001, decay: 0.05, sustain: 0.0, release: 0.03 }
      })
    };

    // Connect voices to buses
    this.voices.kick.connect(this.kickBus);
    this.voices.snare.connect(this.nonKickBus);
    this.voices.hat.connect(this.nonKickBus);
    
    this.updateKit('808'); // Default kit
  }

  private initializePatterns(): void {
    const emptyStep: DrumStep = {
      active: false,
      velocity: 0.8,
      probability: 1.0,
      ratchet: 1
    };

    this.patterns = {
      A: {
        kick: Array(16).fill(null).map(() => ({ ...emptyStep })),
        snare: Array(16).fill(null).map(() => ({ ...emptyStep })),
        hat: Array(16).fill(null).map(() => ({ ...emptyStep }))
      },
      B: {
        kick: Array(16).fill(null).map(() => ({ ...emptyStep })),
        snare: Array(16).fill(null).map(() => ({ ...emptyStep })),
        hat: Array(16).fill(null).map(() => ({ ...emptyStep }))
      }
    };

    // Set up basic pattern for pattern A
    this.patterns.A.kick[0].active = true;
    this.patterns.A.kick[4].active = true;
    this.patterns.A.kick[8].active = true;
    this.patterns.A.kick[12].active = true;
    
    this.patterns.A.snare[4].active = true;
    this.patterns.A.snare[12].active = true;
    
    this.patterns.A.hat[2].active = true;
    this.patterns.A.hat[6].active = true;
    this.patterns.A.hat[10].active = true;
    this.patterns.A.hat[14].active = true;
  }

  private initializeSettings(): void {
    this.settings = {
      swing: 0,
      humanize: 0,
      tempo: 120,
      kit: '808',
      reverb: {
        kick: 0.1,
        snare: 0.3,
        hat: 0.2
      },
      sidechain: {
        enabled: true,
        amount: 0.6
      }
    };
  }

  public updateKit(kit: SampleKit): void {
    this.settings.kit = kit;
    
    // Update voice characteristics based on kit
    switch (kit) {
      case 'CR78':
        this.updateVoiceParams('kick', { pitchDecay: 0.08, octaves: 6 });
        this.updateVoiceParams('snare', { envelope: { decay: 0.15, release: 0.3 } });
        this.updateVoiceParams('hat', { envelope: { decay: 0.08, release: 0.05 } });
        break;
        
      case '808':
        this.updateVoiceParams('kick', { pitchDecay: 0.05, octaves: 10 });
        this.updateVoiceParams('snare', { envelope: { decay: 0.1, release: 0.4 } });
        this.updateVoiceParams('hat', { envelope: { decay: 0.05, release: 0.03 } });
        break;
        
      case '909':
        this.updateVoiceParams('kick', { pitchDecay: 0.03, octaves: 8 });
        this.updateVoiceParams('snare', { envelope: { decay: 0.08, release: 0.3 } });
        this.updateVoiceParams('hat', { envelope: { decay: 0.03, release: 0.02 } });
        break;
        
      case 'Synth':
        this.updateVoiceParams('kick', { pitchDecay: 0.1, octaves: 12 });
        this.updateVoiceParams('snare', { envelope: { decay: 0.2, release: 0.6 } });
        this.updateVoiceParams('hat', { envelope: { decay: 0.1, release: 0.08 } });
        break;
    }
  }

  private updateVoiceParams(voice: DrumVoice, params: any): void {
    const voiceInstance = this.voices[voice];
    if ('pitchDecay' in params && voiceInstance instanceof Tone.MembraneSynth) {
      voiceInstance.pitchDecay = params.pitchDecay;
    }
    if ('octaves' in params && voiceInstance instanceof Tone.MembraneSynth) {
      voiceInstance.octaves = params.octaves;
    }
    if ('envelope' in params) {
      Object.assign(voiceInstance.envelope, params.envelope);
    }
  }

  public play(): void {
    if (this.isPlaying) return;
    
    Tone.Transport.bpm.value = this.settings.tempo;
    
    // Create sequence with swing and humanization
    const pattern = this.patterns[this.currentPattern];
    let stepTime = 0;
    
    this.sequence = new Tone.Sequence(
      (time, step) => {
        this.currentStep = step;
        this.triggerStep(time, step, pattern);
      },
      Array.from({ length: 16 }, (_, i) => i),
      "16n"
    );

    this.sequence.start(0);
    Tone.Transport.start();
    this.isPlaying = true;
  }

  public stop(): void {
    if (!this.isPlaying) return;
    
    Tone.Transport.stop();
    if (this.sequence) {
      this.sequence.stop();
      this.sequence.dispose();
      this.sequence = null;
    }
    this.currentStep = 0;
    this.isPlaying = false;
  }

  private triggerStep(time: number, step: number, pattern: DrumPattern): void {
    // Apply swing timing
    let swingOffset = 0;
    if (step % 2 === 1 && this.settings.swing > 0) {
      swingOffset = (this.settings.swing * 0.1) * (60 / this.settings.tempo);
    }

    (['kick', 'snare', 'hat'] as DrumVoice[]).forEach(voice => {
      const stepData = pattern[voice][step];
      if (!stepData.active) return;

      // Probability check
      if (Math.random() > stepData.probability) return;

      // Humanization
      const humanizeOffset = this.settings.humanize * (Math.random() - 0.5) * 0.02;
      const triggerTime = time + swingOffset + humanizeOffset;

      // Velocity scaling
      const velocity = stepData.velocity * (0.7 + Math.random() * 0.3 * this.settings.humanize);

      // Handle ratcheting
      for (let r = 0; r < stepData.ratchet; r++) {
        const ratchetTime = triggerTime + (r * (60 / this.settings.tempo / 16));
        this.triggerVoice(voice, ratchetTime, velocity);
      }
    });

    // Sidechain trigger
    if (pattern.kick[step].active && this.settings.sidechain.enabled) {
      this.triggerSidechain(time + swingOffset);
    }
  }

  private triggerVoice(voice: DrumVoice, time: number, velocity: number): void {
    const voiceInstance = this.voices[voice];
    const reverbSend = this.settings.reverb[voice];

    if (voice === 'kick' && voiceInstance instanceof Tone.MembraneSynth) {
      voiceInstance.triggerAttackRelease("C1", "16n", time, velocity);
    } else if (voiceInstance instanceof Tone.NoiseSynth) {
      voiceInstance.triggerAttackRelease("16n", time, velocity);
    }

    // Apply reverb send (simplified - in production would use separate sends)
    if (reverbSend > 0) {
      voiceInstance.volume.value = Tone.gainToDb(velocity * (1 - reverbSend * 0.3));
    }
  }

  private triggerSidechain(time: number): void {
    if (!this.settings.sidechain.enabled) return;
    
    // Simulate sidechain ducking by modulating the compressor threshold
    this.sidechainCompressor.threshold.setValueAtTime(-20, time);
    this.sidechainCompressor.threshold.exponentialRampToValueAtTime(
      -20 + (this.settings.sidechain.amount * 15), 
      time + 0.1
    );
    this.sidechainCompressor.threshold.exponentialRampToValueAtTime(-20, time + 0.3);
  }

  public setStep(voice: DrumVoice, step: number, data: Partial<DrumStep>): void {
    Object.assign(this.patterns[this.currentPattern][voice][step], data);
  }

  public clearPattern(): void {
    const pattern = this.patterns[this.currentPattern];
    (['kick', 'snare', 'hat'] as DrumVoice[]).forEach(voice => {
      pattern[voice].forEach(step => {
        step.active = false;
      });
    });
  }

  public randomizePattern(voice?: DrumVoice): void {
    const voices: DrumVoice[] = voice ? [voice] : ['kick', 'snare', 'hat'];
    const pattern = this.patterns[this.currentPattern];

    voices.forEach(v => {
      pattern[v].forEach((step, i) => {
        step.active = Math.random() > 0.7;
        step.velocity = 0.6 + Math.random() * 0.4;
        step.probability = 0.8 + Math.random() * 0.2;
        step.ratchet = Math.random() > 0.9 ? Math.ceil(Math.random() * 3) + 1 : 1;
      });
    });
  }

  public async exportWAV(): Promise<Blob> {
    // Stop current playback
    const wasPlaying = this.isPlaying;
    if (wasPlaying) this.stop();

    // Set up offline rendering
    const offlineContext = new Tone.OfflineContext(2, 4, 44100); // 4 seconds at 44.1kHz
    
    return new Promise((resolve) => {
      // Render pattern in offline context
      offlineContext.render().then((buffer) => {
        // Convert AudioBuffer to WAV blob
        const wavBlob = this.audioBufferToWav(buffer.get());
        
        // Restart playback if it was playing
        if (wasPlaying) this.play();
        
        resolve(wavBlob);
      });
    });
  }

  private audioBufferToWav(audioBuffer: AudioBuffer): Blob {
    const length = audioBuffer.length;
    const numberOfChannels = audioBuffer.numberOfChannels;
    const sampleRate = audioBuffer.sampleRate;
    const arrayBuffer = new ArrayBuffer(44 + length * numberOfChannels * 2);
    const view = new DataView(arrayBuffer);

    // WAV header
    const writeString = (offset: number, string: string) => {
      for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
      }
    };

    writeString(0, 'RIFF');
    view.setUint32(4, 36 + length * numberOfChannels * 2, true);
    writeString(8, 'WAVE');
    writeString(12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, numberOfChannels, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * numberOfChannels * 2, true);
    view.setUint16(32, numberOfChannels * 2, true);
    view.setUint16(34, 16, true);
    writeString(36, 'data');
    view.setUint32(40, length * numberOfChannels * 2, true);

    // Convert audio data
    let offset = 44;
    for (let i = 0; i < length; i++) {
      for (let channel = 0; channel < numberOfChannels; channel++) {
        const sample = Math.max(-1, Math.min(1, audioBuffer.getChannelData(channel)[i]));
        view.setInt16(offset, sample * 0x7FFF, true);
        offset += 2;
      }
    }

    return new Blob([arrayBuffer], { type: 'audio/wav' });
  }

  public exportMIDI(): string {
    // Simple MIDI export (SMF Type-0)
    const pattern = this.patterns[this.currentPattern];
    const ticksPerBeat = 480;
    const beatsPerBar = 4;
    const stepsPerBeat = 4;
    
    let midiData = '';
    
    // MIDI header
    midiData += 'MThd\x00\x00\x00\x06\x00\x00\x00\x01' + String.fromCharCode((ticksPerBeat >> 8) & 0xFF, ticksPerBeat & 0xFF);
    
    // Track header
    let trackData = '';
    
    // Convert pattern to MIDI events
    const noteMap = { kick: 36, snare: 38, hat: 42 }; // GM drum map
    
    (['kick', 'snare', 'hat'] as DrumVoice[]).forEach(voice => {
      const noteNumber = noteMap[voice];
      pattern[voice].forEach((step, i) => {
        if (step.active) {
          const tickTime = i * (ticksPerBeat / stepsPerBeat);
          const velocity = Math.floor(step.velocity * 127);
          
          // Note on
          trackData += this.createMIDIEvent(tickTime, 0x90, noteNumber, velocity);
          // Note off
          trackData += this.createMIDIEvent(tickTime + 10, 0x80, noteNumber, 0);
        }
      });
    });
    
    // End of track
    trackData += '\x00\xFF\x2F\x00';
    
    // Track with length
    midiData += 'MTrk' + String.fromCharCode(
      (trackData.length >> 24) & 0xFF,
      (trackData.length >> 16) & 0xFF,
      (trackData.length >> 8) & 0xFF,
      trackData.length & 0xFF
    ) + trackData;
    
    return btoa(midiData); // Base64 encoded MIDI
  }

  private createMIDIEvent(time: number, status: number, data1: number, data2: number): string {
    const deltaTime = this.encodeVariableLength(Math.floor(time));
    return deltaTime + String.fromCharCode(status, data1, data2);
  }

  private encodeVariableLength(value: number): string {
    let result = '';
    if (value >= 0x200000) result = String.fromCharCode(((value >> 21) & 0x7F) | 0x80);
    if (value >= 0x4000) result += String.fromCharCode(((value >> 14) & 0x7F) | 0x80);
    if (value >= 0x80) result += String.fromCharCode(((value >> 7) & 0x7F) | 0x80);
    result += String.fromCharCode(value & 0x7F);
    return result;
  }

  public tapTempo(): void {
    // Implementation for tap tempo - would track tap intervals and update tempo
    // This is a simplified version
    const now = Date.now();
    if (!this.lastTapTime) {
      this.lastTapTime = now;
      return;
    }
    
    const interval = now - this.lastTapTime;
    const bpm = Math.round(60000 / interval);
    
    if (bpm >= 60 && bpm <= 200) {
      this.settings.tempo = bpm;
      if (this.isPlaying) {
        Tone.Transport.bpm.rampTo(bpm, 0.1);
      }
    }
    
    this.lastTapTime = now;
  }

  private lastTapTime?: number;

  public dispose(): void {
    this.stop();
    Object.values(this.voices).forEach(voice => voice.dispose());
    this.reverb.dispose();
    this.compressor.dispose();
    this.sidechainCompressor.dispose();
    this.kickBus.dispose();
    this.nonKickBus.dispose();
    this.mainBus.dispose();
  }
}