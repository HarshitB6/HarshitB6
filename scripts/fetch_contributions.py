#!/usr/bin/env python3

"""
Fetch GitHub contribution calendar.

Author: HarshitB6 Profile

Outputs:
    data/contributions.json
"""

import json
import os
import re
import requests

from bs4 import BeautifulSoup
from datetime import datetime

USERNAME = "HarshitB6"

URL = f"https://github.com/users/{USERNAME}/contributions"

OUTPUT = "data/contributions.json"


def contribution_level(color):
    """
    Convert GitHub color into level.
    """

    colors = {
        "#ebedf0": 0,
        "#9be9a8": 1,
        "#40c463": 2,
        "#30a14e": 3,
        "#216e39": 4,
    }

    return colors.get(color.lower(), 0)


def fetch():

    print("Fetching contribution graph...")

    r = requests.get(
        URL,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    rects = soup.find_all("rect")

    contributions = []

    total = 0

    for rect in rects:

        if rect.has_attr("data-date"):

            date = rect["data-date"]

            count = int(rect.get("data-count", 0))

            level = int(rect.get("data-level", 0))

            total += count

            contributions.append(
                {
                    "date": date,
                    "count": count,
                    "level": level
                }
            )

    print(f"Days found: {len(contributions)}")
    print(f"Total contributions: {total}")

    os.makedirs("data", exist_ok=True)

    with open(OUTPUT, "w") as f:

        json.dump(
            {
                "username": USERNAME,
                "generated": datetime.utcnow().isoformat(),
                "total": total,
                "days": contributions
            },
            f,
            indent=4
        )

    print("Saved ->", OUTPUT)


if __name__ == "__main__":
    fetch()
