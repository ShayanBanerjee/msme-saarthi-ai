import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import SchemesPage from "./schemes-page";

describe("official scheme discovery", () => {
  it("shows official sources and filters by founder goal", async () => {
    const user = userEvent.setup();
    render(<SchemesPage />);

    expect(screen.getByRole("link", { name: /official source for prime minister/i })).toHaveAttribute(
      "href",
      expect.stringContaining("msme.gov.in"),
    );
    await user.click(screen.getByRole("button", { name: "Register" }));
    expect(screen.getByRole("heading", { name: "Udyam Registration" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: /prime minister/i })).not.toBeInTheDocument();
  });

  it("returns a clear empty state for unmatched searches", async () => {
    const user = userEvent.setup();
    render(<SchemesPage />);
    await user.type(screen.getByRole("searchbox", { name: "Search official schemes" }), "no such programme");
    expect(screen.getByRole("heading", { name: "No matching source yet" })).toBeInTheDocument();
  });
});
