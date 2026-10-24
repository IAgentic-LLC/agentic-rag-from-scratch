import { useEffect, useState } from "react";
import { health } from "./api";
import { RunPanel } from "./components/RunPanel";
import { useRun } from "./useRun";

type View = "agentic" | "plain" | "compare";
// short labels for the chips, the full question is what gets asked
const EXAMPLES: { label: string; q: string }[] = [
  { label: "Air Glide return", q: "Can a customer return Air Glide sneakers bought in last Friday's drop after 10 days?" },
  { label: "Error E-4012", q: "A customer sees error E-4012 at checkout. What do I tell them?" },
  { label: "Gift cards", q: "Can customers return gift cards?" },
  { label: "thanks!", q: "thanks!" },
];

export default function App() {
  const [view, setView] = useState<View>("agentic");
  const [question, setQuestion] = useState("");
  const [model, setModel] = useState("");
  const agent = useRun("agentic");
  const plain = useRun("plain");
  const busy = agent.run.running || plain.run.running;

  useEffect(() => { health().then((h) => setModel(h.chat_model)).catch(() => setModel("backend offline")); }, []);

  const submit = (q = question) => {
    if (!q.trim()) return;
    setQuestion(q);
    if (view !== "plain") agent.start(q);
    if (view !== "agentic") plain.start(q);
  };

  return (
    <div className="stage">
      <nav className="navbar bg-body-tertiary border-bottom py-2">
        <div className="container-fluid px-4">
          <span className="navbar-brand mb-0 h1 fs-5" data-testid="brand">Dropline <span className="fw-normal text-body-secondary">Support Copilot</span></span>
          <ul className="nav nav-pills views" role="tablist" data-testid="views">
            {(["agentic", "plain", "compare"] as View[]).map((v) => (
              <li className="nav-item" key={v} role="presentation">
                <button role="tab" aria-selected={view === v} className={`nav-link py-1 ${view === v ? "active" : ""}`}
                  onClick={() => setView(v)} data-testid={`view-${v}`}>
                  {v === "agentic" ? "Agentic RAG" : v === "plain" ? "Plain RAG" : "Compare"}
                </button>
              </li>
            ))}
          </ul>
          <span className="badge text-bg-secondary font-monospace fw-normal" data-testid="model">{model}</span>
        </div>
      </nav>

      <div className="container-fluid px-4 pt-2 pb-3 stage-body">
        <form className="ask input-group mb-2" onSubmit={(e) => { e.preventDefault(); submit(); }} data-testid="ask-bar">
          <input className="form-control" value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Ask about Dropline policies, error codes, incidents…" data-testid="question" aria-label="Question" />
          <button className="btn btn-primary px-4" type="submit" disabled={busy} data-testid="ask">{busy ? "Working…" : "Ask"}</button>
        </form>
        <div className="examples d-flex flex-wrap align-items-center gap-2 mb-2" data-testid="examples">
          <span className="small text-body-secondary">Try:</span>
          {EXAMPLES.map((e) => <button type="button" className="btn btn-sm btn-outline-secondary" key={e.label} title={e.q} onClick={() => submit(e.q)}>{e.label}</button>)}
        </div>

        <main className={`runs ${view === "compare" ? "compare" : ""}`} data-testid="runs">
          {view !== "agentic" && <RunPanel mode="plain" run={plain.run} compact={view === "compare"} title={view === "compare" ? "Plain RAG" : undefined} />}
          {view !== "plain" && <RunPanel mode="agentic" run={agent.run} compact={view === "compare"} title={view === "compare" ? "Agentic RAG" : undefined} />}
        </main>
      </div>
    </div>
  );
}
