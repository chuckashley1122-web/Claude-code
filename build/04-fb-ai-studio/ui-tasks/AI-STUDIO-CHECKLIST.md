# AI Studio checklist (human, in GHL > AI Studio)

## 1. Generate
- [ ] AI Studio > New Project.
- [ ] Paste the fill script from out/landing/ai_studio_prompt_pack.md above the mega-prompt body (body is NEEDS_EVIDENCE: never supplied).
- [ ] Generate; review against out/landing/content_spec.md and the static mock out/landing/index.html.

## 2. The seven iteration prompts (5-7 changes per round max)
- [ ] Change 1 - logo/colors: `Update the logo and follow the colors from the logo to use in the page`
- [ ] Change 2 - images after hero: `Update these images in the section after the hero section on the landing page`
- [ ] Change 3 - hero background: `Use the attached image in the background of the hero section. Maintain an overlay that has the left and right elements of the hero section stand out. At same time we should be able to see a glimpse of background image.`
- [ ] Change 4 - multi-change: `Remove the image from over the form on the right side of hero. Make logo on header 1.8 times bigger. Add 2-3 navigation menu items on header right side of logo to take us to different sections of page. On left side of phone call option in header add a Google review badge with number of reviews and average rating.`
- [ ] Change 5 - header: `Make header wider and change background to light background`
- [ ] Change 6 - mobile fix: `Remove phone number from header, centralize logo on mobile, fix hero button layout`
- [ ] Change 7 - connect form to CRM: `Connect or integrate the form on the landing page to my CRM`

Skip the review-badge sentence and the before/after images until verified data exists. The logo/colour prompt applies to the page only; paid ad creatives never lead with the logo.

## 3. Connect form to CRM
- [ ] Prompt: 'Connect or integrate the form on the landing page to my CRM' > click Connect > wait.
- [ ] Submit a test (example.com email, 555-01xx phone) and confirm the contact appears with attribution.

## 4. Publish
- [ ] Install pixel via the chat prompt (code from Events Manager).
- [ ] Publish > Publish Changes > Add Custom Domain (see DNS-CHECKLIST.md).
- [ ] Publishing the page: REQUIRES EXPLICIT HUMAN APPROVAL.
