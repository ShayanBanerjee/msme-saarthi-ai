import { Bell, ChevronDown, Crown, Menu, Search, X } from "lucide-react";
import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { BrandMark } from "@/components/brand/brand-mark";
import { useAuth } from "@/features/auth/auth-context";
import { cn } from "@/lib/utils";

import { navigationItems } from "./navigation";

function Brand() {
  return (
    <NavLink className="group flex items-center gap-3" to="/" aria-label="MSME Saarthi home">
      <BrandMark />
      <span><span className="block font-display text-[1.35rem] font-semibold leading-none tracking-wide text-white">SAARTHI</span><span className="mt-1 block text-[0.52rem] font-bold tracking-[0.28em] text-white/35 uppercase">MSME intelligence</span></span>
    </NavLink>
  );
}

function NavigationLinks({ onNavigate }: { readonly onNavigate?: () => void }) {
  return (
    <nav aria-label="Primary navigation"><ul className="space-y-1">
      {navigationItems.map(({ label, path, icon: Icon }) => <li key={path}><NavLink className={({ isActive }) => cn("group flex min-h-10 items-center gap-3 rounded-xl px-3 text-[0.82rem] font-semibold transition-all", isActive ? "bg-white/[0.1] text-white shadow-[inset_3px_0_0_#c4864a]" : "text-white/48 hover:bg-white/[0.05] hover:text-white/80")} end={path === "/"} onClick={onNavigate} to={path}><Icon className="size-4" strokeWidth={1.7} />{label}</NavLink></li>)}
    </ul></nav>
  );
}

function Sidebar() {
  return (
    <aside className="fixed inset-y-0 left-0 z-30 hidden w-[17rem] flex-col border-r border-white/[0.07] bg-obsidian px-5 py-6 lg:flex">
      <Brand />
      <div className="mt-11 flex-1"><p className="mb-3 px-3 text-[0.56rem] font-black tracking-[0.24em] text-white/22 uppercase">Command centre</p><NavigationLinks /></div>
      <NavLink className="group rounded-2xl border border-copper/20 bg-copper/[0.07] p-4" to="/plans"><div className="flex items-center gap-2 text-[0.68rem] font-bold tracking-wide text-copper uppercase"><Crown className="size-3.5" /> Saarthi Pro</div><p className="mt-2 text-xs leading-5 text-white/45">Unlock deeper planning and scheme monitoring.</p><span className="mt-3 block text-xs font-bold text-white/75 group-hover:text-copper">Explore membership →</span></NavLink>
    </aside>
  );
}

function MobileNavigation({ open, onClose }: { readonly open: boolean; readonly onClose: () => void }) {
  useEffect(() => { if (!open) return; const handleEscape = (event: KeyboardEvent) => { if (event.key === "Escape") onClose(); }; document.addEventListener("keydown", handleEscape); return () => document.removeEventListener("keydown", handleEscape); }, [onClose, open]);
  if (!open) return null;
  return <div className="fixed inset-0 z-50 lg:hidden" role="dialog" aria-label="Mobile navigation" aria-modal="true"><button className="absolute inset-0 bg-obsidian/55 backdrop-blur-sm" aria-label="Close navigation" onClick={onClose} /><aside className="relative flex h-full w-[min(86vw,20rem)] flex-col bg-obsidian px-5 py-5 shadow-2xl"><div className="flex items-center justify-between"><Brand /><Button aria-label="Close menu" className="text-white hover:bg-white/10 hover:text-white" onClick={onClose} size="icon" variant="ghost"><X className="size-5" /></Button></div><div className="mt-10 flex-1"><NavigationLinks onNavigate={onClose} /></div><p className="border-t border-white/10 pt-5 text-xs leading-5 text-white/35">Official sources. Deterministic assessments. Clear next moves.</p></aside></div>;
}

function TopNavigation({ mobileOpen, onOpenMenu }: { readonly mobileOpen: boolean; readonly onOpenMenu: () => void }) {
  const { pathname } = useLocation();
  const auth = useAuth();
  const [accountOpen, setAccountOpen] = useState(false);
  if (auth.status !== "authenticated") return null;
  const { user } = auth;
  const title = navigationItems.find((item) => item.path === pathname)?.label ?? "Workspace";
  return <header className="sticky top-0 z-20 border-b border-obsidian/[0.07] bg-[#f3f4f2]/85 backdrop-blur-xl"><div className="flex h-[4.5rem] items-center gap-3 px-4 sm:px-7 lg:px-9"><Button aria-expanded={mobileOpen} aria-label="Open menu" className="lg:hidden" onClick={onOpenMenu} size="icon" variant="outline"><Menu className="size-5" /></Button><div className="min-w-0 flex-1"><p className="text-[0.54rem] font-black tracking-[0.22em] text-copper uppercase">Founder workspace</p><h1 className="truncate text-sm font-bold text-obsidian">{title}</h1></div><label className="relative hidden w-full max-w-xs md:block"><span className="sr-only">Search workspace</span><Search className="pointer-events-none absolute top-1/2 left-3.5 size-4 -translate-y-1/2 text-steel" /><input className="h-10 w-full rounded-full border border-obsidian/8 bg-white/60 pr-4 pl-10 text-sm placeholder:text-steel/60" placeholder="Search schemes and actions" type="search" /></label><Button aria-label="Notifications" size="icon" variant="ghost"><Bell className="size-5" /></Button><div className="relative"><button aria-expanded={accountOpen} className="flex items-center gap-2 rounded-full p-1 pr-1.5 text-left hover:bg-white/70" aria-label={`Account menu for ${user.name}`} onClick={() => setAccountOpen((value) => !value)} type="button"><span className="grid size-9 place-items-center rounded-full bg-graphite text-xs font-bold text-copper">{user.initials}</span><span className="hidden max-w-32 xl:block"><span className="block truncate text-xs font-bold">{user.name}</span><span className="block truncate text-[0.62rem] text-steel">{user.plan === "free" ? "Free workspace" : user.plan}</span></span><ChevronDown className="hidden size-3.5 text-steel lg:block" /></button>{accountOpen && <div className="absolute top-12 right-0 w-56 rounded-2xl border border-obsidian/10 bg-white p-2 shadow-2xl"><div className="border-b border-obsidian/7 px-3 py-2"><p className="truncate text-xs font-bold">{user.businessName}</p><p className="mt-1 truncate text-[0.62rem] text-steel">{user.email}</p></div><button className="mt-1 w-full rounded-xl px-3 py-2 text-left text-xs font-bold text-steel hover:bg-obsidian/5 hover:text-obsidian" onClick={() => void auth.logout()} type="button">Sign out</button></div>}</div></div></header>;
}

export function ApplicationShell() {
  const [mobileOpen, setMobileOpen] = useState(false);
  return <div className="min-h-screen"><a className="fixed top-3 left-1/2 z-[60] -translate-x-1/2 -translate-y-20 rounded-full bg-obsidian px-5 py-3 text-sm font-bold text-white transition-transform focus:translate-y-0" href="#main-content">Skip to content</a><Sidebar /><MobileNavigation open={mobileOpen} onClose={() => setMobileOpen(false)} /><div className="lg:pl-[17rem]"><TopNavigation mobileOpen={mobileOpen} onOpenMenu={() => setMobileOpen(true)} /><main className="px-4 py-6 sm:px-7 lg:px-9 lg:py-8" id="main-content" tabIndex={-1}><div className="page-enter mx-auto max-w-[90rem]"><Outlet /></div></main></div></div>;
}
