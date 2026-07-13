export interface ChatCitation {
  readonly citation_id: string;
  readonly source_label: string;
  readonly source_url: string;
  readonly section: string;
  readonly excerpt: string;
}

export interface ChatCallbacks {
  readonly onStatus: (status: "retrieving" | "generating") => void;
  readonly onText: (text: string) => void;
  readonly onCitation: (citation: ChatCitation) => void;
}

export class ChatApiError extends Error {}

export async function streamChatMessage(conversationId: string, message: string, callbacks: ChatCallbacks): Promise<void> {
  const response = await fetch(`/api/v1/chat/conversations/${conversationId}/messages`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  if (!response.ok || !response.body) {
    const problem = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new ChatApiError(problem?.detail ?? "Saarthi could not start this conversation.");
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value, { stream: !done });
    const frames = buffer.split("\n\n");
    buffer = frames.pop() ?? "";
    for (const frame of frames) {
      const event = frame.split("\n").find((line) => line.startsWith("event:"))?.slice(6).trim();
      const data = frame.split("\n").find((line) => line.startsWith("data:"))?.slice(5).trim();
      if (!event || !data) continue;
      const payload = JSON.parse(data) as Record<string, unknown>;
      if (event === "status" && (payload.status === "retrieving" || payload.status === "generating")) callbacks.onStatus(payload.status);
      if (event === "text_delta" && typeof payload.text === "string") callbacks.onText(payload.text);
      if (event === "citation_preview") callbacks.onCitation(payload.citation as ChatCitation);
    }
    if (done) break;
  }
}
