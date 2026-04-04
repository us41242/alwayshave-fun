#!/usr/bin/env node
/**
 * contact-sheet.js
 * Generates a printable HTML contact sheet of all trail photos.
 * Each image is 1.75 inches tall on 8x11.5 inch pages.
 *
 * Usage: node scripts/contact-sheet.js
 * Then open contact-sheet.html in Chrome and File → Print → Save as PDF
 */

const fs   = require('fs');
const path = require('path');

const PHOTOS_DIR = path.join(__dirname, '..', 'photos');
const OUT_FILE   = path.join(__dirname, '..', 'contact-sheet.html');

// Collect all hero photos (not -card, not LANDING)
function findHeroPhotos(dir) {
  const results = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    const slug    = entry.name;
    const folder  = path.join(dir, slug);
    // Prefer .webp hero, fall back to .jpg
    const webp = path.join(folder, `${slug}.webp`);
    const jpg  = path.join(folder, `${slug}.jpg`);
    if (fs.existsSync(webp)) {
      results.push({ slug, file: webp, rel: `photos/${slug}/${slug}.webp` });
    } else if (fs.existsSync(jpg)) {
      results.push({ slug, file: jpg,  rel: `photos/${slug}/${slug}.jpg` });
    }
  }
  return results.sort((a, b) => a.slug.localeCompare(b.slug));
}

function slugToTitle(slug) {
  return slug
    .replace(/-nv$|-ut$|-az$|-ca$|-co$|-nm$/, '')
    .split('-')
    .map(w => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
}

const photos = findHeroPhotos(PHOTOS_DIR);
console.log(`Found ${photos.length} hero photos`);

const rows = photos.map(p => `
  <figure>
    <img src="${p.rel}" alt="${slugToTitle(p.slug)}">
    <figcaption>${slugToTitle(p.slug)}</figcaption>
  </figure>`).join('');

const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>alwayshave.fun — Trail Photo Contact Sheet</title>
<style>
  @page {
    size: 8in 11.5in;
    margin: 0.35in;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: -apple-system, Helvetica, Arial, sans-serif;
    background: #fff;
    color: #111;
  }

  h1 {
    font-size: 11pt;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    border-bottom: 1px solid #ccc;
    padding-bottom: 4pt;
    margin-bottom: 10pt;
  }

  .grid {
    display: flex;
    flex-wrap: wrap;
    gap: 8pt;
  }

  figure {
    display: flex;
    flex-direction: column;
    gap: 2pt;
    break-inside: avoid;
  }

  figure img {
    height: 1.75in;
    width: auto;
    display: block;
    object-fit: cover;
    border: 0.5pt solid #ddd;
  }

  figcaption {
    font-size: 6.5pt;
    color: #444;
    text-align: center;
    max-width: 100%;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
</style>
</head>
<body>
  <h1>alwayshave.fun &mdash; Trail Photos &mdash; ${new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}</h1>
  <div class="grid">
    ${rows}
  </div>
</body>
</html>`;

fs.writeFileSync(OUT_FILE, html);
console.log(`\nContact sheet written to: contact-sheet.html`);
console.log('Open in Chrome → File → Print → Save as PDF');
