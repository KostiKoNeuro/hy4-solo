import json
import sys
import time
from pathlib import Path

import kie

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "tools" / "raw"
MANIFEST = ROOT / "tools" / "generation_log.json"

MODEL_T2I = "gpt-image-2-5-flare-text-to-image"
MODEL_I2I = "gpt-image-2-5-flare-image-to-image"

LOCK = (
    "Using the provided reference image of this exact same character. Keep the character "
    "design 100% identical: the same chubby round dome-shaped lavender-periwinkle "
    "head-mantle, the same big glossy dark-navy oval eyes with two white catchlights each, "
    "the same soft pink oval blush cheeks, the same tiny gentle smile, the same eight short "
    "stubby curly tentacles with coral-pink round suckers underneath, the same tiny "
    "pale-yellow five-pointed star hair clip on the upper-left of the head, the same soft "
    "matte 3D clay vinyl-toy render, the same pastel colors, the same proportions and the "
    "same clean kawaii mascot style. Only change the pose, expression and props as described. "
    "A single character, centered, full body visible with generous empty padding, no text, "
    "no letters, no watermark, no floor, no ground shadow, fully transparent empty background. "
)

ANCHOR = (
    "A single cute chubby baby octopus character, soft 3D clay vinyl toy render, pastel "
    "kawaii mascot style, high quality clean render. Character design: a chubby round "
    "dome-shaped lavender-periwinkle head-mantle, big glossy dark-navy oval eyes with two "
    "white catchlights each, soft pink oval blush cheeks, a tiny gentle smiling mouth, eight "
    "short stubby curly tentacles in lavender with coral-pink round suckers underneath, and "
    "a tiny pale-yellow five-pointed star hair clip on the upper-left of the head. Smooth "
    "matte clay shading, soft studio light, clean soft outlines, subtle ambient occlusion. "
    "Pose: standing upright and relaxed, facing the viewer in a slight 3/4 front view, "
    "tentacles neatly curled at the base, cheerful calm expression, full body visible, "
    "centered with generous empty padding around it. No text, no letters, no watermark, "
    "no floor, no ground shadow, no props. Fully transparent empty background."
)

POSES = {
    "blink": "Exactly the same relaxed standing pose, but with the eyes happily closed as two gentle downward curved arcs, a soft content smile, blushing cheeks, tentacles neatly curled at the base.",
    "walk1": "Walking to the right mid-stride: body tilted slightly forward, the tentacles on the left side stepping forward while the right-side tentacles push off behind, a lively happy open smile, still upright and balanced, cheerful energy.",
    "walk2": "Walking to the right mid-stride, the opposite phase of the step: the tentacles on the right side stepping forward while the left-side tentacles push off behind, body tilted slightly forward, cheerful open smile, same upright balance.",
    "sleep": "Fast asleep, curled up into a soft cozy round ball, eyes closed as peaceful curved arcs, a tiny sleepy smile, all eight tentacles tucked and curled around the body, completely relaxed and cozy, sitting low.",
    "yawn": "Just woken up and stretching: mouth wide open in a big yawn, eyes squeezed half-shut, all eight tentacles stretched up and outward, sleepy but happy, body elongated upward a little.",
    "grab": "Being lifted up into the air: floating, eyes wide open with a surprised sparkle, a small round 'o' shaped mouth, all eight tentacles splayed out in every direction, body slightly stretched, comically startled but delighted, not scared.",
    "toss": "Flying through the air after being tossed: body tilted about 25 degrees diagonally, all eight tentacles streaming behind from the motion, eyes wide with thrilled excitement, a big open grin, dynamic joyful motion, still adorable.",
    "land": "Just landed and squashed flat like a soft pancake: body comically flattened and widened, dazed dizzy eyes, tentacles splayed out flat to the sides, a funny stunned expression, low to the ground.",
    "eat": "Eating happily: holding a small round golden cookie with two front tentacles, cheeks puffed round, eyes closed in delight, a big happy smile, a few tiny crumb specks floating nearby, pure bliss.",
    "react_link": "Excited about a hyperlink: holding up a short glowing cyan chain made of two oval links with two raised tentacles, eyes sparkling wide, an open delighted smile, the other tentacles waving happily, energetic bouncy pose.",
    "react_number": "Puzzled by numbers: head tilted to one side, one tentacle scratching the top of the head, one eye squinted and one eyebrow raised, three tentacles held up as if counting, a curious confused expression, cute and thoughtful.",
    "react_code": "Hacker mode: wearing tiny round dark-rimmed glasses, a confident pleased smug smile, four tentacles busy typing in the air on an imaginary keyboard, looking very clever and proud of itself, a tiny glow of concentration.",
    "react_text": "Overwhelmed by a very long text: peeking out from under a huge rolled parchment scroll draped over the head and down both sides, only the face and two little tentacles visible, eyes wide and slightly dizzy, comically buried under paper.",
}


def load_manifest():
    if MANIFEST.is_file():
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {"tasks": {}, "credits": 0.0, "start_credit": None, "end_credit": None}


def save_manifest(m):
    MANIFEST.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")


def payload(prompt, i2i_urls=None):
    p = {
        "prompt": prompt,
        "aspect_ratio": "1:1",
        "resolution": "1K",
        "background": "transparent",
    }
    if i2i_urls:
        p["input_urls"] = i2i_urls
    return p


def main():
    s = kie.session()
    m = load_manifest()
    if m.get("start_credit") is None:
        m["start_credit"] = kie.get_credit(s)["data"]
    print("start credit:", m["start_credit"])

    RAW.mkdir(parents=True, exist_ok=True)
    only = set(sys.argv[1:]) if len(sys.argv) > 1 else None
    names = [n for n in ["idle", *POSES] if (only is None or n in only)]

    anchor_path = RAW / "idle.png"
    if anchor_path.is_file():
        print("idle: already present")
    else:
        print("idle: creating text-to-image task...")
        tid = kie.create_task(s, MODEL_T2I, payload(ANCHOR))
        m["tasks"]["idle"] = tid
        save_manifest(m)
        data = kie.poll(s, tid)
        urls = kie.result_urls(data)
        if not urls:
            raise RuntimeError("idle: no result urls")
        kie.download(s, urls[0], anchor_path)
        cc = float(data.get("creditsConsumed") or 0)
        m["credits"] += cc
        save_manifest(m)
        print("idle: done, creditsConsumed =", cc, "bytes =", anchor_path.stat().st_size)

    print("resolving public character-reference URL from the anchor result...")
    anchor_data = kie.poll(s, m["tasks"]["idle"])
    anchor_urls = kie.result_urls(anchor_data)
    if not anchor_urls:
        raise RuntimeError("idle: cannot resolve public result URL")
    anchor_url = anchor_urls[0]
    print("character reference ready")

    pending = {}
    for name in names:
        if name == "idle":
            continue
        dest = RAW / (name + ".png")
        if dest.is_file():
            print(name + ": already present")
            continue
        prompt = LOCK + POSES[name]
        tid = kie.create_task(s, MODEL_I2I, payload(prompt, [anchor_url]))
        m["tasks"][name] = tid
        save_manifest(m)
        pending[name] = tid
        print(name + ": task created", tid)
        time.sleep(0.7)

    for name, tid in pending.items():
        try:
            data = kie.poll(s, tid, timeout=420)
            urls = kie.result_urls(data)
            if not urls:
                raise RuntimeError(name + ": no result urls")
            dest = RAW / (name + ".png")
            kie.download(s, urls[0], dest)
            cc = float(data.get("creditsConsumed") or 0)
            m["credits"] += cc
            save_manifest(m)
            print(name + ": done, creditsConsumed =", cc, "bytes =", dest.stat().st_size)
        except Exception as exc:
            print(name + ": FAILED ->", repr(exc), "(re-run to retry)")

    m["end_credit"] = kie.get_credit(s)["data"]
    save_manifest(m)
    print("end credit:", m["end_credit"])
    print("credits reported by tasks:", m["credits"])
    print("credit delta:", round(m["start_credit"] - m["end_credit"], 2))


if __name__ == "__main__":
    main()
