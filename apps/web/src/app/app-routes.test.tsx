import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "./app";

const routes = [
  ["/", "Your ambition deserves a clearer path."],
  ["/chat", "Ask. Decide. Move."],
  ["/assessments", "Evidence before answers."],
  ["/schemes", "Find support with evidence."],
  ["/growth", "From idea to momentum."],
  ["/studio", "Make the business make sense."],
  ["/plans", "Invest in clarity, not noise."],
  ["/profile", "Build a stronger profile."],
] as const;

afterEach(() => vi.restoreAllMocks());

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({
    id: "user-1",
    tenant_id: "tenant-1",
    email: "ananya@example.test",
    full_name: "Ananya Rao",
    business_name: "Pragati Works",
    initials: "AR",
    plan: "free",
  }), { status: 200, headers: { "Content-Type": "application/json" } })));
});

describe("application routes", () => {
  it.each(routes)("renders %s without console errors", async (path, heading) => {
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => undefined);

    render(
      <MemoryRouter initialEntries={[path]}>
        <App />
      </MemoryRouter>,
    );

    expect(await screen.findByRole("heading", { name: heading })).toBeInTheDocument();
    expect(consoleError).not.toHaveBeenCalled();
  });
});
