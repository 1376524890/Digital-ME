// Shared types between frontend and backend
// These mirror the Pydantic schemas in backend/src/schemas/

// ─── PPPPPI ───
export type PPPPSlotName =
  | "presenting"
  | "predisposing"
  | "precipitating"
  | "perpetuating"
  | "protective"
  | "impact";

export interface PPPPPISlot {
  evidence: string[];
  confidence: number;
  last_updated: string; // ISO datetime
}

// ─── BDI ───
export interface BDIBelief {
  statement: string;
  confidence: number;
  source_ply_id: string;
}

export interface BDIModel {
  beliefs: BDIBelief[];
  desires: BDIBelief[];
  intentions: BDIBelief[];
}

// ─── Cognitive ───
export interface CognitiveError {
  type: "all-or-nothing" | "overgeneralization" | "catastrophizing" | "emotional-reasoning" | "should-statement";
  context: string;
  frequency: "rare" | "occasional" | "frequent";
  confidence: number;
}

// ─── Profile ───
export interface ProfileSnapshot {
  session_id: string;
  pppppi_slots: Record<PPPPSlotName, PPPPPISlot>;
  bdi_model: BDIModel;
  ocean_scores: Record<string, number>;
  cognitive_errors: CognitiveError[];
  vocabulary_profile: {
    preferred: string[];
    avoided: string[];
  };
  syntax_preferences: string[];
  key_taboos: string[];
}

// ─── Interview ───
export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

export interface DimensionCoverage {
  presenting: number;
  predisposing: number;
  precipitating: number;
  perpetuating: number;
  protective: number;
  impact: number;
}

export interface StartInterviewResponse {
  session_id: string;
  greeting: string;
}

export interface PlyEvent {
  ply_id: string;
  coverage_update: DimensionCoverage;
}

export interface SkillOutput {
  skill_file_id: string;
  session_id: string;
  full_content: string;
  token_count: number;
  yaml_valid: boolean;
  warnings: string[];
}
