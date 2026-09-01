#!/usr/bin/env python3
"""Validate recipe records and copy generated data into the static site."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "recipes.json"
DESTINATION = ROOT / "docs" / "data" / "recipes.json"
INDEX = ROOT / "docs" / "index.html"
RECIPE_PAGES = ROOT / "docs" / "recipes"
REQUIRED = {
    "slug",
    "title",
    "creator",
    "platform",
    "image",
    "ingredients",
    "steps",
    "evidence",
}


def main() -> None:
    recipes = json.loads(SOURCE.read_text(encoding="utf-8"))
    if not isinstance(recipes, list) or not recipes:
        raise ValueError("recipes.json must contain a non-empty list")

    slugs: set[str] = set()
    for index, recipe in enumerate(recipes):
        missing = REQUIRED - recipe.keys()
        if missing:
            raise ValueError(f"Recipe {index} is missing {sorted(missing)}")
        if recipe["slug"] in slugs:
            raise ValueError(f"Duplicate slug: {recipe['slug']}")
        slugs.add(recipe["slug"])
        if recipe.get("sourceUrl") and not recipe["sourceUrl"].startswith("https://"):
            raise ValueError(f"Source URL must use HTTPS: {recipe['slug']}")
        if recipe.get("imageSourceUrl") and not recipe["imageSourceUrl"].startswith("https://"):
            raise ValueError(f"Image source URL must use HTTPS: {recipe['slug']}")
        image = ROOT / "docs" / recipe["image"]
        if not image.is_file():
            raise ValueError(f"Missing image for {recipe['slug']}: {image}")

    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE, DESTINATION)

    index_html = INDEX.read_text(encoding="utf-8")
    recipe_html = index_html.replace(
        '<meta charset="utf-8">',
        '<meta charset="utf-8">\n  <base href="../../">',
        1,
    )
    if RECIPE_PAGES.exists():
        shutil.rmtree(RECIPE_PAGES)
    for recipe in recipes:
        page = RECIPE_PAGES / recipe["slug"] / "index.html"
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(recipe_html, encoding="utf-8")

    print(
        f"Built {len(recipes)} recipes and {len(recipes)} direct-link pages "
        f"under {RECIPE_PAGES.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
