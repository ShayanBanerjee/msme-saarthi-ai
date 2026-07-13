export function LoadingScreen() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-fog" role="status">
      <div className="flex items-center gap-3 text-sm font-semibold text-obsidian">
        <span className="size-2 animate-pulse rounded-full bg-copper" aria-hidden="true" />
        Preparing your workspace…
      </div>
    </div>
  );
}
