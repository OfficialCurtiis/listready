# -*- coding: utf-8 -*-
import re, io

SITE = "https://listreadyapp.vercel.app"
# NOTE: style.css and app.js already exist as standalone files and are the
# source of truth (app.js holds the live Gumroad product_id). Do NOT regenerate
# them here. This script only (re)builds the HTML pages + sitemap/robots.

PRESETS = [
    ("0", "Keep original size"),
    ("1600", "eBay / Amazon — 1600px"),
    ("2000", "Etsy — 2000px"),
    ("1200", "Poshmark / Mercari — 1200px"),
    ("1080s", "Instagram square — 1080×1080"),
    ("custom", "Custom…"),
]
def preset_select(default):
    opts = []
    for v, label in PRESETS:
        # webp pro note handled in app.js; here just options
        sel = " selected" if v == default else ""
        opts.append('            <option value="%s"%s>%s</option>' % (v, sel, label))
    return "\n".join(opts)

NAV = ('<div style="text-align:center;margin:8px 0 0;font-size:13px;color:var(--muted)">'
       'Photo guides: '
       '<a href="index.html">Home</a> · '
       '<a href="etsy.html">Etsy</a> · '
       '<a href="ebay.html">eBay</a> · '
       '<a href="amazon.html">Amazon</a> · '
       '<a href="poshmark.html">Poshmark</a> · '
       '<a href="windows.html">Open on Windows</a> · '
       '<a href="video.html">iPhone Video → MP4</a></div>')

TEMPLATE = u"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>%%TITLE%%</title>
<meta name="description" content="%%DESC%%" />
<meta name="keywords" content="%%KEYWORDS%%" />
<link rel="canonical" href="%%CANONICAL%%" />
<meta property="og:title" content="%%OGTITLE%%" />
<meta property="og:description" content="%%DESC%%" />
<meta property="og:type" content="website" />
<meta property="og:url" content="%%CANONICAL%%" />
<meta property="og:image" content="https://listreadyapp.vercel.app/og-image.png" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="%%OGTITLE%%" />
<meta name="twitter:description" content="%%DESC%%" />
<meta name="twitter:image" content="https://listreadyapp.vercel.app/og-image.png" />
%%GSC_META%%<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>\U0001F4F8</text></svg>" />
<link rel="stylesheet" href="style.css" />
</head>
<body>
<header class="top">
  <div class="brand"><span class="logo">\U0001F4F8</span> <a href="index.html" style="color:inherit;text-decoration:none">ListReady</a> <span class="pill">in-browser</span></div>
  <div class="top-actions">
    <span id="statusPill" class="status-pill status-free">Free</span>
    <button id="openPro" class="btn-gold">Upgrade to Pro</button>
  </div>
</header>

<div class="wrap">
  <section class="hero">
    <h1>%%H1%%</h1>
    <p>%%SUB%%</p>
    <div class="trust">\U0001F512 100% private — your photos are processed on your device and never uploaded to any server.</div>
    %%NAV%%
  </section>

  <div class="layout">
    <div class="drop card" id="drop">
      <div style="font-size:36px">⬆️</div>
      <h3>Drop photos here or click to browse</h3>
      <p>JPG, PNG, WEBP, and HEIC supported · add as many as you like</p>
      <button class="btn-primary" id="browseBtn">Choose photos</button>
      <input type="file" id="fileInput" accept="image/*,.heic,.heif" multiple hidden />
    </div>

    <div class="card">
      <div class="controls">
        <div class="field">
          <label>Output format</label>
          <select id="fmt">
            <option value="image/jpeg">JPG (best for marketplaces)</option>
            <option value="image/png">PNG (lossless / transparency)</option>
            <option value="image/webp">WEBP — smallest size \U0001F512 Pro</option>
          </select>
        </div>
        <div class="field">
          <label>Resize preset</label>
          <select id="preset">
%%PRESET_OPTIONS%%
          </select>
          <div class="custom-dims" id="customDims">
            <input type="number" id="cw" placeholder="width px" min="1" />
            <input type="number" id="ch" placeholder="height px (optional)" min="1" />
          </div>
        </div>
        <div class="field">
          <label>Quality / compression <span class="info" tabindex="0" role="button" aria-label="What does quality / compression do?">i<span class="tip"><b>Sets file size vs. image quality.</b> Higher = sharper photos but bigger files. Lower = smaller files that load faster, but can look soft or blocky. <b>80–85 is the sweet spot</b> for most listings and photos.</span></span></label>
          <div class="range-row">
            <input type="range" id="quality" min="40" max="100" value="82" />
            <span class="qval" id="qval">82</span>
          </div>
        </div>
        <div class="field lock locked" id="wmField">
          <span class="lockbadge">PRO</span>
          <label>Watermark text</label>
          <div class="inner">
            <input type="text" id="wmText" placeholder="e.g. @yourshop" />
          </div>
        </div>
      </div>

      <div class="action-bar">
        <button class="btn-primary" id="processBtn" disabled>Process photos</button>
        <button class="btn-ghost" id="clearBtn" disabled>Clear</button>
        <span class="filecount" id="fileCount">No photos selected</span>
      </div>
      <div class="bar" id="bar"><div id="barFill"></div></div>
    </div>

    <div class="card results" id="resultsCard" style="display:none">
      <div class="results-head">
        <h3 style="margin:0">Done ✨ <span id="resCount" style="color:var(--muted);font-weight:600"></span></h3>
        <button class="btn-primary" id="downloadAll">⬇ Download all (.zip)</button>
      </div>
      <div class="grid" id="grid"></div>
    </div>
  </div>

  <section class="features">
    <div class="feat"><div class="ico">\U0001F4F1</div><h4>HEIC → JPG, instantly</h4><p>iPhones save photos as HEIC, which eBay, Amazon, and many desktop uploads reject. Convert in one click.</p></div>
    <div class="feat"><div class="ico">\U0001F4D0</div><h4>Marketplace presets</h4><p>One-tap resizing tuned for Etsy, eBay, Amazon, Poshmark, and Instagram.</p></div>
    <div class="feat"><div class="ico">\U0001F5DC️</div><h4>Smart compression</h4><p>Shrink file size so listings load fast — without making photos look bad.</p></div>
    <div class="feat"><div class="ico">\U0001F6E1️</div><h4>Strips GPS & metadata</h4><p>Re-encoding removes the hidden location data in your photos before you post them publicly.</p></div>
  </section>

  <section class="faq">
    <h2>%%FAQ_TITLE%%</h2>
%%FAQ%%
  </section>
</div>

<footer>
  <div>\U0001F4F8 <b>ListReady</b> — built for online sellers. Runs 100% in your browser.</div>
  <div style="margin-top:6px">Photo guides: <a href="etsy.html">Etsy</a> · <a href="ebay.html">eBay</a> · <a href="amazon.html">Amazon</a> · <a href="poshmark.html">Poshmark</a> · <a href="windows.html">Open on Windows</a> · <a href="video.html">iPhone Video → MP4</a></div>
  <div style="margin-top:6px">No account · no uploads · no tracking of your images.</div>
</footer>

<div class="modal-bg" id="proModal">
  <div class="modal">
    <button class="close" id="closePro">×</button>
    <h2>ListReady Pro</h2>
    <p style="color:var(--muted);margin:0">One-time payment. Yours forever. No subscription.</p>
    <div class="price">$9 <small>one time</small></div>
    <ul class="pro-list">
      <li>Unlimited photos per batch (Free caps at 15)</li>
      <li>WEBP output — up to 35% smaller files</li>
      <li>Custom text watermark on every photo</li>
      <li>Support an indie tool that respects your privacy</li>
    </ul>
    <a id="buyBtn" class="btn-gold" style="display:block;text-align:center;text-decoration:none;padding:12px" href="#" target="_blank" rel="noopener">Get Pro on Gumroad →</a>
    <div style="margin-top:18px;border-top:1px solid var(--line);padding-top:14px">
      <label style="font-size:13px;font-weight:700;color:var(--muted)">Already bought? Enter your license key:</label>
      <div class="license-row">
        <input type="text" id="licenseInput" placeholder="XXXXXXXX-XXXXXXXX-..." />
        <button class="btn-primary" id="activateBtn">Activate</button>
      </div>
      <div class="msg" id="licenseMsg"></div>
    </div>
  </div>
</div>

<div class="toast" id="toast"></div>

<script src="https://cdn.jsdelivr.net/npm/heic2any@0.0.4/dist/heic2any.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>
<script src="app.js"></script>
</body>
</html>
"""

def faq(items):
    out = []
    for q, a in items:
        out.append('    <details><summary>%s</summary><p>%s</p></details>' % (q, a))
    return "\n".join(out)

home_faq = faq([
    ("How do I convert an iPhone HEIC photo to JPG?", "Drop your HEIC files above, choose “JPG” as the output format, and click Process. ListReady decodes the HEIC right in your browser and gives you standard JPG files you can upload anywhere."),
    ("Are my photos uploaded anywhere?", "No. Everything runs locally in your browser using your device’s own processor. Your images never touch a server, which is why it’s free and private."),
    ("What image size should I use for Etsy / eBay / Amazon?", "Etsy recommends about 2000px on the shortest side; eBay and Amazon want 1600px or larger on the longest side to unlock zoom; Poshmark displays squares around 1200px. Use the preset dropdown and we’ll handle it."),
    ("Does it remove location data from my photos?", "Yes. Because we re-encode each image, hidden EXIF data — including GPS coordinates — is stripped automatically, so you don’t broadcast where a photo was taken."),
    ("What’s the difference between Free and Pro?", "Free handles up to 15 photos per batch with JPG/PNG output. Pro unlocks unlimited batches, WEBP output, and custom watermarks — a one-time payment, no subscription."),
])

etsy_faq = faq([
    ("What size should Etsy listing photos be?", "Etsy recommends at least 2000px on the shortest side. A square 2000×2000px image is a safe, consistent choice that displays well everywhere on Etsy. Pick the “Etsy — 2000px” preset above."),
    ("My iPhone HEIC photos won’t upload to Etsy — why?", "Etsy does accept HEIC, but uploads still fail sometimes from a desktop browser or when the file is over ~1MB. The reliable fix is to convert to JPG and keep it under 1MB (or upload from the Etsy app). JPG always works — drop your files above and export JPG."),
    ("Why do my Etsy photos look blurry or pixelated?", "Usually they were uploaded too small or over-compressed. Use 2000px and keep the quality slider high (80+)."),
    ("How do I keep Etsy photos under the file-size limit?", "Etsy loads fastest when each image is under about 1MB. Lower the quality slider until the output size drops below 1MB — you’ll see the new size on each result."),
    ("Are my product photos uploaded to a server?", "Never. ListReady processes everything in your browser, so your photos stay on your device."),
])

ebay_faq = faq([
    ("What is the best photo size for eBay listings?", "eBay requires at least 500px on the longest side, but 1600px on the longest side is the recommended best practice — it unlocks eBay’s zoom feature and looks sharp on mobile. Use the “eBay / Amazon — 1600px” preset."),
    ("Does eBay support iPhone HEIC photos?", "It’s unreliable — convert HEIC to JPG first to avoid failed or rotated uploads. Drop your files above and choose JPG."),
    ("How do I enable zoom on my eBay photos?", "eBay’s zoom only activates on images 1600px or larger on the longest side. Resize to 1600px here and zoom will work."),
    ("What aspect ratio works best on eBay?", "Square (1:1) images fit cleanly in eBay’s search grid and listing view. Shoot or crop square when you can."),
    ("Are my photos uploaded anywhere?", "No — everything is processed locally in your browser. Nothing is sent to a server."),
])

amazon_faq = faq([
    ("What are Amazon’s product image size requirements?", "Amazon needs at least 1000px on the longest side, and 1600px or larger to enable zoom (recommended). Use the “eBay / Amazon — 1600px” preset above. Maximum is 10,000px."),
    ("What background does Amazon require for the main image?", "The main image must have a pure white background — exactly RGB (255, 255, 255) — with the product filling about 85% of the frame. ListReady resizes and converts your photo, but it does not change the background, so shoot or edit on white for your main image."),
    ("Does Amazon accept HEIC images?", "No. Amazon accepts JPEG, PNG, TIFF, and GIF (no HEIC, no animated GIFs). Convert your iPhone HEIC files to JPG here first."),
    ("Why was my Amazon image rejected or suppressed?", "Common causes: too small (under 1000px), wrong format (HEIC), or a non-white main-image background. This tool fixes size and format — resize to 1600px and export JPG."),
    ("Are my photos uploaded to a server?", "No. Processing happens entirely in your browser; your images never leave your device."),
])

poshmark_faq = faq([
    ("What size should Poshmark photos be?", "Poshmark displays listing photos as squares, so shoot or crop square. Around 1200px square keeps them crisp without huge files — use the “Poshmark / Mercari — 1200px” or “Instagram square — 1080×1080” preset."),
    ("Can I upload iPhone HEIC photos to Poshmark?", "Convert them to JPG first to avoid upload errors. Drop your HEIC files above and export JPG."),
    ("How many photos can I add to a Poshmark listing?", "Up to 16. Process them all at once here, then download the batch as a ZIP."),
    ("Will resizing remove the location data from my photos?", "Yes — re-encoding strips hidden EXIF/GPS data automatically, so you don’t reveal where a photo was taken when reselling."),
    ("Are my photos uploaded anywhere?", "No. Everything runs locally in your browser — private by design."),
])

windows_faq = faq([
    ("Why can’t Windows open my iPhone HEIC photos?", "HEIC is Apple’s photo format, and Windows doesn’t support it out of the box — you’d normally need a paid codec from the Microsoft Store. Converting your photos to JPG (or PNG) fixes it instantly: every version of Windows opens those with no extra software."),
    ("How do I convert HEIC to JPG on a Windows PC?", "Drop your HEIC files above, choose JPG (or PNG) as the output, click Process, and download. There’s nothing to install — it runs right in your browser on Chrome, Edge, or Firefox."),
    ("Is it really free? Do I need to install anything?", "100% free, no install, no account, no watermark. The whole thing runs in your browser."),
    ("Are my photos uploaded to a server?", "No — every photo is processed locally on your own PC. Your images never leave your computer, which is why it’s private and free."),
    ("Can I convert a whole folder of HEIC photos at once?", "Yes — drop a batch in and download them all as a single ZIP. (The free version handles up to 15 at a time.)"),
    ("What about iPhone videos (HEVC / .mov) that won’t play on Windows?", "An iPhone-video → MP4 converter is coming soon as a Pro feature, so Windows can play your clips without installing codecs. For now, this tool handles photos."),
])

pages = {
  "index.html": dict(
    title="ListReady — Free HEIC to JPG Converter & Image Resizer for Sellers (Etsy, eBay, Poshmark, Amazon)",
    desc="Convert iPhone HEIC photos to JPG, resize to Etsy/eBay/Amazon/Poshmark sizes, compress, and strip GPS data — 100% free and 100% in your browser. Your photos never get uploaded.",
    keywords="heic to jpg, convert heic, image resizer, etsy photo size, ebay photo resizer, compress images, remove exif, batch image converter, marketplace photo tool",
    ogtitle="ListReady — Free HEIC→JPG + Resizer for Online Sellers",
    canonical=SITE+"/", preset="1600",
    h1="Convert, resize, and compress your photos in seconds",
    sub="Convert <b>HEIC, PNG & WEBP to JPG</b>, resize for Etsy, eBay, Amazon &amp; Poshmark, compress, and strip GPS data — all free, right in your browser.",
    faq_title="Frequently asked questions", faq=home_faq),

  "etsy.html": dict(
    title="Free Etsy Photo Resizer & HEIC to JPG Converter (2000px) — ListReady",
    desc="Resize photos for Etsy to the recommended 2000px, convert iPhone HEIC to JPG, and compress under 1MB — free and 100% in your browser. Nothing uploaded.",
    keywords="etsy photo size, etsy listing image size, resize photos for etsy, etsy heic to jpg, etsy 2000px, etsy image requirements",
    ogtitle="Free Etsy Photo Resizer & HEIC→JPG Converter",
    canonical=SITE+"/etsy.html", preset="2000",
    h1="Resize your photos for Etsy in seconds",
    sub="Convert iPhone <b>HEIC → JPG</b>, resize to Etsy’s recommended <b>2000px</b>, and compress under 1MB — free, private, in your browser.",
    faq_title="Etsy photo questions", faq=etsy_faq),

  "ebay.html": dict(
    title="Free eBay Photo Resizer & HEIC to JPG Converter (1600px Zoom) — ListReady",
    desc="Resize photos for eBay to 1600px to unlock zoom, convert iPhone HEIC to JPG, and compress — free and 100% in your browser. Nothing uploaded.",
    keywords="ebay photo size, ebay image resizer, resize photos for ebay, ebay heic to jpg, ebay 1600px zoom, ebay image requirements",
    ogtitle="Free eBay Photo Resizer & HEIC→JPG Converter",
    canonical=SITE+"/ebay.html", preset="1600",
    h1="Resize your photos for eBay in seconds",
    sub="Convert iPhone <b>HEIC → JPG</b>, resize to <b>1600px</b> to unlock eBay zoom, and compress — free, private, in your browser.",
    faq_title="eBay photo questions", faq=ebay_faq),

  "amazon.html": dict(
    title="Free Amazon Product Image Resizer & HEIC to JPG Converter (1600px) — ListReady",
    desc="Resize Amazon product photos to 1600px+ for zoom and convert iPhone HEIC to JPG — free and 100% in your browser. Nothing uploaded.",
    keywords="amazon product image size, amazon image requirements, resize amazon photos, amazon heic to jpg, amazon 1600px zoom, amazon image specs",
    ogtitle="Free Amazon Product Image Resizer & HEIC→JPG Converter",
    canonical=SITE+"/amazon.html", preset="1600",
    h1="Resize your product photos for Amazon in seconds",
    sub="Convert iPhone <b>HEIC → JPG</b> and resize to Amazon’s recommended <b>1600px+</b> for zoom — free, private, in your browser.",
    faq_title="Amazon photo questions", faq=amazon_faq),

  "poshmark.html": dict(
    title="Free Poshmark Photo Resizer & HEIC to JPG Converter (Square) — ListReady",
    desc="Resize photos for Poshmark to square, convert iPhone HEIC to JPG, and strip location data — free and 100% in your browser. Nothing uploaded.",
    keywords="poshmark photo size, poshmark image resizer, resize photos for poshmark, poshmark heic to jpg, poshmark square photos, mercari photo size",
    ogtitle="Free Poshmark Photo Resizer & HEIC→JPG Converter",
    canonical=SITE+"/poshmark.html", preset="1200",
    h1="Resize your photos for Poshmark in seconds",
    sub="Convert iPhone <b>HEIC → JPG</b>, crop to <b>square</b> for Poshmark, and strip location data — free, private, in your browser.",
    faq_title="Poshmark photo questions", faq=poshmark_faq),

  "windows.html": dict(
    title="Open iPhone HEIC Photos on Windows — Free HEIC to JPG Converter | ListReady",
    desc="Can’t open iPhone HEIC photos on Windows? Convert HEIC to JPG or PNG right in your browser so any Windows PC can view them — free, instant, nothing uploaded.",
    keywords="open heic on windows, view heic on windows, heic to jpg windows, can't open heic, iphone photos won't open on windows, heic viewer, convert heic windows free, heic windows 10 11",
    ogtitle="Open iPhone HEIC Photos on Windows — Free Converter",
    canonical=SITE+"/windows.html", preset="0",
    h1="Open iPhone HEIC photos on Windows",
    sub="Got <b>HEIC</b> photos from an iPhone that Windows won’t open? Convert them to <b>JPG or PNG</b> in seconds so any PC can view them — free, private, in your browser.",
    faq_title="HEIC on Windows questions", faq=windows_faq),
}

for fname, p in pages.items():
    html = TEMPLATE
    html = html.replace("%%TITLE%%", p["title"])
    html = html.replace("%%DESC%%", p["desc"])
    html = html.replace("%%KEYWORDS%%", p["keywords"])
    html = html.replace("%%OGTITLE%%", p["ogtitle"])
    html = html.replace("%%CANONICAL%%", p["canonical"])
    html = html.replace("%%GSC_META%%", "")  # filled later for index after Search Console
    html = html.replace("%%H1%%", p["h1"])
    html = html.replace("%%SUB%%", p["sub"])
    html = html.replace("%%NAV%%", NAV)
    html = html.replace("%%PRESET_OPTIONS%%", preset_select(p["preset"]))
    html = html.replace("%%FAQ_TITLE%%", p["faq_title"])
    html = html.replace("%%FAQ%%", p["faq"])
    open(fname, "w", encoding="utf-8").write(html)
    print("wrote", fname, len(html), "bytes")

# sitemap + robots
urls = [SITE+"/", SITE+"/etsy.html", SITE+"/ebay.html", SITE+"/amazon.html", SITE+"/poshmark.html", SITE+"/windows.html", SITE+"/video.html"]
sm = ['<?xml version="1.0" encoding="UTF-8"?>',
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for u in urls:
    sm.append("  <url><loc>%s</loc><changefreq>weekly</changefreq><priority>%s</priority></url>" % (u, "1.0" if u.endswith("/") else "0.8"))
sm.append("</urlset>")
open("sitemap.xml", "w", encoding="utf-8").write("\n".join(sm) + "\n")
open("robots.txt", "w", encoding="utf-8").write("User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n" % SITE)
print("wrote sitemap.xml, robots.txt (style.css & app.js left untouched)")
