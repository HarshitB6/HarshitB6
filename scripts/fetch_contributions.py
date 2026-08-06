
"""Fetch public GitHub contribution data without the GitHub API."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag


USERNAME = "HarshitB6"
CONTRIBUTIONS_URL = f"https://github.com/users/{USERNAME}/contributions"
ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PATH = ROOT_DIR / "data" / "contributions.json"
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/127.0.0.0 Safari/537.36"
    )
}
TOOLTIP_COUNT_PATTERN = re.compile(r"(?P<count>\d+)\s+contribution")


@dataclass(frozen=True)
class ContributionDay:
    date: str
    count: int
    level: int


@dataclass(frozen=True)
class ContributionSnapshot:
    username: str
    source: str
    generated_at: str
    total_contributions: int
    start_date: str
    end_date: str
    days: list[ContributionDay]

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


class ContributionFetcher:
    def __init__(self, username: str, source_url: str) -> None:
        self.username = username
        self.source_url = source_url

    def fetch(self) -> ContributionSnapshot:
        response = self._build_session().get(
            self.source_url,
            headers=REQUEST_HEADERS,
            timeout=30,
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        days = self._parse_days(soup)
        if not days:
            raise RuntimeError(
                "No contribution cells were found in the GitHub contributions page."
            )

        total_contributions = sum(day.count for day in days)
        return ContributionSnapshot(
            username=self.username,
            source=self.source_url,
            generated_at=datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            total_contributions=total_contributions,
            start_date=days[0].date,
            end_date=days[-1].date,
            days=days,
        )

    def _parse_days(self, soup: BeautifulSoup) -> list[ContributionDay]:
        cells = soup.select("table.ContributionCalendar-grid td.ContributionCalendar-day")
        if not cells:
            cells = soup.select("rect.ContributionCalendar-day")

        tooltip_by_target = {
            tooltip.get("for"): tooltip.get_text(" ", strip=True)
            for tooltip in soup.select("tool-tip[for]")
            if tooltip.get("for")
        }

        parsed_days: list[ContributionDay] = []
        for cell in cells:
            day_value = cell.get("data-date")
            count_value = cell.get("data-level")
            if not day_value or count_value is None:
                continue

            try:
                raw_count = self._extract_count(cell, tooltip_by_target)
                parsed_days.append(
                    ContributionDay(
                        date=day_value,
                        count=int(raw_count),
                        level=int(count_value),
                    )
                )
            except ValueError as error:
                raise RuntimeError(
                    f"GitHub contribution payload contained an unexpected value: {error}"
                ) from error

        parsed_days.sort(key=lambda day: day.date)
        return parsed_days

    def _extract_count(
        self,
        cell: Tag,
        tooltip_by_target: dict[str, str],
    ) -> int:
        raw_count = cell.get("data-count")
        if raw_count is not None:
            return int(raw_count)

        tooltip_text = tooltip_by_target.get(cell.get("id", ""), "")
        if tooltip_text.startswith("No contributions"):
            return 0

        match = TOOLTIP_COUNT_PATTERN.search(tooltip_text)
        if match:
            return int(match.group("count"))

        raise RuntimeError(
            f"Could not determine contribution count for {cell.get('data-date', 'unknown date')}."
        )

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        session.trust_env = False
        return session


def write_snapshot(snapshot: ContributionSnapshot, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(snapshot.to_json(), indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    snapshot = ContributionFetcher(USERNAME, CONTRIBUTIONS_URL).fetch()
    write_snapshot(snapshot, OUTPUT_PATH)
    start = date.fromisoformat(snapshot.start_date)
    end = date.fromisoformat(snapshot.end_date)
    print(
        f"Saved {snapshot.total_contributions} contributions for "
        f"{snapshot.username} from {start.isoformat()} to {end.isoformat()}."
    )


if __name__ == "__main__":
    main()
>>>>>>> a598f22 (Revamp GitHub profile with animated SVGs)
