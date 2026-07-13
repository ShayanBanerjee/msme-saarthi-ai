export type SchemeCategory = "Start" | "Fund" | "Market" | "Build skills" | "Register";

export interface OfficialScheme {
  readonly id: string;
  readonly title: string;
  readonly shortTitle: string;
  readonly category: SchemeCategory;
  readonly authority: string;
  readonly summary: string;
  readonly support: string;
  readonly audience: string;
  readonly sourceUrl: string;
  readonly verifiedOn: string;
  readonly featured?: boolean;
}

/**
 * Curated discovery records, not eligibility rules. Claims are intentionally
 * conservative and link directly to the responsible government authority.
 */
export const officialSchemes: readonly OfficialScheme[] = [
  {
    id: "pmegp",
    title: "Prime Minister’s Employment Generation Programme",
    shortTitle: "PMEGP",
    category: "Start",
    authority: "Ministry of MSME · KVIC",
    summary: "Credit-linked support for establishing new micro-enterprises in the non-farm sector.",
    support: "Project support for new manufacturing and service enterprises",
    audience: "Aspiring and first-generation entrepreneurs",
    sourceUrl:
      "https://www.msme.gov.in/offerings/schemes-and-services/details/prime-minister-employment-generation-programme-and-other-credit-support-schemes-1-MDMzETMtQWa",
    verifiedOn: "13 Jul 2026",
    featured: true,
  },
  {
    id: "cgtmse",
    title: "Credit Guarantee Scheme for Micro and Small Enterprises",
    shortTitle: "CGTMSE",
    category: "Fund",
    authority: "Ministry of MSME · CGTMSE",
    summary: "Guarantee support that enables eligible lenders to extend collateral-free credit to MSEs.",
    support: "Credit guarantee through registered member lending institutions",
    audience: "Eligible micro and small enterprises seeking institutional credit",
    sourceUrl: "https://www.cgtmse.in/",
    verifiedOn: "13 Jul 2026",
    featured: true,
  },
  {
    id: "pms",
    title: "Procurement and Marketing Support Scheme",
    shortTitle: "PMS",
    category: "Market",
    authority: "Office of DC (MSME)",
    summary: "Market-access support covering approved fairs, packaging, barcodes and digital commerce activities.",
    support: "Reimbursement or assistance varies by approved component",
    audience: "Micro and small enterprises with a valid Udyam registration",
    sourceUrl:
      "https://www.msme.gov.in/offerings/schemes-and-services/details/marketing-promotion-schemes-1-QzMzETMtQWa",
    verifiedOn: "13 Jul 2026",
  },
  {
    id: "esdp",
    title: "Entrepreneurship and Skill Development Programme",
    shortTitle: "ESDP",
    category: "Build skills",
    authority: "Office of DC (MSME)",
    summary: "Entrepreneurship and skill programmes intended to promote new enterprises and strengthen existing MSMEs.",
    support: "Awareness, entrepreneurship and skill-development programmes",
    audience: "Aspiring entrepreneurs and existing MSMEs",
    sourceUrl:
      "https://www.msme.gov.in/offerings/schemes-and-services/details/entrepreneurship-and-skill-development-programs-gzMxMTMtQWa",
    verifiedOn: "13 Jul 2026",
  },
  {
    id: "udyam",
    title: "Udyam Registration",
    shortTitle: "Udyam",
    category: "Register",
    authority: "Ministry of MSME",
    summary: "The official, free and paperless government registration route for micro, small and medium enterprises.",
    support: "Permanent registration number and online certificate",
    audience: "People intending to establish or register an MSME",
    sourceUrl: "https://www.udyamregistration.gov.in/default.aspx",
    verifiedOn: "13 Jul 2026",
    featured: true,
  },
] as const;

export const schemeCategories: readonly ("All" | SchemeCategory)[] = [
  "All",
  "Start",
  "Fund",
  "Market",
  "Build skills",
  "Register",
];
