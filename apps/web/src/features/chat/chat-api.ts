export interface ChatCitation {
  readonly citation_id: string;
  readonly source_label: string;
  readonly source_url: string;
  readonly section: string;
  readonly excerpt: string;
  readonly source_kind: "official_scheme" | "business_guide";
  readonly license_label: string | null;
}

export interface BusinessContext {
  readonly stage?: "idea" | "starting" | "operating" | "scaling";
  readonly goal?: "start" | "fund" | "sell" | "formalise" | "improve";
  readonly location?: string;
  readonly sector?: string;
}

export type AdvisorMode = "business_analyst" | "scheme_navigator" | "growth_strategist" | "funding_readiness";
export type ResponseDepth = "concise" | "balanced" | "deep";

export interface ChatHistoryItem {
  readonly role: "user" | "assistant";
  readonly content: string;
  readonly citation_ids: readonly string[];
}

export interface ChatCallbacks {
  readonly onStatus: (status: "understanding" | "retrieving" | "generating") => void;
  readonly onText: (text: string) => void;
  readonly onReplace: (text: string) => void;
  readonly onCitation: (citation: ChatCitation) => void;
  readonly onFinalCitations: (citations: readonly ChatCitation[]) => void;
}

export class ChatApiError extends Error {}

export async function getChatHistory(conversationId: string): Promise<readonly ChatHistoryItem[]> {
  const response = await fetch(`/api/v1/chat/conversations/${conversationId}/messages`, {
    credentials: "include",
  });
  if (!response.ok) throw new ChatApiError("Saarthi could not restore this workspace.");
  const payload = await response.json() as { items: ChatHistoryItem[] };
  return payload.items;
}

export async function clearChatHistory(conversationId: string): Promise<void> {
  const response = await fetch(`/api/v1/chat/conversations/${conversationId}/messages`, {
    method: "DELETE",
    credentials: "include",
  });
  if (!response.ok) throw new ChatApiError("Saarthi could not clear this conversation.");
}

export async function streamChatMessage(
  conversationId: string,
  message: string,
  businessContext: BusinessContext,
  advisorMode: AdvisorMode,
  responseDepth: ResponseDepth,
  callbacks: ChatCallbacks,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(`/api/v1/chat/conversations/${conversationId}/messages`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      business_context: businessContext,
      advisor_mode: advisorMode,
      response_depth: responseDepth,
    }),
    signal,
  });
  if (!response.ok || !response.body) {
    const problem = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new ChatApiError(problem?.detail ?? "Saarthi could not start this conversation.");
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let receivedFinal = false;
  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value, { stream: !done }).replaceAll("\r\n", "\n");
    if (done && buffer.trim()) buffer += "\n\n";
    const frames = buffer.split("\n\n");
    buffer = frames.pop() ?? "";
    for (const frame of frames) {
      const event = frame.split("\n").find((line) => line.startsWith("event:"))?.slice(6).trim();
      const data = frame.split("\n").find((line) => line.startsWith("data:"))?.slice(5).trim();
      if (!event || !data) continue;
      const payload = JSON.parse(data) as Record<string, unknown>;
      if (event === "status" && (payload.status === "understanding" || payload.status === "retrieving" || payload.status === "generating")) callbacks.onStatus(payload.status);
      if (event === "text_delta" && typeof payload.text === "string") callbacks.onText(payload.text);
      if (event === "text_replace" && typeof payload.text === "string") callbacks.onReplace(payload.text);
      if (event === "citation_preview") callbacks.onCitation(payload.citation as ChatCitation);
      if (event === "error") throw new ChatApiError(typeof payload.message === "string" ? payload.message : "Saarthi could not complete this answer.");
      if (event === "final") {
        callbacks.onFinalCitations(Array.isArray(payload.citations) ? payload.citations as ChatCitation[] : []);
        receivedFinal = true;
      }
    }
    if (done) break;
  }
  if (!receivedFinal) throw new ChatApiError("The answer stream ended before it was complete. Please retry.");
}
