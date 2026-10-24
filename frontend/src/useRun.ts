import { useCallback, useRef, useState } from "react";
import { ask } from "./api";
import type { Doc, Final, Mode, NodeName, Step } from "./types";

// Graph node names (from LangGraph updates) -> the step names the UI draws.
const NODE_ALIAS: Record<string, NodeName> = {
  route_question: "route", direct_answer: "direct", retrieve: "retrieve", grade_documents: "grade",
  rewrite_query: "rewrite", generate: "generate", check_grounding: "check", not_found: "not_found", plain: "plain_generate",
};

export interface RunState {
  running: boolean;
  steps: Step[];
  active: NodeName | null;
  answer: string;
  final: Final | null;
  error: string | null;
}

const empty: RunState = { running: false, steps: [], active: null, answer: "", final: null, error: null };

export function useRun(mode: Mode) {
  const [run, setRun] = useState<RunState>(empty);
  const abort = useRef<AbortController | null>(null);

  const start = useCallback(async (question: string) => {
    abort.current?.abort();
    abort.current = new AbortController();
    setRun({ ...empty, running: true });
    try {
      for await (const ev of ask(question, mode, abort.current.signal)) {
        setRun((r) => {
          if (ev.event === "step") {
            const node = ev.data.node as NodeName;
            const answer = node === "generate" ? "" : r.answer;      // a retried answer starts fresh
            return { ...r, active: node, answer, steps: [...r.steps, { node, query: ev.data.query }] };
          }
          if (ev.event === "token") return { ...r, answer: r.answer + ev.data.text };
          if (ev.event === "update") {
            const node = NODE_ALIAS[ev.data.node];
            const steps = [...r.steps];
            const i = steps.map((s) => s.node).lastIndexOf(node === "plain_generate" ? "plain_retrieve" : node);
            if (i >= 0) {
              const d = ev.data as any;
              steps[i] = {
                ...steps[i],
                docs: (d.docs as Doc[] | undefined) ?? steps[i].docs,
                kept: d.relevant ? (d.relevant as Doc[]).map((x) => x.id) : steps[i].kept,
                unsupported: d.unsupported ?? steps[i].unsupported,
                route: d.route ?? steps[i].route,
              };
              if (node === "grade") steps[i].missing = (d as any).missing;
            }
            return { ...r, steps };
          }
          if (ev.event === "final") return { ...r, running: false, active: null, final: ev.data as Final, answer: ev.data.answer };
          return r;
        });
      }
    } catch (e) {
      if ((e as Error).name !== "AbortError") setRun((r) => ({ ...r, running: false, error: (e as Error).message }));
    }
  }, [mode]);

  return { run, start };
}
