import { useEffect, useRef, useState } from "react";
import type { Citation, Final } from "../types";

const OUTCOME: Record<string, { label: string; cls: string }> = {
  answered: { label: "Answered · every claim checked", cls: "text-bg-success" },
  direct: { label: "Direct reply", cls: "text-bg-info" },
  not_found: { label: "Not in the docs · no guess", cls: "text-bg-info" },
  unverified: { label: "Some claims unverified", cls: "text-bg-warning" },
};

/** Render **bold**, bullet lines and [1] markers as clickable citation chips. */
function withCitations(text: string, cites: Citation[], open: (c: Citation) => void) {
  const cite = (s: string, key: string) => s.split(/(\[\d+\])/g).map((part, i) => {
    const m = part.match(/^\[(\d+)\]$/);
    const c = m && cites.find((x) => x.n === Number(m[1]));
    return c ? <button key={key + i} type="button" className="btn btn-outline-primary btn-sm py-0 px-1 mx-1 cite" onClick={() => open(c)} data-testid={`cite-${c.n}`}>{c.n}</button> : <span key={key + i}>{part}</span>;
  });
  return text.replace(/^[-*] /gm, "• ").split(/(\*\*[^*\n]+\*\*)/g).map((seg, i) => {
    const b = seg.match(/^\*\*([^*\n]+)\*\*$/);
    return b ? <strong key={i}>{cite(b[1], `b${i}-`)}</strong> : <span key={i}>{cite(seg, `s${i}-`)}</span>;
  });
}

export function Answer({ text, final, plain }: { text: string; final: Final | null; plain: boolean }) {
  const [source, setSource] = useState<Citation | null>(null);
  const [collapsed, setCollapsed] = useState(false);
  const root = useRef<HTMLDivElement>(null);
  const cites = final?.citations ?? [];
  // "Short answer" first, "Details" after: when the finished answer does not fit the frame, the details fold away behind a toggle
  const cut = text.search(/\n\s*\**\s*details\s*:?\s*\**/i);
  const lead = cut > 0 ? text.slice(0, cut) : text, rest = cut > 0 ? text.slice(cut) : "";
  const nDetails = rest ? (rest.match(/^[-*•] /gm) || []).length : 0;
  const scroller = () => root.current?.parentElement ?? null;

  useEffect(() => {                                        // while streaming, the newest words stay in view
    const el = scroller(); if (el && !final) el.scrollTop = el.scrollHeight;
  }, [text, final]);
  useEffect(() => {                                        // once finished: if it does not fit, fold the details away
    const el = scroller(); if (!el || !final) return;
    if (rest && el.scrollHeight > el.clientHeight + 2) setCollapsed(true);
    el.scrollTop = 0;
  }, [final]);                                             // eslint-disable-line react-hooks/exhaustive-deps

  const shown = collapsed ? lead : text;
  return (
    <div className="answer d-flex flex-column gap-3" data-testid="answer" ref={root}>
      {final && !plain && <div className="align-self-start"><span className={`badge ${OUTCOME[final.outcome]?.cls ?? "text-bg-secondary"}`} data-testid="outcome">{OUTCOME[final.outcome]?.label}</span></div>}
      {final && plain && <div className="align-self-start"><span className="badge text-bg-secondary">No checks · answer not verified</span></div>}
      <div className="answer-text" data-testid="answer-text">{withCitations(shown, cites, setSource)}{!final && text && <span className="caret" />}</div>
      {final && rest && true && (
        <button type="button" className="btn btn-sm btn-outline-secondary align-self-start" data-testid="details-toggle" onClick={() => { setCollapsed(!collapsed); }}>
          {collapsed ? `Show details (${nDetails || "more"}) ▾` : "Hide details ▴"}
        </button>
      )}
      {source && (
        <div className="card border-primary shadow source-pop" data-testid="source">
          <div className="card-body">
            <div className="d-flex justify-content-between align-items-start">
              <code>{source.id}</code>
              <button type="button" className="btn-close" onClick={() => setSource(null)} aria-label="Close" />
            </div>
            <div className="small text-body-secondary mb-1">{source.title} › {source.section}</div>
            <p className="mb-0">{source.text}</p>
          </div>
        </div>
      )}
      {final && (
        <div className="stats d-flex gap-3 flex-wrap text-body-secondary small font-monospace border-top pt-2" data-testid="stats">
          <span>{final.stats.seconds.toFixed(1)} s</span><span>{final.stats.steps} steps</span>
          <span>{final.stats.tokens.toLocaleString()} tokens</span><span>${final.stats.cost_usd.toFixed(4)}</span>
        </div>
      )}
    </div>
  );
}
