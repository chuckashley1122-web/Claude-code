# Deploying the Kent Bates site

It's a plain static site (HTML/CSS/JS, no build step), so it hosts anywhere.
Pick one of the options below.

## Option A — Netlify (easiest, free)

A `netlify.toml` at the repo root is already configured (publish dir
`kentbates-site`, security + cache headers, automatic 404).

1. Go to [app.netlify.com](https://app.netlify.com) → **Add new site → Import an existing project**.
2. Connect this GitHub repo and pick the branch.
3. Leave build command empty; publish directory is read from `netlify.toml`.
4. Deploy. You'll get a `*.netlify.app` URL immediately.

**Drag-and-drop alternative:** zip the `kentbates-site/` folder and drop it on
the Netlify dashboard — live in seconds, no Git needed.

## Option B — GitHub Pages

GitHub Pages serves from the repo root or `/docs`, not an arbitrary subfolder,
so either:
- Move the contents of `kentbates-site/` to the repo root (or a `docs/` folder), **or**
- Add a deploy workflow that uploads `kentbates-site/` as the Pages artifact.

Then: repo **Settings → Pages → Build and deployment → Source: GitHub Actions**
(or **Deploy from a branch** if you moved files to root/`docs`).

## Option C — Any static host / Wix replacement

Upload the contents of `kentbates-site/` to any web host's public directory
(Cloudflare Pages, Vercel, S3 + CloudFront, traditional cPanel hosting, etc.).

## Pointing kentbates.com at it (custom domain)

1. In your host (e.g. Netlify → **Domain settings → Add custom domain**), add
   `kentbates.com` and `www.kentbates.com`.
2. At your domain registrar, update DNS as the host instructs — typically:
   - `CNAME` `www` → your host target, and an `ALIAS`/`A` record for the apex.
3. Enable HTTPS (Netlify/Cloudflare/Pages provision a free certificate automatically).
4. Because the site currently lives on **Wix**, you'll switch the domain's DNS
   away from Wix to the new host — do this once the new site is verified live on
   its temporary URL, to avoid downtime.

## Before going fully live — checklist

- [ ] Replace SVG placeholder artwork in `assets/art/` with real photos (see README).
- [ ] Paste real Stripe Payment Links in `shop.html` (search `REPLACE_`).
- [ ] Optionally export `assets/og-cover.svg` to a 1200×630 PNG for max social compatibility.
- [ ] Point the contact form at Formspree/Netlify Forms if you want inbox capture.
- [ ] Confirm prices, edition sizes and piece titles match real inventory.
