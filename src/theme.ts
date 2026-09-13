import type React from 'react';

// Cinematic palette + shared style primitives for the whole series.

export const GOLD = '#e8b360';
export const GOLD_LIGHT = '#ffde96';
export const GOLD_PALE = '#f6e3bc';
export const NAVY_TOP = '#081226';
export const NAVY_BOTTOM = '#18305c';
export const WHITE = '#ffffff';
export const INK = '#040810';

export const Fonts = {
  fa: 'Vazirmatn, sans-serif',
  faBlack: 'Vazirmatn, sans-serif',
  serifFa: 'Vazirmatn, sans-serif',
  latin: 'Vazirmatn, "Segoe UI", Arial, sans-serif',
};

export const letterbox = 0.115;

export const EASE = 'cubic-bezier(0.22, 1, 0.36, 1)';

// Uniform fade / rise-in helper used by all text layers.
export const riseIn = (frame: number, start: number, dur = 28): React.CSSProperties => {
  const p = Math.min(Math.max((frame - start) / dur, 0), 1);
  const t = 1 - Math.pow(1 - p, 3);
  return {
    opacity: t,
    transform: `translateY(${(1 - t) * 42}px)`,
  };
};