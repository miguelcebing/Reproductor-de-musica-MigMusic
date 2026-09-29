/** Ephemeral notifications (`UX-004`: toasts for feedback and errors). */

import { create } from "zustand";

export type ToastKind = "info" | "success" | "error";

export interface Toast {
  readonly id: number;
  readonly kind: ToastKind;
  readonly text: string;
}

export interface ToastStoreState {
  toasts: readonly Toast[];
  push: (kind: ToastKind, text: string) => number;
  dismiss: (id: number) => void;
  reset: () => void;
}

let nextId = 1;

export const useToastStore = create<ToastStoreState>((set) => ({
  toasts: [],
  push: (kind, text) => {
    const id = nextId++;
    set((state) => ({ toasts: [...state.toasts, { id, kind, text }] }));
    return id;
  },
  dismiss: (id) => set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) })),
  reset: () => set({ toasts: [] }),
}));
