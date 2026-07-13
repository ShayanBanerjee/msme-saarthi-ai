import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { lazy, Suspense, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { ErrorBoundary } from "@/components/feedback/error-boundary";
import { LoadingScreen } from "@/components/feedback/loading-screen";
import { AuthProvider } from "@/features/auth/auth-provider";
import { useAuth } from "@/features/auth/auth-context";
import AuthPage from "@/features/auth/auth-page";
import PublicHomePage from "@/features/landing/public-home-page";

import { ApplicationShell } from "./application-shell";

const DashboardPage = lazy(() => import("@/features/dashboard/dashboard-page"));
const ChatPage = lazy(() => import("@/features/chat/chat-page"));
const AssessmentsPage = lazy(() => import("@/features/assessments/assessments-page"));
const SchemesPage = lazy(() => import("@/features/schemes/schemes-page"));
const GrowthPage = lazy(() => import("@/features/growth/growth-page"));
const PlansPage = lazy(() => import("@/features/plans/plans-page"));
const StudioPage = lazy(() => import("@/features/studio/studio-page"));
const ProfilePage = lazy(() => import("@/features/profile/profile-page"));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30_000 },
  },
});

function AuthenticatedApplication() {
  const auth = useAuth();
  const [authMode, setAuthMode] = useState<"register" | "login" | null>(null);
  if (auth.status === "loading") return <LoadingScreen />;
  if (auth.status === "anonymous") {
    return authMode === null
      ? <PublicHomePage onAuthenticate={setAuthMode} />
      : <AuthPage initialMode={authMode} onBack={() => setAuthMode(null)} />;
  }

  return (
    <Suspense fallback={<LoadingScreen />}>
      <Routes>
        <Route element={<ApplicationShell />}>
          <Route element={<DashboardPage />} index />
          <Route element={<ChatPage />} path="chat" />
          <Route element={<AssessmentsPage />} path="assessments" />
          <Route element={<SchemesPage />} path="schemes" />
          <Route element={<GrowthPage />} path="growth" />
          <Route element={<StudioPage />} path="studio" />
          <Route element={<PlansPage />} path="plans" />
          <Route element={<ProfilePage />} path="profile" />
        </Route>
        <Route element={<Navigate replace to="/" />} path="*" />
      </Routes>
    </Suspense>
  );
}

export function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <AuthenticatedApplication />
        </AuthProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}
