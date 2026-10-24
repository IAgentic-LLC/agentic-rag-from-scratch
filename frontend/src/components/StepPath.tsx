import type { Step } from "../types";

const SHORT: Record<string, string> = {
  route: "Route", direct: "Reply", retrieve: "Search", grade: "Grade", rewrite: "Rewrite", generate: "Answer",
  check: "Check", not_found: "Not found", plain_retrieve: "Vector search", plain_generate: "Answer",
};

/** The steps taken, in order, as one readable line. Used in Compare, where the full map and trace do not fit side by side. */
export function StepPath({ steps, active, done }: { steps: Step[]; active: string | null; done: boolean }) {
  if (!steps.length) return null;
  return (
    <div data-testid="steps-path">
      <div className="small text-body-secondary mb-1">Steps taken: <b className="text-body" data-testid="steps-count">{steps.length}</b></div>
      <div className="d-flex flex-wrap align-items-center gap-1 steps-path">
        {steps.map((s, i) => {
          const last = i === steps.length - 1;
          const cls = last && !done ? "text-bg-primary" : s.node === "rewrite" ? "text-bg-warning" : s.node === "not_found" ? "text-bg-info" : "text-bg-light border";
          return (
            <span key={i} className="d-inline-flex align-items-center gap-1" data-testid={`step-${i + 1}`} data-node={s.node}>
              <span className={`badge fw-medium ${cls} ${active === s.node && !done ? "active-step" : ""}`}>{SHORT[s.node] ?? s.node}</span>
              {!last && <span className="text-body-tertiary" aria-hidden="true">›</span>}
            </span>
          );
        })}
      </div>
    </div>
  );
}
