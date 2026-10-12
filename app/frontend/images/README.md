# Site images

Drop photos here using the filenames below. Until a file exists, the page shows
a placeholder from `placeholders/` (logos fall back to the company name as text).

| File | Where it appears | Recommended size |
|---|---|---|
| `headshot.jpg` | Hero, circular crop | 640×640, square, face centered |
| `hero-bg.jpg` | Hero background, faint overlay | 1920×1080, low-detail/abstract works best |
| `about.jpg` | About → "Professional profile" row | 1280×800 (16:10) |
| `architecture.png` | About → "This site is a live demo" row | 1280×800 (16:10) |
| `projects/fortified-ai.png` | Projects → Fortified AI card | 1280×720 (16:9) |
| `projects/mcp-sandbox.png` | Projects → MCP Sandbox card | 1280×720 (16:9) |
| `logos/interwell-health.svg` | Logo strip | SVG preferred, ~40px tall |
| `logos/workpath.svg` | Logo strip | " |
| `logos/synchrony.svg` | Logo strip | " |
| `logos/new-york-media.svg` | Logo strip | " |
| `logos/kenzan.svg` | Logo strip | " |
| `logos/comcast.svg` | Logo strip | " |
| `logos/aws-certified-developer.svg` | Logo strip (AWS badge) | " |

Logos are shown grayscale and turn to full color on hover. In dark mode employer
logos are color-inverted, so single-color dark logos work best.

To use a different filename or format (e.g. `.webp`), update the `src` in
`../index.html`.

Compress photos before committing (for example `cwebp -q 80` or squoosh.app);
these files ship inside the container image.
