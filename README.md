# 📸 ListReady

**Free, in-browser image & video tools for online sellers.** Convert iPhone HEIC photos to JPG, resize them for Etsy / eBay / Amazon / Poshmark, compress, strip GPS data, and convert iPhone HEVC videos to MP4 — all without uploading your files to a server.

🔗 **Live site:** https://listreadyapp.vercel.app

---

## Why it exists

Two everyday problems for people who sell online:

1. **iPhones save photos as HEIC**, which many marketplaces and Windows PCs won't open or accept.
2. **Every marketplace wants a different image size**, and listing photos often end up blurry or rejected.

Most online converters upload your photos to a server — not great for personal images. ListReady does the work **locally in your browser**, so your files never leave your device.

---

## Features

- **HEIC → JPG / PNG / WEBP** conversion
- **One-click resize presets** for Etsy (2000px), eBay & Amazon (1600px), Poshmark/Mercari (1200px square), and Instagram (1080×1080)
- **Smart compression** to keep listings fast-loading
- **Strips GPS / EXIF metadata** automatically on re-encode (so you don't broadcast your location)
- **Batch processing** with one-click ZIP download
- **iPhone HEVC / .MOV → MP4** video conversion for Windows
- **100% client-side** for the photo tools and short video clips — nothing is uploaded

---

## How it works

Everything for the image tools runs in the browser:

- **HEIC decoding** via [`heic2any`](https://github.com/alexcorvi/heic2any)
- **Resize / compress / EXIF-strip** via the HTML `<canvas>` API (re-encoding drops metadata)
- **Batch ZIP** via [JSZip](https://stuk.github.io/jszip/)
- **Short video clips** convert in-browser via [`ffmpeg.wasm`](https://ffmpegwasm.netlify.app/)

Large videos exceed what a browser tab can hold in memory, so those are the one piece that uses a small server-side transcode service (see `server/`).

---

## Project structure

| Path | What it is |
|------|------------|
| `build.py` | Generates the templated image-tool pages (`index`, `etsy`, `ebay`, `amazon`, `poshmark`, `windows`) plus `sitemap.xml` / `robots.txt`. Edit shared nav/footer/SEO here — **don't hand-edit the generated HTML.** |
| `app.js` | Image tool logic (convert / resize / compress / Pro features). |
| `video.html` + `video.js` | iPhone video → MP4 converter (standalone, not generated). |
| `style.css` | Shared styles. |
| `814.ffmpeg.js`, `ffmpeg.js` | Self-hosted FFmpeg wrapper + worker (must be same-origin). |
| `server/` | Server-side video transcode + license verification (Node + FFmpeg, deploys to Cloud Run). |
| `og-image.png`, `demo.gif` | Social share assets (`gen_assets.py` generates them). |

---

## Local development

It's a static site — no build step needed to run it:

```bash
# serve the folder however you like, e.g.
python3 -m http.server 8000
# then open http://localhost:8000
```

To change shared layout or SEO across the marketplace pages, edit `build.py` and regenerate:

```bash
python3 build.py
```

---

## Tech

- Vanilla HTML / CSS / JavaScript (no framework)
- `heic2any`, JSZip, `ffmpeg.wasm` (loaded from CDN)
- Hosted on Vercel (auto-deploys on every commit)
- Optional Node + FFmpeg service on Cloud Run for large-video transcoding

---

## Pricing

ListReady is **free**. A one-time **$9 Pro** unlock adds unlimited batch sizes, WEBP output, custom watermarks, and large-video conversion. No subscription.

---

*Built for online sellers. Your photos stay on your device.*
