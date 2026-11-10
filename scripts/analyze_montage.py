#!/usr/bin/env python3
"""测量一条 montage 的剪辑节奏、闪白、色彩和音量轮廓。

只依赖标准库和 PATH（或 --ffmpeg）里的 ffmpeg。输出 JSON 摘要，供写参考记录或验收成片使用。
检测是近似值：硬切与闪白可靠，叠化、慢推和画中画切换会漏检；音乐起音只做粗略对齐参考。

用法：
  python analyze_montage.py 参考或成片.mp4 [--fps 15] [--ffmpeg 路径] [--out 结果.json]
"""
import argparse
import array
import json
import math
import shutil
from statistics import median
import subprocess
import sys

W, H = 48, 27
N_PIX = W * H
HOP = 0.02  # 音频帧长，秒
SR = 22050


def run_pipe(cmd):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False).stdout


def video_frames(ffmpeg, path, fps):
    raw = run_pipe([ffmpeg, "-v", "error", "-i", path, "-vf", f"fps={fps},scale={W}:{H}",
                    "-f", "rawvideo", "-pix_fmt", "rgb24", "-"])
    size = N_PIX * 3
    rows, prev = [], None
    for k in range(len(raw) // size):
        fr = raw[k * size:(k + 1) * size]
        r = g = b = lum = sat = diff = 0.0
        cur = [0.0] * N_PIX
        for j in range(N_PIX):
            R, G, B = fr[3 * j], fr[3 * j + 1], fr[3 * j + 2]
            r += R; g += G; b += B
            l = 0.299 * R + 0.587 * G + 0.114 * B
            cur[j] = l
            lum += l
            mx, mn = max(R, G, B), min(R, G, B)
            sat += (mx - mn) / mx if mx else 0
            if prev is not None:
                diff += abs(l - prev[j])
        rows.append((k / fps, lum / N_PIX, r / N_PIX, g / N_PIX, b / N_PIX, sat / N_PIX,
                     diff / N_PIX if prev is not None else 0.0))
        prev = cur
    return rows


def audio_profile(ffmpeg, path):
    raw = run_pipe([ffmpeg, "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(SR),
                    "-f", "s16le", "-"])
    if not raw:
        return None
    pcm = array.array("h")
    pcm.frombytes(raw[: len(raw) // 2 * 2])
    hop = int(SR * HOP)
    n = len(pcm) // hop
    rms, hf = [], []
    for i in range(n):
        seg = pcm[i * hop:(i + 1) * hop]
        s = d = 0.0
        p = seg[0]
        for x in seg:
            s += x * x
            d += (x - p) * (x - p)
            p = x
        rms.append(math.sqrt(s / hop) / 32768)
        hf.append(math.sqrt(d / hop) / 32768)
    flux = [0.0] + [max(0, rms[i] - rms[i - 1]) + 0.5 * max(0, hf[i] - hf[i - 1]) for i in range(1, n)]
    onsets = []
    for i in range(3, n - 3):
        lo, hi = max(0, i - 50), min(n, i + 51)
        mean = sum(flux[lo:hi]) / (hi - lo)
        if flux[i] > mean * 4 and flux[i] >= flux[i - 1] and flux[i] >= flux[i + 1] and flux[i] > 0.01:
            onsets.append(round(i * HOP, 2))
    intervals = [b - a for a, b in zip(onsets, onsets[1:])]
    bpm = None
    if len(intervals) >= 3:
        period = median(intervals)
        regular = sum(abs(gap - period) <= period * 0.12 for gap in intervals)
        if 0.34 <= period <= 1.0 and regular >= 0.75 * len(intervals):
            bpm = round(60 / period, 1)
    step = int(2 / HOP)
    loud2s = [round(1000 * sum(rms[i:i + step]) / max(1, len(rms[i:i + step]))) for i in range(0, n, step)]
    return {"bpm_rough": bpm,
            "onsets": onsets, "loudness_per_2s": loud2s}


def summarize(rows, audio):
    dur = rows[-1][0] if rows else 0
    cuts, flashes = [], []
    for i in range(1, len(rows) - 1):
        d = rows[i][6]
        if d > 28 and d > rows[i - 1][6] * 1.8 and d >= rows[i + 1][6]:
            cuts.append(round(rows[i][0], 2))
        if rows[i][1] - rows[i - 1][1] > 45:
            flashes.append(round(rows[i][0], 2))
    bounds = [0.0] + cuts + [dur]
    shots = [(start, end - start) for start, end in zip(bounds, bounds[1:])]
    srt = sorted(length for _, length in shots)
    pct = lambda q: round(srt[min(len(srt) - 1, int(len(srt) * q))], 2) if srt else None
    long_shots = [[round(start, 1), round(length, 1)] for start, length in shots if length > 4]
    seg_len = 15 if dur > 90 else 5
    segments = []
    t = 0.0
    while t < dur:
        w = [r for r in rows if t <= r[0] < t + seg_len]
        if w:
            m = lambda k: round(sum(r[k] for r in w) / len(w))
            segments.append({"start": t, "luma": m(1), "rgb": [m(2), m(3), m(4)],
                             "saturation": round(sum(r[5] for r in w) / len(w), 2),
                             "cuts": sum(1 for c in cuts if t <= c < t + seg_len),
                             "flashes": sum(1 for f in flashes if t <= f < t + seg_len)})
        t += seg_len
    out = {"duration": round(dur, 1), "cuts": len(cuts), "cuts_per_min": round(len(cuts) / dur * 60, 1) if dur else 0,
           "shot_len_p10_p50_p90": [pct(0.1), pct(0.5), pct(0.9)], "long_shots_over_4s": long_shots,
           "flash_times": flashes, "cut_times": cuts, "segments": segments}
    if audio:
        on = audio["onsets"]
        near = lambda x: any(abs(x - o) <= 0.07 for o in on)
        grid = [1 + 0.37 * k for k in range(int((dur - 1) / 0.37))]
        out["audio"] = {"bpm_rough": audio["bpm_rough"], "loudness_per_2s": audio["loudness_per_2s"],
                        "cut_on_onset_rate": round(sum(map(near, cuts)) / len(cuts), 2) if cuts else None,
                        "random_baseline_rate": round(sum(map(near, grid)) / len(grid), 2) if grid else None}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--fps", type=float, default=15)
    ap.add_argument("--ffmpeg", default=shutil.which("ffmpeg"))
    ap.add_argument("--out")
    a = ap.parse_args()
    if not a.ffmpeg:
        sys.exit("找不到 ffmpeg：请安装或用 --ffmpeg 指定路径")
    rows = video_frames(a.ffmpeg, a.video, a.fps)
    if not rows:
        sys.exit("没有读到视频帧，检查文件路径与格式")
    result = summarize(rows, audio_profile(a.ffmpeg, a.video))
    text = json.dumps(result, ensure_ascii=False, indent=1)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text)
    print(text)


if __name__ == "__main__":
    main()
