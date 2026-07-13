import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import { AuthProvider } from "@/features/auth/auth-provider";

import { ApplicationShell } from "./application-shell";

function renderShell(initialPath = "/") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const initialUser = {
    id: "user-1",
    tenantId: "tenant-1",
    email: "ananya@example.test",
    name: "Ananya Rao",
    businessName: "Pragati Works",
    initials: "AR",
    plan: "free",
  };
  return render(
    <QueryClientProvider client={client}>
      <AuthProvider initialUser={initialUser}>
        <MemoryRouter initialEntries={[initialPath]}>
          <Routes>
            <Route element={<ApplicationShell />}>
              <Route element={<h2>Dashboard content</h2>} index />
              <Route element={<h2>Chat content</h2>} path="chat" />
              <Route element={<h2>Assessments content</h2>} path="assessments" />
              <Route element={<h2>Schemes content</h2>} path="schemes" />
              <Route element={<h2>Growth content</h2>} path="growth" />
              <Route element={<h2>Studio content</h2>} path="studio" />
              <Route element={<h2>Plans content</h2>} path="plans" />
              <Route element={<h2>Profile content</h2>} path="profile" />
            </Route>
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    </QueryClientProvider>,
  );
}

describe("application navigation", () => {
  it("renders all desktop navigation destinations and navigates", async () => {
    const user = userEvent.setup();
    renderShell();

    const primaryNavigation = screen.getByRole("navigation", { name: "Primary navigation" });
    expect(primaryNavigation).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Overview" })).toHaveAttribute("href", "/");
    expect(screen.getByRole("link", { name: "Assessments" })).toHaveAttribute(
      "href",
      "/assessments",
    );
    expect(screen.getByRole("link", { name: "Schemes" })).toHaveAttribute("href", "/schemes");
    expect(screen.getByRole("link", { name: "Profile" })).toHaveAttribute("href", "/profile");

    expect(screen.getByRole("link", { name: "Growth plan" })).toHaveAttribute("href", "/growth");
    expect(screen.getByRole("link", { name: "Venture studio" })).toHaveAttribute("href", "/studio");
    expect(screen.getByRole("link", { name: "Plans" })).toHaveAttribute("href", "/plans");

    await user.click(screen.getByRole("link", { name: "Saarthi AI" }));
    expect(screen.getByRole("heading", { name: "Chat content" })).toBeInTheDocument();
  });

  it("opens, navigates with, and closes the mobile menu", async () => {
    const user = userEvent.setup();
    renderShell();

    const openButton = screen.getByRole("button", { name: "Open menu" });
    expect(openButton).toHaveAttribute("aria-expanded", "false");
    await user.click(openButton);

    const dialog = screen.getByRole("dialog", { name: "Mobile navigation" });
    expect(dialog).toBeInTheDocument();
    expect(openButton).toHaveAttribute("aria-expanded", "true");

    await user.click(screen.getAllByRole("link", { name: "Profile" })[1]!);
    expect(screen.getByRole("heading", { name: "Profile content" })).toBeInTheDocument();
    expect(screen.queryByRole("dialog", { name: "Mobile navigation" })).not.toBeInTheDocument();
  });
});
