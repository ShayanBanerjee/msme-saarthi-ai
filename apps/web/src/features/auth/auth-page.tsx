import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowLeft, ArrowRight, Check, Eye, EyeOff, LockKeyhole, ShieldCheck, Sparkles } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { BrandMark } from "@/components/brand/brand-mark";

import { AuthApiError } from "./auth-api";
import { useAuth } from "./auth-context";

const authSchema = z.object({
  fullName: z.string().trim().max(120),
  businessName: z.string().trim().max(160),
  email: z.string().trim().email("Enter a valid email"),
  password: z.string().min(12, "Use at least 12 characters").max(128),
});

type AuthValues = z.infer<typeof authSchema>;

const benefits = ["Official scheme intelligence", "A focused founder roadmap", "Deterministic eligibility evidence"] as const;

export default function AuthPage({ initialMode = "register", onBack }: { readonly initialMode?: "register" | "login"; readonly onBack?: () => void }) {
  const auth = useAuth();
  const [mode, setMode] = useState<"register" | "login">(initialMode);
  const [showPassword, setShowPassword] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);
  const { register, handleSubmit, formState: { errors, isSubmitting }, reset, setError } = useForm<AuthValues>({
    resolver: zodResolver(authSchema),
    defaultValues: { fullName: "", businessName: "", email: "", password: "" },
  });

  function switchMode(next: "register" | "login") {
    setMode(next); setServerError(null); reset();
  }

  const submit = handleSubmit(async (values) => {
    setServerError(null);
    if (mode === "register" && values.fullName.length < 2) {
      setError("fullName", { message: "Enter your name" });
      return;
    }
    if (mode === "register" && values.businessName.length < 2) {
      setError("businessName", { message: "Name your idea or business" });
      return;
    }
    try {
      if (mode === "register") await auth.register(values);
      else await auth.login({ email: values.email, password: values.password });
    } catch (error) {
      setServerError(error instanceof AuthApiError ? error.message : "Unable to reach the account service.");
    }
  });

  return (
    <main className="auth-stage relative min-h-screen overflow-hidden bg-obsidian text-white">
      <div className="auth-orbit auth-orbit-one" aria-hidden="true" /><div className="auth-orbit auth-orbit-two" aria-hidden="true" /><div className="metal-noise absolute inset-0 opacity-30" aria-hidden="true" />
      <div className="relative z-10 mx-auto grid min-h-screen max-w-[100rem] lg:grid-cols-[1.15fr_0.85fr]">
        <section className="flex flex-col justify-between px-6 py-7 sm:px-10 lg:px-14 lg:py-12">
          <div className="flex items-center justify-between gap-4"><div className="flex items-center gap-3"><BrandMark /><div><p className="font-display text-xl font-semibold tracking-wide">SAARTHI</p><p className="text-[0.52rem] font-bold tracking-[0.28em] text-white/35 uppercase">MSME intelligence</p></div></div>{onBack && <button className="flex items-center gap-2 rounded-full border border-white/10 px-4 py-2 text-xs font-bold text-white/55 transition hover:border-copper/35 hover:text-white" onClick={onBack} type="button"><ArrowLeft className="size-3.5" />Explore schemes</button>}</div>
          <div className="my-16 max-w-3xl lg:my-10">
            <span className="metal-chip"><Sparkles className="size-3.5 text-copper" /> Intelligence for builders</span>
            <h1 className="mt-8 font-display text-5xl font-semibold leading-[0.92] tracking-[-0.045em] sm:text-7xl xl:text-[6.4rem]">The future is built by people who <em className="font-normal text-copper">begin.</em></h1>
            <p className="mt-7 max-w-xl text-sm leading-7 text-white/48 sm:text-base">Build a clearer path from idea to enterprise—with official evidence, structured decisions and the confidence to take the next move.</p>
            <ul className="mt-8 grid gap-3 sm:grid-cols-3">{benefits.map((benefit, index) => <li className="group rounded-2xl border border-white/[0.07] bg-white/[0.035] p-4 text-xs leading-5 text-white/55 backdrop-blur transition hover:-translate-y-1 hover:border-copper/25" key={benefit}><span className="mb-3 grid size-6 place-items-center rounded-full bg-copper/12 text-[0.62rem] font-black text-copper">0{index + 1}</span>{benefit}</li>)}</ul>
          </div>
          <p className="flex items-center gap-2 text-[0.64rem] text-white/28"><ShieldCheck className="size-3.5 text-copper" /> Encrypted profile fields · Argon2id credentials · revocable sessions</p>
        </section>

        <section className="flex items-center border-t border-white/[0.07] bg-white/[0.035] p-5 backdrop-blur-3xl sm:p-9 lg:border-t-0 lg:border-l">
          <div className="mx-auto w-full max-w-md rounded-[2rem] border border-white/[0.09] bg-[#151a20]/90 p-6 shadow-[0_35px_100px_rgba(0,0,0,.35),inset_0_1px_0_rgba(255,255,255,.08)] sm:p-8">
            <div className="flex rounded-full border border-white/[0.08] bg-black/20 p-1" aria-label="Account action">
              {(["register", "login"] as const).map((item) => <button aria-pressed={mode === item} className={`flex-1 rounded-full px-4 py-2.5 text-xs font-bold transition ${mode === item ? "bg-copper text-obsidian shadow-lg" : "text-white/42 hover:text-white"}`} key={item} onClick={() => switchMode(item)} type="button">{item === "register" ? "Create account" : "Sign in"}</button>)}
            </div>
            <div className="mt-8"><p className="text-[0.62rem] font-black tracking-[0.2em] text-copper uppercase">{mode === "register" ? "Your founder workspace" : "Welcome back"}</p><h2 className="mt-2 font-display text-4xl">{mode === "register" ? "Begin with intent." : "Continue building."}</h2><p className="mt-2 text-xs leading-5 text-white/38">{mode === "register" ? "Start free. No payment details required." : "Use the account you created on this device."}</p></div>
            <form className="mt-7 space-y-4" onSubmit={(event) => void submit(event)}>
              {mode === "register" && <div className="grid gap-4 sm:grid-cols-2"><Field error={errors.fullName?.message} label="Your name"><input className="auth-input" autoComplete="name" {...register("fullName")} /></Field><Field error={errors.businessName?.message} label="Idea or business"><input className="auth-input" autoComplete="organization" {...register("businessName")} /></Field></div>}
              <Field error={errors.email?.message} label="Email"><input className="auth-input" autoComplete="email" inputMode="email" {...register("email")} /></Field>
              <Field error={errors.password?.message} label="Password"><div className="relative"><input className="auth-input pr-12" autoComplete={mode === "register" ? "new-password" : "current-password"} type={showPassword ? "text" : "password"} {...register("password")} /><button aria-label={showPassword ? "Hide password" : "Show password"} className="absolute top-1/2 right-3 -translate-y-1/2 text-white/35 hover:text-copper" onClick={() => setShowPassword((value) => !value)} type="button">{showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}</button></div></Field>
              {mode === "register" && <p className="flex items-start gap-2 text-[0.65rem] leading-5 text-white/30"><LockKeyhole className="mt-0.5 size-3.5 shrink-0" />Use 12+ characters. Your password is one-way hashed and cannot be recovered.</p>}
              {serverError && <p className="rounded-xl border border-red-400/20 bg-red-400/[0.07] p-3 text-xs leading-5 text-red-200" role="alert">{serverError}</p>}
              <Button className="h-12 w-full bg-copper text-obsidian shadow-[0_12px_35px_rgba(196,134,74,.22)] hover:bg-[#dda460]" disabled={isSubmitting} type="submit">{isSubmitting ? "Securing your workspace…" : mode === "register" ? "Create my workspace" : "Enter workspace"}<ArrowRight className="size-4" /></Button>
            </form>
            {mode === "register" && <p className="mt-5 flex items-center justify-center gap-2 text-[0.62rem] text-white/25"><Check className="size-3 text-emerald-400" /> Free membership · cancel anytime when paid plans launch</p>}
          </div>
        </section>
      </div>
    </main>
  );
}

function Field({ label, error, children }: { readonly label: string; readonly error?: string; readonly children: React.ReactNode }) {
  return <label className="block"><span className="mb-2 block text-[0.65rem] font-bold text-white/48">{label}</span>{children}{error && <span className="mt-1.5 block text-[0.62rem] text-red-300">{error}</span>}</label>;
}
