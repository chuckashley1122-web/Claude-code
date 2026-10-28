import { DEFAULT_WEAKNESSES, KNOWN_WEAKNESSES, MOCK_COMPANIES } from "./mockData";

export type SwitchLead = {
  company: string;
  domain: string;
  size: number;
  industry: string;
  contract: number;
  trigger: string;
  angle: string;
  subjects: [string, string];
};

export type CompetitorInfo = { domain: string; name: string; category: string };

const titleCase = (s: string) =>
  s.replace(/[-_]+/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()).trim();

export function extractCompanyInfo(input: string): CompetitorInfo {
  const raw = input.trim();
  let host = raw;
  try {
    host = new URL(/^https?:\/\//i.test(raw) ? raw : `https://${raw}`).hostname;
  } catch {
    /* plain name */
  }
  const looksLikeUrl = /\.[a-z]{2,}$/i.test(host) && !/\s/.test(raw);
  const base = looksLikeUrl ? host.replace(/^www\./, "").split(".")[0] : raw;
  const name = titleCase(base);
  const key = base.toLowerCase().replace(/\s+/g, "");
  const known = KNOWN_WEAKNESSES[key];
  return {
    name,
    domain: looksLikeUrl ? host.replace(/^www\./, "") : `${key}.com`,
    category: known?.category ?? "B2B SaaS",
  };
}

// Deterministic PRNG so the same competitor always yields the same list.
function seeded(seed: string) {
  let h = 1779033703 ^ seed.length;
  for (let i = 0; i < seed.length; i++) {
    h = Math.imul(h ^ seed.charCodeAt(i), 3432918353);
    h = (h << 13) | (h >>> 19);
  }
  return () => {
    h = Math.imul(h ^ (h >>> 16), 2246822507);
    h = Math.imul(h ^ (h >>> 13), 3266489909);
    return ((h ^= h >>> 16) >>> 0) / 4294967296;
  };
}

export function generateSubjectLines(competitor: string, myCompany?: string): string[] {
  const me = myCompany?.trim() || "us";
  return [
    `${competitor}'s customers who might switch to ${me}`,
    `Paying too much for ${competitor}? A cheaper way to get the same result`,
    `Saw your team looking at ${competitor} alternatives`,
  ];
}

export function generateSwitchList(
  competitorName: string,
  productCategory: string,
  myCompanyName?: string
): SwitchLead[] {
  const rand = seeded(competitorName.toLowerCase());
  const pool = [...MOCK_COMPANIES];
  for (let i = pool.length - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1));
    [pool[i], pool[j]] = [pool[j], pool[i]];
  }
  const count = 15 + Math.floor(rand() * 11); // 15-25
  const key = competitorName.toLowerCase().replace(/\s+/g, "");
  const weaknesses = KNOWN_WEAKNESSES[key]?.weaknesses ?? DEFAULT_WEAKNESSES;
  const me = myCompanyName?.trim() || "us";

  return pool.slice(0, count).map((c, i) => {
    const w = weaknesses[i % weaknesses.length];
    const trigger = c.trigger.replace(/\{c\}/g, competitorName);
    return {
      company: c.name,
      domain: c.domain,
      size: c.size,
      industry: c.industry,
      contract: c.contract,
      trigger,
      angle: `Lead with ${w}: ${me} gives ${c.name} the same ${productCategory.toLowerCase()} outcome without it.`,
      subjects: [
        `${c.name}: still on ${competitorName}?`,
        `Cut the ${w.split(" ").slice(-2).join(" ")} at ${c.name}`,
      ],
    };
  });
}

export function toCsv(rows: SwitchLead[], competitor: string): string {
  const esc = (v: string | number) => `"${String(v).replace(/"/g, '""')}"`;
  const head = ["Competitor", "Company", "Domain", "Employees", "Industry", "Est. Contract USD", "Switching Trigger", "Displacement Angle", "Subject Line 1", "Subject Line 2"];
  const body = rows.map((r) =>
    [competitor, r.company, r.domain, r.size, r.industry, r.contract, r.trigger, r.angle, r.subjects[0], r.subjects[1]].map(esc).join(",")
  );
  return [head.map(esc).join(","), ...body].join("\n");
}
