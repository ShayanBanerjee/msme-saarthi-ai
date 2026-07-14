export interface PrivateInvestorSource {
  readonly name: string;
  readonly description: string;
  readonly officialUrl: string;
  readonly verificationUrl?: string;
}

/**
 * Private-capital discovery sources are deliberately separate from government
 * schemes. Inclusion is not an endorsement, ranking, or indication that a fund
 * is currently accepting or suitable for a particular startup.
 */
export const privateInvestorSources: readonly PrivateInvestorSource[] = [
  {
    name: "Peak XV Partners",
    description: "Organisation-published company and portfolio discovery source.",
    officialUrl: "https://www.peakxv.com/our-companies",
  },
  {
    name: "Blume Ventures",
    description: "Organisation-published funds and portfolio discovery source.",
    officialUrl: "https://blume.vc/funds",
  },
  {
    name: "3one4 Capital",
    description: "Organisation-published investment and portfolio information.",
    officialUrl: "https://www.3one4capital.com/",
  },
] as const;

export const investorVerificationSources = {
  sebi: "https://sebi.gov.in/sebiweb/other/OtherAction.do?doRecognisedFpi=yes&intmId=16",
  startupIndia: "https://investorconnect.startupindia.gov.in/",
} as const;
