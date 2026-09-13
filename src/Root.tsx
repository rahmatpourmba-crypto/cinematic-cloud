import React from 'react';
import {Composition} from 'remotion';
import {
  CinematicProps,
  CinematicStory,
  StoryThumbnail,
  ThumbnailProps,
  totalFrames,
} from './CinematicStory';

const defaultScenes: CinematicProps['scenes'] = [];

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="CinematicStory"
        component={CinematicStory}
        durationInFrames={totalFrames({
          storyTitleFa: 'قصه سلیمان و طاووس',
          storyTitleEn: 'Solomon and the Hoopoe',
          episode: 1,
          series: 'قصه‌های قرآنی',
          subscribeText: 'لایک و اشتراک یادت نره',
          scenes: [
            {image: '/scenes/placeholder.jpg', audio: '', title: '', caption: '', seconds: 6},
            {image: '/scenes/placeholder.jpg', audio: '', title: '', caption: '', seconds: 6},
            {image: '/scenes/placeholder.jpg', audio: '', title: '', caption: '', seconds: 6},
          ],
        })}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          storyTitleFa: '',
          storyTitleEn: '',
          episode: 1,
          series: '',
          subscribeText: '',
          scenes: defaultScenes,
        }}
        calculateMetadata={async ({props}) => ({
          durationInFrames: totalFrames(props),
        })}
      />

      <Composition
        id="StoryThumbnail"
        component={StoryThumbnail}
        durationInFrames={1}
        fps={30}
        width={1280}
        height={720}
        defaultProps={{
          image: '/scenes/placeholder.jpg',
          faTitle: '',
          enTitle: '',
          episode: 1,
          series: '',
        }}
      />
    </>
  );
};