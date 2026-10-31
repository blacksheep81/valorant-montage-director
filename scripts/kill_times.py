#!/usr/bin/env python3
"""找 Valorant 录屏里的击杀时刻。

两步：
  sheet   把画面中下方的击杀图标区域按每秒 4 帧拼成带时间码的拼图，人工读出每次图标弹出的大致时刻（±0.25 秒）。
  refine  给出大致时刻，逐帧（60fps）找图标出现的那一帧，再在音轨里找它之前最近的开枪/击杀起音，
          卡点以起音为准。输出 JSON。

只依赖标准库和 PATH（或 --ffmpeg）里的 ffmpeg。击杀图标位置按 16:9 原始 HUD 估计，裁切或竖屏素材需要改 --box。

用法：
  python kill_times.py sheet 录屏.mp4 --out sheet.jpg [--ss 47 --t 40]
  python kill_times.py refine 录屏.mp4 2.2 6.5 7.7 [--out kills.json]
"""
import argparse
import array
import json
import math
import shutil
import subprocess
import sys

BOX = "0.42:0.68:0.16:0.2"  # x:y:w:h，相对画面
SR = 24000


def crop_expr(box):
    x, y, w, h = box.split(":")
    return f"crop=iw*{w}:ih*{h}:iw*{x}:ih*{y}"


def sheet(ff, path, out, ss, t, box):
    dur = t
    if dur is None:
        probe = subprocess.run([ff, "-i", path], stderr=subprocess.PIPE, text=True, errors="replace").stderr
        hms = probe.split("Duration: ")[1].split(",")[0].split(":")
        dur = float(hms[0]) * 3600 + float(hms[1]) * 60 + float(hms[2]) - ss
    rows = max(1, math.ceil(dur * 4 / 17))
    vf = (f"fps=4,{crop_expr(box)},scale=160:-2,"
          "drawtext=text='%{pts\\:flt}':x=2:y=2:fontsize=14:fontcolor=yellow:box=1:boxcolor=black@0.7,"
          f"tile=17x{rows}")
    cmd = [ff, "-v", "error", "-y", "-ss", str(ss), "-i", path]
    if t is not None:
        cmd += ["-t", str(t)]
    subprocess.run(cmd + ["-vf", vf, "-frames:v", "1", out], check=True)
    print(f"{out}：时间码从 {ss} 秒起算，读到的时刻要加回 {ss}")


def visual_time(ff, path, rough, box, fps=60, w=32, h=24):
    a = max(0.0, rough - 0.45)
    raw = subprocess.run([ff, "-v", "error", "-ss", f"{a:.3f}", "-i", path, "-t", "0.75",
                          "-vf", f"fps={fps},{crop_expr(box)},scale={w}:{h},format=gray", "-f", "rawvideo", "-"],
                         stdout=subprocess.PIPE, check=True).stdout
    n = w * h
    fr = [raw[i:i + n] for i in range(0, len(raw) - n + 1, n)]
    diffs = [sum(abs(x - y) for x, y in zip(fr[i], fr[i - 1])) / n for i in range(1, len(fr))]
    if not diffs:
        return rough
    peak = max(diffs)
    i = next(j for j, d in enumerate(diffs) if d >= 0.5 * peak)
    return a + (i + 1) / fps


def audio_time(ff, path, t):
    a = max(0.0, t - 0.4)
    raw = subprocess.run([ff, "-v", "error", "-ss", f"{a:.3f}", "-i", path, "-t", "0.5", "-vn", "-ac", "1",
                          "-ar", str(SR), "-f", "s16le", "-"], stdout=subprocess.PIPE).stdout
    x = array.array("h")
    x.frombytes(raw[: len(raw) // 2 * 2])
    hop = SR // 500  # 2ms
    n = len(x) // hop
    if n < 10:
        return None
    e = [math.log(1e-6 + sum(v * v for v in x[i * hop:(i + 1) * hop]) / hop) for i in range(n)]
    rise = [0.0] * 4 + [max(0.0, e[i] - e[i - 4]) for i in range(4, n)]
    lo, hi = max(4, int((t - 0.2 - a) * 500)), min(n - 1, int((t + 0.05 - a) * 500))
    if hi <= lo:
        return None
    j = max(range(lo, hi), key=lambda i: rise[i])
    return a + j / 500


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["sheet", "refine"])
    ap.add_argument("video")
    ap.add_argument("times", nargs="*", type=float, help="refine：sheet 上读到的大致击杀时刻（秒）")
    ap.add_argument("--ffmpeg", default=shutil.which("ffmpeg") or "ffmpeg")
    ap.add_argument("--box", default=BOX, help="击杀图标区域 x:y:w:h，相对画面，默认 16:9 原始 HUD")
    ap.add_argument("--ss", type=float, default=0.0)
    ap.add_argument("--t", type=float)
    ap.add_argument("--out")
    args = ap.parse_args()
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    if args.cmd == "sheet":
        sheet(args.ffmpeg, args.video, args.out or "kill_sheet.jpg", args.ss, args.t, args.box)
        return
    res = []
    for r in args.times:
        v = visual_time(args.ffmpeg, args.video, r, args.box)
        au = audio_time(args.ffmpeg, args.video, v)
        res.append({"rough": r, "icon": round(v, 3), "sound": round(au, 3) if au is not None else None})
    text = json.dumps(res, ensure_ascii=False, indent=1)
    if args.out:
        open(args.out, "w", encoding="utf-8").write(text)
    print(text)


if __name__ == "__main__":
    main()
