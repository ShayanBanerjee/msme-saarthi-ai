import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import ChatPage from "./chat-page";

const conversationId = "10000000-0000-4000-8000-000000000001";

function renderChat() {
  return render(<MemoryRouter><ChatPage /></MemoryRouter>);
}

function sseResponse(replacement?: string): Response {
  const citation = {
    citation_id: "synthetic-official-1",
    document_id: "synthetic-document-1",
    source_label: "Synthetic official source",
    source_url: "https://example.invalid/synthetic",
    page: 2,
    section: "PDF page 2",
    excerpt: "Synthetic evidence.",
    source_kind: "official_scheme",
    license_label: null,
  };
  return new Response([
    "event: status\ndata: {\"status\":\"understanding\"}\n\n",
    "event: status\ndata: {\"status\":\"retrieving\"}\n\n",
    "event: citation_preview\ndata: ", JSON.stringify({ citation }), "\n\n",
    "event: text_delta\ndata: {\"text\":\"A focused synthetic answer.\"}\n\n",
    ...(replacement ? ["event: text_replace\ndata: ", JSON.stringify({ text: replacement }), "\n\n"] : []),
    "event: final\ndata: ", JSON.stringify({
      message_id: "10000000-0000-4000-8000-000000000002",
      citations: [citation],
      prompt_version: "chat.advisor.v4",
    }), "\n\n",
  ].join(""), { status: 200, headers: { "Content-Type": "text/event-stream" } });
}

beforeEach(() => {
  vi.spyOn(crypto, "randomUUID").mockReturnValue(conversationId);
});

afterEach(() => vi.restoreAllMocks());

describe("Saarthi advisor workspace", () => {
  it("sends a message with Enter", async () => {
    const fetchMock = vi.fn<typeof fetch>().mockImplementation((_input, init) => {
      if (init?.method === "POST") return Promise.resolve(sseResponse());
      return Promise.resolve(new Response(JSON.stringify({ conversation_id: conversationId, items: [] }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }));
    });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();

    renderChat();
    await screen.findByRole("heading", { name: /What can I help you grow/i });
    await user.type(screen.getByLabelText("Message Saarthi"), "I need working capital.{enter}");

    await screen.findByText("A focused synthetic answer.");
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    const postCall = fetchMock.mock.calls.find(([, init]) => init?.method === "POST");
    const requestBody = postCall?.[1]?.body;
    expect(typeof requestBody).toBe("string");
    expect(JSON.parse(requestBody as string)).toEqual({
      message: "I need working capital.",
      business_context: {},
      advisor_mode: "business_analyst",
      response_depth: "balanced",
    });
    expect(screen.getByText("Official evidence · PDF page 2")).toBeInTheDocument();
  });

  it("fills the composer from a suggested prompt bubble", async () => {
    vi.stubGlobal("fetch", vi.fn<typeof fetch>().mockResolvedValue(new Response(JSON.stringify({
      conversation_id: conversationId,
      items: [],
    }), { status: 200, headers: { "Content-Type": "application/json" } })));
    const user = userEvent.setup();

    renderChat();
    await screen.findByRole("heading", { name: /What can I help you grow/i });
    await user.click(screen.getByRole("button", { name: "Find schemes for my business" }));

    expect(screen.getByLabelText<HTMLTextAreaElement>("Message Saarthi").value).toContain("Government of India");
  });

  it("keeps Shift+Enter as a new line", async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(new Response(JSON.stringify({
      conversation_id: conversationId,
      items: [],
    }), { status: 200, headers: { "Content-Type": "application/json" } }));
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();

    renderChat();
    const composer = await screen.findByLabelText("Message Saarthi");
    await user.type(composer, "first line{shift>}{enter}{/shift}second line");

    expect(composer).toHaveValue("first line\nsecond line");
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("clears persisted messages and restores the starter prompts", async () => {
    const fetchMock = vi.fn<typeof fetch>().mockImplementation((_input, init) => {
      if (init?.method === "POST") return Promise.resolve(sseResponse());
      if (init?.method === "DELETE") return Promise.resolve(new Response(null, { status: 204 }));
      return Promise.resolve(new Response(JSON.stringify({ conversation_id: conversationId, items: [] }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }));
    });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    renderChat();

    await user.type(await screen.findByLabelText("Message Saarthi"), "Start a temporary chat.{enter}");
    await screen.findByText("A focused synthetic answer.");
    await user.click(screen.getByRole("button", { name: "Clear conversation" }));

    expect(await screen.findByRole("heading", { name: /What can I help you grow/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Find schemes for my business" })).toBeInTheDocument();
    expect(fetchMock.mock.calls.some(([, init]) => init?.method === "DELETE")).toBe(true);
  });

  it("replaces provisional text when the server returns a validated fallback", async () => {
    const replacement = "A safe synthetic fallback.";
    vi.stubGlobal("fetch", vi.fn<typeof fetch>().mockImplementation((_input, init) => {
      if (init?.method === "POST") return Promise.resolve(sseResponse(replacement));
      return Promise.resolve(new Response(JSON.stringify({ conversation_id: conversationId, items: [] }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }));
    }));
    const user = userEvent.setup();
    renderChat();

    await user.type(await screen.findByLabelText("Message Saarthi"), "Test safe replacement.{enter}");

    expect(await screen.findByText(replacement)).toBeInTheDocument();
    expect(screen.queryByText("A focused synthetic answer.")).not.toBeInTheDocument();
  });

  it("shows a safe error when the answer stream fails", async () => {
    const failedStream = new Response(
      "event: status\r\ndata: {\"status\":\"generating\"}\r\n\r\nevent: error\r\ndata: {\"code\":\"answer_generation_failed\",\"message\":\"Saarthi could not complete this answer. Please retry.\",\"retryable\":true}\r\n\r\n",
      { status: 200, headers: { "Content-Type": "text/event-stream" } },
    );
    vi.stubGlobal("fetch", vi.fn<typeof fetch>().mockImplementation((_input, init) => {
      if (init?.method === "POST") return Promise.resolve(failedStream);
      return Promise.resolve(new Response(JSON.stringify({ conversation_id: conversationId, items: [] }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }));
    }));
    const user = userEvent.setup();
    renderChat();

    await user.type(await screen.findByLabelText("Message Saarthi"), "Trigger a safe failure.{enter}");

    expect(await screen.findByRole("alert")).toHaveTextContent("Saarthi could not complete this answer. Please retry.");
  });
});
