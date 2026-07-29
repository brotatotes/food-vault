# Food Vault

Food Vault collects source-linked cooking reels and our own home-tested recipes in one searchable place.

This repository contains the first prototype, a searchable static website, and a small build-time validator.

## Local preview

```bash
python3 tools/build.py
python3 -m http.server 8000 --directory docs
```

Then open <http://localhost:8000>.

## Recipe policy

- Recipes transcribed from public sources link to the original creator and source.
- Home recipes are labeled separately and preserve the recipe as we cooked it.
- Recipes distinguish direct video evidence from uncertain or inferred details.
- Downloaded videos are temporary processing inputs and are not published here.
- Extracted cover frames remain attributed to the linked original source.
- Third-party reference photos include visible source and license credit.

## Status

Prototype. Instagram ingestion works for tested public reels. Automated YouTube ingestion is not currently reliable from the processing server because YouTube blocks anonymous requests from its IP.
