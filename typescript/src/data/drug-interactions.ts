export interface DrugInteraction {
  pair: [string, string];
  names: [string, string];
  severity: string;
  note: string;
}

export const DRUG_INTERACTIONS: DrugInteraction[] = [
  {
    pair: ["11289", "1191"],
    names: ["Warfarin", "Aspirin"],
    severity: "major",
    note: "Increased bleeding risk",
  },
  {
    pair: ["6809", "519"],
    names: ["Metformin", "Alcohol"],
    severity: "major",
    note: "Risk of lactic acidosis",
  },
  {
    pair: ["11289", "2395"],
    names: ["Warfarin", "Clopidogrel"],
    severity: "major",
    note: "Significantly increased bleeding risk",
  },
  {
    pair: ["11289", "5521"],
    names: ["Warfarin", "Ibuprofen"],
    severity: "major",
    note: "NSAIDs increase anticoagulant effect and GI bleeding risk",
  },
  {
    pair: ["36567", "41493"],
    names: ["Simvastatin", "Amiodarone"],
    severity: "major",
    note: "Risk of myopathy and rhabdomyolysis",
  },
  {
    pair: ["50166", "3498"],
    names: ["Fluoxetine", "Tramadol"],
    severity: "major",
    note: "Risk of serotonin syndrome",
  },
  {
    pair: ["4493", "5521"],
    names: ["Ciprofloxacin", "Ibuprofen"],
    severity: "moderate",
    note: "Increased risk of CNS stimulation and seizures",
  },
  {
    pair: ["7454", "11289"],
    names: ["Omeprazole", "Warfarin"],
    severity: "moderate",
    note: "Omeprazole may increase anticoagulant effect of warfarin",
  },
];
