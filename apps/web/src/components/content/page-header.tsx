import type { ReactNode } from "react";

export function PageHeader({
  eyebrow,
  title,
  description,
  action,
}: {
  readonly eyebrow: string;
  readonly title: string;
  readonly description: string;
  readonly action?: ReactNode;
}) {
  return (
    <header className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
      <div className="max-w-2xl">
        <p className="text-[0.65rem] font-black tracking-[0.2em] text-copper uppercase">{eyebrow}</p>
        <h2 className="mt-2 font-display text-4xl font-semibold leading-[1.02] tracking-[-0.02em] text-obsidian sm:text-5xl">{title}</h2>
        <p className="mt-3 max-w-xl text-sm leading-6 text-steel sm:text-base">{description}</p>
      </div>
      {action}
    </header>
  );
}
