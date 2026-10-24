import type { Mode } from "./types";

export type ServerEvent =
  | { event: "step"; data: { node: string; query?: string } }
  | { event: "update"; data: Record<string, unknown> & { node: string } }
  | { event: "token"; data: { text: string } }
  | { event: "final"; data: any };

/** POST a question and yield Server-Sent Events as they arrive. */
export async function* ask(question: string, mode: Mode, signal?: AbortSignal): AsyncGenerator<ServerEvent> {
  const res = await fetch("/api/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, mode }),
    signal,
  });
  if (!res.ok || !res.body) throw new Error(`Server error ${res.status}`);

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");
    let end: number;
    while ((end = buffer.indexOf("\n\n")) !== -1) {       // one SSE message ends with a blank line
      const raw = buffer.slice(0, end);
      buffer = buffer.slice(end + 2);
      let event = "message", data = "";
      for (const line of raw.split("\n")) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        else if (line.startsWith("data:")) data += line.slice(5).trim();
      }
      if (data) yield { event, data: JSON.parse(data) } as ServerEvent;
    }
  }
}

export async function health(): Promise<{ chat_model: string; fast_model: string; chunks: number }> {
  return (await fetch("/api/health")).json();
}
