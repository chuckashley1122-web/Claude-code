# Home-page "Upgrade Your Listing" Section

Two plans live in SmartDirectoryAI today:

| Plan | Monthly | Annual | Role |
|------|---------|--------|------|
| **Community Listing** | $0 | $0 | Free tier — default for new sign-ups |
| **Local Spotlight** | $29 | $299 | Paid upgrade ($49/yr savings) |

Below are three formats for the upgrade section. Use whichever matches the editor SmartDirectoryAI gives you (Page Builder block, rich-text, or raw HTML).

---

## OPTION A — Copy only (paste into a rich-text / Page Builder block)

> **Section heading**
> ## Get Found by More Austin Customers
>
> **Sub-heading**
> Pick the listing that fits your business. Upgrade any time — your data carries over.
>
> ---
>
> ### Community Listing — Free
> Perfect for getting on the map.
> - Business name, address & hours
> - One category & one photo
> - Map pin on city directory
> - Contact button
>
> **Button:** *List My Business Free* → links to **Add New Business** form
>
> ---
>
> ### Local Spotlight — $29/mo or $299/yr (save $49)
> For businesses that want to win local search.
> - Everything in Community, plus:
> - Up to 10 photos & a video header
> - Priority placement in search & category pages
> - Featured in the "Discover Our Free Listings" carousel on the home page
> - Reviews & lead-capture form
> - Monthly performance report
>
> **Button:** *Upgrade to Local Spotlight* → links to checkout / plan upgrade page
>
> ---
>
> *Cancel any time. No contract.*

---

## OPTION B — HTML block (paste into a Custom HTML / Code block)

Tailwind-flavored classes; falls back gracefully if Tailwind isn't loaded.

```html
<section style="padding:64px 16px;background:#f8fafc;">
  <div style="max-width:1100px;margin:0 auto;text-align:center;">
    <h2 style="font-size:32px;font-weight:700;margin:0 0 8px;color:#0f172a;">
      Get Found by More Austin Customers
    </h2>
    <p style="font-size:18px;color:#475569;margin:0 0 40px;">
      Pick the listing that fits your business. Upgrade any time — your data carries over.
    </p>

    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:24px;text-align:left;">

      <!-- Free plan -->
      <div style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:32px;display:flex;flex-direction:column;">
        <div style="font-size:14px;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:0.05em;">Community Listing</div>
        <div style="font-size:40px;font-weight:700;color:#0f172a;margin:8px 0 4px;">Free</div>
        <div style="color:#64748b;margin-bottom:24px;">Perfect for getting on the map.</div>
        <ul style="list-style:none;padding:0;margin:0 0 32px;color:#334155;line-height:1.8;">
          <li>✓ Business name, address &amp; hours</li>
          <li>✓ One category &amp; one photo</li>
          <li>✓ Map pin on city directory</li>
          <li>✓ Contact button</li>
        </ul>
        <a href="/add-business" style="margin-top:auto;display:inline-block;text-align:center;background:#fff;color:#0f172a;border:2px solid #0f172a;padding:14px 24px;border-radius:8px;font-weight:600;text-decoration:none;">
          List My Business Free
        </a>
      </div>

      <!-- Paid plan, highlighted -->
      <div style="background:#0f172a;color:#fff;border-radius:12px;padding:32px;display:flex;flex-direction:column;position:relative;box-shadow:0 10px 30px rgba(15,23,42,0.15);">
        <div style="position:absolute;top:-12px;right:24px;background:#22c55e;color:#fff;font-size:12px;font-weight:700;padding:4px 12px;border-radius:999px;text-transform:uppercase;letter-spacing:0.05em;">Most Popular</div>
        <div style="font-size:14px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:0.05em;">Local Spotlight</div>
        <div style="font-size:40px;font-weight:700;margin:8px 0 4px;">
          $29<span style="font-size:18px;font-weight:500;color:#94a3b8;">/mo</span>
        </div>
        <div style="color:#94a3b8;margin-bottom:24px;">or $299/yr — save $49</div>
        <ul style="list-style:none;padding:0;margin:0 0 32px;line-height:1.8;">
          <li>✓ Everything in Community, plus:</li>
          <li>✓ Up to 10 photos &amp; a video header</li>
          <li>✓ Priority placement in search</li>
          <li>✓ Featured on the home-page carousel</li>
          <li>✓ Reviews &amp; lead-capture form</li>
          <li>✓ Monthly performance report</li>
        </ul>
        <a href="/upgrade" style="margin-top:auto;display:inline-block;text-align:center;background:#22c55e;color:#0f172a;padding:14px 24px;border-radius:8px;font-weight:700;text-decoration:none;">
          Upgrade to Local Spotlight
        </a>
      </div>

    </div>

    <p style="color:#64748b;margin-top:24px;font-size:14px;">
      Cancel any time. No contract.
    </p>
  </div>
</section>
```

---

## OPTION C — Compact banner (above-the-fold ribbon under hero)

For a less-bulky placement right under the hero image:

```html
<div style="background:#22c55e;color:#0f172a;text-align:center;padding:16px;font-weight:600;">
  Want to stand out? <a href="/upgrade" style="color:#0f172a;text-decoration:underline;">Upgrade to Local Spotlight — $29/mo</a> and get featured on the home page.
</div>
```

---

## Where to place it on the home page

Recommended order (top → bottom):

1. Hero image + search bar *(already live)*
2. **NEW: Option C banner** (one-line upgrade nudge)
3. "Discover Our Free Listings" carousel *(already live)*
4. **NEW: Option A or B pricing section**
5. Existing categories / footer

That gives free visitors two touchpoints — a low-friction nudge near the hero, plus a full comparison further down once they've seen the listings in action.

---

## Setting the plans up in SmartDirectoryAI

From your screenshot you already have both plans defined under **SmartDirectoryAI → Settings → Price and Planning**. To wire them to the home-page buttons:

1. In **Price and Planning**, open **Local Spotlight** → copy the **plan slug or upgrade URL** (often `/upgrade?plan=local-spotlight` or similar).
2. Open **Community Listing** → confirm it's the **DEFAULT** plan so new sign-ups land on it automatically (yours already is).
3. In the home-page editor, paste the HTML above and update the two `href`s:
   - Free plan button → your **Add New Business** signup URL
   - Paid plan button → the **Local Spotlight checkout** URL from step 1
4. Under **Advanced Settings** on the Local Spotlight plan, double-check:
   - Trial days (0 if you don't want a trial)
   - Whether annual auto-applies the discount
   - Which features are gated to this plan (10-photo limit, featured-carousel flag, etc.) — these need to match the bullet points in the marketing copy.
5. Save, then test the full flow in an incognito window: visit home page → click **Upgrade** → make sure checkout shows $29/mo and $299/yr correctly.
