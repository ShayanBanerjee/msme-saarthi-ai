import { ArrowRight, Check, Circle, Compass, Flag, Rocket } from "lucide-react";
import { Link } from "react-router-dom";

import { PageHeader } from "@/components/content/page-header";
import { buttonVariants } from "@/components/ui/button-variants";

const milestones = [
  { title: "Shape the opportunity", note: "Define the customer, problem and revenue model.", status: "complete" },
  { title: "Formalise the enterprise", note: "Choose a structure and use the official Udyam route when applicable.", status: "current" },
  { title: "Build a funding case", note: "Prepare project cost, promoter contribution and cash-flow assumptions.", status: "next" },
  { title: "Find the first market", note: "Select one customer segment and a measurable 30-day sales experiment.", status: "next" },
] as const;

export default function GrowthPage() {
  return (
    <div className="space-y-8">
      <PageHeader
        action={<Link className={buttonVariants()} to="/chat">Build with Saarthi <ArrowRight className="size-4" /></Link>}
        description="Turn a business idea into a practical sequence of evidence, registration, funding readiness and market experiments."
        eyebrow="Your venture runway"
        title="From idea to momentum."
      />

      <section className="metal-panel overflow-hidden rounded-[2rem] p-6 sm:p-8" aria-labelledby="focus-title">
        <div className="grid gap-8 lg:grid-cols-[1.25fr_0.75fr] lg:items-end">
          <div>
            <span className="metal-chip"><Rocket className="size-3.5" /> 30-day focus</span>
            <h3 className="mt-6 max-w-2xl font-display text-4xl leading-tight text-white" id="focus-title">Make your idea fundable by making it specific.</h3>
            <p className="mt-4 max-w-xl text-sm leading-6 text-white/55">Write a one-page project note: customer, solution, setup cost, monthly expenses, price and first ten prospects. Saarthi can help structure it—not invent the numbers.</p>
          </div>
          <div className="rounded-3xl border border-white/10 bg-white/[0.055] p-5 backdrop-blur">
            <div className="flex items-center justify-between text-xs font-bold text-white/65"><span>Foundation readiness</span><span className="text-copper">42%</span></div>
            <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-white/10"><div className="h-full w-[42%] rounded-full bg-copper" /></div>
            <p className="mt-4 text-xs leading-5 text-white/45">Demo progress based on the sample workspace. No financial outcome is predicted.</p>
          </div>
        </div>
      </section>

      <div className="grid gap-5 lg:grid-cols-[1fr_20rem]">
        <section className="surface-card p-6 sm:p-8" aria-labelledby="roadmap-title">
          <div className="flex items-center gap-3"><Compass className="size-5 text-copper" /><h3 className="font-display text-2xl" id="roadmap-title">Founder roadmap</h3></div>
          <ol className="mt-8 space-y-1">
            {milestones.map((item, index) => (
              <li className="relative flex gap-4 pb-7" key={item.title}>
                {index < milestones.length - 1 && <span className="absolute top-7 left-[0.7rem] h-[calc(100%-0.35rem)] w-px bg-steel/20" />}
                <span className={`relative z-10 grid size-6 shrink-0 place-items-center rounded-full ${item.status === "complete" ? "bg-emerald-400 text-obsidian" : item.status === "current" ? "bg-copper text-obsidian shadow-[0_0_0_5px_rgba(196,134,74,0.12)]" : "border border-steel/30 bg-white text-steel"}`}>
                  {item.status === "complete" ? <Check className="size-3.5" /> : <Circle className="size-2.5" />}
                </span>
                <div><h4 className="text-sm font-bold text-obsidian">{item.title}</h4><p className="mt-1 text-sm leading-6 text-steel">{item.note}</p></div>
              </li>
            ))}
          </ol>
        </section>
        <aside className="surface-card p-6">
          <Flag className="size-6 text-copper" />
          <p className="mt-5 text-xs font-black tracking-[0.18em] text-copper uppercase">Today’s move</p>
          <h3 className="mt-2 font-display text-2xl text-obsidian">Interview one potential customer.</h3>
          <p className="mt-3 text-sm leading-6 text-steel">Ask how they solve the problem today, what it costs and what would make them switch.</p>
          <Link className={buttonVariants({ className: "mt-6 w-full" })} to="/chat">Prepare questions</Link>
        </aside>
      </div>
    </div>
  );
}
