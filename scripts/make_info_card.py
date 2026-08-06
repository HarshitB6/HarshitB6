"""Render the terminal-style profile information card SVG."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PATH = ROOT_DIR / "info-card.svg"

WIDTH = 920
HEIGHT = 420
BACKGROUND = "#08111f"
PANEL_ALT = "#11203a"
BORDER = "#1a436b"
TEXT_PRIMARY = "#d7f3ff"
TEXT_SECONDARY = "#8fbbd5"
TEXT_ACCENT = "#7ee7ff"
TEXT_SUCCESS = "#61f2b5"
TEXT_MUTED = "#517394"
LABEL_FONT_SIZE = 17
VALUE_FONT_SIZE = 17
PROMPT_FONT_SIZE = 18
META_FONT_SIZE = 14


@dataclass(frozen=True)
class LineItem:
    label: str
    value: str
    accent: str = TEXT_PRIMARY


class InfoCardRenderer:
    def __init__(self) -> None:
        self.lines = [
            LineItem("Name", "Harshit Bhardwaj", TEXT_ACCENT),
            LineItem("GitHub", "@HarshitB6"),
            LineItem("Role", "Computer Science Student"),
            LineItem("College", "Bharati Vidyapeeth College of Engineering"),
            LineItem("Graduation", "2028"),
            LineItem("Languages", "Python, C++, Java, SQL"),
            LineItem("Current Focus", "Artificial Intelligence, Machine Learning, Backend, DSA"),
            LineItem("Current Project", "DocuMind"),
            LineItem("Goal", "Software Engineering Internship", TEXT_SUCCESS),
        ]
        self.label_x = 52
        self.colon_x = self.label_x + self._max_label_width() + 22
        self.value_x = self.colon_x + 24
        self.line_start_y = 126
        self.line_gap = 28

    def render(self, output_path: Path) -> None:
        line_markup = "\n".join(self._render_line(index, item) for index, item in enumerate(self.lines))
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="100%" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">
  <title id="title">Neofetch-inspired info card for Harshit Bhardwaj</title>
  <desc id="desc">Terminal-style profile card with education, focus areas, languages, and current project.</desc>
  <defs>
    <linearGradient id="panelGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f1b2f" />
      <stop offset="100%" stop-color="#08111f" />
    </linearGradient>
    <filter id="panelShadow" x="-20%" y="-20%" width="140%" height="150%">
      <feDropShadow dx="0" dy="14" stdDeviation="20" flood-color="#01050a" flood-opacity="0.5" />
    </filter>
    <filter id="goalGlow" x="-30%" y="-40%" width="180%" height="200%">
      <feDropShadow dx="0" dy="0" stdDeviation="1.6" flood-color="#b2ffe0" flood-opacity="0.22" />
    </filter>
    <style>
      text {{
        font-family: Consolas, 'SFMono-Regular', 'Liberation Mono', monospace;
      }}
      .frame {{
        fill: url(#panelGradient);
        stroke: {BORDER};
        stroke-width: 1.2;
      }}
      .line {{
        opacity: 1;
      }}
      .prompt {{
        fill: {TEXT_SUCCESS};
        font-size: {PROMPT_FONT_SIZE}px;
        letter-spacing: 0.18px;
      }}
      .meta {{
        fill: {TEXT_MUTED};
        font-size: {META_FONT_SIZE}px;
        letter-spacing: 0.24px;
      }}
      .label {{
        fill: {TEXT_SECONDARY};
        font-size: {LABEL_FONT_SIZE}px;
      }}
      .value {{
        font-size: {VALUE_FONT_SIZE}px;
      }}
      .value-goal {{
        font-weight: 700;
      }}
      .divider {{
        stroke: {PANEL_ALT};
        stroke-width: 1;
      }}
    </style>
  </defs>
  <rect x="0" y="0" width="{WIDTH}" height="{HEIGHT}" fill="{BACKGROUND}" rx="18" ry="18" />
  <rect class="frame" x="12" y="12" width="{WIDTH - 24}" height="{HEIGHT - 24}" rx="20" ry="20" filter="url(#panelShadow)" />
  <circle cx="42" cy="42" r="6" fill="#ff5f56" />
  <circle cx="62" cy="42" r="6" fill="#ffbd2e" />
  <circle cx="82" cy="42" r="6" fill="#27c93f" />
  <text class="prompt" x="118" y="48">harshit@github:~$ whoami</text>
  <text class="meta" x="118" y="72">terminal profile snapshot</text>
  <line class="divider" x1="32" y1="92" x2="{WIDTH - 32}" y2="92" />
  {line_markup}
</svg>
"""
        output_path.write_text(svg, encoding="utf-8")

    def _render_line(self, index: int, item: LineItem) -> str:
        y = self.line_start_y + index * self.line_gap
        safe_label = self._escape_text(item.label)
        safe_value = self._escape_text(item.value)
        delay_ms = index * 140
        duration_ms = 540
        value_class = "value value-goal" if item.label == "Goal" else "value"
        value_filter = ' filter="url(#goalGlow)"' if item.label == "Goal" else ""
        return (
            f'<g class="line" transform="translate(0 0)">'
            f'<text class="label" x="{self.label_x}" y="{y}">{safe_label}</text>'
            f'<text class="label" x="{self.colon_x}" y="{y}">:</text>'
            f'<text class="{value_class}" x="{self.value_x}" y="{y}" fill="{item.accent}"{value_filter}>{safe_value}</text>'
            f'<set attributeName="opacity" to="0" begin="0s" dur="{delay_ms}ms" fill="freeze" />'
            f'<animate attributeName="opacity" from="0" to="1" begin="{delay_ms}ms" '
            f'dur="{duration_ms}ms" fill="freeze" />'
            f'<animateTransform attributeName="transform" type="translate" '
            f'from="-10 0" to="0 0" begin="{delay_ms}ms" dur="{duration_ms}ms" '
            f'fill="freeze" calcMode="spline" keySplines="0.16 1 0.3 1" keyTimes="0;1" />'
            f"</g>"
        )

    def _escape_text(self, value: str) -> str:
        return (
            value.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    def _max_label_width(self) -> int:
        return max(self._estimate_text_width(item.label) for item in self.lines)

    def _estimate_text_width(self, value: str) -> int:
        return int(len(value) * LABEL_FONT_SIZE * 0.62)


def main() -> None:
    InfoCardRenderer().render(OUTPUT_PATH)
    print(f"Rendered {OUTPUT_PATH.name}.")


if __name__ == "__main__":
    main()
