#!/usr/bin/env python3
"""Validate recipe records and copy generated data into the static site."""

from __future__ import annotations

import json
import shutil
from datetime import datetime
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
    "addedAt",
}


def build_takeouts() -> None:
    source = ROOT / "data" / "takeouts.json"
    takeouts = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(takeouts, list) or not takeouts:
        raise ValueError("takeouts.json must contain a non-empty list")
    slugs: set[str] = set()
    required = {"slug", "name", "cuisine", "area", "order", "tip", "sourceUrl"}
    for place in takeouts:
        if required - place.keys():
            raise ValueError(f"Takeout record is incomplete: {place.get('slug')}")
        if any(not isinstance(place[field], str) or not place[field].strip() for field in required):
            raise ValueError(f"Takeout fields must be non-empty strings: {place['slug']}")
        if place["slug"] in slugs:
            raise ValueError(f"Duplicate takeout slug: {place['slug']}")
        slugs.add(place["slug"])
        if not place["sourceUrl"].startswith("https://"):
            raise ValueError(f"Takeout source must use HTTPS: {place['slug']}")
    destination = ROOT / "docs" / "data" / "takeouts.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    print(f"Built {len(takeouts)} healthy takeout options")


def build_recipe_links(source_urls: set[str]) -> None:
    source = ROOT / "data" / "recipe-links.json"
    links = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(links, list):
        raise ValueError("recipe-links.json must contain a list")
    required = {"slug", "title", "sourceUrl", "status", "note"}
    slugs: set[str] = set()
    for link in links:
        if required - link.keys() or any(not isinstance(link[field], str) or not link[field].strip() for field in required):
            raise ValueError("Saved recipe link is incomplete")
        if link["slug"] in slugs:
            raise ValueError(f"Duplicate saved-link slug: {link['slug']}")
        slugs.add(link["slug"])
        url = link["sourceUrl"]
        if not url.startswith("https://") or url.rstrip("/") in source_urls:
            raise ValueError(f"Invalid or duplicate saved source URL: {url}")
        source_urls.add(url.rstrip("/"))
    shutil.copy2(source, ROOT / "docs" / "data" / "recipe-links.json")
    print(f"Built {len(links)} saved recipe links awaiting details")


def main() -> None:
    recipes = json.loads(SOURCE.read_text(encoding="utf-8"))
    if not isinstance(recipes, list) or not recipes:
        raise ValueError("recipes.json must contain a non-empty list")

    slugs: set[str] = set()
    source_urls: set[str] = set()
    for index, recipe in enumerate(recipes):
        missing = REQUIRED - recipe.keys()
        if missing:
            raise ValueError(f"Recipe {index} is missing {sorted(missing)}")
        if recipe["slug"] in slugs:
            raise ValueError(f"Duplicate slug: {recipe['slug']}")
        slugs.add(recipe["slug"])
        try:
            added_at = datetime.fromisoformat(recipe["addedAt"].replace("Z", "+00:00"))
            if added_at.utcoffset() is None:
                raise ValueError("timezone required")
        except (TypeError, ValueError, AttributeError) as error:
            raise ValueError(f"Invalid timezone-aware addedAt: {recipe['slug']}") from error
        if recipe.get("sourceUrl") and not recipe["sourceUrl"].startswith("https://"):
            raise ValueError(f"Source URL must use HTTPS: {recipe['slug']}")
        for url in [recipe.get("sourceUrl"), *[item["url"] for item in recipe.get("additionalSources", [])]]:
            if not url:
                continue
            if not url.startswith("https://"):
                raise ValueError(f"Source URL must use HTTPS: {recipe['slug']}")
            key = url.rstrip("/")
            if key in source_urls:
                raise ValueError(f"Duplicate source URL: {url}")
            source_urls.add(key)
        if recipe.get("imageSourceUrl") and not recipe["imageSourceUrl"].startswith("https://"):
            raise ValueError(f"Image source URL must use HTTPS: {recipe['slug']}")
        image = ROOT / "docs" / recipe["image"]
        if not image.is_file():
            raise ValueError(f"Missing image for {recipe['slug']}: {image}")

    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE, DESTINATION)
    build_takeouts()
    build_recipe_links(source_urls)

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
