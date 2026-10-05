# UI work order 003-B: Prepare (do not launch) the Meta lead form and NEW draft campaign

**Spec:** SPEC-03 (High-Ticket Agency). **Build root:** `build/03-high-ticket/`. **Owner:** Chuck Ashley.
**Why a human:** Meta Ads Manager and image tools need a logged-in browser.

**The live campaign `CAJ_HVAC27_US_PURCHASE_TEST02` is FROZEN. Do not edit, pause, or duplicate it. Build the new campaign as a
separate NEW draft, because editing resets Meta's learning phase.**

## Steps

Follow `build/03-high-ticket/ui-tasks/META-BUILD-CHECKLIST.md`. In summary:

1. Generate the five ad images (1080x1350 plus a 1080x1080 crop each) from the `image_prompt` in `out/creatives/A01.json` ... `A05.json`.
   The headline or offer leads; the CA-J logo is only a small footer.
2. Create the Instant Form: question "Do you own or make marketing decisions for an HVAC company?", Yes continues, No ends.
   Qualified ending button "Book a time" links to https://ca-jenterprises.com/ai. Use the real privacy policy URL only.
3. Create a NEW campaign named `CAJ-HT-HVAC-Leads-<YYYYMMDD>`, objective Leads, Instant Forms, status PAUSED.
4. Add one ad set and five ads using `out/copy/A01.md` ... `A05.md`. Check every preview on mobile.
5. Leave the daily budget unset.

## Approval gates

Daily budget, test cap, payment method, any image tool purchase, and launch: REQUIRES EXPLICIT HUMAN APPROVAL.
`AD_SPEND_CAP_USD` stays 0 until a written amount is approved.

## Done when

The form and the paused draft campaign exist, all five previews are checked, and nothing is running.
