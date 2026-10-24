import type { Mode } from "../types";
import type { RunState } from "../useRun";
import { Answer } from "./Answer";
import { GraphMap } from "./GraphMap";
import { StepPath } from "./StepPath";
import { Trace } from "./Trace";

/** One run: answer | step map | trace. In Compare each panel stacks the answer over map + trace so both fit one screen. */
export function RunPanel({ mode, run, title, compact }: { mode: Mode; run: RunState; title?: string; compact?: boolean }) {
  return (
    <section className={`card panel panel-${mode} ${compact ? "compact" : ""}`} data-testid={`panel-${mode}`}>
      {title && <h2 className="card-header h6 mb-0 panel-title" data-testid={`title-${mode}`}>{title}</h2>}
      <div className="card-body panel-body">
        <div className="col-answer" data-testid={`col-answer-${mode}`}>
          {run.error && <div className="alert alert-danger error" role="alert">{run.error}</div>}
          {(run.answer || run.final) ? <Answer text={run.answer} final={run.final} plain={mode === "plain"} />
            : run.running ? <div className="d-flex align-items-center gap-2 text-body-secondary py-3 thinking"><span className="spinner-border spinner-border-sm" aria-hidden="true" />Thinking…</div>
              : <div className="text-body-secondary py-3 empty">Ask a question or pick an example to start.</div>}
        </div>
        {compact ? (
          <div className="col-path" data-testid={`col-path-${mode}`}><StepPath steps={run.steps} active={run.active} done={!!run.final} /></div>
        ) : (
          <div className="col-side" data-testid={`col-side-${mode}`}>
            <div className="col-graph" data-testid={`col-graph-${mode}`}>
              <GraphMap mode={mode} steps={run.steps} active={run.active} done={!!run.final} />
            </div>
            <div className="col-trace" data-testid={`col-trace-${mode}`}>
              <Trace steps={run.steps} />
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
