import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Img,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {GOLD, GOLD_LIGHT, GOLD_PALE, NAVY_BOTTOM, NAVY_TOP} from './theme';
import {GoldRule} from './effects';
import {riseIn} from './theme';

// Procedural luxury navy/gold backdrop used by title + end cards.
export const NavyBackground: React.FC = () => {
  return (
    <AbsoluteFill
      style={{
        background: `linear-gradient(160deg, ${NAVY_TOP} 0%, #0e1c3a 45%, ${NAVY_BOTTOM} 100%)`,
      }}
    >
      <AbsoluteFill
        style={{
          background:
            'radial-gradient(circle 480px at 50% 34%, rgba(232,179,96,0.16), transparent 70%)',
        }}
      />
      <GoldHalo />
    </AbsoluteFill>
  );
};

export const GoldHalo: React.FC = () => {
  const frame = useCurrentFrame();
  const {width, height} = useVideoConfig();
  const cx = width / 2;
  const cy = height * 0.34;
  const pulse = 1 + 0.04 * Math.sin(frame * 0.05);
  const r = 150 * pulse;
  return (
    <>
      <div
        style={{
          position: 'absolute',
          left: cx - r,
          top: cy - r,
          width: r * 2,
          height: r * 2,
          borderRadius: '50%',
          border: `3px solid ${GOLD}`,
          boxShadow: `0 0 60px 10px rgba(232,179,96,0.35)`,
        }}
      />
      <div
        style={{
          position: 'absolute',
          left: cx - r * 0.46,
          top: cy - r * 0.2,
          width: r * 0.92,
          height: r * 0.42,
          borderRadius: '50%',
          background: 'rgba(8,18,38,0.9)',
          boxShadow: 'inset 0 0 30px rgba(232,179,96,0.25)',
        }}
      />
    </>
  );
};

type KenBurnsProps = {
  src: string;
  index: number;
  zoom?: number;
};

// Cinematic zoom/pan on a generated still.
export const KenBurns: React.FC<KenBurnsProps> = ({src, index, zoom = 0.16}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const p = frame / Math.max(durationInFrames - 1, 1);
  const scale = 1 + zoom * p;
  const maxShift = 5;
  const pan =
    index % 2 === 0
      ? interpolate(p, [0, 1], [0, -maxShift])
      : interpolate(p, [0, 1], [maxShift, 0]);
  return (
    <AbsoluteFill style={{overflow: 'hidden', background: '#05070c'}}>
      <Img
        src={staticFile(src)}
        style={{
          position: 'absolute',
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          transform: `scale(${scale}) translateX(${pan}%)`,
          filter: 'saturate(1.16) contrast(1.06)',
        }}
      />
    </AbsoluteFill>
  );
};

type TitleScreenProps = {
  faTitle: string;
  enTitle: string;
  episode: number;
  series: string;
};

export const TitleScreen: React.FC<TitleScreenProps> = ({
  faTitle,
  enTitle,
  episode,
  series,
}) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill>
      <NavyBackground />
      <AbsoluteFill
        style={{
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '0 10%',
          zIndex: 5,
        }}
      >
        <div
          style={{
            ...riseIn(frame, 8),
            fontFamily: 'Vazirmatn',
            fontWeight: 700,
            fontSize: 24,
            letterSpacing: 8,
            color: GOLD_PALE,
            marginBottom: 60,
          }}
        >
          {series}
        </div>
        <div
          style={{
            ...riseIn(frame, 22, 26),
            fontFamily: 'Vazirmatn',
            fontWeight: 900,
            fontSize: 82,
            lineHeight: 1.35,
            color: '#FFFFFF',
            textAlign: 'center',
            textShadow: '0 6px 40px rgba(0,0,0,0.55)',
          }}
        >
          {faTitle}
        </div>
        <div
          style={{
            opacity: interpolate(frame, [40, 56], [0, 1], {extrapolateRight: 'clamp'}),
            margin: '26px 0',
          }}
        >
          <GoldRule width={110} delay={40} />
        </div>
        <div
          style={{
            ...riseIn(frame, 46, 22),
            fontFamily: 'Vazirmatn',
            fontWeight: 700,
            fontSize: 26,
            letterSpacing: 6,
            color: '#bfc8dd',
            textTransform: 'uppercase',
            textAlign: 'center',
          }}
        >
          {enTitle}
        </div>
        <div
          style={{
            ...riseIn(frame, 58, 20),
            marginTop: 72,
            padding: '14px 34px',
            borderRadius: 60,
            border: `2px solid ${GOLD_LIGHT}`,
            color: GOLD_LIGHT,
            fontFamily: 'Vazirmatn',
            fontWeight: 700,
            fontSize: 30,
            letterSpacing: 2,
          }}
        >
          قسمت {episode}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

type ChapterSceneProps = {
  image: string;
  index: number;
  chapterNumber: number;
  title: string;
  caption: string;
  audioSrc: string;
};

export const ChapterScene: React.FC<ChapterSceneProps> = ({
  image,
  index,
  chapterNumber,
  title,
  caption,
  audioSrc,
}) => {
  const frame = useCurrentFrame();
  const {width} = useVideoConfig();
  const progress = interpolate(frame, [0, 60], [0, 1], {
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill>
      <KenBurns src={image} index={index} />

      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(4,8,16,0.45) 0%, rgba(4,8,16,0) 32%, rgba(4,8,16,0) 55%, rgba(4,8,16,0.82) 100%)',
          zIndex: 2,
        }}
      />

      <Audio src={staticFile(audioSrc)} />

      <AbsoluteFill
        style={{
          zIndex: 3,
          flexDirection: 'column',
          justifyContent: 'space-between',
          padding: '8% 7%',
        }}
      >
        <div
          style={{
            ...riseIn(frame, 3, 18),
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'flex-start',
          }}
        >
          <div
            style={{
              fontFamily: 'Vazirmatn',
              fontWeight: 700,
              fontSize: 20,
              letterSpacing: 6,
              color: GOLD_LIGHT,
            }}
          >
            {`فصل ${chapterNumber}`}
          </div>
          <div style={{margin: '12px 0'}}>
            <GoldRule width={70} delay={8} />
          </div>
          <div
            style={{
              fontFamily: 'Vazirmatn',
              fontWeight: 900,
              fontSize: 44,
              color: '#FFFFFF',
              textShadow: '0 4px 30px rgba(0,0,0,0.6)',
            }}
          >
            {title}
          </div>
        </div>

        <div style={{...riseIn(frame, 14, 24), maxWidth: '90%'}}>
          <div
            style={{
              fontFamily: 'Vazirmatn',
              fontWeight: 700,
              fontSize: 30,
              lineHeight: 2,
              color: '#F2F5FB',
              textAlign: 'right',
              direction: 'rtl',
              textShadow: '0 3px 24px rgba(0,0,0,0.75)',
            }}
          >
            {caption}
          </div>
          <div style={{marginTop: 18, display: 'flex', justifyContent: 'flex-end'}}>
            <div
              style={{
                width: `${Math.max(20, (progress * width) / 10)}px`,
                height: 3,
                background: GOLD,
                boxShadow: `0 0 16px ${GOLD_LIGHT}`,
              }}
            />
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

type EndCardProps = {
  series: string;
  subscribeText: string;
};

export const EndCard: React.FC<EndCardProps> = ({series, subscribeText}) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill>
      <NavyBackground />
      <AbsoluteFill
        style={{
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 5,
          textAlign: 'center',
          padding: '0 8%',
        }}
      >
        <div
          style={{
            ...riseIn(frame, 4, 20),
            fontFamily: 'Vazirmatn',
            fontWeight: 900,
            fontSize: 62,
            lineHeight: 1.55,
            color: '#FFFFFF',
          }}
        >
          {subscribeText}
        </div>
        <div style={{margin: '30px 0'}}>
          <GoldRule width={120} delay={26} />
        </div>
        <div style={{display: 'flex', gap: 24, marginTop: 26}}>
          <div
            style={{
              padding: '18px 44px',
              borderRadius: 60,
              background: 'linear-gradient(135deg, #c8943f, #e8b360)',
              color: '#0a1222',
              fontFamily: 'Vazirmatn',
              fontWeight: 900,
              fontSize: 30,
              boxShadow: '0 10px 40px rgba(232,179,96,0.4)',
              ...riseIn(frame, 34, 18),
            }}
          >
            اشتراک
          </div>
          <div
            style={{
              padding: '18px 44px',
              borderRadius: 60,
              border: `2px solid ${GOLD_LIGHT}`,
              color: GOLD_LIGHT,
              fontFamily: 'Vazirmatn',
              fontWeight: 700,
              fontSize: 30,
              ...riseIn(frame, 42, 18),
            }}
          >
            لایک
          </div>
        </div>
        <div
          style={{
            ...riseIn(frame, 54, 16),
            position: 'absolute',
            bottom: '10%',
            fontFamily: 'Vazirmatn',
            fontWeight: 700,
            fontSize: 24,
            letterSpacing: 4,
            color: '#9db1d6',
          }}
        >
          {series}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};