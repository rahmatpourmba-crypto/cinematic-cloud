import React from 'react';
import {
  AbsoluteFill,
  Sequence,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {FilmGrain, Letterbox, LightVault, Vignette} from './effects';
import {ChapterScene, EndCard, TitleScreen} from './scenes';
import {GOLD, GOLD_LIGHT} from './theme';

export type CinematicScene = {
  image: string;
  audio: string;
  title: string;
  caption: string;
  seconds: number;
};

export type CinematicProps = {
  storyTitleFa: string;
  storyTitleEn: string;
  episode: number;
  series: string;
  subscribeText: string;
  scenes: CinematicScene[];
  fps?: number;
};

export const TITLE_SECONDS = 4.5;
export const END_SECONDS = 4;
export const PAUSE_SECONDS = 0.4;

export const totalFrames = (p: CinematicProps): number => {
  const fps = p.fps ?? 30;
  const body = p.scenes.reduce(
    (acc, s) => acc + Math.round((s.seconds + PAUSE_SECONDS) * fps),
    0,
  );
  return Math.round(TITLE_SECONDS * fps) + body + Math.round(END_SECONDS * fps);
};

export const CinematicStory: React.FC<CinematicProps> = (props) => {
  const fps = props.fps ?? 30;
  let acc = Math.round(TITLE_SECONDS * fps);

  const chapters = props.scenes.map((s, i) => {
    const frames = Math.round((s.seconds + PAUSE_SECONDS) * fps);
    const from = acc;
    acc += frames;
    return (
      <Sequence key={i} from={from} durationInFrames={frames}>
        <ChapterScene
          image={s.image}
          audioSrc={s.audio}
          index={i}
          chapterNumber={i + 1}
          title={s.title}
          caption={s.caption}
        />
      </Sequence>
    );
  });

  return (
    <AbsoluteFill style={{backgroundColor: '#000'}}>
      <Sequence from={0} durationInFrames={Math.round(TITLE_SECONDS * fps)}>
        <TitleScreen
          faTitle={props.storyTitleFa}
          enTitle={props.storyTitleEn}
          episode={props.episode}
          series={props.series}
        />
      </Sequence>

      {chapters}

      <Sequence from={acc} durationInFrames={Math.round(END_SECONDS * fps)}>
        <EndCard series={props.series} subscribeText={props.subscribeText} />
      </Sequence>

      <Letterbox />
      <Vignette />
      <LightVault />
      <FilmGrain />
    </AbsoluteFill>
  );
};

// Static 1280x720 YouTube thumbnail (rendered with `remotion still`).
export type ThumbnailProps = {
  image: string;
  faTitle: string;
  enTitle?: string;
  episode?: number;
  series?: string;
};

export const StoryThumbnail: React.FC<ThumbnailProps> = ({
  image,
  faTitle,
  enTitle,
  episode,
  series,
}) => {
  const frame = useCurrentFrame();
  const {height} = useVideoConfig();
  const titleY = height * 0.30;
  return (
    <AbsoluteFill style={{backgroundColor: '#040810'}}>
      <AbsoluteFill style={{overflow: 'hidden'}}>
        {/* background image, static */}
        <img
          src={staticFile(image)}
          draggable={false}
          style={{
            position: 'absolute',
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(1.05) translateX(${Math.sin(frame * 0.1) * 1}%)`,
          }}
        />
      </AbsoluteFill>
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(110deg, rgba(4,8,16,0.15) 0%, rgba(4,8,16,0.0) 45%, rgba(4,8,16,0.0) 60%, rgba(4,8,16,0.9) 100%)',
        }}
      />
      <div
        style={{
          position: 'absolute',
          top: titleY,
          right: '10%',
          left: '42%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'flex-end',
        }}
      >
        {series ? (
          <div
            style={{
              fontFamily: 'Vazirmatn',
              fontWeight: 700,
              fontSize: 26,
              letterSpacing: 5,
              color: GOLD_LIGHT,
              marginBottom: 10,
            }}
          >
            {series}
          </div>
        ) : null}
        <div
          style={{
            fontFamily: 'Vazirmatn',
            fontWeight: 900,
            fontSize: 64,
            lineHeight: 1.35,
            color: '#FFFFFF',
            textAlign: 'right',
            textShadow: '0 6px 30px rgba(0,0,0,0.7)',
          }}
        >
          {faTitle}
        </div>
        {enTitle ? (
          <div
            style={{
              fontFamily: 'Vazirmatn',
              fontWeight: 700,
              fontSize: 22,
              letterSpacing: 4,
              color: '#cfd6e6',
              marginTop: 10,
              textTransform: 'uppercase',
            }}
          >
            {enTitle}
          </div>
        ) : null}
      </div>
      {episode ? (
        <div
          style={{
            position: 'absolute',
            bottom: '8%',
            left: '8%',
            padding: '12px 30px',
            borderRadius: 50,
            border: `3px solid ${GOLD}`,
            color: GOLD,
            fontFamily: 'Vazirmatn',
            fontWeight: 900,
            fontSize: 34,
            letterSpacing: 2,
            background: 'rgba(4,8,16,0.55)',
          }}
        >
          قسمت {episode}
        </div>
      ) : null}
      <FilmGrain opacity={0.03} />
    </AbsoluteFill>
  );
};