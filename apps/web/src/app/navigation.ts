import {
  BadgeIndianRupee,
  ChartNoAxesCombined,
  DraftingCompass,
  ClipboardCheck,
  LayoutDashboard,
  MessageCircleMore,
  ScrollText,
  UserRound,
  type LucideIcon,
} from "lucide-react";

export interface NavigationItem {
  readonly label: string;
  readonly path: string;
  readonly icon: LucideIcon;
}

export const navigationItems: readonly NavigationItem[] = [
  { label: "Saarthi AI", path: "/chat", icon: MessageCircleMore },
  { label: "Overview", path: "/", icon: LayoutDashboard },
  { label: "Schemes", path: "/schemes", icon: ScrollText },
  { label: "Growth plan", path: "/growth", icon: ChartNoAxesCombined },
  { label: "Venture studio", path: "/studio", icon: DraftingCompass },
  { label: "Assessments", path: "/assessments", icon: ClipboardCheck },
  { label: "Plans", path: "/plans", icon: BadgeIndianRupee },
  { label: "Profile", path: "/profile", icon: UserRound },
];
