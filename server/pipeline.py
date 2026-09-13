"""Full render pipeline: images -> narration -> Remotion render -> still ->
optional GCS upload -> optional YouTube upload."""
import argparse
import sys
import time
from pathlib import Path

from . import config, renderer, youtube_up
from .assetgen import generate_image
from .gcs import upload_file
from .tts import synthesize
from .utils import ensure_utf8, ffprobe_duration, get_story, load_app


def _asset_name(story_id: str, episode: int, idx: int) -> str:
    return f"e{episode}_{story_id}_c{idx}"


def prepare_scene_assets(app, story, episode, force=False):
    """Generate images + narration and return scene dicts for Remotion."""
    scenes = []
    for idx, ch in enumerate(story["chapters"]):
        name = _asset_name(story["id"], episode, idx)
        img = config.SCENES_DIR / f"{name}.jpg"
        aud = config.AUDIO_DIR / f"{name}.mp3"
        seed = 1000 + episode * 100 + idx

        prompt = ch.get("prompt") or story.get("prompt", "")
        generate_image(prompt, img, seed, force=force)

        text = ch.get("text", "")
        synthesize(text, aud, force=force)
        dur = ffprobe_duration(aud)

        scenes.append({
            "image": f"/scenes/{name}.jpg",
            "audio": f"/audio/{name}.mp3",
            "title": ch.get("title", f"فصل {idx + 1}"),
            "caption": text,
            "seconds": dur + 0.6,
        })
        print(f"  scene {idx + 1}/{len(story['chapters'])}: {dur:.1f}s", flush=True)
    return scenes


def build_props(app, story, episode, scenes):
    return {
        "storyTitleFa": story["title_fa"],
        "storyTitleEn": story["title_en"],
        "episode": episode,
        "series": app.get("series", "قصه‌های قرآنی"),
        "subscribeText": app.get("subscribe_text", "لایک و اشتراک یادت نره"),
        "scenes": scenes,
        "fps": config.FPS,
    }


def build_still_props(app, story, episode, scenes):
    first = scenes[0]
    return {
        "image": first["image"],
        "faTitle": story["title_fa"],
        "enTitle": story["title_en"],
        "episode": episode,
        "series": app.get("series", "قصه‌های قرآنی"),
    }


def run_story(app, story, episode, upload_yt=False, force=False, out_dir=None):
    out_dir = Path(out_dir) if out_dir else config.OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    name = f"e{episode}_{story['id']}"
    video_path = out_dir / f"{name}_cinematic.mp4"
    thumb_path = out_dir / f"{name}_thumb.png"

    print(f"\n=== {story['title_fa']} (episode {episode}) ===", flush=True)
    if video_path.exists() and not force:
        print(f"  skip: {video_path.name} already exists", flush=True)
        return _result(story, episode, video_path, thumb_path, None)

    scenes = prepare_scene_assets(app, story, episode, force=force)

    props = build_props(app, story, episode, scenes)
    renderer.render_video(props, video_path, fps=config.FPS)

    thumb_props = build_still_props(app, story, episode, scenes)
    renderer.render_still(thumb_props, thumb_path)

    video_url = upload_file(video_path, f"videos/{name}_cinematic.mp4")
    thumb_url = upload_file(thumb_path, f"videos/{name}_thumb.png")

    yt_id = None
    if upload_yt:
        yt_id = _upload_yt(app, story, episode, video_path, thumb_path)

    return _result(story, episode, video_path, thumb_path, yt_id, video_url, thumb_url)


def _result(story, episode, video, thumb, yt_id, video_url="", thumb_url=""):
    return {
        "story_id": story["id"],
        "title_fa": story["title_fa"],
        "episode": episode,
        "video": str(video),
        "thumbnail": str(thumb),
        "video_url": video_url,
        "thumbnail_url": thumb_url,
        "youtube_id": yt_id,
        "youtube_url": f"https://youtu.be/{yt_id}" if yt_id else None,
    }


def _upload_yt(app, story, episode, video_path, thumb_path):
    yt = youtube_up.build_service()
    title = f"{story['title_en']} | Episode {episode}"
    desc = (
        f"{story['description']}\n\n"
        f"\u062f\u0627\u0633\u062a\u0627\u0646: {story['title_fa']}\n"
        f"\u062a\u06af\u200c\u0647\u0627: {', '.join(story.get('tags', []))}\n\n"
        f"\u0633\u0631\u06cc \u0627\u0644: {app.get('series', '')} | {app.get('series_en', '')}\n"
        f"\u062a\u0627\u0631\u06cc\u062e: {time.strftime('%Y-%m-%d')}\n"
        "\u0627\u06af\u0631 \u0627\u0632 \u0627\u06cc\u0646 \u0648\u06cc\u062f\u06cc\u0648 \u062e\u0634\u062a\u0627\u0646 \u0622\u0645\u062f "
        "\u0644\u0627\u06cc\u06a9 \u0648 \u0627\u0634\u062a\u0631\u0627\u06a9 \u06a9\u0646\u06cc\u062f."
    )
    return youtube_up.upload_video(
        yt, video_path, thumb_path, title, desc,
        tags=story.get("tags", []), privacy=config.YT_PRIVACY,
        category_id=config.YT_CATEGORY,
    )


def main():
    ensure_utf8()
    parser = argparse.ArgumentParser(description="Cinematic story video pipeline")
    parser.add_argument("--story", default=None, help="story id (default: all)")
    parser.add_argument("--episode", type=int, default=1)
    parser.add_argument("--upload", action="store_true", help="upload to YouTube")
    parser.add_argument("--force", action="store_true", help="regenerate assets")
    parser.add_argument("--out", default=None, help="output directory")
    parser.add_argument("--list", action="store_true", help="list story ids")
    args = parser.parse_args()

    app = load_app()
    if args.list:
        for s in app["stories"]:
            print(f"  - {s['id']}: {s['title_fa']}")
        return

    if args.story:
        story = get_story(app, args.story)
        if not story:
            print(f"error: unknown story '{args.story}'", file=sys.stderr)
            sys.exit(1)
        stories = [story]
    else:
        stories = app["stories"]

    for s in stories:
        res = run_story(app, s, args.episode, upload_yt=args.upload,
                        force=args.force, out_dir=args.out)
        print(json_dumps(res))


def json_dumps(res):
    import json

    return json.dumps(res, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()