import { ArrowRight, ClipboardCheck, Scale, ShieldCheck } from "lucide-react";
import { Link } from "react-router-dom";

import { PageHeader } from "@/components/content/page-header";
import { buttonVariants } from "@/components/ui/button-variants";

export default function AssessmentsPage() {
  return (
    <div className="space-y-8">
      <PageHeader description="Reproducible decisions from versioned profile facts and published scheme rules—never an AI guess." eyebrow="Eligibility workspace" title="Evidence before answers." />
      <section className="metal-panel overflow-hidden rounded-[2.25rem] p-7 sm:p-10" aria-labelledby="empty-assessment-title"><div className="grid gap-8 lg:grid-cols-[1fr_auto] lg:items-end"><div><span className="grid size-14 place-items-center rounded-2xl border border-white/10 bg-white/[0.06] text-copper"><ClipboardCheck className="size-6" /></span><h3 className="mt-6 font-display text-4xl text-white" id="empty-assessment-title">No assessment has been run.</h3><p className="mt-3 max-w-xl text-sm leading-7 text-white/48">Choose an official scheme and complete the required structured facts. Missing information returns “insufficient information”—it never silently becomes a failure.</p></div><Link className={buttonVariants({ className: "bg-copper text-obsidian hover:bg-[#dda460]" })} to="/schemes">Choose a scheme <ArrowRight className="size-4" /></Link></div></section>
      <div className="grid gap-4 md:grid-cols-3">{[{ icon: Scale, title: "Deterministic", text: "The same versioned inputs always produce the same result." }, { icon: ShieldCheck, title: "Bounded", text: "The language model cannot create or override eligibility." }, { icon: ClipboardCheck, title: "Explainable", text: "Passed, failed and unknown rules remain visible." }].map(({ icon: Icon, title, text }) => <article className="surface-card p-5" key={title}><Icon className="size-5 text-copper" /><h3 className="mt-4 font-display text-2xl">{title}</h3><p className="mt-2 text-sm leading-6 text-steel">{text}</p></article>)}</div>
    </div>
  );
}
