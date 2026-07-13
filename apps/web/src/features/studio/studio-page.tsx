import { ArrowRight, BadgeIndianRupee, Boxes, Crosshair, DraftingCompass, FlaskConical, UsersRound } from "lucide-react";
import { Link } from "react-router-dom";

import { PageHeader } from "@/components/content/page-header";
import { buttonVariants } from "@/components/ui/button-variants";

const canvas = [
  { number: "01", title: "Customer tension", prompt: "What costly, frequent problem deserves a better answer?", icon: UsersRound, accent: "text-sky-300" },
  { number: "02", title: "Founder promise", prompt: "What measurable change will your customer pay to achieve?", icon: Crosshair, accent: "text-copper" },
  { number: "03", title: "Proof engine", prompt: "What is the smallest real-world test that could disprove your idea?", icon: FlaskConical, accent: "text-emerald-300" },
  { number: "04", title: "Economic core", prompt: "Price, variable cost, acquisition effort and time to cash.", icon: BadgeIndianRupee, accent: "text-amber-300" },
] as const;

export default function StudioPage() {
  return (
    <div className="space-y-7">
      <PageHeader action={<Link className={buttonVariants()} to="/chat">Think with Saarthi <ArrowRight className="size-4" /></Link>} description="A founder canvas for turning conviction into testable assumptions—before you spend heavily or seek capital." eyebrow="Venture design room" title="Make the business make sense." />
      <section className="metal-panel relative overflow-hidden rounded-[2.4rem] p-6 sm:p-9" aria-labelledby="venture-canvas-title">
        <div className="absolute top-0 right-0 size-80 rounded-full bg-copper/[0.08] blur-3xl" />
        <div className="relative flex flex-col justify-between gap-5 sm:flex-row sm:items-end"><div><span className="metal-chip"><DraftingCompass className="size-3.5 text-copper" /> Venture thesis · draft</span><h3 className="mt-5 max-w-2xl font-display text-4xl leading-tight sm:text-5xl" id="venture-canvas-title">Clarity compounds before capital does.</h3></div><p className="max-w-sm text-xs leading-6 text-white/38">Work from evidence, not optimism. These prompts are planning aids—not investment, tax, legal or credit advice.</p></div>
        <div className="relative mt-9 grid gap-3 md:grid-cols-2 xl:grid-cols-4">{canvas.map(({ number, title, prompt, icon: Icon, accent }) => <article className="group min-h-60 rounded-[1.6rem] border border-white/[0.08] bg-white/[0.045] p-5 backdrop-blur transition duration-500 hover:-translate-y-2 hover:border-copper/25 hover:bg-white/[0.065]" key={title}><div className="flex items-center justify-between"><span className="text-[0.62rem] font-black tracking-[0.2em] text-white/25">{number}</span><Icon className={`size-5 ${accent}`} /></div><div className="mt-16"><h4 className="font-display text-2xl">{title}</h4><p className="mt-3 text-xs leading-6 text-white/42">{prompt}</p></div></article>)}</div>
      </section>
      <div className="grid gap-5 lg:grid-cols-[1.15fr_0.85fr]">
        <section className="surface-card p-6 sm:p-8"><div className="flex items-center gap-3"><Boxes className="size-5 text-copper" /><h3 className="font-display text-3xl">Capital sequence</h3></div><div className="mt-7 grid gap-2 sm:grid-cols-4">{["Customer proof", "Founder capital", "Revenue loop", "External capital"].map((step, index) => <div className="rounded-2xl border border-obsidian/[0.07] bg-white/60 p-4" key={step}><span className="text-[0.6rem] font-black text-copper">0{index + 1}</span><p className="mt-7 text-xs font-bold">{step}</p></div>)}</div><p className="mt-5 text-xs leading-5 text-steel">The right sequence depends on the venture. Government support, credit, equity and revenue have different costs, obligations and eligibility boundaries.</p></section>
        <aside className="surface-card p-6 sm:p-8"><p className="text-[0.62rem] font-black tracking-[0.18em] text-copper uppercase">Founder signal</p><h3 className="mt-3 font-display text-3xl">What did you learn this week that changed the plan?</h3><p className="mt-3 text-sm leading-6 text-steel">Strong ventures update from customer evidence. Write one learning, one assumption it challenges and one experiment for next week.</p><Link className={buttonVariants({ variant: "outline", className: "mt-6" })} to="/growth">Open growth roadmap</Link></aside>
      </div>
    </div>
  );
}
