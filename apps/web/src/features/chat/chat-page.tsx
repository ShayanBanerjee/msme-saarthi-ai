import { ArrowUp, BookOpen, Lightbulb, MessageCircleMore, ShieldCheck, Sparkles } from "lucide-react";
import { type FormEvent, useState } from "react";

import { PageHeader } from "@/components/content/page-header";
import { Button } from "@/components/ui/button";
import { officialSchemes } from "@/features/schemes/scheme-data";

const prompts = ["I want to start a manufacturing unit", "How should I prepare to seek funding?", "Help me find my first customers"] as const;

export default function ChatPage() {
  const [draft, setDraft] = useState("");
  const [question, setQuestion] = useState<string | null>(null);
  const pmegp = officialSchemes.find((scheme) => scheme.id === "pmegp");
  if (!pmegp) {
    throw new Error("The PMEGP source record is required for guided preview mode");
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const value = draft.trim();
    if (!value) return;
    setQuestion(value);
    setDraft("");
  }

  return (
    <div className="space-y-7">
      <PageHeader description="Think through the next move with source-aware guidance. Saarthi can explain evidence, but only the deterministic engine can assess eligibility." eyebrow="Founder intelligence" title="Ask. Decide. Move." />
      <section className="metal-panel grid min-h-[38rem] overflow-hidden rounded-[2.25rem] lg:grid-cols-[17rem_1fr]" aria-label="Saarthi conversation workspace">
        <aside className="hidden border-r border-white/[0.07] p-5 lg:flex lg:flex-col">
          <span className="metal-chip w-fit"><Sparkles className="size-3.5 text-copper" /> Guided preview</span>
          <p className="mt-8 text-[0.6rem] font-black tracking-[0.2em] text-white/30 uppercase">Start with a goal</p>
          <div className="mt-3 space-y-2">{prompts.map((prompt) => <button className="w-full rounded-xl border border-white/[0.07] bg-white/[0.035] p-3 text-left text-xs leading-5 text-white/55 transition hover:border-copper/25 hover:text-white" key={prompt} onClick={() => setDraft(prompt)} type="button">{prompt}</button>)}</div>
          <div className="mt-auto rounded-2xl border border-copper/15 bg-copper/[0.06] p-4"><ShieldCheck className="size-4 text-copper" /><p className="mt-2 text-[0.68rem] leading-5 text-white/40">No approval predictions. No invented scheme rules. Official action stays on official portals.</p></div>
        </aside>
        <div className="flex min-h-[38rem] flex-col">
          <div className="flex flex-1 flex-col overflow-y-auto px-5 py-8 sm:px-8">
            {!question ? <div className="my-auto max-w-2xl"><span className="grid size-14 place-items-center rounded-2xl border border-white/10 bg-white/[0.06] text-copper"><MessageCircleMore className="size-6" /></span><h3 className="mt-6 font-display text-4xl leading-tight text-white sm:text-5xl">What are you building?</h3><p className="mt-3 max-w-lg text-sm leading-7 text-white/48">Share the idea, business stage, location and the biggest constraint. Start broad—Saarthi will help structure the question.</p><div className="mt-7 flex flex-wrap gap-2 lg:hidden">{prompts.map((prompt) => <button className="rounded-full border border-white/10 px-4 py-2 text-xs font-semibold text-white/55" key={prompt} onClick={() => setDraft(prompt)} type="button">{prompt}</button>)}</div></div> : <div className="space-y-6"><div className="ml-auto max-w-xl rounded-2xl rounded-br-sm bg-copper px-5 py-4 text-sm font-semibold leading-6 text-obsidian">{question}</div><div className="max-w-2xl rounded-2xl rounded-bl-sm border border-white/[0.08] bg-white/[0.055] p-5"><p className="text-sm leading-7 text-white/68">A useful first step is to turn that goal into a one-page project brief: customer, problem, proposed offer, setup cost, monthly cost, price and first sales milestone. For a new micro-enterprise, PMEGP is one official programme worth reading—but eligibility and finance depend on its current rules and the implementing authority.</p><a className="mt-5 flex items-start gap-3 rounded-xl border border-white/[0.08] bg-black/10 p-3 hover:border-copper/30" href={pmegp.sourceUrl} rel="noreferrer" target="_blank"><BookOpen className="mt-0.5 size-4 shrink-0 text-copper" /><span><strong className="block text-xs text-white/75">Official source · {pmegp.shortTitle}</strong><span className="mt-1 block text-[0.66rem] text-white/35">{pmegp.authority} · checked {pmegp.verifiedOn}</span></span></a><p className="mt-4 flex gap-2 text-[0.65rem] leading-5 text-white/30"><Lightbulb className="mt-0.5 size-3.5 shrink-0" />Preview guidance uses a fixed, source-backed response. Connect approved authentication and model adapters before production AI chat.</p></div></div>}
          </div>
          <form className="border-t border-white/[0.07] p-4 sm:p-5" onSubmit={submit}><label className="sr-only" htmlFor="chat-message">Message Saarthi</label><div className="flex items-end gap-2 rounded-2xl border border-white/10 bg-white/[0.06] p-2 pl-4 focus-within:border-copper/50"><textarea className="min-h-10 flex-1 resize-none bg-transparent py-2 text-sm text-white outline-none placeholder:text-white/28" id="chat-message" onChange={(event) => setDraft(event.target.value)} placeholder="Describe your business goal…" rows={1} value={draft} /><Button aria-label="Send message" className="bg-copper text-obsidian hover:bg-[#dda460]" size="icon" type="submit"><ArrowUp className="size-4" /></Button></div><p className="mt-2 text-center text-[0.64rem] text-white/28">Preview mode · material scheme claims include official citations</p></form>
        </div>
      </section>
    </div>
  );
}
