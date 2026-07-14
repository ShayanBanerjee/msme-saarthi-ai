import {
  ArrowUp,
  BookOpen,
  CircleStop,
  Clipboard,
  Landmark,
  Lightbulb,
  Plus,
  Trash2,
  TrendingUp,
  UserRound,
  WalletCards,
} from "lucide-react";
import { type FormEvent, type KeyboardEvent, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { BrandMark } from "@/components/brand/brand-mark";

import {
  type AdvisorMode,
  ChatApiError,
  type ChatCitation,
  clearChatHistory,
  getChatHistory,
  streamChatMessage,
} from "./chat-api";

const promptTemplates = [
  {
    mode: "scheme_navigator",
    icon: Landmark,
    title: "Find schemes for my business",
    prompt: "Understand my business first, then find the most relevant Government of India and state schemes. Cite every material scheme claim and tell me what details you still need.",
  },
  {
    mode: "business_analyst",
    icon: Lightbulb,
    title: "Review my business problem",
    prompt: "Listen to my business problem like an experienced analyst. Ask focused questions, identify the likely constraint, and help me choose the next practical step.",
  },
  {
    mode: "funding_readiness",
    icon: WalletCards,
    title: "Prepare for funding",
    prompt: "Help me clarify how much funding I need, what it will be used for, and which evidence I should prepare before approaching a lender or programme.",
  },
  {
    mode: "growth_strategist",
    icon: TrendingUp,
    title: "Create a 30-day growth plan",
    prompt: "Help me choose one customer segment, improve my offer, and create a focused 30-day sales experiment with measurable weekly actions.",
  },
] as const satisfies readonly {
  mode: AdvisorMode;
  icon: typeof Landmark;
  title: string;
  prompt: string;
}[];

type ChatStatus = "idle" | "loading" | "understanding" | "retrieving" | "generating" | "error";

interface Turn {
  readonly id: string;
  readonly question: string;
  answer: string;
  citations: ChatCitation[];
}

function getConversationId(): string {
  const key = "msme-saarthi-chat-workspace";
  let storage: Storage | null = null;
  try { storage = window.localStorage; } catch { storage = null; }
  const stored = storage?.getItem(key);
  if (stored) return stored;
  const created = crypto.randomUUID();
  storage?.setItem(key, created);
  return created;
}

function historyToTurns(items: Awaited<ReturnType<typeof getChatHistory>>): Turn[] {
  const turns: Turn[] = [];
  for (const item of items) {
    if (item.role === "user") turns.push({ id: crypto.randomUUID(), question: item.content, answer: "", citations: [] });
    else {
      const previous = turns.at(-1);
      if (previous) previous.answer = item.content;
    }
  }
  return turns.filter((turn) => turn.answer || turn.question);
}

function AnswerContent({ streaming, text }: { readonly streaming: boolean; readonly text: string }) {
  return <div className="space-y-3">{text.split("\n").filter(Boolean).map((line, index) => {
    const clean = line.replace(/^#{1,3}\s*/, "").replace(/\*\*/g, "").trim();
    const heading = /^(what i heard|analyst diagnosis|best official paths|evidence paths|practical growth moves|a practical next move|your next|risks|assumptions|30\/60\/90)/i.test(clean);
    if (heading) return <h3 className="chat-answer-heading chat-text-enter" key={`${clean}-${index}`}>{clean}</h3>;
    if (/^[-•]\s/.test(clean)) return <div className="chat-answer-list-item chat-text-enter" key={`${clean}-${index}`}><span />{clean.replace(/^[-•]\s*/, "")}</div>;
    return <p className="chat-answer-paragraph chat-text-enter" key={`${clean}-${index}`}>{clean}</p>;
  })}{streaming && <span aria-hidden="true" className="chat-stream-cursor" />}</div>;
}

export default function ChatPage() {
  const [draft, setDraft] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [status, setStatus] = useState<ChatStatus>("loading");
  const [error, setError] = useState<string | null>(null);
  const [advisorMode, setAdvisorMode] = useState<AdvisorMode>("business_analyst");
  const [isClearing, setIsClearing] = useState(false);
  const conversationId = useRef(getConversationId());
  const abortController = useRef<AbortController | null>(null);
  const conversationEnd = useRef<HTMLDivElement>(null);
  const composer = useRef<HTMLTextAreaElement>(null);
  const form = useRef<HTMLFormElement>(null);
  const isBusy = ["understanding", "retrieving", "generating"].includes(status);

  useEffect(() => {
    let active = true;
    void getChatHistory(conversationId.current)
      .then((items) => { if (active) setTurns(historyToTurns(items)); })
      .catch(() => { if (active) setError("This conversation could not be restored. Start a new chat to continue."); })
      .finally(() => { if (active) setStatus("idle"); });
    return () => { active = false; abortController.current?.abort(); };
  }, []);

  useEffect(() => {
    conversationEnd.current?.scrollIntoView?.({ behavior: "smooth", block: "end" });
  }, [turns, status]);

  function newConversation() {
    const id = crypto.randomUUID();
    try { window.localStorage?.setItem("msme-saarthi-chat-workspace", id); } catch { /* Storage is optional. */ }
    conversationId.current = id;
    setTurns([]);
    setDraft("");
    setAdvisorMode("business_analyst");
    setError(null);
    setStatus("idle");
    window.setTimeout(() => composer.current?.focus(), 0);
  }

  function chooseTemplate(template: (typeof promptTemplates)[number]) {
    setAdvisorMode(template.mode);
    setDraft(template.prompt);
    window.setTimeout(() => composer.current?.focus(), 0);
  }

  async function clearConversation() {
    if (isBusy || isClearing) return;
    setIsClearing(true);
    setError(null);
    try {
      await clearChatHistory(conversationId.current);
      newConversation();
    } catch (cause) {
      setError(cause instanceof ChatApiError ? cause.message : "This conversation could not be cleared.");
    } finally {
      setIsClearing(false);
    }
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
      await streamChatMessage(conversationId.current, value, {}, advisorMode, "balanced", {
        onStatus: setStatus,
        onText: (text) => setTurns((items) => items.map((turn) => turn.id === id ? { ...turn, answer: turn.answer + text } : turn)),
        onReplace: (text) => setTurns((items) => items.map((turn) => turn.id === id ? { ...turn, answer: text } : turn)),
        onCitation: (citation) => setTurns((items) => items.map((turn) => turn.id === id && !turn.citations.some((item) => item.citation_id === citation.citation_id) ? { ...turn, citations: [...turn.citations, citation] } : turn)),
        onFinalCitations: (citations) => setTurns((items) => items.map((turn) => turn.id === id ? { ...turn, citations: [...citations] } : turn)),
      }, controller.signal);
      setStatus("idle");
    } catch (cause) {
      if (cause instanceof DOMException && cause.name === "AbortError") {
        setStatus("idle");
        setTurns((items) => items.map((turn) => turn.id === id && !turn.answer ? { ...turn, answer: "Response stopped. Refine the question when you are ready." } : turn));
      } else {
        setStatus("error");
        setError(cause instanceof ChatApiError ? cause.message : "The advisor connection was interrupted.");
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

  const statusCopy = status === "understanding"
    ? "Understanding your question"
    : status === "retrieving"
      ? "Searching reviewed sources"
      : status === "generating"
        ? "Writing a cited response"
        : "Saarthi can make mistakes. Verify important programme details with the cited authority.";

  function renderComposer(isHome: boolean) {
    return <form className={isHome ? "chat-composer-home" : "chat-composer-dock"} onSubmit={(event) => void submit(event)} ref={form}>
      <div className="chat-composer-box">
        <label className="sr-only" htmlFor="chat-message">Message Saarthi</label>
        <textarea
          autoFocus={isHome}
          id="chat-message"
          maxLength={8_000}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={onComposerKeyDown}
          placeholder="Message Saarthi"
          ref={composer}
          rows={isHome ? 2 : 1}
          value={draft}
        />
        <div className="chat-composer-actions">
          <span className="chat-source-state"><span />Official sources on</span>
          {isBusy
            ? <Button aria-label="Stop response" className="chat-send-button" onClick={() => abortController.current?.abort()} size="icon" type="button"><CircleStop className="size-4" /></Button>
            : <Button aria-label="Send message" className="chat-send-button" disabled={!draft.trim()} size="icon" type="submit"><ArrowUp className="size-4" /></Button>}
        </div>
      </div>
      <p className="chat-composer-note">{statusCopy}</p>
    </form>;
  }

  return <section className="chat-workspace" aria-label="Saarthi AI conversation">
    <header className="chat-header">
      <div className="flex min-w-0 items-center gap-2.5">
        <BrandMark size="sm" />
        <div className="min-w-0">
          <h1 className="truncate text-sm font-bold text-obsidian">Saarthi</h1>
          <p className="truncate text-[0.65rem] text-steel">MSME schemes and business guidance</p>
        </div>
      </div>
      <div className="flex items-center gap-1.5">
        <Link aria-label="Open profile" className="chat-header-button chat-profile-button" to="/profile"><UserRound className="size-4" /></Link>
        {turns.length > 0 && <button aria-label="Clear conversation" className="chat-header-button chat-clear-button" disabled={isBusy || isClearing} onClick={() => void clearConversation()} title="Clear conversation" type="button"><Trash2 className="size-4" /><span>{isClearing ? "Clearing…" : "Clear"}</span></button>}
        <button className="chat-header-button" onClick={newConversation} type="button"><Plus className="size-4" /><span className="hidden sm:inline">New chat</span></button>
      </div>
    </header>

    <div aria-live="polite" className="chat-scroll">
      {status === "loading" ? <div className="chat-loading"><BrandMark size="sm" /><span>Opening your conversation…</span></div> : turns.length === 0 ? (
        <div className="chat-empty-state">
          <BrandMark size="lg" />
          <h2>What can I help you grow?</h2>
          <p>Ask naturally about your business, funding, or government schemes. I’ll listen first and show sources when programme facts matter.</p>
          {renderComposer(true)}
          <div aria-label="Suggested prompts" className="chat-suggestions">
            {promptTemplates.map((template) => {
              const Icon = template.icon;
              return <button key={template.title} onClick={() => chooseTemplate(template)} type="button"><Icon className="size-4" /><span>{template.title}</span></button>;
            })}
          </div>
          <div aria-label="Reviewed discovery sources" className="chat-source-portals">
            <span>Reviewed discovery sources</span>
            <a href="https://www.myscheme.gov.in/" rel="noreferrer" target="_blank"><img alt="myScheme" height="13" src="/images/official/myscheme-logo.svg" width="74" /><small>National platform · MeitY</small></a>
            <a href="https://www.startupindia.gov.in/content/sih/en/government-schemes.html" rel="noreferrer" target="_blank"><Landmark className="size-4" /><strong>Startup India</strong><small>Central schemes</small></a>
          </div>
        </div>
      ) : (
        <div className="chat-thread">
          {turns.map((turn, index) => <article className="chat-turn" key={turn.id}>
            <div className="chat-user-message">{turn.question}</div>
            <div className="chat-assistant-row">
              <BrandMark size="sm" />
              <div className="min-w-0 flex-1">
                <div className="chat-answer-toolbar"><strong>Saarthi</strong>{turn.answer && <button aria-label="Copy answer" onClick={() => void navigator.clipboard?.writeText(turn.answer)} type="button"><Clipboard className="size-3.5" /></button>}</div>
                {turn.answer ? <><AnswerContent streaming={isBusy && index === turns.length - 1} text={turn.answer} />{isBusy && index === turns.length - 1 && <div aria-label="Saarthi is composing" className="chat-thinking chat-thinking-inline" role="status"><span /><span /><span /><p>{statusCopy}</p></div>}</> : <div aria-label="Saarthi is composing" className="chat-thinking" role="status"><span /><span /><span /><p>{statusCopy}</p></div>}
                {turn.citations.length > 0 && <div className="chat-citations">
                  <p>Sources</p>
                  <div>{turn.citations.map((citation) => <a href={citation.source_url} key={citation.citation_id} rel="noreferrer" target="_blank"><BookOpen className="size-4" /><span><strong>{citation.source_label}</strong><small>{citation.source_kind === "official_scheme" ? "Official evidence" : `Open business guide${citation.license_label ? ` · ${citation.license_label}` : ""}`} · {citation.section}</small></span></a>)}</div>
                </div>}
              </div>
            </div>
          </article>)}
        </div>
      )}
      {error && <p className="chat-error" role="alert">{error}</p>}
      <div ref={conversationEnd} />
    </div>

    {turns.length > 0 && renderComposer(false)}
  </section>;
}
