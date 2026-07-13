import { Check, Crown, ShieldCheck, Sparkles } from "lucide-react";

import { PageHeader } from "@/components/content/page-header";
import { Button } from "@/components/ui/button";

const plans = [
  {
    name: "Free",
    price: "₹0",
    note: "For exploring an idea",
    features: ["Official scheme discovery", "Saved business profile", "3 guided conversations per month", "Deterministic eligibility previews"],
    action: "Current plan",
    featured: false,
  },
  {
    name: "Saarthi Pro",
    price: "₹999",
    suffix: "/ month",
    note: "For building with momentum",
    features: ["Everything in Free", "Unlimited guided conversations", "Growth-plan workspace", "Priority scheme alerts", "Exportable action briefs"],
    action: "Join Pro waitlist",
    featured: true,
  },
] as const;

export default function PlansPage() {
  return (
    <div className="space-y-8">
      <PageHeader description="Start free. Upgrade when deeper planning and monitoring save you time. Payments are not collected in this preview." eyebrow="Simple membership" title="Invest in clarity, not noise." />
      <section className="mx-auto grid max-w-4xl gap-5 lg:grid-cols-2" aria-label="Membership plans">
        {plans.map((plan) => (
          <article className={plan.featured ? "metal-panel relative overflow-hidden rounded-[2rem] p-7 text-white" : "surface-card p-7"} key={plan.name}>
            {plan.featured && <div className="absolute -top-24 -right-20 size-56 rounded-full bg-copper/20 blur-3xl" />}
            <div className="relative">
              <div className="flex items-center justify-between"><span className={`grid size-11 place-items-center rounded-2xl ${plan.featured ? "bg-copper text-obsidian" : "bg-copper/10 text-copper"}`}>{plan.featured ? <Crown className="size-5" /> : <Sparkles className="size-5" />}</span>{plan.featured && <span className="metal-chip">Founding offer</span>}</div>
              <h3 className="mt-6 font-display text-3xl">{plan.name}</h3>
              <p className={`mt-1 text-sm ${plan.featured ? "text-white/48" : "text-steel"}`}>{plan.note}</p>
              <p className="mt-7"><span className="font-display text-5xl">{plan.price}</span>{"suffix" in plan && <span className="ml-2 text-sm text-white/45">{plan.suffix}</span>}</p>
              <ul className="mt-7 space-y-3">
                {plan.features.map((feature) => <li className="flex items-start gap-3 text-sm" key={feature}><Check className={`mt-0.5 size-4 shrink-0 ${plan.featured ? "text-copper" : "text-emerald-600"}`} /><span className={plan.featured ? "text-white/68" : "text-steel"}>{feature}</span></li>)}
              </ul>
              <Button className={`mt-8 w-full ${plan.featured ? "bg-copper text-obsidian hover:bg-[#dda460]" : ""}`} disabled={!plan.featured}>{plan.action}</Button>
            </div>
          </article>
        ))}
      </section>
      <aside className="mx-auto flex max-w-3xl gap-3 rounded-2xl border border-steel/10 bg-white/60 p-4 text-xs leading-5 text-steel"><ShieldCheck className="mt-0.5 size-4 shrink-0 text-copper" /><p>Pro pricing is a product proposal, not an active subscription. No payment details are requested or stored. Final pricing, taxes, cancellation terms and provider checkout require approval before launch.</p></aside>
    </div>
  );
}
