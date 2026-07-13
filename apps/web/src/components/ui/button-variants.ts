import { cva } from "class-variance-authority";

export const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-full text-sm font-bold transition-all disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        primary: "bg-obsidian text-white shadow-[0_8px_22px_rgba(16,20,25,.15)] hover:-translate-y-0.5 hover:bg-graphite",
        outline: "border border-obsidian/12 bg-white/70 text-obsidian hover:border-copper/40 hover:bg-white",
        ghost: "text-obsidian hover:bg-obsidian/6",
      },
      size: {
        default: "h-10 px-5",
        icon: "size-10 p-0",
        sm: "h-9 px-4 text-xs",
      },
    },
    defaultVariants: { variant: "primary", size: "default" },
  },
);
