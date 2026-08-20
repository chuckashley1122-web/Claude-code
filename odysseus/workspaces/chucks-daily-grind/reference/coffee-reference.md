# Coffee reference — Chuck's Daily Grind

**Status:** DRAFT. Not yet approved. `approved: false` in the knowledge manifest.

The technical source of truth for coffee content. Every ratio, temperature, and
timing in a published guide should trace to this file — the
`coffee-seo-content` skill is built to refuse unsourced technical claims, and
this is the source it draws on.

**Two standing rules for everything below.**

1. **No health claims.** Nothing here supports one. Coffee tastes good; that is
   the claim. See `../system-prompt.md` for the boundary.
2. **These are starting points, not laws.** Coffee is full of confidently
   repeated folklore. Ranges are given because the right answer depends on the
   bean, the roast, the grinder, and the water. Content should say so rather
   than presenting one number as correct.

---

## 1. Brew ratios

Expressed as coffee-to-water by weight. A kitchen scale matters more to results
than most equipment upgrades — that is a defensible claim and a good article.

| Method | Ratio (coffee:water) | Grind | Time | Notes |
|---|---|---|---|---|
| Pour-over (V60, Kalita, Chemex) | 1:15 – 1:17 | Medium-fine to medium | 2:30 – 4:00 | Chemex suits the coarser end of the range; its thicker filter slows flow |
| French press | 1:12 – 1:15 | Coarse | 4:00 steep | Break the crust, skim, then plunge slowly |
| Espresso | 1:2 (dose:yield) | Fine | 25 – 30 s | Roughly 9 bar. A "ristretto" pulls shorter, a "lungo" longer |
| AeroPress | 1:12 – 1:16 | Medium-fine | 1:00 – 2:00 | Enormously variable by recipe; state the recipe used |
| Moka pot | 1:10 – 1:12 | Fine-medium, coarser than espresso | 4 – 5 min on low | Preheated water in the base reduces the risk of scorching |
| Cold brew concentrate | 1:5 – 1:8 | Coarse | 12 – 24 h | Dilute to taste, commonly around 1:1 |
| Cold brew ready-to-drink | 1:15 – 1:17 | Coarse | 12 – 18 h | No dilution intended |
| Batch brewer | 1:16 – 1:18 | Medium | Machine-dependent | Verify the machine actually reaches brew temperature |

A widely used starting point is **60 g of coffee per litre of water** (about
1:16.7), which sits inside the pour-over and batch ranges above.

---

## 2. Water

**Temperature.** 195–205 °F (90–96 °C) is the standard brewing range. Off-boil
water rested about 30 seconds lands in it. Lighter roasts generally tolerate the
top of the range; darker roasts can taste harsh there.

**Cold brew** is the exception — the long contact time replaces heat, and the
lower-temperature extraction is why the result tastes different, not merely
colder.

**Water chemistry.** Water is more than 98% of the cup, and hard or heavily
treated water is a common hidden cause of disappointing coffee.

- Total dissolved solids: roughly 150 ppm is a common target, with a workable
  band either side.
- Some calcium hardness aids extraction; too much causes scale.
- Alkalinity buffers acidity — high alkalinity flattens the cup and makes bright
  coffees taste dull.
- Distilled or zero-TDS water extracts poorly. Minerals are doing work.

For most people the practical advice is a simple carbon filter, and a note that
very hard tap water is worth addressing before buying better beans.

**Extraction targets.** The commonly cited window is roughly **18–22%**
extraction yield with a brew strength around **1.15–1.35% TDS**. Under-extracted
coffee reads sour, thin, and salty; over-extracted reads bitter, hollow, and
drying. Most home brewing problems are one of those two, and grind size is
usually the lever.

---

## 3. Grind

Grind size is the primary variable once ratio and temperature are set.

| Setting | Comparable to | Methods |
|---|---|---|
| Extra coarse | Peppercorns | Cold brew |
| Coarse | Sea salt | French press |
| Medium-coarse | Rough sand | Chemex, some batch |
| Medium | Sand | Pour-over, batch, drip |
| Medium-fine | Fine sand | AeroPress, some pour-over |
| Fine | Powdered sugar, slightly gritty | Espresso, moka |
| Extra fine | Flour | Turkish |

**Burr vs blade.** Burr grinders produce a consistent particle size; blade
grinders chop unevenly, so the same brew simultaneously over-extracts fines and
under-extracts boulders. This is the single most defensible equipment
recommendation in coffee — and it is also where content should avoid gatekeeping:
an inexpensive hand burr grinder outperforms an expensive blade grinder.

**Troubleshooting, in one line each.** Sour, weak, brews too fast → grind finer.
Bitter, harsh, brews too slow → grind coarser. Change one variable at a time.

---

## 4. Processing methods

How the fruit is removed from the seed. Processing influences the cup as much as
origin does, and it is one of the most useful things to explain to customers.

**Washed (wet).** Fruit removed before drying, usually with a fermentation stage.
Produces the cleanest, most transparent expression of origin and varietal.
Typically brighter and more acidic. The reference point for most specialty
coffee.

**Natural (dry).** Cherry dried whole, with the seed inside the fruit. Fruit
sugars influence the seed during drying. Typically heavier bodied, sweeter, with
pronounced fruit — berry and tropical notes are common. Requires careful drying;
poorly executed naturals ferment unpleasantly.

**Honey / pulped natural.** Between the two: skin removed, some or all mucilage
left on during drying. Often subdivided by how much mucilage remains and how
much light the drying beds receive — white, yellow, red, and black, in ascending
order of mucilage retained and drying time. Generally sweet with softer acidity
than washed.

**Wet-hulled (giling basah).** Associated with Indonesia, particularly Sumatra.
Hulled at a higher moisture content than usual. Produces the low-acid, heavy,
earthy, herbal profile that reads as distinctly Sumatran.

**Anaerobic and carbonic maceration.** Fermentation in a sealed, oxygen-limited
vessel, sometimes under CO2 pressure. Produces intense, unusual, sometimes
polarizing profiles — heavy fruit, funk, occasionally boozy or cinnamon-like.
Modern, variable, and worth describing honestly: some people love these and some
find them overwhelming.

**Decaffeination** is a separate process, not a roast level:

- **Swiss Water** — water and carbon filtration, no added solvent. Commonly
  highlighted on labels.
- **EA (ethyl acetate), often called sugarcane** — a solvent naturally present
  in fruit, frequently used in Colombia.
- **CO2** — supercritical carbon dioxide, more common at commercial scale.

Decaf is not caffeine-free. Trace amounts remain under every method.

---

## 5. Origins

Broad regional characteristics. These are tendencies, not guarantees — a
specific lot can sit anywhere, and content should never assert a flavour for a
coffee that has not actually been tasted.

### Africa

**Ethiopia.** Widely regarded as coffee's origin. Regions include Yirgacheffe,
Sidamo, Guji, Limu, and Harrar. Frequently floral, citrus, and tea-like when
washed; berry-forward and jammy when natural. Much Ethiopian coffee comes from
indigenous varieties collectively described as heirloom rather than a single
named cultivar.

**Kenya.** Known for the SL28 and SL34 varieties. Typically intense, with
blackcurrant and a marked, structured acidity. Kenya grades by screen size —
**AA** denotes bean size, **not** quality, though the two are often correlated
and frequently confused in marketing copy.

**Rwanda and Burundi.** Often bright, floral, with clean acidity — Bourbon-derived
varieties are common.

### Central and South America

**Colombia.** Broad range by region and altitude. Commonly balanced, caramel
sweetness, moderate acidity, approachable. A frequent base for blends.

**Brazil.** The largest producer. Typically low-acid, nutty, chocolatey, heavy
bodied. Widely used in espresso blends for exactly those qualities.

**Guatemala.** Regions including Antigua and Huehuetenango. Often chocolate and
spice with a defined acidity.

**Costa Rica.** Clean and bright, with a strong honey-processing tradition.

**Panama.** Best known for Gesha from the Boquete region — floral, jasmine, tea-
like, and among the most expensive coffee sold at auction.

### Asia and Pacific

**Indonesia (Sumatra, Java, Sulawesi).** Wet-hulled Sumatran is earthy, herbal,
full bodied, low acid — distinctive and genuinely polarizing.

**Vietnam.** Predominantly Robusta, mostly commodity, though specialty
production is growing.

**Papua New Guinea.** Often fruit-forward with medium body.

**Yemen.** Historic origin, distinctive and often wine-like or dried-fruit
driven. Small production and correspondingly expensive.

---

## 6. Varieties

**Typica and Bourbon** — the two foundational Arabica lineages most others
descend from. Bourbon is generally regarded as sweeter; Typica as clean and
classic. Both are relatively low-yielding and disease-susceptible.

**Gesha (also spelled Geisha)** — Ethiopian in origin, made famous in Panama.
Distinctive floral and tea-like character. Low yield and high price.

**SL28 / SL34** — selections developed in Kenya, associated with that origin's
blackcurrant intensity.

**Caturra, Catuai, Mundo Novo** — productive Latin American cultivars derived
from Bourbon and Typica.

**Pacamara** — a large-beaned cross, often complex and unusual in the cup.

**Castillo and Colombia** — disease-resistant varieties widely planted in
Colombia. Their cup quality relative to older varieties is genuinely debated;
content should present that as a live discussion rather than settled.

**Arabica vs Robusta.** Arabica dominates specialty: more aromatic complexity,
higher acidity, and roughly half the caffeine of Robusta. Robusta is hardier and
higher-yielding, with a heavier, more bitter, rubbery profile — though
well-produced fine Robusta exists and the blanket dismissal of it in marketing
copy is lazier than it is accurate.

---

## 7. Roast levels

Roast level describes development, not bean strength.

**Light.** Dropped around or shortly after first crack. Retains the most origin
character — acidity, florals, fruit. Dense, and generally needs a finer grind and
hotter water.

**Medium.** Between first and second crack. Balances origin character against
roast-developed sweetness. Caramel and chocolate notes emerge.

**Dark.** At or past second crack. Roast character dominates origin: bittersweet,
smoky, heavy. Oils appear on the surface. Distinctions between origins narrow.

Two corrections worth writing content about, because both are widely believed
and both are wrong:

- **Dark roast is not stronger in caffeine.** By weight, caffeine is roughly
  comparable across roast levels — and because darker beans are less dense, a
  scoop of dark roast can contain slightly *less* caffeine than the same scoop
  of light. Measuring by weight rather than volume removes the difference.
- **Oily beans do not mean fresh beans.** Surface oil indicates roast level, not
  freshness.

---

## 8. Freshness and storage

**Degassing.** Freshly roasted coffee releases CO2. Most coffee is best from
roughly **3 to 14 days** after roast, with espresso often preferring the later
part of that window. Too fresh and extraction is uneven and gassy.

**Roast date, not best-before.** A roast date on the bag is the meaningful
signal. A best-before date a year out says nothing useful.

**Storage.** Airtight, at room temperature, away from light, heat, and moisture.
One-way valve bags exist precisely to let CO2 out without letting oxygen in.

**Refrigerator: no.** Temperature cycling causes condensation, and coffee readily
takes on surrounding odours.

**Freezer: genuinely debated.** Freezing well-sealed beans in single-use portions
and never refreezing has support. Repeatedly removing a bag from the freezer does
not. Present it as an open question, because it is.

**Whole bean vs pre-ground.** Ground coffee stales dramatically faster — vastly
more surface area exposed to oxygen. This is the highest-impact freshness advice
there is, and it costs the customer nothing.

---

## 9. Grading and terminology

**SCA cupping score.** The Specialty Coffee Association's 100-point scale. A
score of **80 and above** is the conventional threshold for "specialty."
Anything at 90+ is exceptional and rare.

**Never claim a score for a coffee that has not been formally cupped and
scored.** An invented score is a fabricated certification.

**Certifications** — organic, Fair Trade, Rainforest Alliance, Bird Friendly,
and direct trade relationships. Each has a specific meaning and, except for
direct trade, a specific certifying body. **Never claim a certification that is
not documented in the product catalogue.** Direct trade is not a certification;
it describes a sourcing relationship and is not independently verified.

**Single origin vs blend.** Single origin comes from one origin, and may be
narrowed further to a single region, farm, or lot. Blends combine coffees for a
target profile and consistency. Neither is inherently better — blends dominate
espresso for good reasons.

---

## 10. Caffeine

Content may state caffeine content **only where the figure is sourced**, and
should always frame it as approximate.

Caffeine per serving varies with dose, brew method, ratio, extraction, and
species. A brewed cup and an espresso shot differ substantially per serving even
though espresso is far more concentrated per millilitre — a distinction worth
explaining and frequently muddled.

**Beyond that, nothing.** No claims about focus, energy, metabolism, alertness,
health effects, tolerance, or interaction with any condition or medication. If a
customer asks a caffeine-and-health question, the answer is that we are not the
right people to answer it, and a pointer to a doctor. See
`../agents.md`, agent 4.

---

## Verify before approval

1. **Check the ratios and temperatures against your own brewing.** These are
   accepted general ranges, not Chuck's Daily Grind house recipes. If the house
   method differs, the house method wins and this file should say so.
2. Confirm the extraction and TDS windows against a current SCA reference if
   content will cite them as standards.
3. Confirm the water-chemistry targets before publishing specific numbers.
4. Confirm the caffeine section is narrow enough. It is deliberately the most
   restrictive section here.
5. Regional flavour profiles are tendencies. Confirm the framing prevents copy
   from asserting a profile for a specific untasted lot.
6. Decide the house position on freezing, or confirm that presenting it as
   debated is intended.
7. Confirm nothing in this file could be read as a health claim.
