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

## Structure

```
kentbates-site/
├── index.html, gallery.html, about.html, shop.html, contact.html
├── css/style.css        # full design system (tokens, components, responsive)
├── js/main.js           # mobile nav, scroll reveal, gallery filter, form, prefill
├── assets/art/          # drop real artwork images here (see below)
├── robots.txt
├── sitemap.xml
└── README.md
```

## Replacing the placeholder artwork

The gallery and product tiles currently use **CSS gradient placeholders** (the
`.art-fill` element with classes like `.c-space`, `.c-fame`). When you have real
artwork, swap each placeholder for an image:

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

## Notes & next steps

- **Contact form** uses a `mailto:` fallback so it works on any static host
  (GitHub Pages, Netlify, etc.). To capture submissions without opening an email
  client, point the `<form>` at a service like Formspree/Netlify Forms.
- **Real e-commerce checkout** isn't included (static site). The shop uses an
  "inquire to buy" flow that prefills the contact form. To take payments, embed
  Shopify Buy Buttons, Stripe Payment Links, or Gumroad on the product cards.
- All copy is editable directly in the HTML. Prices, titles and edition sizes are
  placeholders — update them to match real inventory.
- Colors, fonts and spacing live as tokens at the top of `css/style.css`.
