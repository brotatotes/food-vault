# Food Vault

Food Vault collects source-linked recipes, home-tested dishes and balanced Durham takeout ideas in one place.

This repository contains the first prototype, a searchable static website, and a small build-time validator.

## Local preview

```bash
python3 tools/build.py
python3 -m http.server 8000 --directory docs
```

Then open <http://localhost:8000>.

Use `/#healthy-takeouts` for the restaurant collection. `data/takeouts.json` holds the seven restaurant entries and ordering suggestions. These are not verified nutritional ratings. `data/recipe-links.json` keeps inaccessible recipe sources separate from complete recipes, with their limitations visible.

Recipes display newest-added first, including filtered and searched results. Every recipe requires an immutable timezone-aware ISO `addedAt` value. Set it when adding a recipe, and preserve it during later edits. Historical dates were backfilled from each recipe's first appearance in repository history, not the source article's publication date. Same-batch ties retain data-file order. Keep per-recipe image crops on the record rather than tying crops to a card's position.

## Checks

```bash
python3 -m unittest discover -s tests
node --check docs/app.js
python3 tools/check_site.py --base-url http://localhost:8000 --output-dir .tmp/qa --slug avgolemono-soup --slug classic-braised-taiwanese-beef-stew --slug one-pot-pumpkin-mushroom-rice
```

The browser check requires Python Playwright and Chromium. It exercises collection navigation, direct links, search, browser history, image loading, dialogs and responsive overflow, and saves bounded screenshots for visual inspection. It does not replace human or vision-model inspection.

## Recipe policy

- Recipes transcribed from public sources link to the original creator and source.
- Home recipes are labeled separately and preserve the recipe as we cooked it.
- Recipes distinguish direct video evidence from uncertain or inferred details.
- Downloaded videos are temporary processing inputs and are not published here.
- Extracted cover frames remain attributed to the linked original source.
- Third-party reference photos include visible source and license credit.
- Recipe-source photographs retain visible creator credit. Source links do not imply a license grant.
- Never publish private chat participants or dietary history. Public order suggestions may identify ingredients without naming an individual.

## Status

Prototype. Instagram ingestion works for tested public reels. Automated YouTube ingestion is not currently reliable from the processing server because YouTube blocks anonymous requests from its IP.
