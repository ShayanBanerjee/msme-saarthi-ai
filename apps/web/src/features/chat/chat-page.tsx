import { ArrowUp, BookOpen, Bot, CircleStop, DatabaseZap, MessageCircleMore, ShieldCheck, Sparkles } from "lucide-react";
import { type FormEvent, useRef, useState } from "react";

import { PageHeader } from "@/components/content/page-header";
import { Button } from "@/components/ui/button";

import { ChatApiError, type ChatCitation, streamChatMessage } from "./chat-api";

const prompts = ["Which official schemes could help me start a manufacturing unit?", "What should I prepare before seeking MSME finance?", "How can Udyam registration help my business journey?"] as const;
const pipeline = ["Question", "Hybrid retrieval", "LangGraph", "Cited answer"] as const;

interface Turn { readonly id: string; readonly question: string; answer: string; citations: ChatCitation[]; }

export default function ChatPage() {
  const [draft, setDraft] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [status, setStatus] = useState<"idle" | "retrieving" | "generating" | "error">("idle");
  const [error, setError] = useState<string | null>(null);
  const conversationId = useRef(crypto.randomUUID());

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const value = draft.trim();
    if (!value || status === "retrieving" || status === "generating") return;
    const id = crypto.randomUUID();
    setTurns((items) => [...items, { id, question: value, answer: "", citations: [] }]);
    setDraft(""); setError(null); setStatus("retrieving");
    try {
      await streamChatMessage(conversationId.current, value, {
        onStatus: setStatus,
        onText: (text) => setTurns((items) => items.map((turn) => turn.id === id ? { ...turn, answer: turn.answer + text } : turn)),
        onCitation: (citation) => setTurns((items) => items.map((turn) => turn.id === id ? { ...turn, citations: [...turn.citations, citation] } : turn)),
      });
      setStatus("idle");
    } catch (cause) {
      setStatus("error");
      setError(cause instanceof ChatApiError ? cause.message : "The assistant connection was interrupted.");
    }
  }

  return (
    <div className="space-y-7">
      <PageHeader description="Ask about starting, financing and growing an Indian enterprise. Saarthi retrieves reviewed evidence, orchestrates a bounded graph and streams a cited answer." eyebrow="Live RAG workspace" title="Ask. Retrieve. Verify." />
      <section className="metal-panel grid min-h-[42rem] overflow-hidden rounded-[2.25rem] lg:grid-cols-[19rem_1fr]" aria-label="Saarthi RAG conversation workspace">
        <aside className="hidden border-r border-white/[0.07] p-5 lg:flex lg:flex-col">
          <span className="metal-chip w-fit"><Sparkles className="size-3.5 text-copper" /> Saarthi RAG</span>
          <p className="mt-8 text-[0.6rem] font-black tracking-[0.2em] text-white/30 uppercase">Try a real question</p>
          <div className="mt-3 space-y-2">{prompts.map((prompt) => <button className="w-full rounded-xl border border-white/[0.07] bg-white/[0.035] p-3 text-left text-xs leading-5 text-white/55 transition hover:border-copper/25 hover:text-white" key={prompt} onClick={() => setDraft(prompt)} type="button">{prompt}</button>)}</div>
          <div className="mt-8"><p className="text-[0.6rem] font-black tracking-[0.18em] text-white/30 uppercase">Evidence path</p><ol className="mt-3 space-y-2">{pipeline.map((step, index) => <li className="flex items-center gap-2 text-[0.67rem] text-white/42" key={step}><span className="grid size-5 place-items-center rounded-full bg-white/[0.06] text-[0.55rem] text-copper">{index + 1}</span>{step}</li>)}</ol></div>
          <div className="mt-auto rounded-2xl border border-copper/15 bg-copper/[0.06] p-4"><ShieldCheck className="size-4 text-copper" /><p className="mt-2 text-[0.68rem] leading-5 text-white/40">AI explains retrieved evidence. It never independently decides scheme eligibility.</p></div>
        </aside>
        <div className="flex min-h-[42rem] flex-col">
          <div className="flex flex-1 flex-col overflow-y-auto px-5 py-8 sm:px-8">
            {turns.length === 0 ? <div className="my-auto max-w-2xl"><span className="grid size-14 place-items-center rounded-2xl border border-white/10 bg-white/[0.06] text-copper"><MessageCircleMore className="size-6" /></span><h3 className="mt-6 font-display text-4xl leading-tight text-white sm:text-5xl">Bring a business question.</h3><p className="mt-3 max-w-lg text-sm leading-7 text-white/48">Include your location, business stage and constraint. Saarthi searches reviewed programme evidence and keeps every scheme claim attached to a source.</p><div className="mt-7 flex flex-wrap gap-2 lg:hidden">{prompts.map((prompt) => <button className="rounded-full border border-white/10 px-4 py-2 text-xs font-semibold text-white/55" key={prompt} onClick={() => setDraft(prompt)} type="button">{prompt}</button>)}</div><div className="mt-9 flex flex-wrap gap-4 text-[0.65rem] text-white/35"><span className="flex items-center gap-2"><DatabaseZap className="size-3.5 text-copper" />Retrieved evidence</span><span className="flex items-center gap-2"><Bot className="size-3.5 text-copper" />Provider-neutral AI</span><span className="flex items-center gap-2"><BookOpen className="size-3.5 text-copper" />Resolvable citations</span></div></div> : <div className="space-y-8">{turns.map((turn) => <article className="space-y-4" key={turn.id}><div className="ml-auto max-w-xl rounded-2xl rounded-br-sm bg-copper px-5 py-4 text-sm font-semibold leading-6 text-obsidian">{turn.question}</div><div className="max-w-3xl rounded-2xl rounded-bl-sm border border-white/[0.08] bg-white/[0.055] p-5"><p className="whitespace-pre-wrap text-sm leading-7 text-white/68">{turn.answer || <span className="animate-pulse text-white/35">Searching reviewed evidence…</span>}</p>{turn.citations.length > 0 && <div className="mt-5 grid gap-2 sm:grid-cols-2">{turn.citations.map((citation) => <a className="flex items-start gap-3 rounded-xl border border-white/[0.08] bg-black/10 p-3 hover:border-copper/30" href={citation.source_url} key={citation.citation_id} rel="noreferrer" target="_blank"><BookOpen className="mt-0.5 size-4 shrink-0 text-copper" /><span><strong className="block text-xs text-white/75">{citation.source_label}</strong><span className="mt-1 block text-[0.62rem] text-white/35">{citation.section} · official source ↗</span></span></a>)}</div>}</div></article>)}</div>}
            {error && <p className="mt-5 rounded-2xl border border-red-400/20 bg-red-400/[0.07] p-4 text-xs text-red-200" role="alert">{error}</p>}
          </div>
          <form className="border-t border-white/[0.07] p-4 sm:p-5" onSubmit={(event) => void submit(event)}><label className="sr-only" htmlFor="chat-message">Message Saarthi</label><div className="flex items-end gap-2 rounded-2xl border border-white/10 bg-white/[0.06] p-2 pl-4 focus-within:border-copper/50"><textarea className="min-h-10 flex-1 resize-none bg-transparent py-2 text-sm text-white outline-none placeholder:text-white/28" id="chat-message" onChange={(event) => setDraft(event.target.value)} placeholder="Ask about an official scheme or business goal…" rows={1} value={draft} /><Button aria-label="Send message" className="bg-copper text-obsidian hover:bg-[#dda460]" disabled={status === "retrieving" || status === "generating"} size="icon" type="submit">{status === "retrieving" || status === "generating" ? <CircleStop className="size-4 animate-pulse" /> : <ArrowUp className="size-4" />}</Button></div><p className="mt-2 text-center text-[0.64rem] text-white/28">{status === "retrieving" ? "Retrieving official evidence…" : status === "generating" ? "Generating a grounded answer…" : "Cited guidance · deterministic eligibility only"}</p></form>
        </div>
      </section>
    </div>
  );
}
