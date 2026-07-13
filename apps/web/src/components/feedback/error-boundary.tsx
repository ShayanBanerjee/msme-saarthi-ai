import { Component, type ErrorInfo, type ReactNode } from "react";

import { Button } from "@/components/ui/button";

interface Props {
  readonly children: ReactNode;
}

interface State {
  readonly hasError: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = { hasError: false };

  public static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  public componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("Application render failed", { error, componentStack: info.componentStack });
  }

  public render() {
    if (this.state.hasError) {
      return (
        <main className="grid min-h-screen place-items-center bg-fog p-6">
          <section className="max-w-md rounded-3xl border border-obsidian/10 bg-white p-8 text-center shadow-sm">
            <p className="text-xs font-bold tracking-[0.2em] text-coral uppercase">Something changed</p>
            <h1 className="mt-3 font-display text-3xl text-obsidian">This page needs a fresh start.</h1>
            <p className="mt-3 text-sm leading-6 text-steel">
              Your information is safe. Reload the workspace to try again.
            </p>
            <Button className="mt-6" onClick={() => window.location.reload()}>
              Reload workspace
            </Button>
          </section>
        </main>
      );
    }
    return this.props.children;
  }
}
