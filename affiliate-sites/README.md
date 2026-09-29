# affiliate-sites

Five independent static review sites, one folder each. No build step, no
frameworks, no external requests — open any `index.html` in a browser, or
serve a folder as-is.

## Sites

| Folder | Niche | Pages |
| --- | --- | --- |
| `hvac-tools/` | HVAC contractor software and equipment | 10 (9 reviews + homepage) |
| `roofing-tools/` | Roofing contractor software and materials | 10 (9 reviews + homepage) |
| `plumbing-tools/` | Plumbing business software and supply | 10 (9 reviews + homepage) |
| `pool-service-tools/` | Pool service software and chemistry | 10 (9 reviews + homepage) |
| `electrical-tools/` | Electrical contractor software and testing gear | 10 (9 reviews + homepage) |
| **Total** | | **50** |

## Structure

```
affiliate-sites/
  <site>/
    index.html      comparison table + in-page search
    style.css       per-site colour scheme
    reviews/
      <tool>.html   one review per tool
```

## Before publishing

1. **Affiliate links.** Every review has a placeholder
   `<a class="btn" href="#">`, marked with an HTML comment. Replace each
   `href` with your affiliate URL. They already carry
   `rel="nofollow sponsored noopener"`.
2. **Verify prices.** Starting prices are rounded public figures and move.
   Quote-only vendors are marked as such. Check before publishing.
3. **Keep the disclosures.** The FTC banner is in the header of every page
   and the Amazon Associates statement is in every footer. Both are
   required and should stay above and below the fold respectively.

## Deliberately absent

No star ratings, scores, review counts, testimonials, awards, credentials,
or earnings claims anywhere in the set. None of it is verified, so
publishing it would be false advertising. Each review carries a short note
saying so.
