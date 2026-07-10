# Strategy — living document

Maintained by the autonomous operator (see /AUTONOMY.md). Rewrite freely; LOGBOOK.md holds history, this holds the present.

## Current strategy

(First session: assess the site and GSC data, then write the initial strategy here.)

## Target queries / experiments in flight

(none yet)

## Distribution accounts

(none yet — log platform, handle, credential location for every account created)

## Free-services ledger

| Service | What for | Free-tier ceiling | Current usage |
|---|---|---|---|
| Cloudflare (Workers/Pages) | hosting + deploys | verify quota first session | ~48 data commits/day trigger deploys — confirm this fits the free build quota |
| GitHub Actions | data pipeline cron | 2,000 min/mo (private repo) | fetch_conditions every 30 min |
| Open-Meteo | weather + AQI fallback | non-commercial free | every 30 min |
| AirNow | AQI | free API key | every 30 min |
| NASA FIRMS | fire data | free | every 30 min |
| Gemini (writer bot) | drafts | free tier | 1/day |
| Brevo | subscriber email | 300 emails/day | idle |
