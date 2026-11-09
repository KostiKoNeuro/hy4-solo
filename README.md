# Tencent Hy4 solo: 5 tests, one prompt each, no fixes

One model, five tests, one shot each. No hints from me: Hy4 writes, runs and checks its own work.
In test 3 it picked which animal it sees itself as, drew itself as an octopus and moved onto my desktop.

**▶ Play in your browser:** https://kostikoneuro.github.io/hy4-solo/
**🎬 Video (Russian):** [YOUTUBE LINK]
**💬 Telegram:** https://t.me/kostik_neuro

> Русский: все тесты, кроме питомца, открываются прямо в браузере по ссылке выше. Питомца Окто можно скачать и запустить на Windows (инструкция ниже). Промпты на русском и английском в папке [`prompts/`](prompts/).

## The tests

| # | Test | Result |
|---|---|---|
| 1 | **SVG animation**: a giraffe trying to squeeze into a tiny phone booth to make a call | [open](1-svg/scene.svg) |
| 2 | **Rube Goldberg machine**: wake a sleeping hamster in the silliest way possible, Matter.js | [play](2-goldberg/) |
| 3 | **Desktop pet**: the model picks its own animal, draws its sprites via kie.ai and lives on my Windows desktop | [download](3-desktop-pet/) |
| 4 | **Mini golf**: we give it our three hand-drawn holes, it invents a better one, draws the blueprint and builds the game | [play](4-minigolf/) |
| 5 | **Hamster habitat**: low-poly 3D colony in Three.js that lives for generations | [play](5-hamsters/) |

Controls: golf: drag back from the ball and release, **O** = blueprint overlay. Hamsters: click a hamster to follow it, speed ×0.5 to ×4 at the bottom.

Tests 1 to 3 are in Russian (the prompts were Russian). From test 4 on, the prompt asked for English text in the result.

## The desktop pet (test 3)

Octo, a purple octopus with a star: «eight tentacles = eight tools and tasks at once». 14 poses drawn with kie.ai (GPT Image 2.5 Flare), 84 credits, about $0.42.

To run it on Windows 10/11: install Python 3, then

```
pip install PySide6
3-desktop-pet\Oktopet\run.bat
```

Right-click the tray icon to feed it, put it to sleep or quit. It walks on the taskbar, you can grab and throw it, it falls asleep when you don't touch anything for a minute, and it reacts to what you copy: a link, a number, code, a long text. No network calls and no API key in the app.
[`tools/`](3-desktop-pet/tools/) are the model's own scripts: sprite generation (`gen_sprites.py`, `kie.py`, the key was read from a local `.env` that is not here), sprite cleanup and the checks it ran on itself.

## Time and cost

Costs at CometAPI prices (80% of Tencent's list price: $0.834 input / $0.042 cached / $2.501 output per 1M tokens). Token counts come from the request logs.

| Test | Harness | Time | Cost |
|---|---|---|---|
| 1 SVG | Claude Code | 14 min | $0.89 |
| 2 Goldberg | OpenCode | 37 min | $0.74 |
| 3 Desktop pet | OpenCode | 66 min * | $0.86 + kie.ai $0.42 |
| 4 Mini golf | OpenCode | 50 min | $0.87 |
| 5 Hamsters | OpenCode | 37 min | $0.82 |
| **Total** | | **3 h 25 min** | **$4.17** (+ $0.42 images) |

\* About 24 minutes of it my harness was stuck: the pet app kept the launch command's output open and the agent waited. I closed the stuck instance twice and the model went on. I did not touch its code or files.

## How it was run, honestly

- **Two harnesses.** Test 1 ran in Claude Code 2.1.272 through a local proxy to CometAPI (CometAPI refused Claude Code's extra headers, the proxy removed them; this is not an official setup). On test 2 the request kept getting cut at about 7.5 minutes while the model was still thinking, and every retry started from zero: 76 minutes, no files. That attempt is not counted. Tests 2 to 5 ran in **OpenCode 1.19**, the same harness as in the Hy4 vs DeepSeek duel, with a headless Playwright browser so the model can check its own work.
- Reasoning `high`. One prompt per test, no fixes, $5 and 3 hours per test (no test hit the limits).
- **Images.** In tests 2 and 3 my OpenCode config did not enable image input, so Hy4 could not see its own screenshots and sprites; it checked them by pixel statistics. The duel config was the same, so in the duel Hy4 most likely did not see images either: that was my mistake, not the model's. From test 4 on image input was on, and the first, 1-minute test 4 attempt without it was restarted from scratch with the same prompt.
- Test 3: kie.ai was the only paid service allowed, with a $1 limit; the key sat in a local `.env` and was not printed or put into the app.

## What I found when I checked

- **Goldberg:** 3 of 3 runs, all 10 stages, the bell rings every time. But at a few stages the collision only triggers a script that sets the next part's speed, and the hamster wakes up on a 0.65 s timer after the bell, not from the ringing. The physics runs one step per frame, so on a high refresh rate monitor the machine is several times faster: 8.7 s by the math, 3.8 s in my browser.
- **Golf:** both routes, the short risky one and the long safe one, can be done in 2 strokes, so the risk does not really pay off.
- **Hamsters:** 5 minutes at ×4, 12 in-game days: 13 births, 13 deaths, 5 generations, once down to 2 hamsters and back. AUTO-FEED is on by default and refills food and water every dawn; turn it off to see hunger.
