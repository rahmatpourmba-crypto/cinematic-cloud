import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {GOLD, GOLD_PALE, letterbox} from './theme';

const BAR_H = `${letterbox * 100}%`;

export const Letterbox: React.FC = () => (
  <>
    <div
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        height: BAR_H,
        background: 'black',
        zIndex: 980,
      }}
    />
    <div
      style={{
        position: 'absolute',
        bottom: 0,
        left: 0,
        right: 0,
        height: BAR_H,
        background: 'black',
        zIndex: 980,
      }}
    />
  </>
);

export const Vignette: React.FC = () => (
  <AbsoluteFill
    style={{
      zIndex: 940,
      pointerEvents: 'none',
      boxShadow: 'inset 0 0 260px 60px rgba(0,0,0,0.82)',
      background:
        'radial-gradient(ellipse at center, transparent 55%, rgba(6,10,20,0.55) 100%)',
    }}
  />
);

// Animated film grain driven by frame number (deterministic, cheap).
const GRAIN = 26;
const seeds: Array<[number, number, number]> = [];
for (let i = 0; i < GRAIN; i++) {
  seeds.push([
    (i * 37) % 100,
    (i * 53 + 11) % 77,
    Math.abs((Math.sin(i * 12.9898) * 43758.5453) % 1) * 40 + 4,
  ]);
}

export const FilmGrain: React.FC<{opacity?: number}> = ({opacity = 0.05}) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{zIndex: 960, pointerEvents: 'none'}}>
      {seeds.map(([x, y, size], i) => {
        const drift = ((frame * 0.6 + i * 13) % 100) * (Math.sin(i) > 0 ? 1 : -1) * 0.02;
        const o = Math.min(1, opacity * (0.5 + 0.5 * Math.abs(Math.sin(frame * 0.5 + i))));
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: `${(x + drift) % 100}%`,
              top: `${(y + Math.abs(drift * 1.4)) % 90}%`,
              width: size,
              height: size,
              borderRadius: '50%',
              background: 'rgba(255,255,255,0.8)',
              opacity: o,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

// Soft gold light leak sweeping across a corner.
export const LightVault: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const p = frame / durationInFrames;
  const x = interpolate(p, [0, 1], [-35, 135]);
  const o = 0.10 + 0.07 * Math.sin(frame * 0.02);
  return (
    <div
      style={{
        position: 'absolute',
        top: '-15%',
        left: `${x}%`,
        width: '45%',
        height: '130%',
        transform: 'rotate(14deg)',
        background:
          'linear-gradient(90deg, transparent, rgba(232,179,96,0.5), transparent)',
        opacity: o,
        zIndex: 950,
        filter: 'blur(70px)',
      }}
    />
  );
};

export const GoldRule: React.FC<{width?: number; delay?: number}> = ({
  width = 90,
  delay = 0,
}) => {
  const frame = useCurrentFrame();
  const scaleX = interpolate(frame, [delay, delay + 18], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return (
    <div
      style={{
        height: 3,
        width,
        transform: `scaleX(${scaleX})`,
        transformOrigin: 'right',
        background: `linear-gradient(90deg, ${GOLD_PALE}, ${GOLD})`,
        boxShadow: `0 0 18px rgba(232,179,96,0.65)`,
      }}
    />
  );
};