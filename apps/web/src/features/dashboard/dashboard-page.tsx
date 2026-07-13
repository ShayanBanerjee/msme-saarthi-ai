import { ArrowRight, BadgeIndianRupee, Building2, CheckCircle2, Compass, Sparkles, TrendingUp } from "lucide-react";
import { Link } from "react-router-dom";

import { buttonVariants } from "@/components/ui/button-variants";
import { officialSchemes } from "@/features/schemes/scheme-data";

const metrics = [
  { label: "Official programmes", value: "05", note: "Curated and source-linked", icon: Compass },
  { label: "Founder readiness", value: "42%", note: "2 next moves identified", icon: TrendingUp },
  { label: "Profile confidence", value: "75%", note: "Demo workspace", icon: CheckCircle2 },
] as const;

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <section className="metal-panel relative overflow-hidden rounded-[2.25rem] px-6 py-8 sm:px-9 sm:py-10 lg:px-12 lg:py-12" aria-labelledby="welcome-title">
        <div className="absolute -top-32 -right-28 size-80 rounded-full border border-copper/20 bg-copper/[0.06]" />
        <div className="absolute top-12 right-14 hidden h-48 w-px bg-gradient-to-b from-transparent via-white/15 to-transparent lg:block" />
        <div className="relative max-w-3xl">
          <span className="metal-chip"><Sparkles className="size-3.5 text-copper" /> Built for Indian enterprise</span>
          <h2 className="mt-7 font-display text-5xl font-semibold leading-[0.95] tracking-[-0.035em] text-white sm:text-6xl lg:text-7xl" id="welcome-title">Your ambition deserves <em className="mt-1 block font-normal text-copper">a clearer path.</em></h2>
          <p className="mt-6 max-w-xl text-sm leading-7 text-white/55 sm:text-base">Discover official support, test readiness with deterministic rules, and turn the next business milestone into a focused plan.</p>
          <div className="mt-8 flex flex-wrap gap-3"><Link className={buttonVariants({ className: "bg-copper text-obsidian hover:bg-[#dda460]" })} to="/growth">Build my growth plan <ArrowRight className="size-4" /></Link><Link className={buttonVariants({ variant: "outline", className: "border-white/15 bg-white/[0.06] text-white hover:border-white/30 hover:bg-white/10" })} to="/schemes">Explore official schemes</Link></div>
        </div>
      </section>

      <section aria-labelledby="workspace-summary" className="grid gap-4 md:grid-cols-3">
        <h3 className="sr-only" id="workspace-summary">Workspace summary</h3>
        {metrics.map(({ label, value, note, icon: Icon }) => <article className="surface-card flex items-center gap-4 p-5" key={label}><span className="grid size-11 shrink-0 place-items-center rounded-2xl bg-obsidian text-copper"><Icon className="size-5" /></span><div><p className="text-[0.62rem] font-black tracking-[0.14em] text-steel uppercase">{label}</p><div className="mt-1 flex items-baseline gap-2"><strong className="font-display text-3xl text-obsidian">{value}</strong><span className="text-xs text-steel">{note}</span></div></div></article>)}
      </section>

      <div className="grid gap-5 xl:grid-cols-[1.25fr_0.75fr]">
        <section className="surface-card p-6 sm:p-7" aria-labelledby="opportunity-title">
          <div className="flex items-end justify-between gap-4"><div><p className="text-[0.62rem] font-black tracking-[0.18em] text-copper uppercase">Opportunity radar</p><h3 className="mt-1 font-display text-3xl" id="opportunity-title">Worth exploring now</h3></div><Link className="text-xs font-bold text-steel hover:text-copper" to="/schemes">View all →</Link></div>
          <div className="mt-6 grid gap-3 sm:grid-cols-3">
            {officialSchemes.filter((scheme) => scheme.featured).map((scheme) => <a className="group rounded-2xl border border-obsidian/[0.07] bg-white/60 p-4 transition hover:-translate-y-1 hover:border-copper/25 hover:shadow-lg" href={scheme.sourceUrl} key={scheme.id} rel="noreferrer" target="_blank"><span className="text-[0.6rem] font-black tracking-wider text-copper uppercase">{scheme.category}</span><h4 className="mt-4 font-display text-xl leading-tight">{scheme.shortTitle}</h4><p className="mt-2 line-clamp-3 text-xs leading-5 text-steel">{scheme.summary}</p><span className="mt-4 flex items-center gap-1 text-[0.65rem] font-bold text-obsidian">Official source <ArrowRight className="size-3 transition-transform group-hover:translate-x-1" /></span></a>)}
          </div>
        </section>
        <section className="surface-card p-6 sm:p-7" aria-labelledby="next-moves-title">
          <div className="flex items-center justify-between"><h3 className="font-display text-3xl" id="next-moves-title">Next moves</h3><Building2 className="size-5 text-copper" /></div>
          <ol className="mt-6 space-y-5">
            <li className="flex gap-3"><span className="grid size-7 shrink-0 place-items-center rounded-full bg-copper text-xs font-black text-obsidian">1</span><div><p className="text-sm font-bold">Define your first customer</p><p className="mt-1 text-xs leading-5 text-steel">Name one segment and the costly problem you solve.</p></div></li>
            <li className="flex gap-3"><span className="grid size-7 shrink-0 place-items-center rounded-full bg-obsidian text-xs font-black text-white">2</span><div><p className="text-sm font-bold">Complete business facts</p><p className="mt-1 text-xs leading-5 text-steel">Improve scheme matching without uploading documents.</p></div></li>
          </ol>
          <Link className={buttonVariants({ variant: "outline", className: "mt-6 w-full" })} to="/profile">Strengthen profile</Link>
        </section>
      </div>
      <aside className="flex items-start gap-3 rounded-2xl border border-copper/20 bg-copper/[0.06] px-4 py-3 text-xs leading-5 text-steel"><BadgeIndianRupee className="mt-0.5 size-4 shrink-0 text-copper" /><p>Scheme discovery is informational. Eligibility and approval belong to the published rules and responsible authority; always verify at the linked official source.</p></aside>
    </div>
  );
}
