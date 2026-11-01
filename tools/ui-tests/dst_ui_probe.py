from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import pyautogui
from PIL import Image


ROOT = Path(__file__).resolve().parent
TEMPLATE_DIR = ROOT / "templates"
OUTPUT_DIR = ROOT / "output"


@dataclass
class Match:
    score: float
    x: int
    y: int
    w: int
    h: int
    scale: float

    @property
    def center(self) -> tuple[int, int]:
        return self.x + self.w // 2, self.y + self.h // 2


def ensure_dirs() -> None:
    TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def screenshot_pil(region: tuple[int, int, int, int] | None = None) -> Image.Image:
    return pyautogui.screenshot(region=region)


def pil_to_bgr(image: Image.Image) -> np.ndarray:
    rgb = np.array(image.convert("RGB"))
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def read_bgr(path: Path) -> np.ndarray:
    data = np.fromfile(str(path), dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError(f"Failed to read image: {path}")
    return image


def write_bgr(path: Path, image: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ok, encoded = cv2.imencode(path.suffix or ".png", image)
    if not ok:
        raise RuntimeError(f"Failed to encode image: {path}")
    encoded.tofile(str(path))


def parse_region(value: str | None) -> tuple[int, int, int, int] | None:
    if not value:
        return None
    parts = [int(part.strip()) for part in value.split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("region must be x,y,w,h")
    return tuple(parts)  # type: ignore[return-value]


def resolve_template(name: str) -> Path:
    path = Path(name)
    if path.is_absolute():
        return path
    return TEMPLATE_DIR / path


def scaled_templates(template: np.ndarray, min_scale: float, max_scale: float, steps: int) -> list[tuple[float, np.ndarray]]:
    if steps <= 1 or min_scale == max_scale:
        return [(1.0, template)]
    scales = np.linspace(min_scale, max_scale, steps)
    result: list[tuple[float, np.ndarray]] = []
    for scale in scales:
        resized = cv2.resize(template, None, fx=float(scale), fy=float(scale), interpolation=cv2.INTER_AREA)
        if resized.shape[0] >= 4 and resized.shape[1] >= 4:
            result.append((float(scale), resized))
    return result


def find_template(
    screen: np.ndarray,
    template: np.ndarray,
    threshold: float,
    min_scale: float,
    max_scale: float,
    scale_steps: int,
) -> Match | None:
    best: Match | None = None
    screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)

    for scale, candidate in scaled_templates(template, min_scale, max_scale, scale_steps):
        if candidate.shape[0] > screen.shape[0] or candidate.shape[1] > screen.shape[1]:
            continue
        template_gray = cv2.cvtColor(candidate, cv2.COLOR_BGR2GRAY)
        result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        _, max_value, _, max_loc = cv2.minMaxLoc(result)
        match = Match(
            score=float(max_value),
            x=int(max_loc[0]),
            y=int(max_loc[1]),
            w=int(candidate.shape[1]),
            h=int(candidate.shape[0]),
            scale=scale,
        )
        if best is None or match.score > best.score:
            best = match

    if best is None or best.score < threshold:
        return None
    return best


def draw_match(screen: np.ndarray, match: Match) -> np.ndarray:
    annotated = screen.copy()
    cv2.rectangle(annotated, (match.x, match.y), (match.x + match.w, match.y + match.h), (0, 255, 0), 2)
    cv2.putText(
        annotated,
        f"{match.score:.3f} scale={match.scale:.2f}",
        (match.x, max(16, match.y - 8)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 255, 0),
        1,
        cv2.LINE_AA,
    )
    return annotated


def command_capture(args: argparse.Namespace) -> int:
    ensure_dirs()
    print("Move mouse to top-left corner, then press Enter.")
    input()
    x1, y1 = pyautogui.position()
    print(f"top-left: {x1},{y1}")
    print("Move mouse to bottom-right corner, then press Enter.")
    input()
    x2, y2 = pyautogui.position()
    print(f"bottom-right: {x2},{y2}")

    left, top = min(x1, x2), min(y1, y2)
    width, height = abs(x2 - x1), abs(y2 - y1)
    if width < 4 or height < 4:
        raise RuntimeError("Selected region is too small.")

    image = screenshot_pil(region=(left, top, width, height))
    output = TEMPLATE_DIR / f"{args.name}.png"
    image.save(output)
    metadata = {
        "name": args.name,
        "file": str(output),
        "captured_region": {"x": left, "y": top, "w": width, "h": height},
        "captured_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    (TEMPLATE_DIR / f"{args.name}.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(json.dumps(metadata, indent=2))
    return 0


def command_find(args: argparse.Namespace) -> int:
    ensure_dirs()
    region = parse_region(args.region)
    screen = pil_to_bgr(screenshot_pil(region=region))
    template_path = resolve_template(args.template)
    template = read_bgr(template_path)
    match = find_template(screen, template, args.threshold, args.min_scale, args.max_scale, args.scale_steps)

    screen_origin_x = region[0] if region else 0
    screen_origin_y = region[1] if region else 0
    if match is None:
        write_bgr(OUTPUT_DIR / "last_find_failed.png", screen)
        print(json.dumps({"ok": False, "template": str(template_path), "threshold": args.threshold}, indent=2))
        return 1

    match.x += screen_origin_x
    match.y += screen_origin_y
    annotated = draw_match(pil_to_bgr(screenshot_pil()), match)
    write_bgr(OUTPUT_DIR / "last_find.png", annotated)
    print(json.dumps({"ok": True, **match.__dict__, "center": match.center, "template": str(template_path)}, indent=2))
    return 0


def command_click(args: argparse.Namespace) -> int:
    find_args = argparse.Namespace(**vars(args))
    region = parse_region(args.region)
    screen = pil_to_bgr(screenshot_pil(region=region))
    template = read_bgr(resolve_template(args.template))
    match = find_template(screen, template, args.threshold, args.min_scale, args.max_scale, args.scale_steps)
    if match is None:
        print(json.dumps({"ok": False, "template": args.template, "threshold": args.threshold}, indent=2))
        return 1
    if region:
        match.x += region[0]
        match.y += region[1]
    x, y = match.center
    pyautogui.click(x, y)
    print(json.dumps({"ok": True, "clicked": [x, y], **match.__dict__}, indent=2))
    return 0


def command_wait(args: argparse.Namespace) -> int:
    deadline = time.time() + args.timeout
    while time.time() < deadline:
        screen = pil_to_bgr(screenshot_pil(region=parse_region(args.region)))
        template = read_bgr(resolve_template(args.template))
        match = find_template(screen, template, args.threshold, args.min_scale, args.max_scale, args.scale_steps)
        if match is not None:
            print(json.dumps({"ok": True, **match.__dict__, "center": match.center}, indent=2))
            return 0
        time.sleep(args.interval)
    print(json.dumps({"ok": False, "reason": "timeout", "template": args.template}, indent=2))
    return 1


def command_motion(args: argparse.Namespace) -> int:
    region = parse_region(args.region)
    if region is None:
        raise RuntimeError("motion requires --region x,y,w,h")

    frames: list[np.ndarray] = []
    deadline = time.time() + args.seconds
    while time.time() < deadline:
        frames.append(pil_to_bgr(screenshot_pil(region=region)))
        time.sleep(args.interval)

    if len(frames) < 2:
        raise RuntimeError("Not enough frames captured.")

    diffs: list[float] = []
    for left, right in zip(frames, frames[1:]):
        gray_left = cv2.cvtColor(left, cv2.COLOR_BGR2GRAY)
        gray_right = cv2.cvtColor(right, cv2.COLOR_BGR2GRAY)
        diffs.append(float(np.mean(cv2.absdiff(gray_left, gray_right))))

    avg_diff = float(np.mean(diffs))
    ok = avg_diff >= args.min_diff
    print(json.dumps({"ok": ok, "avg_diff": avg_diff, "min_diff": args.min_diff, "frames": len(frames)}, indent=2))
    return 0 if ok else 1


def add_common_match_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--template", required=True, help="Template filename under templates/ or absolute path.")
    parser.add_argument("--threshold", type=float, default=0.82)
    parser.add_argument("--region", help="Optional screen region: x,y,w,h")
    parser.add_argument("--min-scale", type=float, default=0.90)
    parser.add_argument("--max-scale", type=float, default=1.10)
    parser.add_argument("--scale-steps", type=int, default=9)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="DST UI probe helpers based on PyAutoGUI and OpenCV.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    capture = subparsers.add_parser("capture", help="Capture a template from the current screen.")
    capture.add_argument("--name", required=True)
    capture.set_defaults(func=command_capture)

    find = subparsers.add_parser("find", help="Find a template on screen.")
    add_common_match_args(find)
    find.set_defaults(func=command_find)

    click = subparsers.add_parser("click", help="Click the center of a matched template.")
    add_common_match_args(click)
    click.set_defaults(func=command_click)

    wait = subparsers.add_parser("wait", help="Wait until a template appears.")
    add_common_match_args(wait)
    wait.add_argument("--timeout", type=float, default=15.0)
    wait.add_argument("--interval", type=float, default=0.5)
    wait.set_defaults(func=command_wait)

    motion = subparsers.add_parser("motion", help="Check whether a screen region changes over time.")
    motion.add_argument("--region", required=True, help="Screen region: x,y,w,h")
    motion.add_argument("--seconds", type=float, default=2.0)
    motion.add_argument("--interval", type=float, default=0.2)
    motion.add_argument("--min-diff", type=float, default=1.5)
    motion.set_defaults(func=command_motion)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
