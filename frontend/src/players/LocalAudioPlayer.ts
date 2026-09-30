/** HTML5 audio player implementation for local files (`LOCAL-001`). */

import type { AudioPlayer, PlayerEventType, PlayerEventListener } from "./AudioPlayer";
import { getObjectUrlForTrack } from "../services/localFileUrls";

export class LocalAudioPlayer implements AudioPlayer {
  private readonly audio: HTMLAudioElement;
  private readonly listeners: Map<PlayerEventType, Set<PlayerEventListener>> = new Map();
  private _source = "";

  constructor() {
    this.audio = new Audio();
    this.audio.preload = "metadata";
    this.audio.crossOrigin = "anonymous";

    this.audio.addEventListener("play", () => this.emit("play"));
    this.audio.addEventListener("pause", () => this.emit("pause"));
    this.audio.addEventListener("ended", () => this.emit("ended"));
    this.audio.addEventListener("timeupdate", () => this.emit("timeupdate", { currentTime: this.audio.currentTime }));
    this.audio.addEventListener("error", () => this.emit("error", { error: this.audio.error }));
    this.audio.addEventListener("loadedmetadata", () => this.emit("loadedmetadata"));
  }

  get source(): string {
    return this._source;
  }

  get isPlaying(): boolean {
    return !this.audio.paused;
  }

  get currentTime(): number {
    return this.audio.currentTime;
  }

  get duration(): number {
    return this.audio.duration ?? 0;
  }

  get volume(): number {
    return this.audio.volume;
  }

  get muted(): boolean {
    return this.audio.muted;
  }

  async load(source: string, options?: { startTime?: number }): Promise<void> {
    this._source = source;
    const objectUrl = await getObjectUrlForTrack(source);
    if (!objectUrl) {
      throw new Error(`No object URL found for local track ${source}`);
    }
    this.audio.src = objectUrl;
    await new Promise<void>((resolve, reject) => {
      const onLoaded = () => {
        cleanup();
        resolve();
      };
      const onError = () => {
        cleanup();
        reject(new Error(`Failed to load ${source}`));
      };
      const cleanup = () => {
        this.audio.removeEventListener("canplaythrough", onLoaded);
        this.audio.removeEventListener("error", onError);
      };
      this.audio.addEventListener("canplaythrough", onLoaded, { once: true });
      this.audio.addEventListener("error", onError, { once: true });
      this.audio.load();
    });
    if (options?.startTime !== undefined) {
      this.audio.currentTime = options.startTime;
    }
  }

  async play(): Promise<void> {
    await this.audio.play();
  }

  pause(): void {
    this.audio.pause();
  }

  async seek(time: number): Promise<void> {
    this.audio.currentTime = Math.min(Math.max(0, time), this.duration);
  }

  setVolume(volume: number): void {
    this.audio.volume = Math.min(1, Math.max(0, volume));
  }

  setMuted(muted: boolean): void {
    this.audio.muted = muted;
  }

  destroy(): void {
    this.audio.pause();
    this.audio.src = "";
    this.audio.removeAttribute("src");
    this.listeners.clear();
  }

  on(event: PlayerEventType, listener: PlayerEventListener): () => void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(listener);
    return () => this.listeners.get(event)?.delete(listener);
  }

  private emit(type: PlayerEventType, payload?: unknown): void {
    this.listeners.get(type)?.forEach((listener) => listener({ type, payload }));
  }
}