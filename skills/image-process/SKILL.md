---
name: image-process
description: Select and validate source-preserving media assets for entities and events.
---

# Image processing

Input: media candidates from official or clearly licensed public sources.

1. Prefer the official original file showing one unobstructed subject at useful resolution.
2. Record the original URL, source, dimensions, media type, license when known, alt text, and SHA-256 hash.
3. Reject screenshots, watermarked composites, low-resolution frames, unrelated multi-subject images, guessed reconstructions, and generated placeholders.
4. Leave the asset empty when no qualifying source exists.
5. Never rewrite or hide provenance during resizing or format conversion.

Output media proposals for review; do not silently replace a verified asset.
