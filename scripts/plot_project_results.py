"""Plot the overall score comparison for the project.

This script uses only hard-coded scores from existing experiment reports.
It does not read outputs/, models/, or minimind/. It prefers matplotlib and
falls back to a tiny standard-library PNG writer when matplotlib is unavailable.
"""

from pathlib import Path
import struct
import zlib

try:
    import matplotlib.pyplot as plt
except ModuleNotFoundError:
    plt = None


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = PROJECT_ROOT / "assets"
OUTPUT_PATH = ASSETS_DIR / "model_score_comparison.png"

SCORES = [
    ("MiniMind\nbaseline", 5.025),
    ("MiniMind\nLoRA v1", 5.375),
    ("MiniMind\nLoRA v2", 5.645),
    ("Qwen\nbaseline", 6.275),
    ("Qwen\nLoRA v4", 7.865),
]

FALLBACK_LABELS = ["MM BASE", "MM LORA1", "MM LORA2", "QWEN BASE", "QWEN LORA4"]

FONT = {
    " ": ["000", "000", "000", "000", "000", "000", "000"],
    ".": ["000", "000", "000", "000", "000", "110", "110"],
    "-": ["000", "000", "000", "111", "000", "000", "000"],
    "0": ["111", "101", "101", "101", "101", "101", "111"],
    "1": ["010", "110", "010", "010", "010", "010", "111"],
    "2": ["111", "001", "001", "111", "100", "100", "111"],
    "3": ["111", "001", "001", "111", "001", "001", "111"],
    "4": ["101", "101", "101", "111", "001", "001", "001"],
    "5": ["111", "100", "100", "111", "001", "001", "111"],
    "6": ["111", "100", "100", "111", "101", "101", "111"],
    "7": ["111", "001", "001", "010", "010", "010", "010"],
    "8": ["111", "101", "101", "111", "101", "101", "111"],
    "9": ["111", "101", "101", "111", "001", "001", "111"],
    "A": ["010", "101", "101", "111", "101", "101", "101"],
    "B": ["110", "101", "101", "110", "101", "101", "110"],
    "C": ["111", "100", "100", "100", "100", "100", "111"],
    "D": ["110", "101", "101", "101", "101", "101", "110"],
    "E": ["111", "100", "100", "110", "100", "100", "111"],
    "F": ["111", "100", "100", "110", "100", "100", "100"],
    "I": ["111", "010", "010", "010", "010", "010", "111"],
    "L": ["100", "100", "100", "100", "100", "100", "111"],
    "M": ["101", "111", "111", "101", "101", "101", "101"],
    "N": ["101", "111", "111", "111", "101", "101", "101"],
    "O": ["111", "101", "101", "101", "101", "101", "111"],
    "P": ["110", "101", "101", "110", "100", "100", "100"],
    "Q": ["111", "101", "101", "101", "111", "001", "001"],
    "R": ["110", "101", "101", "110", "101", "101", "101"],
    "S": ["111", "100", "100", "111", "001", "001", "111"],
    "T": ["111", "010", "010", "010", "010", "010", "010"],
    "V": ["101", "101", "101", "101", "101", "101", "010"],
    "W": ["101", "101", "101", "101", "111", "111", "101"],
}


def main() -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    if plt is None:
        write_fallback_png(OUTPUT_PATH)
        print(f"matplotlib is unavailable; saved fallback chart to: {OUTPUT_PATH}")
        return

    labels = [item[0] for item in SCORES]
    values = [item[1] for item in SCORES]
    colors = ["#7f8c8d", "#95a5a6", "#5dade2", "#58d68d", "#27ae60"]

    fig, ax = plt.subplots(figsize=(9, 5.2))
    bars = ax.bar(labels, values, color=colors)
    ax.set_title("Overall Score Comparison: MiniMind vs Qwen LoRA", fontsize=14, pad=14)
    ax.set_ylabel("Rule-based overall score")
    ax.set_ylim(0, 10)
    ax.grid(axis="y", linestyle="--", alpha=0.35)

    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 0.12,
            f"{value:.3f}",
            ha="center",
            va="bottom",
            fontsize=10,
        )

    note = "Scores come from existing rule-based evaluation reports; they are not a substitute for human review."
    fig.text(0.5, 0.015, note, ha="center", fontsize=9, color="#555555")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(OUTPUT_PATH, dpi=180)
    plt.close(fig)
    print(f"Saved chart to: {OUTPUT_PATH}")


def write_chunk(file, chunk_type: bytes, data: bytes) -> None:
    file.write(struct.pack(">I", len(data)))
    file.write(chunk_type)
    file.write(data)
    crc = zlib.crc32(chunk_type)
    crc = zlib.crc32(data, crc)
    file.write(struct.pack(">I", crc & 0xFFFFFFFF))


def set_pixel(pixels: bytearray, width: int, x: int, y: int, color: tuple[int, int, int]) -> None:
    if x < 0 or y < 0 or x >= width:
        return
    offset = (y * width + x) * 3
    if 0 <= offset < len(pixels) - 2:
        pixels[offset:offset + 3] = bytes(color)


def fill_rect(
    pixels: bytearray,
    width: int,
    height: int,
    left: int,
    top: int,
    right: int,
    bottom: int,
    color: tuple[int, int, int],
) -> None:
    left = max(left, 0)
    right = min(right, width)
    top = max(top, 0)
    bottom = min(bottom, height)
    for y in range(top, bottom):
        row_start = (y * width + left) * 3
        row_end = (y * width + right) * 3
        pixels[row_start:row_end] = bytes(color) * (right - left)


def draw_text(
    pixels: bytearray,
    width: int,
    height: int,
    x: int,
    y: int,
    text: str,
    color: tuple[int, int, int] = (45, 45, 45),
    scale: int = 2,
) -> None:
    cursor = x
    for char in text.upper():
        glyph = FONT.get(char, FONT[" "])
        for gy, row in enumerate(glyph):
            for gx, bit in enumerate(row):
                if bit == "1":
                    fill_rect(
                        pixels,
                        width,
                        height,
                        cursor + gx * scale,
                        y + gy * scale,
                        cursor + (gx + 1) * scale,
                        y + (gy + 1) * scale,
                        color,
                    )
        cursor += 4 * scale


def write_fallback_png(path: Path) -> None:
    """Write a simple dependency-free bar chart.

    The fallback intentionally keeps the chart plain. Labels are represented by
    model order and score values are documented in PROJECT_OVERVIEW.md and
    results_summary.md.
    """
    width, height = 900, 520
    pixels = bytearray((255, 255, 255) * width * height)
    margin_left, margin_bottom, margin_top = 80, 80, 60
    chart_width = width - margin_left - 50
    chart_height = height - margin_top - margin_bottom
    axis_color = (50, 50, 50)
    grid_color = (220, 220, 220)
    colors = [
        (127, 140, 141),
        (149, 165, 166),
        (93, 173, 226),
        (88, 214, 141),
        (39, 174, 96),
    ]

    draw_text(pixels, width, height, 265, 20, "OVERALL SCORE COMPARISON", scale=3)
    draw_text(pixels, width, height, 15, 120, "SCORE", scale=2)
    draw_text(pixels, width, height, 15, 142, "0-10", scale=2)

    # Grid and axes.
    for tick in range(0, 11, 2):
        y = margin_top + chart_height - int(chart_height * tick / 10)
        fill_rect(pixels, width, height, margin_left, y, margin_left + chart_width, y + 1, grid_color)
        draw_text(pixels, width, height, 45, y - 7, str(tick), scale=2)
    fill_rect(pixels, width, height, margin_left, margin_top, margin_left + 2, margin_top + chart_height, axis_color)
    fill_rect(
        pixels,
        width,
        height,
        margin_left,
        margin_top + chart_height,
        margin_left + chart_width,
        margin_top + chart_height + 2,
        axis_color,
    )

    slot = chart_width // len(SCORES)
    bar_width = 80
    for index, (_, value) in enumerate(SCORES):
        x_center = margin_left + slot * index + slot // 2
        bar_height = int(chart_height * value / 10)
        left = x_center - bar_width // 2
        right = x_center + bar_width // 2
        top = margin_top + chart_height - bar_height
        bottom = margin_top + chart_height
        fill_rect(pixels, width, height, left, top, right, bottom, colors[index])
        draw_text(pixels, width, height, left + 8, max(top - 22, 45), f"{value:.3f}", scale=2)
        draw_text(pixels, width, height, x_center - 42, bottom + 16, FALLBACK_LABELS[index], scale=2)

    draw_text(
        pixels,
        width,
        height,
        165,
        height - 26,
        "RULE BASED SCORE NOT HUMAN BUSINESS EVAL",
        color=(90, 90, 90),
        scale=2,
    )

    raw = bytearray()
    for y in range(height):
        raw.append(0)
        raw.extend(pixels[y * width * 3:(y + 1) * width * 3])

    with path.open("wb") as file:
        file.write(b"\x89PNG\r\n\x1a\n")
        write_chunk(file, b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        write_chunk(file, b"IDAT", zlib.compress(bytes(raw), level=9))
        write_chunk(file, b"IEND", b"")


if __name__ == "__main__":
    main()
