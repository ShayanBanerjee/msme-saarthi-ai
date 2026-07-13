import { ArrowUpRight, BookOpenCheck, CheckCircle2, Search, SlidersHorizontal } from "lucide-react";
import { useMemo, useState } from "react";

import { PageHeader } from "@/components/content/page-header";

import { officialSchemes, schemeCategories, type SchemeCategory } from "./scheme-data";

export default function SchemesPage() {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState<"All" | SchemeCategory>("All");
  const filtered = useMemo(() => officialSchemes.filter((scheme) => (category === "All" || scheme.category === category) && `${scheme.title} ${scheme.summary} ${scheme.authority}`.toLowerCase().includes(query.toLowerCase().trim())), [category, query]);

  return (
    <div className="space-y-7">
      <PageHeader description="A carefully curated starting point for official central MSME support. Open the source before relying on any programme detail." eyebrow="Official opportunity library" title="Find support with evidence." />
      <section className="surface-card p-3" aria-label="Scheme search and filters">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
          <label className="relative flex-1"><span className="sr-only">Search official schemes</span><Search className="absolute top-1/2 left-4 size-4 -translate-y-1/2 text-steel" /><input className="h-12 w-full rounded-2xl border border-transparent bg-white px-11 text-sm outline-none focus:border-copper/35" onChange={(event) => setQuery(event.target.value)} placeholder="Search by programme, authority or goal" type="search" value={query} /></label>
          <div className="flex items-center gap-2 overflow-x-auto pb-1 lg:pb-0"><SlidersHorizontal className="mx-2 size-4 shrink-0 text-steel" />{schemeCategories.map((item) => <button aria-pressed={category === item} className={`shrink-0 rounded-full px-3.5 py-2 text-xs font-bold transition ${category === item ? "bg-obsidian text-white" : "bg-white text-steel hover:text-obsidian"}`} key={item} onClick={() => setCategory(item)} type="button">{item}</button>)}</div>
        </div>
      </section>
      <div className="flex items-center justify-between"><p className="text-xs font-bold text-steel">{filtered.length} official {filtered.length === 1 ? "record" : "records"}</p><p className="flex items-center gap-1.5 text-[0.65rem] font-bold text-emerald-700"><CheckCircle2 className="size-3.5" /> Sources checked 13 Jul 2026</p></div>
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3" aria-label="Official scheme results">
        {filtered.map((scheme, index) => <article className={`group flex min-h-[20rem] flex-col overflow-hidden rounded-[2rem] border p-6 transition duration-300 hover:-translate-y-1 hover:shadow-xl ${index === 0 ? "metal-panel border-white/5 text-white" : "surface-card"}`} key={scheme.id}><div className="flex items-start justify-between"><div><span className={`text-[0.6rem] font-black tracking-[0.16em] uppercase ${index === 0 ? "text-copper" : "text-copper"}`}>{scheme.category}</span><p className={`mt-1 text-[0.65rem] ${index === 0 ? "text-white/38" : "text-steel"}`}>{scheme.authority}</p></div><a aria-label={`Open official source for ${scheme.title}`} className={`grid size-10 place-items-center rounded-full transition ${index === 0 ? "bg-white/10 text-white hover:bg-copper hover:text-obsidian" : "bg-obsidian text-white hover:bg-copper hover:text-obsidian"}`} href={scheme.sourceUrl} rel="noreferrer" target="_blank"><ArrowUpRight className="size-4" /></a></div><div className="mt-auto pt-10"><p className={`text-xs font-black tracking-wider uppercase ${index === 0 ? "text-white/42" : "text-steel"}`}>{scheme.shortTitle}</p><h3 className="mt-2 font-display text-3xl font-semibold leading-[1.03]">{scheme.title}</h3><p className={`mt-4 text-sm leading-6 ${index === 0 ? "text-white/55" : "text-steel"}`}>{scheme.summary}</p><div className={`mt-5 border-t pt-4 ${index === 0 ? "border-white/10" : "border-obsidian/8"}`}><p className={`text-[0.68rem] leading-5 ${index === 0 ? "text-white/42" : "text-steel"}`}><strong className={index === 0 ? "text-white/65" : "text-obsidian"}>For:</strong> {scheme.audience}</p></div></div></article>)}
      </section>
      {filtered.length === 0 && <div className="surface-card px-6 py-14 text-center"><BookOpenCheck className="mx-auto size-7 text-copper" /><h3 className="mt-4 font-display text-2xl">No matching source yet</h3><p className="mt-2 text-sm text-steel">Try a broader goal or clear the category filter.</p></div>}
      <aside className="rounded-2xl border border-obsidian/8 bg-white/55 p-4 text-xs leading-5 text-steel"><strong className="text-obsidian">Important:</strong> This catalogue is curated, not a complete government database or an eligibility decision. Programme status and terms can change. “Verified” means the linked official page was checked on the displayed date.</aside>
    </div>
  );
}
