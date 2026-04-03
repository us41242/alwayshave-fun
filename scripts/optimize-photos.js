#!/usr/bin/env node
/**
 * optimize-photos.js
 * Generates two WebP variants from each source JPEG:
 *   {slug}.webp      — 2000px wide, hero/full-page use
 *   {slug}-card.webp — 800×320px, center-cropped, card thumbnails
 *
 * Originals (.jpg) are left untouched.
 * Usage: node scripts/optimize-photos.js
 */

const sharp = require('sharp');
const path  = require('path');
const fs    = require('fs');

const PHOTOS_DIR   = path.join(__dirname, '..', 'photos');
const HERO_WIDTH   = 2000;
const CARD_WIDTH   = 800;
const CARD_HEIGHT  = 320;
const WEBP_QUALITY = 82;

function findJpegs(dir, results = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      findJpegs(full, results);
    } else if (/\.(jpg|jpeg)$/i.test(entry.name) && !entry.name.includes('-card')) {
      results.push(full);
    }
  }
  return results;
}

function isUpToDate(src, dest) {
  if (!fs.existsSync(dest)) return false;
  return fs.statSync(dest).mtimeMs >= fs.statSync(src).mtimeMs;
}

async function optimise(src) {
  const base     = src.replace(/\.(jpg|jpeg)$/i, '');
  const heroDest = base + '.webp';
  const cardDest = base + '-card.webp';
  const rel      = path.relative(PHOTOS_DIR, src);

  const heroSkip = isUpToDate(src, heroDest);
  const cardSkip = isUpToDate(src, cardDest);

  if (heroSkip && cardSkip) {
    console.log(`  skip  ${rel} (both up to date)`);
    return;
  }

  const srcKB = Math.round(fs.statSync(src).size / 1024);

  if (!heroSkip) {
    await sharp(src)
      .resize({ width: HERO_WIDTH, withoutEnlargement: true })
      .webp({ quality: WEBP_QUALITY })
      .toFile(heroDest);
    const heroKB = Math.round(fs.statSync(heroDest).size / 1024);
    console.log(`  ✓ hero  ${rel}  ${srcKB}KB → ${heroKB}KB`);
  }

  if (!cardSkip) {
    await sharp(src)
      .resize({ width: CARD_WIDTH, height: CARD_HEIGHT, fit: 'cover', position: 'center' })
      .webp({ quality: WEBP_QUALITY })
      .toFile(cardDest);
    const cardKB = Math.round(fs.statSync(cardDest).size / 1024);
    console.log(`  ✓ card  ${rel}  ${srcKB}KB → ${cardKB}KB  [${CARD_WIDTH}×${CARD_HEIGHT}]`);
  }
}

(async () => {
  const jpegs = findJpegs(PHOTOS_DIR);
  console.log(`Found ${jpegs.length} JPEG(s) in photos/\n`);

  let ok = 0, failed = 0;
  for (const src of jpegs) {
    try {
      await optimise(src);
      ok++;
    } catch (err) {
      console.error(`  ✗  ${src}\n     ${err.message}`);
      failed++;
    }
  }

  console.log(`\nDone. ${ok} processed${failed ? `, ${failed} failed` : ''}.`);
})();
