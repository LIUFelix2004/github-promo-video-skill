#!/usr/bin/env python3
"""Render a <=28s GitHub profile promo video in the unified GitHub-white card style.

Pipeline (all text rendered locally with PIL -> zero typos, zero foreign logos):
  1. Cover: real captured profile-page frame, perspective-animated from a flat
     cross-section far view to an upright tilted close view, soft shadow on a
     light gradient ground.
  2. Three repo cards: count-up star/fork numbers, README summary rows stagger
     in, tech chips fade in.
  3. Finale: paper strips slide in + big circular avatar with a pink ring.
Segments are stitched with ffmpeg xfade; optional user-supplied BGM.

Usage: python3 render_promo.py --config config.json --out out.mp4 [--workdir DIR]
Requires: Pillow, numpy, ffmpeg, a CJK font (Noto Sans CJK preferred).
"""
import argparse, json, os, subprocess, sys, tempfile

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

FPS = 24
FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.otf",
]
FONT_BOLD_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.otf",
]


def pick_font(cands):
    for c in cands:
        if os.path.exists(c):
            return c
    raise SystemExit("No CJK font found; install Noto Sans CJK (fonts-noto-cjk).")


REG = pick_font(FONT_CANDIDATES)
BOLD = pick_font(FONT_BOLD_CANDIDATES)


def F(sz, bold=False):
    return ImageFont.truetype(BOLD if bold else REG, int(sz))


def coeffs(out_pts, in_pts):
    m = []
    for p1, p2 in zip(out_pts, in_pts):
        m.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0] * p1[0], -p2[0] * p1[1]])
        m.append([0, 0, 0, p1[0], p1[1], 1, -p2[1] * p1[0], -p2[1] * p1[1]])
    A = np.matrix(m, dtype=float)
    B = np.array(in_pts).reshape(8)
    return np.array(np.linalg.solve(A, B)).reshape(8)


def ease(t):
    return t * t * (3 - 2 * t)


def easeout(t):
    return 1 - (1 - t) ** 3


def render_cover(page_path, n_frames, outdir):
    """Flat cross-section far view -> upright tilted close view, with shadow."""
    S = 0.75
    W, H = int(2600 * S), int(1463 * S)
    page = Image.open(page_path).convert("RGB").resize(
        (int(1500 * S), int(1250 * S)), Image.LANCZOS)
    pw, ph = page.size
    SRC = [(0, 0), (pw, 0), (pw, ph), (0, ph)]
    START = [(x * S, y * S) for x, y in [(880, 520), (1750, 480), (1980, 880), (620, 880)]]
    END = [(x * S, y * S) for x, y in [(430, 180), (2230, 330), (2230, 1180), (430, 1330)]]
    mask_src = Image.new("L", (pw, ph), 255)
    grad = np.zeros((H, W, 3), dtype=np.uint8)
    for yy in range(H):
        grad[yy, :, :] = [int(233 + (247 - 233) * yy / H),
                          int(238 + (249 - 238) * yy / H),
                          int(242 + (250 - 242) * yy / H)]
    os.makedirs(outdir, exist_ok=True)
    for i in range(n_frames):
        u = ease(i / max(1, n_frames - 1))
        quad = [(s[0] + (e[0] - s[0]) * u, s[1] + (e[1] - s[1]) * u)
                for s, e in zip(START, END)]
        c = coeffs(quad, SRC)
        bg = Image.fromarray(grad.copy())
        sil = mask_src.transform((W, H), Image.PERSPECTIVE, c, Image.BICUBIC)
        sh = Image.new("L", (W, H), 0)
        sh.paste(120, (int(10 * S), int(34 * S)), sil)
        sh = sh.filter(ImageFilter.GaussianBlur(18))
        bg.paste((120, 128, 140), (0, 0), sh.point(lambda v: v // 2))
        bg.paste(page.transform((W, H), Image.PERSPECTIVE, c, Image.BICUBIC), (0, 0), sil)
        bg.save(os.path.join(outdir, f"c{i:03d}.png"))


CS = 0.6
CW, CH = int(2600 * CS), int(1463 * CS)


def X(v):
    return v * CS


def draw_card(cfg, avatar, i):
    img = Image.new("RGB", (CW, CH), (246, 248, 250))
    d = ImageDraw.Draw(img, "RGBA")
    d.rounded_rectangle([X(240), X(150), X(2360), X(1360)], radius=int(X(36)),
                        fill=(255, 255, 255), outline=(209, 217, 224), width=3)
    pre = cfg.get("pre", "")
    d.text((X(320), X(215)), pre, font=F(X(56)), fill=(89, 99, 110))
    w1 = d.textlength(pre, font=F(X(56)))
    d.text((X(320) + w1 + 8, X(205)), cfg["name"], font=F(X(70), True), fill=(31, 35, 40))
    avs = int(X(170))
    av = avatar.resize((avs, avs))
    msk = Image.new("L", (avs, avs), 0)
    ImageDraw.Draw(msk).ellipse([0, 0, avs, avs], fill=255)
    img.paste(av, (int(X(2130)), int(X(205))), msk)
    d = ImageDraw.Draw(img, "RGBA")
    d.text((X(320), X(325)), cfg["sub"], font=F(X(58)), fill=(31, 35, 40))
    d.line([X(320), X(445), X(2280), X(445)], fill=(209, 217, 224), width=3)
    ct = easeout(max(0, min(1, (i - 8) / 50)))
    n1 = int(cfg["n1"] * ct)
    n2 = int(cfg["n2"] * ct)
    d.text((X(320), X(505)), str(n1), font=F(X(185), True), fill=(200, 30, 45))
    w2 = d.textlength(str(n1), font=F(X(185), True))
    d.text((X(320) + w2 + 25, X(610)), cfg["l1"], font=F(X(80)), fill=(89, 99, 110))
    d.text((X(1420), X(505)), str(n2), font=F(X(185), True), fill=(9, 105, 218))
    w3 = d.textlength(str(n2), font=F(X(185), True))
    d.text((X(1420) + w3 + 25, X(610)), cfg["l2"], font=F(X(80)), fill=(89, 99, 110))
    for k, row in enumerate(cfg["rows"]):
        rt = max(0, min(1, (i - (52 + 14 * k)) / 14))
        if rt > 0:
            off = int((1 - easeout(rt)) * X(60))
            al = int(255 * rt)
            yy = X(795 + 104 * k)
            d.ellipse([X(330) + off, yy + X(16), X(362) + off, yy + X(48)],
                      fill=(26, 127, 55, al))
            d.text((X(395) + off, yy), row, font=F(X(56)), fill=(31, 35, 40, al))
    chips = cfg.get("chips") or []
    if chips:
        ca = max(0, min(1, (i - 104) / 16))
        if ca > 0:
            cols = [(200, 90, 30), (13, 148, 136), (9, 105, 218),
                    (31, 35, 40), (13, 148, 136), (87, 96, 106)]
            cx = X(320)
            cy = X(1235)
            for j, ch in enumerate(chips):
                fnt = F(X(44), True)
                tw = d.textlength(ch, font=fnt)
                d.rounded_rectangle([cx, cy, cx + tw + X(52), cy + X(80)],
                                    radius=int(X(16)), fill=cols[j % 6] + (int(255 * ca),))
                d.text((cx + X(26), cy + X(13)), ch, font=fnt,
                       fill=(255, 255, 255, int(255 * ca)))
                cx += tw + X(52) + X(22)
    return img


def render_finale(strips, avatar, n_frames, outdir):
    os.makedirs(outdir, exist_ok=True)
    styled = []
    for idx, txt in enumerate(strips):
        if idx == len(strips) - 1:
            styled.append((txt, (216, 38, 48), (255, 255, 255)))
        else:
            styled.append((txt, (255, 255, 255), (31, 35, 40)))
    for i in range(n_frames):
        img = Image.new("RGB", (CW, CH), (246, 248, 250))
        d = ImageDraw.Draw(img, "RGBA")
        sc = easeout(max(0, min(1, (i - 6) / 36)))
        if sc > 0:
            r = int(X(300) * sc)
            cx, cy = int(X(1980)), int(X(730))
            av = avatar.resize((2 * r, 2 * r))
            msk = Image.new("L", (2 * r, 2 * r), 0)
            ImageDraw.Draw(msk).ellipse([0, 0, 2 * r, 2 * r], fill=255)
            img.paste(av, (cx - r, cy - r), msk)
            d = ImageDraw.Draw(img, "RGBA")
            d.ellipse([cx - r - 10, cy - r - 10, cx + r + 10, cy + r + 10],
                      outline=(236, 60, 140), width=9)
        for k, (txt, bgc, fgc) in enumerate(styled):
            rt = easeout(max(0, min(1, (i - (10 + 14 * k)) / 14)))
            if rt <= 0:
                continue
            fnt = F(X(72), True)
            tw = d.textlength(txt, font=fnt)
            wpx = tw + X(90)
            hpx = X(118)
            y0 = X(215 + 190 * k)
            x0 = X(180) - (1 - rt) * X(500)
            shadow = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
            ImageDraw.Draw(shadow).rounded_rectangle(
                [x0 + 6, y0 + 8, x0 + wpx + 6, y0 + hpx + 8],
                radius=int(X(14)), fill=(0, 0, 0, 60))
            img = Image.alpha_composite(img.convert("RGBA"), shadow).convert("RGB")
            d = ImageDraw.Draw(img, "RGBA")
            d.rounded_rectangle([x0, y0, x0 + wpx, y0 + hpx], radius=int(X(14)), fill=bgc)
            d.text((x0 + X(45), y0 + X(20)), txt, font=fnt, fill=fgc)
        img.save(os.path.join(outdir, f"f{i:03d}.png"))


def frames_to_clip(frames_dir, pattern, out_path, extra_vf=""):
    vf = "scale=1280:720,format=yuv420p"
    if extra_vf:
        vf = extra_vf + "," + vf
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS),
                    "-i", os.path.join(frames_dir, pattern), "-vf", vf,
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20", out_path],
                   check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workdir", default=None)
    args = ap.parse_args()
    with open(args.config, encoding="utf-8") as fh:
        cfg = json.load(fh)
    base = os.path.dirname(os.path.abspath(args.config))

    def resolve(p):
        return p if os.path.isabs(p) else os.path.join(base, p)

    workdir = args.workdir or tempfile.mkdtemp(prefix="ghpromo_")
    os.makedirs(workdir, exist_ok=True)
    dur = cfg.get("durations", {})
    d_cover = float(dur.get("cover", 5.5))
    d_cards = [float(x) for x in dur.get("cards", [6.5, 6.0, 6.0])]
    d_fin = float(dur.get("finale", 4.5))
    avatar = Image.open(resolve(cfg["avatar"])).convert("RGB")

    # --- segments ---
    cover_dir = os.path.join(workdir, "cover")
    render_cover(resolve(cfg["page_frame"]), int(d_cover * FPS), cover_dir)
    cover_mp4 = os.path.join(workdir, "cover.mp4")
    frames_to_clip(cover_dir, "c%03d.png", cover_mp4, "fade=t=in:st=0:d=0.4")

    clips = [cover_mp4]
    durs = [d_cover]
    for idx, card in enumerate(cfg["cards"]):
        cdir = os.path.join(workdir, f"card{idx}")
        os.makedirs(cdir, exist_ok=True)
        n = int(d_cards[idx] * FPS)
        for i in range(n):
            draw_card(card, avatar, i).save(os.path.join(cdir, f"f{i:03d}.png"))
        cmp4 = os.path.join(workdir, f"card{idx}.mp4")
        frames_to_clip(cdir, "f%03d.png", cmp4)
        clips.append(cmp4)
        durs.append(d_cards[idx])

    fin_dir = os.path.join(workdir, "fin")
    render_finale(cfg["finale_strips"], avatar, int(d_fin * FPS), fin_dir)
    fin_mp4 = os.path.join(workdir, "fin.mp4")
    frames_to_clip(fin_dir, "f%03d.png", fin_mp4)
    clips.append(fin_mp4)
    durs.append(d_fin)

    # --- stitch with xfade (1s transitions; first is a white flash) ---
    trans = 1.0
    total = sum(durs) - trans * (len(clips) - 1)
    inputs = []
    for c in clips:
        inputs += ["-i", c]
    bgm = cfg.get("bgm")
    if bgm:
        inputs += ["-i", resolve(bgm)]
    filt = []
    prev = "[0:v]"
    elapsed = durs[0]
    transitions = ["fadewhite", "fade", "fade", "fade"]
    for j in range(1, len(clips)):
        off = elapsed - trans
        label = "[vout]" if j == len(clips) - 1 else f"[v{j}]"
        filt.append(f"{prev}[{j}:v]xfade=transition={transitions[j - 1]}:duration={trans}:offset={off:.2f}{label}")
        prev = label
        elapsed += durs[j] - trans
    if bgm:
        filt.append(f"[{len(clips)}:a]atrim=0:{total:.2f},afade=t=out:st={max(0, total - 2.5):.2f}:d=2.5[aout]")
        maps = ["-map", "[vout]", "-map", "[aout]"]
        audio = ["-c:a", "aac", "-b:a", "192k"]
    else:
        maps = ["-map", "[vout]"]
        audio = ["-an"]
    cmd = ["ffmpeg", "-y", "-v", "error"] + inputs + [
        "-filter_complex", ";".join(filt)] + maps + [
        "-c:v", "libx264", "-preset", "medium", "-crf", "20"] + audio + [
        "-t", f"{total:.2f}", args.out]
    subprocess.run(cmd, check=True)
    print(f"done: {args.out} ({total:.1f}s, workdir {workdir})")


if __name__ == "__main__":
    main()
