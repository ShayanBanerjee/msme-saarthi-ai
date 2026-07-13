import { Building2, Check, Factory, MapPin, ShieldCheck, UsersRound } from "lucide-react";

import { PageHeader } from "@/components/content/page-header";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/features/auth/auth-context";

export default function ProfilePage() {
  const auth = useAuth();
  if (auth.status !== "authenticated") return null;
  const details = [
    { label: "Founder", value: auth.user.name, icon: Building2, confirmed: true },
    { label: "Business or idea", value: auth.user.businessName, icon: MapPin, confirmed: true },
    { label: "Primary activity", value: "Not provided", icon: Factory, confirmed: false },
    { label: "Team size", value: "Not provided", icon: UsersRound, confirmed: false },
  ] as const;
  return (
    <div className="space-y-8">
      <PageHeader
        action={<Button variant="outline"><ShieldCheck className="size-4" /> Encrypted profile</Button>}
        description="A small set of structured facts improves discovery and gives the rule engine auditable inputs."
        eyebrow="Business identity"
        title="Build a stronger profile."
      />
      <div className="grid gap-5 lg:grid-cols-[1fr_22rem]">
        <section className="surface-card p-6 sm:p-8" aria-labelledby="profile-details-title">
          <h3 className="font-display text-3xl" id="profile-details-title">Enterprise facts</h3>
          <dl className="mt-6 divide-y divide-obsidian/[0.07]">
            {details.map(({ label, value, icon: Icon, confirmed }) => (
              <div className="flex items-center gap-4 py-5" key={label}>
                <span className={`grid size-10 place-items-center rounded-2xl ${confirmed ? "bg-obsidian text-copper" : "border border-dashed border-steel/25 text-steel"}`}><Icon className="size-4" /></span>
                <div><dt className="text-[0.65rem] font-bold text-steel">{label}</dt><dd className={`mt-1 text-sm font-bold ${confirmed ? "text-obsidian" : "text-steel"}`}>{value}</dd></div>
                {confirmed && <Check className="ml-auto size-4 text-emerald-600" aria-label="Confirmed" />}
              </div>
            ))}
          </dl>
        </section>
        <aside className="metal-panel rounded-[2rem] p-6">
          <ShieldCheck className="size-7 text-copper" />
          <h3 className="mt-5 font-display text-3xl">Facts, not documents.</h3>
          <p className="mt-3 text-sm leading-6 text-white/48">This preview does not request identity, banking or tax documents. Sensitive production data requires approved retention and security controls.</p>
          <div className="mt-8">
            <div className="flex justify-between text-xs font-bold"><span>Profile strength</span><span className="text-copper">50%</span></div>
            <div className="mt-2 h-1.5 rounded-full bg-white/10"><div className="h-full w-1/2 rounded-full bg-copper" /></div>
          </div>
        </aside>
      </div>
    </div>
  );
}
