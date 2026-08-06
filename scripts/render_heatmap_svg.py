"""Render the contribution heatmap SVG from the scraped JSON snapshot."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
INPUT_PATH = ROOT_DIR / "data" / "contributions.json"
OUTPUT_PATH = ROOT_DIR / "contrib-heatmap.svg"

CELL_SIZE = 12
CELL_GAP = 4
ROWS = 7
WEEKS = 53
LEFT_PADDING = 72
RIGHT_PADDING = 28
BOTTOM_PADDING = 64
INNER_RADIUS = 10

TITLE_Y = 24
TITLE_TO_META_GAP = 18
META_ROW_HEIGHT = 14
META_TO_MONTH_GAP = 18
MONTH_TO_GRID_GAP = 18
MONTH_LABEL_Y_OFFSET = 0
META_MIN_GAP = 32
META_MAX_GAP = 48
MONTH_LABEL_MIN_GAP = 10
LEGEND_GAP = 8

FONT_BODY = 11
FONT_TITLE = 12

SURFACE_ALT = "#11203a"
BORDER = "#1c3b63"
TEXT_PRIMARY = "#d7f3ff"
TEXT_SECONDARY = "#89aeca"
TEXT_MONTH = "#a9cde4"
TEXT_MUTED = "#5b7c98"
LEVEL_COLORS = ["#0f1a2c", "#0e3b63", "#0b5f95", "#19a7d8", "#7ee7ff"]
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DAY_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}


@dataclass(frozen=True)
class DayCell:
    day: date
    count: int
    level: int
    week_index: int
    row_index: int


@dataclass(frozen=True)
class HeaderItem:
    text: str
    x: float
    y: int


@dataclass(frozen=True)
class HeaderLayout:
    metadata_items: list[HeaderItem]
    month_items: list[HeaderItem]
    month_y: int
    grid_top: int
    height: int
    width: int
    grid_width: int
    grid_height: int


class ContributionHeatmap:
    def __init__(self, input_path: Path) -> None:
        self.input_path = input_path

    def load_days(self) -> tuple[list[DayCell], int]:
        payload = json.loads(self.input_path.read_text(encoding="utf-8"))
        days = {
            date.fromisoformat(item["date"]): (int(item["count"]), int(item["level"]))
            for item in payload["days"]
        }
        if not days:
            raise RuntimeError("Contribution dataset is empty.")

        start_day = min(days)
        while start_day.weekday() != 6:
            start_day -= timedelta(days=1)

        grid_days: list[DayCell] = []
        for index in range(WEEKS * ROWS):
            current_day = start_day + timedelta(days=index)
            grid_days.append(
                DayCell(
                    day=current_day,
                    count=days.get(current_day, (0, 0))[0],
                    level=days.get(current_day, (0, 0))[1],
                    week_index=index // ROWS,
                    row_index=index % ROWS,
                )
            )

        return grid_days, int(payload["total_contributions"])

    def render(self, output_path: Path) -> None:
        grid_days, total_contributions = self.load_days()
        layout = self._compute_layout(grid_days)

        metadata_markup = "\n".join(
            f'<text class="footer meta-item" x="{item.x:.1f}" y="{item.y}">{item.text}</text>'
            for item in layout.metadata_items
        )
        month_markup = "\n".join(
            f'<text class="label month-label" x="{item.x:.1f}" y="{item.y}">{item.text}</text>'
            for item in layout.month_items
        )
        day_markup = "\n".join(self._render_day_labels(layout.grid_top))
        rect_markup = "\n".join(self._render_cell(cell, layout.grid_top) for cell in grid_days)
        wave_overlay = self._render_wave_overlay(layout.grid_width, layout.grid_height, layout.grid_top)
        legend_markup = self._render_legend(layout.width, layout.height)

        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="100%" viewBox="0 0 {layout.width} {layout.height}" role="img" aria-labelledby="title desc">
  <title id="title">GitHub contribution heatmap for Harshit Bhardwaj</title>
  <desc id="desc">Animated contribution calendar showing {total_contributions} public contributions over the last year.</desc>
  <defs>
    <linearGradient id="frameGlow" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0e2037" />
      <stop offset="100%" stop-color="#08111f" />
    </linearGradient>
    <filter id="softShadow" x="-20%" y="-20%" width="140%" height="160%">
      <feDropShadow dx="0" dy="10" stdDeviation="16" flood-color="#01050a" flood-opacity="0.45" />
    </filter>
    <filter id="activeCellGlow" x="-60%" y="-60%" width="220%" height="220%">
      <feDropShadow dx="0" dy="0.7" stdDeviation="1.2" flood-color="#8ed8ff" flood-opacity="0.15" />
    </filter>
    <clipPath id="gridClip">
      <rect x="{LEFT_PADDING}" y="{layout.grid_top}" width="{layout.grid_width}" height="{layout.grid_height}" rx="6" ry="6" />
    </clipPath>
    <style>
      text {{
        font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
      }}
      .frame {{
        fill: url(#frameGlow);
        stroke: {BORDER};
        stroke-width: 1;
      }}
      .label {{
        fill: {TEXT_SECONDARY};
        font-size: {FONT_BODY}px;
        letter-spacing: 0.18px;
      }}
      .month-label {{
        fill: {TEXT_MONTH};
      }}
      .heading {{
        fill: {TEXT_PRIMARY};
        font-size: {FONT_TITLE}px;
        font-weight: 600;
      }}
      .footer {{
        fill: {TEXT_MUTED};
        font-size: {FONT_BODY}px;
      }}
      .cell {{
        shape-rendering: geometricPrecision;
      }}
      .wave-overlay {{
        opacity: 0;
      }}
    </style>
  </defs>
  <rect class="frame" x="0.5" y="0.5" rx="{INNER_RADIUS}" ry="{INNER_RADIUS}" width="{layout.width - 1}" height="{layout.height - 1}" filter="url(#softShadow)" />
  <text class="heading" x="{LEFT_PADDING}" y="{TITLE_Y}">harshit@github ~$ ./contributions.sh</text>
  {metadata_markup}
  {month_markup}
  {day_markup}
  <g aria-label="Contribution cells">
    {rect_markup}
  </g>
  {wave_overlay}
  {legend_markup}
  <text class="footer" x="{LEFT_PADDING}" y="{layout.height - 16}">{total_contributions} contributions recorded from public profile activity.</text>
</svg>
"""
        output_path.write_text(svg, encoding="utf-8")

    def _compute_layout(self, grid_days: list[DayCell]) -> HeaderLayout:
        grid_width = (WEEKS * (CELL_SIZE + CELL_GAP)) - CELL_GAP
        grid_height = (ROWS * (CELL_SIZE + CELL_GAP)) - CELL_GAP
        width = LEFT_PADDING + grid_width + RIGHT_PADDING

        metadata_items = self._layout_items(
            ["53 weeks", "Real public profile activity", "Diagonal single-pass reveal"],
            start_x=LEFT_PADDING,
            end_x=LEFT_PADDING + grid_width,
            y_start=TITLE_Y + TITLE_TO_META_GAP,
            row_height=META_ROW_HEIGHT,
            min_gap=META_MIN_GAP,
            max_gap=META_MAX_GAP,
        )
        metadata_bottom = max((item.y for item in metadata_items), default=TITLE_Y)
        month_y = metadata_bottom + META_TO_MONTH_GAP
        month_items = self._build_month_labels(grid_days, month_y)
        grid_top = month_y + MONTH_TO_GRID_GAP
        height = grid_top + grid_height + BOTTOM_PADDING
        return HeaderLayout(
            metadata_items=metadata_items,
            month_items=month_items,
            month_y=month_y,
            grid_top=grid_top,
            height=height,
            width=width,
            grid_width=grid_width,
            grid_height=grid_height,
        )

    def _build_month_labels(self, grid_days: list[DayCell], month_y: int) -> list[HeaderItem]:
        items: list[HeaderItem] = []
        seen_months: set[tuple[int, int]] = set()
        previous_right = float("-inf")
        for cell in grid_days:
            month_key = (cell.day.year, cell.day.month)
            if month_key in seen_months or cell.day.day > 7:
                continue

            label = MONTH_NAMES[cell.day.month - 1]
            x = float(LEFT_PADDING + cell.week_index * (CELL_SIZE + CELL_GAP))
            width = self._estimate_text_width(label, FONT_BODY)
            if x < previous_right + MONTH_LABEL_MIN_GAP:
                continue

            seen_months.add(month_key)
            items.append(HeaderItem(text=label, x=x, y=month_y + MONTH_LABEL_Y_OFFSET))
            previous_right = x + width
        return items

    def _render_day_labels(self, grid_top: int) -> list[str]:
        labels: list[str] = []
        for row_index, label in DAY_LABELS.items():
            y = grid_top + row_index * (CELL_SIZE + CELL_GAP) + CELL_SIZE - 2
            labels.append(f'<text class="label" x="20" y="{y}">{label}</text>')
        return labels

    def _render_cell(self, cell: DayCell, grid_top: int) -> str:
        x = LEFT_PADDING + cell.week_index * (CELL_SIZE + CELL_GAP)
        y = grid_top + cell.row_index * (CELL_SIZE + CELL_GAP)
        delay_ms = (cell.week_index + cell.row_index) * 12
        duration_ms = 900
        fill = LEVEL_COLORS[max(0, min(cell.level, len(LEVEL_COLORS) - 1))]
        active_filter = ' filter="url(#activeCellGlow)"' if cell.level > 0 else ""
        title = self._format_tooltip(cell.day, cell.count)
        return (
            f'<rect class="cell" x="{x}" y="{y}" width="{CELL_SIZE}" height="{CELL_SIZE}" rx="3" ry="3" '
            f'fill="{fill}" stroke="{SURFACE_ALT}" stroke-width="0.6"{active_filter}>'
            f"<title>{title}</title>"
            f'<set attributeName="opacity" to="0" begin="0s" dur="{delay_ms}ms" fill="freeze" />'
            f'<animate attributeName="opacity" from="0" to="1" begin="{delay_ms}ms" dur="{duration_ms}ms" fill="freeze" />'
            f'<animateTransform attributeName="transform" type="translate" from="-1.5 4" to="0 0" '
            f'begin="{delay_ms}ms" dur="{duration_ms}ms" fill="freeze" calcMode="spline" '
            f'keySplines="0.16 1 0.3 1" keyTimes="0;1" />'
            f"</rect>"
        )

    def _render_wave_overlay(self, grid_width: int, grid_height: int, grid_top: int) -> str:
        start_x = LEFT_PADDING - 170
        travel_distance = grid_width + 340
        y = grid_top - 16
        height = grid_height + 32
        return (
            f'<g clip-path="url(#gridClip)">'
            f'<g class="wave-overlay">'
            f'<rect x="{start_x}" y="{y}" width="120" height="{height}" rx="18" ry="18" fill="#d8f6ff" opacity="0.08" transform="skewX(-26)">'
            f'<set attributeName="opacity" to="0" begin="0s" dur="60ms" fill="freeze" />'
            f'<animate attributeName="opacity" values="0;0.12;0" keyTimes="0;0.45;1" dur="1550ms" begin="180ms" fill="freeze" />'
            f'<animateTransform attributeName="transform" type="translate" from="0 0" to="{travel_distance} 0" begin="180ms" dur="1550ms" '
            f'additive="sum" fill="freeze" calcMode="spline" keySplines="0.2 0.9 0.2 1" keyTimes="0;1" />'
            f'<animateTransform attributeName="transform" type="skewX" from="-26" to="-26" begin="180ms" dur="1550ms" additive="sum" fill="freeze" />'
            f"</rect></g></g>"
        )

    def _layout_items(
        self,
        items: list[str],
        start_x: int,
        end_x: int,
        y_start: int,
        row_height: int,
        min_gap: int,
        max_gap: int,
    ) -> list[HeaderItem]:
        if not items:
            return []

        available_width = max(0.0, float(end_x - start_x))
        measured = [(item, self._estimate_text_width(item, FONT_BODY)) for item in items]
        rows: list[list[tuple[str, float]]] = []
        current_row: list[tuple[str, float]] = []
        current_width = 0.0

        for item, item_width in measured:
            gap = float(min_gap if current_row else 0)
            projected_width = current_width + gap + item_width
            if current_row and projected_width > available_width:
                rows.append(current_row)
                current_row = [(item, item_width)]
                current_width = item_width
            else:
                current_row.append((item, item_width))
                current_width = projected_width

        if current_row:
            rows.append(current_row)

        laid_out: list[HeaderItem] = []
        for row_index, row in enumerate(rows):
            total_text_width = sum(width for _, width in row)
            gap_count = len(row) - 1
            free_space = max(0.0, available_width - total_text_width)
            gap_size = 0.0
            content_width = total_text_width
            if gap_count > 0:
                gap_size = min(float(max_gap), max(float(min_gap), free_space / gap_count))
                content_width += gap_size * gap_count

            cursor_x = start_x + max(0.0, (available_width - content_width) / 2)
            row_y = y_start + row_index * row_height
            for text, item_width in row:
                laid_out.append(HeaderItem(text=text, x=cursor_x, y=row_y))
                cursor_x += item_width + gap_size

        return laid_out

    def _format_tooltip(self, contribution_day: date, count: int) -> str:
        day_label = contribution_day.strftime("%b %d, %Y")
        if count == 0:
            return f"No contributions on {day_label}"
        noun = "contribution" if count == 1 else "contributions"
        return f"{count} {noun} on {day_label}"

    def _estimate_text_width(self, text: str, font_size: int) -> float:
        return len(text) * font_size * 0.56

    def _render_legend(self, width: int, height: int) -> str:
        legend_y = height - 34
        swatch_width = len(LEVEL_COLORS) * CELL_SIZE + (len(LEVEL_COLORS) - 1) * 4
        less_width = self._estimate_text_width("Less", FONT_BODY)
        more_width = self._estimate_text_width("More", FONT_BODY)
        legend_width = less_width + LEGEND_GAP + swatch_width + LEGEND_GAP + more_width
        start_x = width - RIGHT_PADDING - legend_width

        parts = [f'<text class="label" x="{start_x:.1f}" y="{legend_y + 10}">Less</text>']
        swatch_start_x = start_x + less_width + LEGEND_GAP
        for index, color in enumerate(LEVEL_COLORS):
            x = swatch_start_x + index * (CELL_SIZE + 4)
            parts.append(
                f'<rect x="{x:.1f}" y="{legend_y}" width="{CELL_SIZE}" height="{CELL_SIZE}" rx="3" ry="3" fill="{color}" stroke="{SURFACE_ALT}" stroke-width="0.6" />'
            )
        parts.append(
            f'<text class="label" x="{swatch_start_x + swatch_width + LEGEND_GAP:.1f}" y="{legend_y + 10}">More</text>'
        )
        return "\n".join(parts)


def main() -> None:
    renderer = ContributionHeatmap(INPUT_PATH)
    renderer.render(OUTPUT_PATH)
    print(f"Rendered {OUTPUT_PATH.name} from {INPUT_PATH.relative_to(ROOT_DIR)}.")


if __name__ == "__main__":
    main()
