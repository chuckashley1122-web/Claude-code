# Meta build checklist

**The live campaign `CAJ_HVAC27_US_PURCHASE_TEST02` is FROZEN — do not edit, pause, or duplicate it; build any new campaign as a separate NEW draft, because editing resets Meta's learning phase.**

Every spend line is marked `REQUIRES EXPLICIT HUMAN APPROVAL`. Nothing is launched by this build.

### META-01 Meta Business portfolio: Page and ad account

- Object: Meta Business portfolio
- Field: Page and ad account
- Value: Page ID NEEDS_EVIDENCE, ad account NEEDS_EVIDENCE
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Both IDs recorded with evidence in config
- Status: Not started

### META-02 Ad account: Payment method

- Object: Ad account
- Field: Payment method
- Value: Do not add or change - REQUIRES EXPLICIT HUMAN APPROVAL
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: No new payment method
- Spend: REQUIRES EXPLICIT HUMAN APPROVAL
- Status: Not started

### META-03 Instant Form: Type

- Object: Instant Form
- Field: Type
- Value: More volume
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Form preview
- Status: Not started

### META-04 Instant Form: Question

- Object: Instant Form
- Field: Question
- Value: Do you own or make marketing decisions for an HVAC company?
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Preview shows exact question; Yes/No options
- Status: Not started

### META-05 Instant Form: Qualified ending

- Object: Instant Form
- Field: Qualified ending
- Value: One last step — book your strategy session. / Choose a time to review your goals, service area and marketing needs. / button 'Book a time' -> https://ca-jenterprises.com/ai
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Preview on mobile
- Status: Not started

### META-06 Instant Form: Privacy policy URL

- Object: Instant Form
- Field: Privacy policy URL
- Value: NEEDS_EVIDENCE (never guessed)
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: URL opens the published policy
- Status: Not started

### META-07 Campaign (NEW draft): Name

- Object: Campaign (NEW draft)
- Field: Name
- Value: CAJ-HT-HVAC-Leads-<YYYYMMDD of draft creation>
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Name is new; it is not the frozen campaign
- Status: Not started

### META-08 Campaign (NEW draft): Objective / destination

- Object: Campaign (NEW draft)
- Field: Objective / destination
- Value: Leads; Instant Forms; lead volume optimization
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Campaign summary
- Status: Not started

### META-09 Campaign (NEW draft): Status

- Object: Campaign (NEW draft)
- Field: Status
- Value: PAUSED (never published by this build)
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Status column shows Paused/Draft
- Status: Not started

### META-10 Campaign (NEW draft): Daily budget

- Object: Campaign (NEW draft)
- Field: Daily budget
- Value: NOT SET. AD_SPEND_CAP_USD = 0 - REQUIRES EXPLICIT HUMAN APPROVAL
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: No budget saved without written approval
- Spend: REQUIRES EXPLICIT HUMAN APPROVAL
- Status: Not started

### META-11 Campaign (NEW draft): Special Ad Category

- Object: Campaign (NEW draft)
- Field: Special Ad Category
- Value: Determine from the actual campaign and current platform prompts
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Recorded in decision log
- Status: Not started

### META-12 Ad set 1: Audience / geography

- Object: Ad set 1
- Field: Audience / geography
- Value: Service area NEEDS_EVIDENCE; HVAC owners and decision makers (not homeowners)
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Audience summary
- Status: Not started

### META-13 Ad A01: Image + copy

- Object: Ad A01
- Field: Image + copy
- Value: out/creatives/A01.json + out/copy/A01.md; same Instant Form attached
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Preview: image, primary text, headline, CTA, Page identity, destination, mobile rendering
- Status: Not started

### META-14 Ad A02: Image + copy

- Object: Ad A02
- Field: Image + copy
- Value: out/creatives/A02.json + out/copy/A02.md; same Instant Form attached
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Preview: image, primary text, headline, CTA, Page identity, destination, mobile rendering
- Status: Not started

### META-15 Ad A03: Image + copy

- Object: Ad A03
- Field: Image + copy
- Value: out/creatives/A03.json + out/copy/A03.md; same Instant Form attached
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Preview: image, primary text, headline, CTA, Page identity, destination, mobile rendering
- Status: Not started

### META-16 Ad A04: Image + copy

- Object: Ad A04
- Field: Image + copy
- Value: out/creatives/A04.json + out/copy/A04.md; same Instant Form attached
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Preview: image, primary text, headline, CTA, Page identity, destination, mobile rendering
- Status: Not started

### META-17 Ad A05: Image + copy

- Object: Ad A05
- Field: Image + copy
- Value: out/creatives/A05.json + out/copy/A05.md; same Instant Form attached
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Preview: image, primary text, headline, CTA, Page identity, destination, mobile rendering
- Status: Not started

### META-18 Ad images: Generate 5 x (1080x1350 + 1080x1080)

- Object: Ad images
- Field: Generate 5 x (1080x1350 + 1080x1080)
- Value: Use each image_prompt; any paid image tool - REQUIRES EXPLICIT HUMAN APPROVAL
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: Spelling, brand, legibility, margins, crop preview
- Spend: REQUIRES EXPLICIT HUMAN APPROVAL
- Status: Not started

### META-19 Pixel / Dataset / CAPI: Create or connect

- Object: Pixel / Dataset / CAPI
- Field: Create or connect
- Value: NEEDS_EVIDENCE whether needed for lead ads; any token stays in .env only
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: No token in any committed file
- Status: Not started

### META-20 Whop: Campaign interface

- Object: Whop
- Field: Campaign interface
- Value: Do not purchase a tool to reproduce the video interface
- Target location: `UWc5vKBgFVPdxNTRAy2s`
- Verify by: No new subscription
- Spend: REQUIRES EXPLICIT HUMAN APPROVAL
- Status: Not started
