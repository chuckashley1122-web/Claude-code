"use client";

import { useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Download, Lock, Search, Zap } from "lucide-react";
import { Avatar } from "@/components/Avatar";
import {
  CompetitorInfo,
  SwitchLead,
  extractCompanyInfo,
  generateSubjectLines,
  generateSwitchList,
  toCsv,
} from "@/lib/generate";

const STEPS = [
  "Extracting company name, product category…",
  "Scanning technographic data (sample)…",
  "Scanning review sites for complaints (sample)…",
  "Analyzing switching signals…",
];
const PREVIEW = 5;
const usd = (n: number) => `$${(n / 1000).toFixed(0)}k`;

export default function Home() {
  const [input, setInput] = useState("");
  const [me, setMe] = useState("");
  const [email, setEmail] = useState("");
  const [unlocked, setUnlocked] = useState(false);
  const [step, setStep] = useState(-1);
  const [info, setInfo] = useState<CompetitorInfo | null>(null);
  const [rows, setRows] = useState<SwitchLead[]>([]);

  const loading = step >= 0 && step < STEPS.length;
  const subjects = useMemo(() => (info ? generateSubjectLines(info.name, me) : []), [info, me]);

  async function run(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim()) return;
    const parsed = extractCompanyInfo(input);
    setRows([]);
    setUnlocked(false);
    setInfo(null);
    for (let i = 0; i < STEPS.length; i++) {
      setStep(i);
      await new Promise((r) => setTimeout(r, 700));
    }
    setInfo(parsed);
    setRows(generateSwitchList(parsed.name, parsed.category, me));
    setStep(STEPS.length);
  }

  function unlock(e: React.FormEvent) {
    e.preventDefault();
    console.log("SwitchList email capture:", email);
    setUnlocked(true);
  }

  function exportCsv() {
    if (!info) return;
    const blob = new Blob([toCsv(rows, info.name)], { type: "text/csv" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `switchlist-${info.name.toLowerCase().replace(/\s+/g, "-")}.csv`;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  const done = step === STEPS.length && info;

  return (
    <main className="mx-auto max-w-6xl px-4 py-12 sm:px-6">
      <section className="text-center">
        <div className="mb-4 inline-flex items-center gap-1.5 rounded-full border border-neutral-200 px-3 py-1 text-xs font-medium text-neutral-600">
          <Zap size={12} /> SwitchList
        </div>
        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
          Find {info?.name ?? "[Competitor]"}&apos;s Customers Who Want to Switch
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-neutral-600">
          Enter any competitor. Get 15–25 companies showing switching signals, with messaging to win them.
        </p>
        <form onSubmit={run} className="mx-auto mt-8 flex max-w-3xl flex-col gap-3 sm:flex-row">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Competitor URL or name"
            aria-label="Competitor URL or name"
            className="flex-1 rounded-lg border border-neutral-300 px-4 py-3 outline-none focus:border-black"
          />
          <input
            value={me}
            onChange={(e) => setMe(e.target.value)}
            placeholder="Your company (optional)"
            aria-label="Your company name"
            className="flex-1 rounded-lg border border-neutral-300 px-4 py-3 outline-none focus:border-black"
          />
          <button
            disabled={loading}
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-black px-6 py-3 font-medium text-white disabled:opacity-60"
          >
            <Search size={16} /> Generate List
          </button>
        </form>
        <p className="mt-3 text-xs text-neutral-500">
          Demo mode: results below are illustrative sample data, not live company records.
        </p>
      </section>

      <AnimatePresence>
        {loading && (
          <motion.section initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="mx-auto mt-12 max-w-xl">
            <ul className="space-y-2 text-sm">
              {STEPS.map((s, i) => (
                <li key={s} className={i <= step ? "text-black" : "text-neutral-300"}>
                  {i < step ? "✓" : i === step ? "›" : "·"} {s}
                </li>
              ))}
            </ul>
            <div className="mt-4 h-2 overflow-hidden rounded-full bg-neutral-100">
              <motion.div
                className="h-full bg-black"
                initial={{ width: 0 }}
                animate={{ width: `${((step + 1) / STEPS.length) * 100}%` }}
                transition={{ duration: 0.6 }}
              />
            </div>
          </motion.section>
        )}
      </AnimatePresence>

      {done && (
        <>
          <section className="mt-12">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
              <span className="inline-flex items-center gap-2 rounded-full bg-red-100 px-3 py-1 text-sm font-medium text-red-700">
                <Avatar name={info.name} size={18} /> {info.name} customers
              </span>
              {unlocked && (
                <button onClick={exportCsv} className="inline-flex items-center gap-2 rounded-lg border border-neutral-300 px-4 py-2 text-sm font-medium hover:bg-neutral-50">
                  <Download size={14} /> Export CSV
                </button>
              )}
            </div>

            <div className="relative overflow-x-auto rounded-xl border border-neutral-200">
              <table className="w-full min-w-[960px] text-left text-sm">
                <thead className="bg-neutral-50 text-xs uppercase text-neutral-500">
                  <tr>
                    {["Company", "Size", "Industry", "Contract Est.", "Switching Trigger", "Displacement Angle", "Subject Lines"].map((h) => (
                      <th key={h} className="px-4 py-3 font-medium">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r, i) => {
                    const locked = !unlocked && i >= PREVIEW;
                    return (
                      <tr key={r.company} className={`align-top odd:bg-white even:bg-neutral-50/60 hover:bg-neutral-100 ${locked ? "select-none blur-sm" : ""}`} aria-hidden={locked}>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2 font-medium"><Avatar name={r.company} />{r.company}</div>
                        </td>
                        <td className="px-4 py-3">{r.size}</td>
                        <td className="px-4 py-3">{r.industry}</td>
                        <td className="px-4 py-3">{usd(r.contract)}</td>
                        <td className="px-4 py-3">
                          <span className="inline-flex gap-1.5 rounded bg-yellow-100 px-2 py-1 text-yellow-900">
                            <Zap size={13} className="mt-0.5 shrink-0" /> {r.trigger}
                          </span>
                        </td>
                        <td className="px-4 py-3">{r.angle}</td>
                        <td className="px-4 py-3 text-neutral-700">
                          <ul className="list-disc space-y-1 pl-4">{r.subjects.map((s) => <li key={s}>{s}</li>)}</ul>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              {!unlocked && rows.length > PREVIEW && (
                <div className="absolute inset-x-0 bottom-0 flex h-[55%] items-end justify-center bg-gradient-to-t from-white via-white/90 to-transparent pb-8">
                  <form onSubmit={unlock} className="w-full max-w-md px-4 text-center">
                    <p className="mb-3 flex items-center justify-center gap-2 font-semibold">
                      <Lock size={16} /> Unlock full list of {rows.length} companies + messaging
                    </p>
                    <div className="flex flex-col gap-2 sm:flex-row">
                      <input
                        type="email"
                        required
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="Work email"
                        aria-label="Work email"
                        className="flex-1 rounded-lg border border-neutral-300 bg-white px-4 py-2.5 outline-none focus:border-black"
                      />
                      <button className="rounded-lg bg-black px-5 py-2.5 font-medium text-white">Get Full List</button>
                    </div>
                  </form>
                </div>
              )}
            </div>
          </section>

          <section className="mt-12">
            <h2 className="text-xl font-semibold">Top 3 subject lines</h2>
            <ol className="mt-3 space-y-2">
              {subjects.map((s, i) => (
                <li key={s} className="rounded-lg border border-neutral-200 px-4 py-3">
                  <span className="mr-2 font-semibold text-neutral-400">{i + 1}.</span>{s}
                </li>
              ))}
            </ol>
          </section>

          <section className="mt-12 rounded-2xl bg-black p-8 text-center text-white">
            <p className="mx-auto max-w-2xl text-lg">
              We build full competitor displacement campaigns: verified lists, custom sequences calling out the switch, and managed sends. This sample is what we do at scale.
            </p>
            <div className="mt-5 flex flex-wrap justify-center gap-3">
              <a href="mailto:chuck@ca-jconsulting.com?subject=Book%20a%20call%20-%20SwitchList" className="rounded-lg bg-white px-5 py-2.5 font-medium text-black">Book a Call</a>
              <a
                href={`mailto:chuck@ca-jconsulting.com?subject=${encodeURIComponent(`${info.name}'s customers who might switch to ${me || "us"}`)}&body=${encodeURIComponent(`I pulled a list of ${info.name}'s customers who are showing switching signals. Want me to send it over with the messaging angles?`)}`}
                className="rounded-lg border border-white/40 px-5 py-2.5 font-medium"
              >
                Cold Email CTA
              </a>
            </div>
            <p className="mx-auto mt-6 max-w-xl text-sm text-white/70">
              Cold email: &quot;I pulled a list of {info.name}&apos;s customers who are showing switching signals. Want me to send it over with the messaging angles?&quot;
            </p>
          </section>
        </>
      )}
    </main>
  );
}
