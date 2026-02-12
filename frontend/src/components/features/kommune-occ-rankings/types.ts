export interface KommuneScore {
  kommune: string;
  total_bruksareal: number;
}

export interface ScoringSummary {
  kommuner?: KommuneScore[];
}
