import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import PublicHomePage from "./public-home-page";
import { jurisdictionSources } from "../schemes/jurisdiction-source-data";

describe("public scheme discovery", () => {
  it("leads with sourced schemes and exposes every Indian jurisdiction", () => {
    render(<PublicHomePage onAuthenticate={vi.fn()} />);

    expect(screen.getByRole("heading", { name: /there may be a scheme for your next move/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /open ministry source/i })).toHaveAttribute("href", expect.stringContaining("msme.gov.in"));
    expect(screen.getByText("Andhra Pradesh")).toBeInTheDocument();
    expect(screen.getByText("West Bengal")).toBeInTheDocument();
    expect(screen.getByText("Delhi")).toBeInTheDocument();
    expect(screen.getByText("Draft policy")).toBeInTheDocument();
    expect(jurisdictionSources).toHaveLength(36);
  });

  it("keeps registration behind a subtle user action", async () => {
    const user = userEvent.setup();
    const onAuthenticate = vi.fn();
    render(<PublicHomePage onAuthenticate={onAuthenticate} />);

    await user.click(screen.getByRole("button", { name: "Create free workspace" }));
    expect(onAuthenticate).toHaveBeenCalledWith("register");
  });

  it("filters the state and union territory atlas", async () => {
    const user = userEvent.setup();
    render(<PublicHomePage onAuthenticate={vi.fn()} />);

    await user.type(screen.getByRole("searchbox", { name: /find your state/i }), "Kerala");
    expect(screen.getByText("Kerala")).toBeInTheDocument();
    expect(screen.queryByText("Karnataka")).not.toBeInTheDocument();
  });
});
