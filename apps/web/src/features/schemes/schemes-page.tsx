import { ArrowUpRight, BookOpenCheck, BriefcaseBusiness, CheckCircle2, Crown, LockKeyhole, Search, SlidersHorizontal } from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { PageHeader } from "@/components/content/page-header";

import { officialSchemes, schemeCategories, type SchemeCategory } from "./scheme-data";
import { investorVerificationSources, privateInvestorSources } from "./private-investor-data";

export default function SchemesPage() {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState<"All" | SchemeCategory>("All");
  const filtered = useMemo(() => officialSchemes.filter((scheme) => (category === "All" || scheme.category === category) && `${scheme.title} ${scheme.summary} ${scheme.authority}`.toLowerCase().includes(query.toLowerCase().trim())), [category, query]);

  return (
    <div className="space-y-7">
      <PageHeader description="Explore reviewed government pathways for starting, innovating, financing, formalising and growing an enterprise. Open the authority source before relying on any programme detail." eyebrow="Official opportunity library" title="Find support with evidence." />
      <section className="surface-card p-3" aria-label="Scheme search and filters">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
          <label className="relative flex-1"><span className="sr-only">Search official schemes</span><Search className="absolute top-1/2 left-4 size-4 -translate-y-1/2 text-steel" /><input className="h-12 w-full rounded-2xl border border-transparent bg-white px-11 text-sm outline-none focus:border-copper/35" onChange={(event) => setQuery(event.target.value)} placeholder="Search by programme, authority or goal" type="search" value={query} /></label>
          <div className="flex items-center gap-2 overflow-x-auto pb-1 lg:pb-0"><SlidersHorizontal className="mx-2 size-4 shrink-0 text-steel" />{schemeCategories.map((item) => <button aria-pressed={category === item} className={`shrink-0 rounded-full px-3.5 py-2 text-xs font-bold transition ${category === item ? "bg-obsidian text-white" : "bg-white text-steel hover:text-obsidian"}`} key={item} onClick={() => setCategory(item)} type="button">{item}</button>)}</div>
        </div>
      </section>
      <div className="flex items-center justify-between"><p className="text-xs font-bold text-steel">{filtered.length} official {filtered.length === 1 ? "record" : "records"}</p><p className="flex items-center gap-1.5 text-[0.65rem] font-bold text-emerald-700"><CheckCircle2 className="size-3.5" /> Sources checked 15 Jul 2026</p></div>
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3" aria-label="Official scheme results">
        {filtered.map((scheme) => { const featured = scheme.featured === true; return <article className={`group flex min-h-[20rem] flex-col overflow-hidden rounded-[2rem] border p-6 transition duration-300 hover:-translate-y-1 hover:shadow-xl ${featured ? "metal-panel border-white/5 text-white" : "surface-card"}`} key={scheme.id}><div className="flex items-start justify-between"><div><span className="text-[0.6rem] font-black tracking-[0.16em] text-copper uppercase">{scheme.category}</span><p className={`mt-1 text-[0.65rem] ${featured ? "text-white/38" : "text-steel"}`}>{scheme.authority}</p></div><a aria-label={`Open official source for ${scheme.title}`} className={`grid size-10 place-items-center rounded-full transition ${featured ? "bg-white/10 text-white hover:bg-copper hover:text-obsidian" : "bg-obsidian text-white hover:bg-copper hover:text-obsidian"}`} href={scheme.sourceUrl} rel="noreferrer" target="_blank"><ArrowUpRight className="size-4" /></a></div><div className="mt-auto pt-10"><div className="flex flex-wrap items-center gap-2"><p className={`text-xs font-black tracking-wider uppercase ${featured ? "text-white/42" : "text-steel"}`}>{scheme.shortTitle}</p>{scheme.statusNote && <span className={`rounded-full px-2 py-1 text-[0.55rem] font-bold ${featured ? "bg-white/8 text-white/45" : "bg-amber-100 text-amber-800"}`}>{scheme.statusNote}</span>}</div><h3 className="mt-2 font-display text-3xl font-semibold leading-[1.03]">{scheme.title}</h3><p className={`mt-4 text-sm leading-6 ${featured ? "text-white/55" : "text-steel"}`}>{scheme.summary}</p><div className={`mt-5 border-t pt-4 ${featured ? "border-white/10" : "border-obsidian/8"}`}><p className={`text-[0.68rem] leading-5 ${featured ? "text-white/42" : "text-steel"}`}><strong className={featured ? "text-white/65" : "text-obsidian"}>For:</strong> {scheme.audience}</p></div></div></article>; })}
      </section>
      {filtered.length === 0 && <div className="surface-card px-6 py-14 text-center"><BookOpenCheck className="mx-auto size-7 text-copper" /><h3 className="mt-4 font-display text-2xl">No matching source yet</h3><p className="mt-2 text-sm text-steel">Try a broader goal or clear the category filter.</p></div>}
      <aside className="rounded-2xl border border-obsidian/8 bg-white/55 p-4 text-xs leading-5 text-steel"><strong className="text-obsidian">Important:</strong> This catalogue is curated, not a complete government database or an eligibility decision. Programme status and terms can change. “Verified” means the linked official page was checked on the displayed date.</aside>
      <section className="investor-vault" aria-labelledby="investor-vault-title">
        <div className="investor-vault-copy"><span className="metal-chip"><Crown className="size-3.5 text-copper" /> Saarthi Pro</span><h2 id="investor-vault-title">Private capital intelligence—kept separate from government support.</h2><p>Explore selected investor organisations, verify registered AIF records, and prepare a stage-aware outreach brief. Inclusion is never an endorsement or promise of investment.</p><div className="mt-5 flex flex-wrap gap-3 text-[0.62rem] font-bold text-white/42"><a href={investorVerificationSources.sebi} rel="noreferrer" target="_blank">SEBI verification ↗</a><a href={investorVerificationSources.startupIndia} rel="noreferrer" target="_blank">Startup India Investor Connect ↗</a></div></div>
        <div className="investor-vault-grid">{privateInvestorSources.map((investor) => <article key={investor.name}><div className="flex items-center justify-between"><span><BriefcaseBusiness className="size-4" /></span><LockKeyhole className="size-3.5 text-white/25" /></div><h3>{investor.name}</h3><p>{investor.description}</p><a href={investor.officialUrl} rel="noreferrer" target="_blank">Open official site <ArrowUpRight className="size-3.5" /></a></article>)}</div>
        <Link className="investor-vault-cta" to="/plans">View Pro access <ArrowUpRight className="size-4" /></Link>
      </section>
    </div>
  );
}
