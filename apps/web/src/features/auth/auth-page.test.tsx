import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { AuthContext, type AuthState } from "./auth-context";
import AuthPage from "./auth-page";

function renderPage(register = vi.fn(), login = vi.fn()) {
  const value: AuthState = {
    status: "anonymous",
    user: null,
    register,
    login,
    logout: vi.fn(),
  };
  return render(<AuthContext.Provider value={value}><AuthPage /></AuthContext.Provider>);
}

describe("account onboarding", () => {
  it("validates and submits registration", async () => {
    const user = userEvent.setup();
    const register = vi.fn().mockResolvedValue(undefined);
    renderPage(register);

    await user.type(screen.getByRole("textbox", { name: "Your name" }), "Asha Mehta");
    await user.type(screen.getByRole("textbox", { name: "Idea or business" }), "Asha Works");
    await user.type(screen.getByRole("textbox", { name: "Email" }), "asha@example.test");
    await user.type(screen.getByLabelText("Password"), "Correct-Horse-Foundry-2026");
    await user.click(screen.getByRole("button", { name: /create my workspace/i }));

    expect(register).toHaveBeenCalledWith({
      fullName: "Asha Mehta",
      businessName: "Asha Works",
      email: "asha@example.test",
      password: "Correct-Horse-Foundry-2026",
    });
  });

  it("switches to sign in without showing registration fields", async () => {
    const user = userEvent.setup();
    renderPage();
    await user.click(screen.getByRole("button", { name: "Sign in" }));
    expect(screen.queryByRole("textbox", { name: "Your name" })).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Continue building." })).toBeInTheDocument();
  });
});
