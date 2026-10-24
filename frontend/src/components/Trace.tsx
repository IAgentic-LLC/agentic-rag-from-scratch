import { useEffect, useRef } from "react";
import type { Step } from "../types";

const LABEL: Record<string, string> = {
  route: "Decided where the question goes", direct: "Replied directly, no search needed",
  retrieve: "Searched the docs", grade: "Checked which results actually help",
  rewrite: "Rewrote the search to find what was missing", generate: "Wrote an answer from the sources",
  check: "Verified every claim against the sources", not_found: "Stopped: the docs don't cover this",
  plain_retrieve: "One vector search", plain_generate: "Wrote an answer (no checks)",
};

/** The step trace. Short runs show every detail. Past 5 steps each step becomes one line and only the newest step stays open,
 *  so all steps remain in frame. Every step and its key parts have a data-testid so the edit can spotlight them. */
export function Trace({ steps }: { steps: Step[] }) {
  const ref = useRef<HTMLOListElement>(null);
  const dense = steps.length > 5;
  useEffect(() => { const el = ref.current; if (el) el.scrollTo({ top: el.scrollHeight, behavior: "smooth" }); }, [steps.length]);
  return (
    <ol className={`list-group list-group-numbered trace ${dense ? "dense" : ""}`} data-testid="trace" ref={ref}>
      {steps.map((s, i) => {
        const open = !dense || i === steps.length - 1;          // dense runs: only the newest step shows its full detail
        const missing = s.node === "grade" && s.kept && s.missing ? s.missing : null;
        return (
          <li key={i} className={`list-group-item t-${s.node} ${open ? "open" : "line"}`} data-testid={`trace-item-${i + 1}`} data-node={s.node}>
            <span className="t-label fw-semibold">{LABEL[s.node] ?? s.node}</span>
            {s.route && <span className="t-detail small text-body-secondary">route: <b className="text-body">{s.route}</b></span>}
            {s.query && <span className="t-detail small font-monospace text-primary-emphasis" data-testid="trace-query" title={s.query}>“{s.query}”</span>}
            {s.docs && (open && !dense
              ? <ul className="list-unstyled d-flex flex-wrap gap-1 mb-0 mt-1 t-chips" data-testid="trace-docs">
                  {s.docs.map((d) => <li key={d.id}><code className="badge text-bg-light border fw-normal">{d.id}</code></li>)}
                </ul>
              : <span className="t-detail small text-body-secondary" data-testid="trace-docs">{s.docs.length} results{open ? <> · <code className="fw-normal">{s.docs[0].id}</code> +{s.docs.length - 1}</> : null}</span>)}
            {s.node === "grade" && s.kept && (
              <span className="t-detail small text-body-secondary" data-testid="trace-grade">kept <b className="text-body">{s.kept.length}</b> so far{missing ? <> · <span data-testid="trace-missing" className="missing" title={missing}>missing: <i>{missing}</i></span></> : null}</span>
            )}
            {s.unsupported && s.unsupported.length > 0 && (
              <span className="t-detail small text-warning-emphasis">Not supported by sources: {s.unsupported.join("; ")}</span>
            )}
          </li>
        );
      })}
    </ol>
  );
}
