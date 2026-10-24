import type { Mode, NodeName, Step } from "../types";

interface Props { mode: Mode; steps: Step[]; active: NodeName | null; done: boolean }

type Box = { x: number; y: number; label: string };
// A wide, left-to-right map: the main path on the top row, the side exits and the retry loop underneath.
const AGENT: Partial<Record<NodeName, Box>> = {
  route: { x: 62, y: 34, label: "Route" },
  retrieve: { x: 192, y: 34, label: "Search" },
  grade: { x: 322, y: 34, label: "Grade" },
  generate: { x: 452, y: 34, label: "Answer" },
  check: { x: 582, y: 34, label: "Check" },
  direct: { x: 62, y: 120, label: "Reply" },
  rewrite: { x: 257, y: 120, label: "Rewrite" },
  not_found: { x: 387, y: 120, label: "Not found" },
};
const PLAIN: Partial<Record<NodeName, Box>> = {
  plain_retrieve: { x: 192, y: 34, label: "Vector search" },
  plain_generate: { x: 452, y: 34, label: "Answer" },
};

const H2 = 20;   // half height of a node box (half width: 52, wider in the plain map for its longer label)
// [from, to, path] – straight lines unless a curve is given
const AGENT_EDGES: [NodeName, NodeName, string?][] = [
  ["route", "retrieve"], ["retrieve", "grade"], ["grade", "generate"], ["generate", "check"],
  ["route", "direct"], ["grade", "not_found", "M322 54 V 82 Q 322 120 335 120"],
  ["grade", "rewrite", "M300 54 L 285 98"], ["rewrite", "retrieve", "M232 104 Q 192 100 192 54"],
  ["check", "generate", "M582 14 Q 582 -4 452 -4 L 452 14"],
];

export function GraphMap({ mode, steps, active }: Props) {
  const W2 = mode === "plain" ? 68 : 52;
  const boxes = mode === "agentic" ? AGENT : PLAIN;
  const edges = mode === "agentic" ? AGENT_EDGES : ([["plain_retrieve", "plain_generate"]] as [NodeName, NodeName][]);
  const visited = new Set(steps.map((s) => s.node));
  const order = steps.map((s) => s.node);
  const walked = new Set(order.slice(1).map((n, i) => `${order[i]}>${n}`));
  const count = (n: NodeName) => order.filter((o) => o === n).length;

  return (
    <svg viewBox="0 -12 646 154" className="graph" role="img" aria-label="The agent's steps" data-testid={`graph-${mode}`}>
      <defs>
        <marker id={`arrow-${mode}`} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M0 0L10 5L0 10z" fill="currentColor" />
        </marker>
      </defs>
      {edges.map(([a, b, path]) => {
        const A = boxes[a]!, B = boxes[b]!;
        const on = walked.has(`${a}>${b}`);
        const d = path ?? (A.y === B.y
          ? `M${A.x + (B.x > A.x ? W2 : -W2)} ${A.y}H${B.x + (B.x > A.x ? -W2 : W2)}`
          : `M${A.x} ${A.y + H2}V${B.y - H2}`);
        return <path key={`${a}${b}`} d={d} className={`edge ${on ? "on" : ""}`} markerEnd={`url(#arrow-${mode})`} />;
      })}
      {Object.entries(boxes).map(([name, b]) => {
        const n = name as NodeName;
        const state = active === n ? "active" : visited.has(n) ? "visited" : "idle";
        const times = count(n);
        return (
          <g key={n} className={`node ${state}`} data-testid={`node-${n}`} data-state={state}>
            <rect x={b!.x - W2} y={b!.y - H2} width={W2 * 2} height={H2 * 2} rx="8" />
            <text x={b!.x} y={b!.y + 6} textAnchor="middle">{b!.label}</text>
            {times > 1 && <g className="badge-count"><circle cx={b!.x + W2 - 2} cy={b!.y - H2 + 1} r="11" /><text x={b!.x + W2 - 2} y={b!.y - H2 + 5} textAnchor="middle">×{times}</text></g>}
          </g>
        );
      })}
    </svg>
  );
}
