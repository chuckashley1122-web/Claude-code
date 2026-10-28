// SAMPLE DATA ONLY. Companies are fictional; any resemblance to real firms is
// coincidental. Swap this for BuiltWith / G2 / job-post feeds to go live.

export type MockCompany = {
  name: string;
  domain: string;
  size: number;
  industry: string;
  contract: number;
  trigger: string; // {c} = competitor name
};

export const MOCK_COMPANIES: MockCompany[] = [
  { name: "Brightloop", domain: "brightloop.example", size: 500, industry: "SaaS", contract: 20000, trigger: 'Left 1-star G2 review: "Pricing is getting out of hand" 3 days ago' },
  { name: "Lineworks", domain: "lineworks.example", size: 120, industry: "SaaS", contract: 12000, trigger: "Hiring Head of Support: scaling pain on {c}" },
  { name: "Vantora", domain: "vantora.example", size: 800, industry: "DevTools", contract: 35000, trigger: 'Support Lead posted on LinkedIn: "Looking for {c} alternatives"' },
  { name: "Retrofit Labs", domain: "retrofitlabs.example", size: 300, industry: "SaaS", contract: 18000, trigger: "Growth signal: doubled support team in last 2 months" },
  { name: "Northpine", domain: "northpine.example", size: 210, industry: "E-commerce", contract: 15000, trigger: '2-star Capterra review: "Setup took months, support is slow"' },
  { name: "Quillbase", domain: "quillbase.example", size: 65, industry: "FinTech", contract: 9000, trigger: "Renewal window: contract likely up in next 60 days" },
  { name: "Harborstack", domain: "harborstack.example", size: 940, industry: "Cloud Infrastructure", contract: 48000, trigger: "CTO tweeted about vendor consolidation and cutting tool sprawl" },
  { name: "Mintwave", domain: "mintwave.example", size: 150, industry: "FinTech", contract: 14000, trigger: "Hiring 5 SDRs: growth signal, outgrowing current stack" },
  { name: "Gridly", domain: "gridly.example", size: 380, industry: "Analytics", contract: 22000, trigger: 'G2 review: "Every feature is an add-on now"' },
  { name: "Tidepool Health", domain: "tidepoolhealth.example", size: 260, industry: "HealthTech", contract: 19000, trigger: "Posted RFP for customer messaging platform" },
  { name: "Cobalt & Co", domain: "cobaltco.example", size: 90, industry: "Marketing Tech", contract: 8000, trigger: "Pricing page change: seats cost jumped, complaints in community forum" },
  { name: "Ironleaf", domain: "ironleaf.example", size: 720, industry: "Manufacturing Software", contract: 41000, trigger: "New VP Customer Success started 3 weeks ago (tool reviews likely)" },
  { name: "Pixelmint", domain: "pixelmint.example", size: 55, industry: "Design Tools", contract: 7000, trigger: 'Founder reply on Reddit: "{c} is overkill for a team our size"' },
  { name: "Skyforge", domain: "skyforge.example", size: 430, industry: "SaaS", contract: 26000, trigger: "Engineering blog: migrating off legacy support tooling" },
  { name: "Lumenpath", domain: "lumenpath.example", size: 175, industry: "EdTech", contract: 13000, trigger: "Opened 3 public support tickets about {c} outages this quarter" },
  { name: "Foxglove AI", domain: "foxglove.example", size: 110, industry: "AI", contract: 16000, trigger: "Series B announced: budget for stack upgrades" },
  { name: "Bluepeak Logistics", domain: "bluepeak.example", size: 600, industry: "Logistics", contract: 33000, trigger: "G2 review 2 weeks ago: integrations keep breaking" },
  { name: "Sagewire", domain: "sagewire.example", size: 240, industry: "Legal Tech", contract: 17000, trigger: "Job post: Support Ops Manager with migration experience" },
  { name: "Emberdesk", domain: "emberdesk.example", size: 80, industry: "SaaS", contract: 8500, trigger: "CEO liked 3 posts comparing {c} alternatives" },
  { name: "Copperline", domain: "copperline.example", size: 330, industry: "Retail Tech", contract: 21000, trigger: "Capterra review: auto-renewed at a 30% price hike" },
  { name: "Driftwood Labs", domain: "driftwood.example", size: 145, industry: "DevTools", contract: 12500, trigger: "Hiring 4 support engineers: ticket volume outpacing tooling" },
  { name: "Atlas Mutual Tech", domain: "atlasmutual.example", size: 880, industry: "InsurTech", contract: 52000, trigger: "Earnings call: priority to cut vendor costs 15%" },
  { name: "Nimbusly", domain: "nimbusly.example", size: 70, industry: "SaaS", contract: 7500, trigger: '1-star G2 review: "Can\'t export our own data cleanly"' },
  { name: "Redwood Pay", domain: "redwoodpay.example", size: 410, industry: "FinTech", contract: 27000, trigger: "Switched status page vendor last month: stack review underway" },
  { name: "Sparkgrid", domain: "sparkgrid.example", size: 195, industry: "Energy Software", contract: 15500, trigger: "Product lead asked about alternatives in a SaaS community Slack" },
];

export const KNOWN_WEAKNESSES: Record<string, { category: string; weaknesses: string[] }> = {
  intercom: { category: "Customer Support Software", weaknesses: ["expensive per-seat and per-resolution pricing", "complex setup", "add-on creep"] },
  hubspot: { category: "CRM & Marketing Automation", weaknesses: ["steep tier jumps", "bloated feature set", "costly contacts-based pricing"] },
  salesforce: { category: "CRM", weaknesses: ["heavy admin overhead", "long implementations", "expensive customization"] },
  zendesk: { category: "Customer Support Software", weaknesses: ["dated UI", "pricey add-ons", "slow support itself"] },
  mailchimp: { category: "Email Marketing", weaknesses: ["pricing by contact count", "limited automation depth"] },
  slack: { category: "Team Messaging", weaknesses: ["per-seat cost at scale", "notification overload"] },
};
export const DEFAULT_WEAKNESSES = ["high cost at scale", "slow support", "clunky onboarding"];
