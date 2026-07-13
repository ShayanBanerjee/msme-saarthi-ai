import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import ChatPage from "./chat-page";

const conversationId = "10000000-0000-4000-8000-000000000001";

function sseResponse(): Response {
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
    "event: final\ndata: {\"message_id\":\"10000000-0000-4000-8000-000000000002\",\"citations\":[],\"prompt_version\":\"chat.advisor.v2\"}\n\n",
  ].join(""), { status: 200, headers: { "Content-Type": "text/event-stream" } });
}

beforeEach(() => {
  vi.spyOn(crypto, "randomUUID").mockReturnValue(conversationId);
});

afterEach(() => vi.restoreAllMocks());

describe("Saarthi advisor workspace", () => {
  it("sends with Enter and includes the user-confirmed business brief", async () => {
    const fetchMock = vi.fn<typeof fetch>().mockImplementation((_input, init) => {
      if (init?.method === "POST") return Promise.resolve(sseResponse());
      return Promise.resolve(new Response(JSON.stringify({ conversation_id: conversationId, items: [] }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }));
    });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();

    render(<ChatPage />);
    await screen.findByRole("heading", { name: /Tell me what is making/i });
    await user.click(screen.getByRole("button", { name: "starting" }));
    await user.type(screen.getByLabelText("State / UT"), "Maharashtra");
    await user.type(screen.getByLabelText("Sector"), "food processing");
    await user.selectOptions(screen.getByLabelText("Priority"), "fund");
    await user.type(screen.getByLabelText("Message Saarthi"), "I need working capital.{enter}");

    await screen.findByText("A focused synthetic answer.");
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    const postCall = fetchMock.mock.calls.find(([, init]) => init?.method === "POST");
    const requestBody = postCall?.[1]?.body;
    expect(typeof requestBody).toBe("string");
    expect(JSON.parse(requestBody as string)).toEqual({
      message: "I need working capital.",
      business_context: {
        stage: "starting",
        goal: "fund",
        location: "Maharashtra",
        sector: "food processing",
      },
    });
    expect(screen.getByText("Official scheme source · p.2")).toBeInTheDocument();
  });

  it("keeps Shift+Enter as a new line", async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(new Response(JSON.stringify({
      conversation_id: conversationId,
      items: [],
    }), { status: 200, headers: { "Content-Type": "application/json" } }));
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();

    render(<ChatPage />);
    const composer = await screen.findByLabelText("Message Saarthi");
    await user.type(composer, "first line{shift>}{enter}{/shift}second line");

    expect(composer).toHaveValue("first line\nsecond line");
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
