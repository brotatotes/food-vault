# Food Vault

Food Vault turns public cooking reels into source-linked draft recipes that are easier to search and cook from.

This repository contains the first prototype. It currently includes two Instagram recipes, a searchable static website, and a small build-time validator.

## Local preview

```bash
python3 tools/build.py
python3 -m http.server 8000 --directory docs
```

Then open <http://localhost:8000>.

## Recipe policy

- Every recipe links to the original creator and video.
- Recipes distinguish direct video evidence from uncertain or inferred details.
- Downloaded videos are temporary processing inputs and are not published here.
- Extracted cover frames remain attributed to the linked original source.

## Status

Prototype. Instagram ingestion works for tested public reels. Automated YouTube ingestion is not currently reliable from the processing server because YouTube blocks anonymous requests from its IP.
