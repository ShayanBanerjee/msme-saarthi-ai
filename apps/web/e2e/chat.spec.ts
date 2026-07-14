import { expect, type Page, test } from "@playwright/test";

const authenticatedUser = {
  id: "10000000-0000-4000-8000-000000000001",
  tenant_id: "20000000-0000-4000-8000-000000000001",
  email: "founder@example.test",
  full_name: "Synthetic Founder",
  business_name: "Synthetic Works",
  initials: "SF",
  plan: "free",
};

const citation = {
  citation_id: "synthetic-citation-1",
  document_id: "synthetic-document-1",
  source_label: "Synthetic MSME Evidence",
  source_url: "https://example.invalid/synthetic-msme-evidence",
  page: 7,
  section: "PDF page 7",
  excerpt: "Synthetic evidence used only for browser testing.",
  source_kind: "official_scheme",
  license_label: null,
};

const streamBody = [
  "event: status\ndata: {\"status\":\"understanding\"}\n\n",
  "event: status\ndata: {\"status\":\"retrieving\"}\n\n",
  `event: citation_preview\ndata: ${JSON.stringify({ citation })}\n\n`,
  "event: status\ndata: {\"status\":\"generating\"}\n\n",
  "event: text_delta\ndata: {\"text\":\"A cited synthetic \"}\n\n",
  "event: text_delta\ndata: {\"text\":\"scheme path is ready to verify.\"}\n\n",
  `event: final\ndata: ${JSON.stringify({ message_id: "30000000-0000-4000-8000-000000000001", citations: [citation], prompt_version: "chat.advisor.v4" })}\n\n`,
].join("");

interface MockChat {
  readonly requests: Record<string, unknown>[];
  readonly browserErrors: string[];
  readonly deletions: { count: number };
}

async function mockAuthenticatedChat(page: Page): Promise<MockChat> {
  const requests: Record<string, unknown>[] = [];
  const browserErrors: string[] = [];
  const deletions = { count: 0 };
  page.on("console", (message) => {
    if (message.type() === "error") browserErrors.push(message.text());
  });
  page.on("pageerror", (error) => browserErrors.push(error.message));

  await page.route("**/api/v1/auth/me", async (route) => {
    await route.fulfill({ json: authenticatedUser });
  });
  await page.route("**/api/v1/chat/conversations/**/messages", async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({ json: { conversation_id: "40000000-0000-4000-8000-000000000001", items: [] } });
      return;
    }
    if (route.request().method() === "DELETE") {
      deletions.count += 1;
      await route.fulfill({ status: 204, body: "" });
      return;
    }
    requests.push(route.request().postDataJSON() as Record<string, unknown>);
    await new Promise((resolve) => setTimeout(resolve, 450));
    await route.fulfill({
      status: 200,
      contentType: "text/event-stream",
      headers: { "Cache-Control": "no-cache" },
      body: streamBody,
    });
  });
  return { requests, browserErrors, deletions };
}

test.describe("@desktop cited chat", () => {
  test("selects a prompt bubble and sends it with the matching advisor mode", async ({ page }) => {
    const { browserErrors, requests } = await mockAuthenticatedChat(page);
    await page.goto("/chat");

    await page.getByRole("button", { name: "Find schemes for my business" }).click();

    await expect(page.getByLabel("Message Saarthi")).toHaveValue(/Government of India/);
    await page.getByRole("button", { name: "Send message" }).click();
    await expect(page.getByText("A cited synthetic scheme path is ready to verify.")).toBeVisible();
    expect(requests).toEqual([expect.objectContaining({ advisor_mode: "scheme_navigator" })]);
    expect(browserErrors).toEqual([]);
  });

  test("submits with Enter and renders streamed text with its citation", async ({ page }) => {
    const { browserErrors, deletions, requests } = await mockAuthenticatedChat(page);
    await page.goto("/chat");

    const composer = page.getByLabel("Message Saarthi");
    await composer.fill("Find a synthetic scheme path for my workshop");
    await composer.press("Enter");

    await expect(page.getByText("Find a synthetic scheme path for my workshop")).toBeVisible();
    await expect(page.getByRole("status", { name: "Saarthi is composing" })).toBeVisible();
    await expect(page.getByText("A cited synthetic scheme path is ready to verify.")).toBeVisible();
    const source = page.getByRole("link", { name: /Synthetic MSME Evidence/ });
    await expect(source).toBeVisible();
    await expect(source).toHaveAttribute("href", citation.source_url);
    await expect(source).toContainText("Official evidence · PDF page 7");
    expect(requests).toEqual([expect.objectContaining({
      message: "Find a synthetic scheme path for my workshop",
      advisor_mode: "business_analyst",
      response_depth: "balanced",
    })]);
    await page.getByRole("button", { name: "Clear conversation" }).click();
    await expect(page.getByRole("heading", { name: "What can I help you grow?" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Find schemes for my business" })).toBeVisible();
    expect(deletions.count).toBe(1);
    expect(browserErrors).toEqual([]);
  });
});

test.describe("@mobile cited chat", () => {
  test("keeps the composer usable before and after a response", async ({ page }) => {
    const { browserErrors } = await mockAuthenticatedChat(page);
    await page.goto("/chat");

    const composer = page.getByLabel("Message Saarthi");
    await expect(composer).toBeVisible();
    await page.getByRole("button", { name: "Create a 30-day growth plan" }).tap();
    await expect(composer).toHaveValue(/30-day sales experiment/);
    await composer.fill("Give my mobile workshop a synthetic next step");
    await page.getByRole("button", { name: "Send message" }).tap();

    await expect(page.getByText("A cited synthetic scheme path is ready to verify.")).toBeVisible();
    await expect(page.getByLabel("Message Saarthi")).toBeVisible();
    await expect(page.getByRole("button", { name: "Send message" })).toBeVisible();
    expect(browserErrors).toEqual([]);
  });
});
