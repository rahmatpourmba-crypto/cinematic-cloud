import path from 'node:path';
import {Config} from '@remotion/cli/config';

Config.setVideoImageFormat('jpeg');
Config.setOverwriteOutput(true);
Config.setChromiumOpenGlRenderer('swangle');
Config.setChromiumHeadlessMode(true);
// The static server must serve our generated assets from ./public, regardless
// of where the entry point lives.
Config.setPublicDir(path.resolve('public'));