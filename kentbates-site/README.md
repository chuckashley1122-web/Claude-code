# Kent Bates — Website

A redesigned, conversion-focused website for **kentbates.com**, the portfolio and
shop of surreal pop-collage artist **Kent Bates**. Built as a fast, responsive,
static site (plain HTML, CSS and a little vanilla JS — no build step, no dependencies).

This site was built using the prompt methodology in the reference screenshots:
**Blueprint → Content → High-converting Homepage → Full HTML/CSS → Landing/Shop →
Design review → SEO + Final audit.**

## Pages

| File | Purpose |
| --- | --- |
| `index.html` | High-converting homepage: hero, featured collections, about teaser, shop preview, commission CTA |
| `gallery.html` | Filterable gallery of works (Space / Fame / Money / Studio) |
| `about.html` | Artist statement, process, materials, influences, history |
| `shop.html` | Originals, limited prints and merch with inquire-to-buy flow |
| `contact.html` | Contact + commission form (mailto-based, works on any static host) |
| `collection-man-vs-nature.html` · `collection-the-studio.html` · `collection-icons-idols.html` | Individual collection pages, each with its own gallery + lightbox |
| `faq.html` | Buying / shipping / returns / commissions FAQ (accordion + FAQ schema) |
| `404.html` | Branded not-found page (set as the host's error page) |

**Gallery lightbox:** any page with a `.gallery-grid` automatically gets a
click-to-enlarge lightbox (keyboard accessible: Enter/Space to open, ← → to move,
Esc to close) — no per-page markup needed; it's built by `js/main.js`.

## Structure

```
kentbates-site/
├── index.html, gallery.html, about.html, shop.html, contact.html
├── 404.html             # branded error page
├── css/style.css        # full design system (tokens, components, responsive)
├── js/main.js           # mobile nav, scroll reveal, gallery filter, form, prefill
├── assets/
│   ├── art/             # 6 SVG collage placeholders (swap for real photos)
│   ├── favicon.svg      # brand mark (browser tab / bookmark icon)
│   └── og-cover.svg     # social share image (1200×630)
├── robots.txt
├── sitemap.xml
└── README.md
```

> **Theme:** blue / grey / green / white. All colors are tokens at the top of
> `css/style.css` (`--blue`, `--green`, `--grey`, plus canvas/ink), so reskinning
> is a few-line change.

> **Social image note:** `og-cover.svg` is a crisp placeholder. A few platforms
> only render raster share images — export it to a 1200×630 **PNG/JPG** and update
> the `og:image` URLs if you want maximum compatibility.

## Replacing the placeholder artwork

The gallery and product tiles currently use **handcrafted SVG collage placeholders**
in `assets/art/` (`space.svg`, `fame.svg`, `money.svg`, `icon.svg`, `retro.svg`,
`studio.svg`), wired up through the `.c-*` classes in `css/style.css`. They're
vector, so they stay crisp at any size.

Two ways to use real artwork when it's ready:

1. **Quick swap (keep the markup):** drop a real image over a theme by editing one
   line in `css/style.css`, e.g. `.c-space { --collage: url("../assets/art/space.jpg"); }`
2. **Best for SEO/accessibility (add an `<img>`):** the CSS already detects an
   `<img>` inside `.art-fill` and hides the placeholder layer automatically —

```html
<!-- before (placeholder) -->
<div class="art-fill c-space"><span class="label">Orbit / Decay · 2024</span></div>

<!-- after (real image) -->
<figure class="art-fill">
  <img src="assets/art/orbit-decay.jpg" alt="Orbit / Decay, mixed-media collage, 2024" />
  <span class="label">Orbit / Decay · 2024</span>
</figure>
```

Use descriptive `alt` text (good for SEO and accessibility). Also add a real
social-share image at `assets/og-cover.jpg` (≈1200×630) — it's referenced by the
Open Graph tags in `index.html`.

## Local preview

```bash
cd kentbates-site
python3 -m http.server 8000
# open http://localhost:8000
```

## Checkout (Stripe Payment Links)

The Shop's prints and merch have **Buy now** buttons wired for
[Stripe Payment Links](https://stripe.com/payments/payment-links) — no backend,
no code, works on any static host. Originals stay inquiry-only (they're 1-of-1).

Until you add real links, the buttons safely fall back to the inquiry form, so the
shop is never a dead end. To go live:

1. In your Stripe Dashboard, create a **Payment Link** for each product.
2. In `shop.html`, replace each placeholder `href="https://buy.stripe.com/REPLACE_…"`
   with the real link Stripe gives you (search the file for `REPLACE_`).
3. That's it — the JS in `js/main.js` automatically lets configured links through
   and only falls back for ones still containing `REPLACE_`.

Prefer something else? The same buttons work with **Gumroad** (overlay embed) or
**Shopify Buy Buttons** — just swap the `href`/embed on each card.

## Notes & next steps

- **Contact form** uses a `mailto:` fallback so it works on any static host
  (GitHub Pages, Netlify, etc.). To capture submissions without opening an email
  client, point the `<form>` at a service like Formspree/Netlify Forms.
- All copy is editable directly in the HTML. Prices, titles and edition sizes are
  placeholders — update them to match real inventory.
- Colors, fonts and spacing live as tokens at the top of `css/style.css`.
