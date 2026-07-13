import {
  ArrowRight,
  ArrowUpRight,
  BadgeIndianRupee,
  Bot,
  CheckCircle2,
  ChevronRight,
  Factory,
  DatabaseZap,
  Landmark,
  Search,
  ShieldCheck,
  Sparkles,
  Target,
} from "lucide-react";
import { useMemo, useState } from "react";

import { officialSchemes, schemeCategories, type SchemeCategory } from "@/features/schemes/scheme-data";
import { jurisdictionSources, startupIndiaPlaybookUrl, type JurisdictionKind } from "@/features/schemes/jurisdiction-source-data";

const mySchemeUrl = "https://www.myscheme.gov.in/";

interface PublicHomePageProps {
  readonly onAuthenticate: (mode: "register" | "login") => void;
}

const journeys = [
  { icon: Sparkles, label: "Start a company", copy: "Registration, founder support and first-enterprise pathways." },
  { icon: BadgeIndianRupee, label: "Find finance", copy: "Explore guarantees, credit-linked support and funding routes." },
  { icon: Factory, label: "Upgrade operations", copy: "Quality, technology, skills and productivity programmes." },
  { icon: Target, label: "Reach markets", copy: "Procurement, exhibitions, digital commerce and export support." },
] as const;

export default function PublicHomePage({ onAuthenticate }: PublicHomePageProps) {
  const [category, setCategory] = useState<"All" | SchemeCategory>("All");
  const [regionQuery, setRegionQuery] = useState("");
  const [regionKind, setRegionKind] = useState<"All" | JurisdictionKind>("All");
  const schemes = officialSchemes.filter((scheme) => category === "All" || scheme.category === category);
  const regions = useMemo(() => jurisdictionSources.filter((region) =>
    (regionKind === "All" || region.kind === regionKind) && region.name.toLowerCase().includes(regionQuery.trim().toLowerCase()),
  ), [regionKind, regionQuery]);

  return (
    <main className="public-stage min-h-screen overflow-hidden text-obsidian">
      <header className="public-nav" aria-label="Primary navigation">
        <a className="flex items-center gap-3" href="#top"><span className="public-mark">S</span><span><span className="block font-display text-xl font-semibold tracking-wide">SAARTHI</span><span className="block text-[0.5rem] font-black tracking-[0.25em] text-steel uppercase">MSME opportunity intelligence</span></span></a>
        <nav className="hidden items-center gap-7 text-xs font-bold text-steel md:flex" aria-label="Explore"><a href="#programmes">Schemes</a><a href="#saarthi-ai">AI assistant</a><a href="#states">States & UTs</a><a href="#plans">Plans</a></nav>
        <div className="flex items-center gap-2"><button className="hidden rounded-full px-4 py-2.5 text-xs font-bold text-steel hover:text-obsidian sm:block" onClick={() => onAuthenticate("login")} type="button">Sign in</button><button className="rounded-full bg-obsidian px-4 py-2.5 text-xs font-bold text-white shadow-lg transition hover:-translate-y-0.5 hover:bg-copper hover:text-obsidian sm:px-5" onClick={() => onAuthenticate("register")} type="button">Create free workspace</button></div>
      </header>

      <section className="public-hero relative" id="top">
        <div className="hero-grid" aria-hidden="true" />
        <div className="relative z-10 mx-auto grid max-w-[94rem] gap-12 px-5 pb-16 pt-16 sm:px-8 lg:grid-cols-[1.12fr_0.88fr] lg:px-12 lg:pb-24 lg:pt-24">
          <div>
            <a className="source-pill" href={mySchemeUrl} rel="noreferrer" target="_blank"><CheckCircle2 className="size-3.5" /> Built around official Government of India sources <ArrowUpRight className="size-3" /></a>
            <h1 className="mt-8 max-w-4xl font-display text-6xl font-semibold leading-[0.88] tracking-[-0.05em] text-white sm:text-7xl lg:text-[6.5rem]">There may be a scheme for your <em className="font-normal text-copper">next move.</em></h1>
            <p className="mt-7 max-w-2xl text-sm leading-7 text-white/55 sm:text-base">Discover credible Central and State pathways to start, finance, modernise and grow an Indian enterprise—then turn scattered programme information into a focused plan.</p>
            <div className="mt-9 flex flex-wrap gap-3"><a className="hero-primary" href="#programmes">Explore official schemes <ArrowRight className="size-4" /></a><button className="hero-secondary" onClick={() => onAuthenticate("register")} type="button">Map schemes to my business</button></div>
            <div className="mt-11 flex flex-wrap gap-x-8 gap-y-4 border-t border-white/10 pt-6 text-[0.65rem] font-bold text-white/40"><span><strong className="mr-2 font-display text-2xl text-white">36</strong>States & UTs mapped</span><span><strong className="mr-2 font-display text-2xl text-white">5</strong>central starting points</span><span><strong className="mr-2 font-display text-2xl text-white">0</strong>LLM eligibility guesses</span></div>
          </div>

          <aside className="hero-opportunity relative" aria-label="Featured official programme"><img alt="Indian manufacturing entrepreneur inspecting a precision component" className="absolute inset-0 size-full object-cover" src="/images/indian-msme-founder-v1.png" /><div className="absolute inset-0 bg-gradient-to-t from-[#090c10] via-[#090c10]/65 to-[#090c10]/15" />
            <div className="relative flex items-center justify-between"><span className="metal-chip"><Landmark className="size-3.5 text-copper" /> Official source</span><span className="live-dot">Source checked</span></div>
            <div className="relative mt-auto pt-20"><p className="text-[0.65rem] font-black tracking-[0.18em] text-copper uppercase">A place to begin</p><p className="mt-3 font-display text-5xl font-semibold leading-none text-white">PMEGP</p><h2 className="mt-3 max-w-md font-display text-2xl leading-tight text-white/80">Support for establishing new micro-enterprises in the non-farm sector.</h2><p className="mt-5 max-w-md text-xs leading-6 text-white/45">This is discovery, not an eligibility decision. Review the current programme terms at the Ministry of MSME.</p><a className="mt-8 inline-flex items-center gap-2 text-xs font-black text-white hover:text-copper" href={officialSchemes.find((scheme) => scheme.id === "pmegp")?.sourceUrl ?? mySchemeUrl} rel="noreferrer" target="_blank">Open Ministry source <ArrowUpRight className="size-4" /></a></div>
          </aside>
        </div>
      </section>

      <section className="mx-auto max-w-[94rem] px-5 pt-20 sm:px-8 lg:px-12" id="saarthi-ai" aria-labelledby="ai-title"><div className="ai-showcase"><div><span className="metal-chip"><Bot className="size-3.5 text-copper" /> Live RAG assistant</span><h2 className="mt-7 font-display text-5xl font-semibold leading-[.94] text-white sm:text-6xl" id="ai-title">Ask a question. See the evidence travel with the answer.</h2><p className="mt-6 max-w-xl text-sm leading-7 text-white/48">Saarthi retrieves bounded official evidence, runs a minimal LangGraph workflow and streams a response with resolvable citations. Eligibility remains with the deterministic rule engine.</p><button className="hero-primary mt-8" onClick={() => onAuthenticate("register")} type="button">Open Saarthi AI <ArrowRight className="size-4" /></button></div><div className="rag-visual"><div className="rag-question">Which programme could help me start a small manufacturing unit?</div><div className="rag-status"><DatabaseZap className="size-4 text-copper" /><span>Retrieving reviewed evidence</span><span className="ml-auto flex gap-1"><i /><i /><i /></span></div><div className="rag-answer"><Sparkles className="size-4 shrink-0 text-copper" /><p>PMEGP is one official starting point worth reviewing for a new non-farm micro-enterprise. Eligibility and finance depend on current published rules. <strong>[Ministry source]</strong></p></div><div className="rag-citation"><Landmark className="size-4 text-copper" /><span>Ministry of MSME · PMEGP</span><CheckCircle2 className="ml-auto size-4 text-emerald-400" /></div></div></div></section>

      <section className="mx-auto max-w-[94rem] px-5 py-20 sm:px-8 lg:px-12" aria-labelledby="journey-title">
        <p className="section-kicker">Start with your ambition</p><h2 className="section-title" id="journey-title">What does your business need next?</h2><p className="section-copy">Saarthi starts with a real business goal, then narrows the official landscape around it.</p>
        <div className="mt-10 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{journeys.map(({ icon: Icon, label, copy }, index) => <a className="journey-card group" href="#programmes" key={label}><span className="journey-number">0{index + 1}</span><Icon className="mt-12 size-6 text-copper" /><h3 className="mt-6 font-display text-2xl font-semibold">{label}</h3><p className="mt-2 text-xs leading-6 text-steel">{copy}</p><ChevronRight className="mt-7 size-4 transition group-hover:translate-x-1" /></a>)}</div>
      </section>

      <section className="mx-auto max-w-[94rem] px-5 pb-24 sm:px-8 lg:px-12" id="programmes" aria-labelledby="programmes-title">
        <div className="flex flex-col justify-between gap-6 lg:flex-row lg:items-end"><div><p className="section-kicker">Official programme library</p><h2 className="section-title" id="programmes-title">Signals worth following.</h2><p className="section-copy">A curated set of Central programmes and registrations, with every material summary linked to its authority.</p></div><div className="flex max-w-full gap-2 overflow-x-auto pb-1">{schemeCategories.map((item) => <button aria-pressed={category === item} className={`shrink-0 rounded-full px-4 py-2.5 text-xs font-bold ${category === item ? "bg-obsidian text-white" : "border border-obsidian/10 bg-white/60 text-steel"}`} key={item} onClick={() => setCategory(item)} type="button">{item}</button>)}</div></div>
        <div className="mt-10 grid gap-4 md:grid-cols-2 xl:grid-cols-3">{schemes.map((scheme, index) => <article className={`public-scheme-card ${index === 0 ? "public-scheme-featured" : ""}`} key={scheme.id}><div className="flex items-start justify-between gap-4"><span className="text-[0.62rem] font-black tracking-[0.15em] text-copper uppercase">{scheme.category} · {scheme.shortTitle}</span><a aria-label={`Open official source for ${scheme.title}`} className="source-arrow" href={scheme.sourceUrl} rel="noreferrer" target="_blank"><ArrowUpRight className="size-4" /></a></div><div className="mt-auto pt-16"><p className="text-[0.65rem] text-steel">{scheme.authority}</p><h3 className="mt-3 font-display text-3xl font-semibold leading-none">{scheme.title}</h3><p className="mt-4 text-xs leading-6 text-steel">{scheme.summary}</p><p className="mt-6 border-t border-current/10 pt-4 text-[0.65rem] leading-5 opacity-65"><strong>For:</strong> {scheme.audience}</p></div></article>)}</div>
        <div className="mt-5 flex flex-col justify-between gap-3 rounded-2xl border border-obsidian/8 bg-white/50 p-4 text-[0.68rem] leading-5 text-steel sm:flex-row sm:items-center"><p><strong className="text-obsidian">Curated, not exhaustive.</strong> Programme status and conditions can change. Always check the official linked source.</p><a className="shrink-0 font-black text-obsidian hover:text-copper" href={mySchemeUrl} rel="noreferrer" target="_blank">Search all on myScheme ↗</a></div>
      </section>

      <section className="state-section py-24" id="states" aria-labelledby="states-title">
        <div className="mx-auto max-w-[94rem] px-5 sm:px-8 lg:px-12"><div className="grid gap-10 lg:grid-cols-[0.7fr_1.3fr]"><div><p className="section-kicker text-copper">State opportunity atlas</p><h2 className="mt-4 font-display text-5xl font-semibold leading-[0.95] text-white sm:text-6xl" id="states-title">India’s support landscape is local, too.</h2><p className="mt-6 max-w-md text-sm leading-7 text-white/48">Browse all 28 States and 8 Union Territories through entry points listed in Startup India’s June 2026 government-schemes playbook.</p><a className="mt-7 inline-flex items-center gap-2 text-xs font-black text-white hover:text-copper" href={startupIndiaPlaybookUrl} rel="noreferrer" target="_blank">View the source playbook <ArrowUpRight className="size-4" /></a><div className="mt-10 rounded-2xl border border-amber-300/15 bg-amber-200/[0.05] p-4 text-[0.68rem] leading-5 text-white/40"><strong className="text-white/70">Coverage note:</strong> These are discovery entry points copied from the official national playbook—not a claim that every linked policy, benefit or application window is active.</div></div>
          <div><div className="flex flex-col gap-3 sm:flex-row"><label className="relative flex-1"><span className="sr-only">Find your State or Union Territory</span><Search className="absolute left-4 top-1/2 size-4 -translate-y-1/2 text-white/35" /><input className="region-search" onChange={(event) => setRegionQuery(event.target.value)} placeholder="Find your State or Union Territory" type="search" value={regionQuery} /></label><div className="flex gap-2">{(["All", "State", "Union Territory"] as const).map((item) => <button aria-pressed={regionKind === item} className={`rounded-full px-3.5 py-2.5 text-[0.65rem] font-bold ${regionKind === item ? "bg-copper text-obsidian" : "border border-white/10 text-white/50"}`} key={item} onClick={() => setRegionKind(item)} type="button">{item === "Union Territory" ? "UT" : item}</button>)}</div></div>
            <div className="region-grid mt-6" aria-live="polite">{regions.map((region) => <a className="region-link group" href={region.initiativeUrl} key={region.name} rel="noreferrer" target="_blank"><span><span className="block text-xs font-bold text-white/78">{region.name}</span><span className={`mt-1 block text-[0.58rem] ${region.sourceStatus === "Draft policy" ? "text-amber-300/65" : "text-white/28"}`}>{region.sourceStatus}</span></span><ArrowUpRight className="size-3.5 text-white/20 transition group-hover:text-copper" /></a>)}</div>{regions.length === 0 && <p className="mt-6 rounded-2xl border border-white/10 p-8 text-center text-sm text-white/45">No matching jurisdiction.</p>}</div></div></div>
      </section>

      <section className="mx-auto max-w-[94rem] px-5 py-24 sm:px-8 lg:px-12" id="plans" aria-labelledby="plans-title"><div className="text-center"><p className="section-kicker">From discovery to decision</p><h2 className="section-title" id="plans-title">Explore freely. Pay for the fit map.</h2><p className="section-copy mx-auto">Official links remain open to everyone. The future paid workspace is for structured matching, comparison and ongoing guidance—not access to public information.</p></div><div className="mx-auto mt-12 grid max-w-5xl gap-5 lg:grid-cols-2"><article className="plan-card"><p className="text-[0.65rem] font-black tracking-[0.16em] text-steel uppercase">Explorer · Free</p><p className="mt-4 font-display text-5xl font-semibold">₹0</p><p className="mt-3 text-sm text-steel">Find official starting points and build a profile.</p><ul className="plan-list"><li>Curated Central scheme discovery</li><li>36-jurisdiction source atlas</li><li>Founder workspace and profile</li></ul><button className="plan-button" onClick={() => onAuthenticate("register")} type="button">Start free</button></article><article className="plan-card plan-card-pro"><span className="absolute right-6 top-6 rounded-full bg-copper px-3 py-1 text-[0.58rem] font-black text-obsidian">COMING SOON</span><p className="text-[0.65rem] font-black tracking-[0.16em] text-copper uppercase">Saarthi Pro · Guided</p><p className="mt-4 font-display text-5xl font-semibold text-white">Fit map</p><p className="mt-3 text-sm text-white/48">Turn your use case and evidence into a prioritised scheme workflow.</p><ul className="plan-list text-white/62"><li>Business-to-scheme fit signals</li><li>Deterministic eligibility assessments</li><li>Comparisons, evidence gaps and alerts</li></ul><button className="plan-button border-white/15 bg-white text-obsidian" onClick={() => onAuthenticate("register")} type="button">Join with a free workspace</button></article></div></section>

      <section className="mx-auto max-w-[94rem] px-5 pb-24 sm:px-8 lg:px-12" id="trust"><div className="trust-panel"><div><ShieldCheck className="size-7 text-copper" /><h2 className="mt-7 max-w-2xl font-display text-5xl font-semibold leading-none text-white">Evidence first. Eligibility without guesswork.</h2></div><div className="grid gap-6 text-xs leading-6 text-white/48 sm:grid-cols-2"><p><strong className="block text-white">Claims carry a source.</strong> Material scheme summaries resolve to an authority page before they become advice.</p><p><strong className="block text-white">Rules decide eligibility.</strong> AI can explain or collect missing facts; it cannot independently declare a business eligible.</p><p><strong className="block text-white">No government affiliation implied.</strong> Saarthi is an independent discovery product and does not use the State Emblem.</p><p><strong className="block text-white">Your workspace is protected.</strong> Encrypted profile fields, hashed credentials and revocable secure sessions.</p></div></div></section>

      <footer className="border-t border-obsidian/8 px-5 py-8 sm:px-8"><div className="mx-auto flex max-w-[94rem] flex-col justify-between gap-4 text-[0.65rem] text-steel sm:flex-row"><p>MSME Saarthi AI · Independent official-source discovery</p><p>Not a government portal · Verify terms before acting</p></div></footer>
    </main>
  );
}
