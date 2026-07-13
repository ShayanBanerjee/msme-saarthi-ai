export type JurisdictionKind = "State" | "Union Territory";
export type SourceStatus = "Portal" | "Policy" | "Draft policy" | "Startup India listing";

export interface JurisdictionSource {
  readonly name: string;
  readonly kind: JurisdictionKind;
  readonly sourceStatus: SourceStatus;
  readonly initiativeUrl: string;
}

export const startupIndiaPlaybookUrl =
  "https://www.startupindia.gov.in/content/dam/startupindia/homebanners/Startup-Schemes-Playbook-June-2026.pdf";

/**
 * Discovery links transcribed from Startup India's June 2026 government-scheme
 * playbook (pp. 103–105). These are entry points, not assertions that a benefit
 * or application window is currently active.
 */
export const jurisdictionSources: readonly JurisdictionSource[] = [
  { name: "Andaman & Nicobar Islands", kind: "Union Territory", sourceStatus: "Policy", initiativeUrl: "https://southandaman.nic.in/document/innovation-and-start-up-policy-2018/" },
  { name: "Andhra Pradesh", kind: "State", sourceStatus: "Portal", initiativeUrl: "https://apis.ap.gov.in/home/" },
  { name: "Arunachal Pradesh", kind: "State", sourceStatus: "Portal", initiativeUrl: "https://www.startup.arunachal.gov.in/startup-policy" },
  { name: "Assam", kind: "State", sourceStatus: "Portal", initiativeUrl: "http://startup.assam.gov.in/" },
  { name: "Bihar", kind: "State", sourceStatus: "Portal", initiativeUrl: "https://startup.bihar.gov.in/" },
  { name: "Chandigarh", kind: "Union Territory", sourceStatus: "Startup India listing", initiativeUrl: startupIndiaPlaybookUrl },
  { name: "Chhattisgarh", kind: "State", sourceStatus: "Portal", initiativeUrl: "https://invest.cg.gov.in/startup" },
  { name: "Dadra & Nagar Haveli and Daman & Diu", kind: "Union Territory", sourceStatus: "Policy", initiativeUrl: "https://swp.dddgov.in/assets/pdf/Notification_IPS_2022_DNH_DD.pdf" },
  { name: "Delhi", kind: "Union Territory", sourceStatus: "Draft policy", initiativeUrl: "https://industries.delhi.gov.in/sites/default/files/Industries/marquee-files/draft_delhi_startup_policy.pdf" },
  { name: "Goa", kind: "State", sourceStatus: "Portal", initiativeUrl: "https://www.startup.goa.gov.in/index" },
  { name: "Gujarat", kind: "State", sourceStatus: "Portal", initiativeUrl: "https://startup.gujarat.gov.in/home" },
  { name: "Haryana", kind: "State", sourceStatus: "Portal", initiativeUrl: "https://startupharyana.gov.in/" },
  { name: "Himachal Pradesh", kind: "State", sourceStatus: "Portal", initiativeUrl: "https://emerginghimachal.hp.gov.in/startup/" },
  { name: "Jammu & Kashmir", kind: "Union Territory", sourceStatus: "Portal", initiativeUrl: "https://startupjk.com/" },
  { name: "Jharkhand", kind: "State", sourceStatus: "Policy", initiativeUrl: "https://abvil.jharkhand.gov.in/documents/Policy2023.pdf" },
  { name: "Karnataka", kind: "State", sourceStatus: "Portal", initiativeUrl: "https://www.missionstartupkarnataka.org/?en" },
  { name: "Kerala", kind: "State", sourceStatus: "Portal", initiativeUrl: "https://startupmission.kerala.gov.in/" },
  { name: "Ladakh", kind: "Union Territory", sourceStatus: "Portal", initiativeUrl: "https://ediiladakh.org/" },
  { name: "Lakshadweep", kind: "Union Territory", sourceStatus: "Policy", initiativeUrl: "https://lakshadweep.gov.in/notice/25-capital-investment-subsidy/" },
  { name: "Madhya Pradesh", kind: "State", sourceStatus: "Portal", initiativeUrl: "https://startup.mp.gov.in/" },
  { name: "Maharashtra", kind: "State", sourceStatus: "Portal", initiativeUrl: "https://msins.in/" },
  { name: "Manipur", kind: "State", sourceStatus: "Portal", initiativeUrl: "https://startupmanipur.in/" },
  { name: "Meghalaya", kind: "State", sourceStatus: "Portal", initiativeUrl: "https://www.primemeghalaya.com/" },
  { name: "Mizoram", kind: "State", sourceStatus: "Portal", initiativeUrl: "https://startupmizoram.com/" },
  { name: "Nagaland", kind: "State", sourceStatus: "Portal", initiativeUrl: "https://www.startupnagaland.in/" },
  { name: "Odisha", kind: "State", sourceStatus: "Portal", initiativeUrl: "https://startupodisha.gov.in/" },
  { name: "Puducherry", kind: "Union Territory", sourceStatus: "Policy", initiativeUrl: "https://industry.py.gov.in/startup-policy-2019" },
  { name: "Punjab", kind: "State", sourceStatus: "Portal", initiativeUrl: "https://pbindustries.gov.in/startup/home" },
  { name: "Rajasthan", kind: "State", sourceStatus: "Portal", initiativeUrl: "https://istart.rajasthan.gov.in/" },
  { name: "Sikkim", kind: "State", sourceStatus: "Portal", initiativeUrl: "https://sikkimentrepreneur.org" },
  { name: "Tamil Nadu", kind: "State", sourceStatus: "Portal", initiativeUrl: "https://startuptn.in/" },
  { name: "Telangana", kind: "State", sourceStatus: "Portal", initiativeUrl: "https://startup.telangana.gov.in/" },
  { name: "Tripura", kind: "State", sourceStatus: "Portal", initiativeUrl: "https://startup.tripura.gov.in/" },
  { name: "Uttar Pradesh", kind: "State", sourceStatus: "Portal", initiativeUrl: "https://startinup.up.gov.in/" },
  { name: "Uttarakhand", kind: "State", sourceStatus: "Portal", initiativeUrl: "https://startuputtarakhand.uk.gov.in/" },
  { name: "West Bengal", kind: "State", sourceStatus: "Portal", initiativeUrl: "https://www.startupbengal.in/" },
] as const;
