export type Mode = "agentic" | "plain";
export type NodeName =
  | "route" | "direct" | "retrieve" | "grade" | "rewrite" | "generate" | "check" | "not_found"
  | "plain_retrieve" | "plain_generate";

export interface Doc { id: string; title: string; section: string; text: string; score?: number }
export interface Citation { n: number; id: string; title: string; section: string; text: string }

export interface Step {
  node: NodeName;
  query?: string;
  docs?: Doc[];            // what this search returned
  kept?: string[];         // ids the grader kept so far
  missing?: string;        // what the grader said was missing
  unsupported?: string[];  // claims the checker rejected
  route?: string;
}

export interface Stats { seconds: number; steps: number; tokens: number; cost_usd: number }
export type Outcome = "answered" | "direct" | "not_found" | "unverified";

export interface Final { answer: string; citations: Citation[]; outcome: Outcome; queries: string[]; stats: Stats }
