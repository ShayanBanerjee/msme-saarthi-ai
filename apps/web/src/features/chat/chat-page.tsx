import {
  ArrowUp,
  BookOpen,
  Bot,
  Check,
  CircleStop,
  Compass,
  DatabaseZap,
  Lightbulb,
  MessageCircleMore,
  Plus,
  ShieldCheck,
  Sparkles,
  Target,
} from "lucide-react";
import { type FormEvent, type KeyboardEvent, useEffect, useRef, useState } from "react";

import { PageHeader } from "@/components/content/page-header";
import { Button } from "@/components/ui/button";

import {
  type BusinessContext,
  ChatApiError,
  type ChatCitation,
  getChatHistory,
  streamChatMessage,
} from "./chat-api";

const prompts = [
  { icon: Compass, label: "Find my best scheme paths", prompt: "Listen to my business situation and help me identify the most relevant official scheme paths to verify." },
  { icon: Target, label: "Build a 30-day growth plan", prompt: "Help me diagnose my biggest growth constraint and turn it into a practical 30-day action plan." },
  { icon: Lightbulb, label: "Pressure-test my idea", prompt: "Ask me focused questions to pressure-test my business idea, customer problem, and route to market." },
] as const;

const stages = ["idea", "starting", "operating", "scaling"] as const;
const goals = [
  ["start", "Start"],
  ["fund", "Access finance"],
  ["sell", "Grow sales"],
  ["formalise", "Formalise"],
  ["improve", "Improve operations"],
] as const;

type ChatStatus = "idle" | "loading" | "understanding" | "retrieving" | "generating" | "error";

interface Turn {
  readonly id: string;
  readonly question: string;
  answer: string;
  citations: ChatCitation[];
}

function getConversationId(): string {
  const key = "msme-saarthi-chat-workspace";
  const storage = (() => {
    try { return window.localStorage ?? null; } catch { return null; }
  })();
  const stored = storage?.getItem(key);
  if (stored) return stored;
  const created = crypto.randomUUID();
  storage?.setItem(key, created);
  return created;
}

function historyToTurns(items: Awaited<ReturnType<typeof getChatHistory>>): Turn[] {
  const turns: Turn[] = [];
  for (const item of items) {
    if (item.role === "user") {
      turns.push({ id: crypto.randomUUID(), question: item.content, answer: "", citations: [] });
    } else {
      const previous = turns.at(-1);
      if (previous) previous.answer = item.content;
    }
  }
  return turns.filter((turn) => turn.answer || turn.question);
}

function AnswerContent({ text }: { readonly text: string }) {
  return <div className="space-y-3">{text.split("\n").filter(Boolean).map((line, index) => {
    const clean = line.replace(/^#{1,3}\s*/, "").replace(/\*\*/g, "").trim();
    const heading = /^(what i heard|best official paths|evidence paths|practical growth moves|a practical next move|your next 30 days)/i.test(clean);
    if (heading) return <h4 className="pt-2 text-[0.68rem] font-black tracking-[0.16em] text-copper uppercase" key={`${clean}-${index}`}>{clean}</h4>;
    if (/^[-•]\s/.test(clean)) return <div className="flex gap-3 text-sm leading-7 text-white/68" key={`${clean}-${index}`}><span className="mt-3 size-1.5 shrink-0 rounded-full bg-copper" /><span>{clean.replace(/^[-•]\s*/, "")}</span></div>;
    return <p className="text-sm leading-7 text-white/68" key={`${clean}-${index}`}>{clean}</p>;
  })}</div>;
}

export default function ChatPage() {
  const [draft, setDraft] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [status, setStatus] = useState<ChatStatus>("loading");
  const [error, setError] = useState<string | null>(null);
  const [context, setContext] = useState<BusinessContext>({});
  const conversationId = useRef(getConversationId());
  const abortController = useRef<AbortController | null>(null);
  const conversationEnd = useRef<HTMLDivElement>(null);
  const form = useRef<HTMLFormElement>(null);
  const isBusy = ["understanding", "retrieving", "generating"].includes(status);

  useEffect(() => {
    let active = true;
    void getChatHistory(conversationId.current)
      .then((items) => { if (active) setTurns(historyToTurns(items)); })
      .catch(() => { if (active) setError("This workspace could not be restored. You can still begin a new conversation."); })
      .finally(() => { if (active) setStatus("idle"); });
    return () => { active = false; abortController.current?.abort(); };
  }, []);

  useEffect(() => {
    conversationEnd.current?.scrollIntoView?.({ behavior: "smooth", block: "end" });
  }, [turns, status]);

  function newWorkspace() {
    const id = crypto.randomUUID();
    try { window.localStorage?.setItem("msme-saarthi-chat-workspace", id); } catch { /* storage is optional */ }
    conversationId.current = id;
    setTurns([]);
    setDraft("");
    setError(null);
    setStatus("idle");
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const value = draft.trim();
    if (!value || isBusy) return;
    const id = crypto.randomUUID();
    const controller = new AbortController();
    abortController.current = controller;
    setTurns((items) => [...items, { id, question: value, answer: "", citations: [] }]);
    setDraft("");
    setError(null);
    setStatus("understanding");
    try {
      await streamChatMessage(conversationId.current, value, context, {
        onStatus: setStatus,
        onText: (text) => setTurns((items) => items.map((turn) => turn.id === id ? { ...turn, answer: turn.answer + text } : turn)),
        onCitation: (citation) => setTurns((items) => items.map((turn) => turn.id === id && !turn.citations.some((item) => item.citation_id === citation.citation_id) ? { ...turn, citations: [...turn.citations, citation] } : turn)),
      }, controller.signal);
      setStatus("idle");
    } catch (cause) {
      if (cause instanceof DOMException && cause.name === "AbortError") {
        setStatus("idle");
        setTurns((items) => items.map((turn) => turn.id === id && !turn.answer ? { ...turn, answer: "Response stopped. You can refine the question and try again." } : turn));
      } else {
        setStatus("error");
        setError(cause instanceof ChatApiError ? cause.message : "The assistant connection was interrupted.");
      }
    } finally {
      abortController.current = null;
    }
  }

  function onComposerKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      form.current?.requestSubmit();
    }
  }

  const statusCopy = status === "understanding" ? "Understanding your business…" : status === "retrieving" ? "Searching official schemes and trusted guides…" : status === "generating" ? "Building a focused, cited response…" : "Enter to send · Shift + Enter for a new line";

  return (
    <div className="space-y-7">
      <PageHeader description="A grounded MSME advisor that listens first, searches reviewed government evidence, and turns the result into practical next steps." eyebrow="AI Saarthi · evidence workspace" title="Ask. Retrieve. Verify." />
      <section className="metal-panel grid min-h-[46rem] overflow-hidden rounded-[2.25rem] xl:grid-cols-[20rem_1fr]" aria-label="Saarthi business advisory workspace">
        <aside className="border-b border-white/[0.07] p-5 xl:border-r xl:border-b-0">
          <div className="flex items-center justify-between">
            <span className="metal-chip"><Sparkles className="size-3.5 text-copper" /> Advisor brief</span>
            <button className="rounded-lg p-2 text-white/35 transition hover:bg-white/[0.06] hover:text-white" onClick={newWorkspace} title="Start a new workspace" type="button"><Plus className="size-4" /></button>
          </div>
          <p className="mt-4 text-xs leading-5 text-white/42">Share only what helps focus the search. Saarthi will ask when something important is missing.</p>
          <fieldset className="mt-6"><legend className="text-[0.6rem] font-black tracking-[0.18em] text-white/30 uppercase">Business stage</legend><div className="mt-2 grid grid-cols-2 gap-2">{stages.map((stage) => <button aria-pressed={context.stage === stage} className={`rounded-xl border px-3 py-2 text-left text-xs capitalize transition ${context.stage === stage ? "border-copper/50 bg-copper/12 text-copper" : "border-white/[0.07] bg-white/[0.03] text-white/45 hover:text-white"}`} key={stage} onClick={() => setContext((value) => ({ ...value, stage }))} type="button">{context.stage === stage && <Check className="mr-1 inline size-3" />}{stage}</button>)}</div></fieldset>
          <label className="mt-5 block text-[0.6rem] font-black tracking-[0.18em] text-white/30 uppercase" htmlFor="advisor-location">State / UT</label>
          <input className="mt-2 w-full rounded-xl border border-white/[0.08] bg-white/[0.035] px-3 py-2.5 text-xs text-white outline-none placeholder:text-white/22 focus:border-copper/45" id="advisor-location" maxLength={80} onChange={(event) => setContext((value) => ({ ...value, location: event.target.value || undefined }))} placeholder="e.g. Maharashtra" value={context.location ?? ""} />
          <label className="mt-4 block text-[0.6rem] font-black tracking-[0.18em] text-white/30 uppercase" htmlFor="advisor-sector">Sector</label>
          <input className="mt-2 w-full rounded-xl border border-white/[0.08] bg-white/[0.035] px-3 py-2.5 text-xs text-white outline-none placeholder:text-white/22 focus:border-copper/45" id="advisor-sector" maxLength={120} onChange={(event) => setContext((value) => ({ ...value, sector: event.target.value || undefined }))} placeholder="e.g. food processing" value={context.sector ?? ""} />
          <label className="mt-4 block text-[0.6rem] font-black tracking-[0.18em] text-white/30 uppercase" htmlFor="advisor-goal">Priority</label>
          <select className="mt-2 w-full rounded-xl border border-white/[0.08] bg-[#171717] px-3 py-2.5 text-xs text-white/65 outline-none focus:border-copper/45" id="advisor-goal" onChange={(event) => setContext((value) => ({ ...value, goal: (event.target.value || undefined) as BusinessContext["goal"] }))} value={context.goal ?? ""}><option value="">Choose one</option>{goals.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select>
          <div className="mt-6 hidden rounded-2xl border border-copper/15 bg-copper/[0.06] p-4 xl:block"><ShieldCheck className="size-4 text-copper" /><p className="mt-2 text-[0.68rem] leading-5 text-white/42">Scheme facts use official evidence. General growth techniques are labeled separately. Eligibility always stays with deterministic rules.</p></div>
        </aside>

        <div className="flex min-h-[46rem] min-w-0 flex-col">
          <div aria-live="polite" className="flex-1 overflow-y-auto px-5 py-7 sm:px-8">
            {status === "loading" ? <div className="grid h-full place-items-center text-sm text-white/35">Restoring your private workspace…</div> : turns.length === 0 ? (
              <div className="mx-auto flex min-h-[32rem] max-w-3xl flex-col justify-center">
                <span className="grid size-14 place-items-center rounded-2xl border border-copper/20 bg-copper/[0.08] text-copper"><MessageCircleMore className="size-6" /></span>
                <h2 className="mt-6 max-w-2xl font-display text-4xl leading-tight text-white sm:text-5xl">Tell me what is making the business difficult right now.</h2>
                <p className="mt-4 max-w-2xl text-sm leading-7 text-white/48">Saarthi listens across turns, asks focused questions, separates official programme evidence from general business practice, and helps you choose the next sensible move.</p>
                <div className="mt-8 grid gap-3 md:grid-cols-3">{prompts.map(({ icon: Icon, label, prompt }) => <button className="group rounded-2xl border border-white/[0.08] bg-white/[0.035] p-4 text-left transition hover:-translate-y-0.5 hover:border-copper/30 hover:bg-copper/[0.05]" key={label} onClick={() => setDraft(prompt)} type="button"><Icon className="size-4 text-copper" /><strong className="mt-3 block text-xs text-white/72">{label}</strong><span className="mt-1 block text-[0.66rem] leading-5 text-white/32">Add it to the composer</span></button>)}</div>
                <div className="mt-8 flex flex-wrap gap-4 text-[0.65rem] text-white/32"><span className="flex items-center gap-2"><DatabaseZap className="size-3.5 text-copper" />Hybrid evidence search</span><span className="flex items-center gap-2"><Bot className="size-3.5 text-copper" />Conversation-aware</span><span className="flex items-center gap-2"><BookOpen className="size-3.5 text-copper" />Source-level citations</span></div>
              </div>
            ) : <div className="mx-auto max-w-4xl space-y-9">{turns.map((turn) => <article className="space-y-4" key={turn.id}><div className="ml-auto max-w-2xl rounded-2xl rounded-br-sm bg-gradient-to-br from-[#dca363] to-[#b8793e] px-5 py-4 text-sm font-semibold leading-6 text-obsidian shadow-[0_12px_40px_rgba(202,139,77,0.14)]">{turn.question}</div><div className="max-w-3xl rounded-2xl rounded-bl-sm border border-white/[0.08] bg-white/[0.045] p-5 sm:p-6"><div className="mb-4 flex items-center gap-2 text-[0.62rem] font-black tracking-[0.14em] text-white/30 uppercase"><span className="grid size-6 place-items-center rounded-lg bg-copper/10 text-copper"><Sparkles className="size-3" /></span>Saarthi analysis</div>{turn.answer ? <AnswerContent text={turn.answer} /> : <p className="animate-pulse text-sm text-white/35">Listening and searching reviewed evidence…</p>}{turn.citations.length > 0 && <div className="mt-6 border-t border-white/[0.07] pt-5"><p className="text-[0.6rem] font-black tracking-[0.16em] text-white/28 uppercase">Evidence used</p><div className="mt-3 grid gap-2 sm:grid-cols-2">{turn.citations.map((citation) => <a className="group flex items-start gap-3 rounded-xl border border-white/[0.08] bg-black/10 p-3 transition hover:border-copper/35" href={citation.source_url} key={citation.citation_id} rel="noreferrer" target="_blank"><BookOpen className="mt-0.5 size-4 shrink-0 text-copper" /><span className="min-w-0"><strong className="block truncate text-xs text-white/75">{citation.source_label}</strong><span className="mt-1 block text-[0.62rem] text-white/35">{citation.source_kind === "official_scheme" ? "Official scheme source" : `Open business guide${citation.license_label ? ` · ${citation.license_label}` : ""}`} · p.{citation.section.replace("PDF page ", "")}</span></span></a>)}</div></div>}</div></article>)}</div>}
            {error && <p className="mx-auto mt-5 max-w-4xl rounded-2xl border border-red-400/20 bg-red-400/[0.07] p-4 text-xs text-red-200" role="alert">{error}</p>}
            <div ref={conversationEnd} />
          </div>

          <form className="border-t border-white/[0.07] bg-black/10 p-4 sm:p-5" onSubmit={(event) => void submit(event)} ref={form}>
            <div className="mx-auto max-w-4xl"><label className="sr-only" htmlFor="chat-message">Message Saarthi</label><div className="flex items-end gap-2 rounded-2xl border border-white/10 bg-white/[0.06] p-2 pl-4 shadow-[0_16px_60px_rgba(0,0,0,0.2)] transition focus-within:border-copper/50"><textarea className="max-h-40 min-h-11 flex-1 resize-none bg-transparent py-2.5 text-sm leading-6 text-white outline-none placeholder:text-white/28" id="chat-message" onChange={(event) => setDraft(event.target.value)} onKeyDown={onComposerKeyDown} placeholder="Describe the business, constraint, and outcome you need…" rows={1} value={draft} />{isBusy ? <Button aria-label="Stop response" className="bg-white/10 text-white hover:bg-white/15" onClick={() => abortController.current?.abort()} size="icon" type="button"><CircleStop className="size-4" /></Button> : <Button aria-label="Send message" className="bg-copper text-obsidian hover:bg-[#dda460]" disabled={!draft.trim()} size="icon" type="submit"><ArrowUp className="size-4" /></Button>}</div><p className="mt-2 text-center text-[0.64rem] text-white/28">{statusCopy}</p></div>
          </form>
        </div>
      </section>
    </div>
  );
}
