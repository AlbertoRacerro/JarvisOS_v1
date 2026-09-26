import type { ReactNode } from "react";

// Model output is untrusted text. This renders a small, readable subset of
// Markdown (paragraphs, lists, fenced code, `code`, **bold**) as plain React
// elements: no HTML parsing, no links, no execution.

function inline(text: string, keyPrefix: string): ReactNode[] {
  const parts: ReactNode[] = [];
  const pattern = /(`[^`\n]+`|\*\*[^*\n]+\*\*)/g;
  let last = 0;
  let match: RegExpExecArray | null;
  let index = 0;
  while ((match = pattern.exec(text)) !== null) {
    if (match.index > last) parts.push(text.slice(last, match.index));
    const token = match[0];
    parts.push(token.startsWith("`")
      ? <code key={`${keyPrefix}-${index++}`}>{token.slice(1, -1)}</code>
      : <strong key={`${keyPrefix}-${index++}`}>{token.slice(2, -2)}</strong>);
    last = match.index + token.length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return parts;
}

type Block =
  | { kind: "p"; lines: string[] }
  | { kind: "ul"; items: string[] }
  | { kind: "ol"; items: string[] }
  | { kind: "code"; lines: string[] }
  | { kind: "h"; text: string };

function parse(text: string): Block[] {
  const blocks: Block[] = [];
  const lines = text.replace(/\r\n/g, "\n").split("\n");
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (line.trim().startsWith("```")) {
      const code: string[] = [];
      i += 1;
      while (i < lines.length && !lines[i].trim().startsWith("```")) code.push(lines[i++]);
      i += 1;
      blocks.push({ kind: "code", lines: code });
      continue;
    }
    if (!line.trim()) { i += 1; continue; }
    const heading = /^#{1,4}\s+(.*)$/.exec(line.trim());
    if (heading) { blocks.push({ kind: "h", text: heading[1] }); i += 1; continue; }
    const bullet = /^\s*[-*•]\s+(.*)$/;
    const numbered = /^\s*\d+[.)]\s+(.*)$/;
    const listPattern = bullet.test(line) ? bullet : numbered.test(line) ? numbered : null;
    if (listPattern) {
      const items: string[] = [];
      while (i < lines.length && listPattern.test(lines[i])) {
        items.push((listPattern.exec(lines[i]) as RegExpExecArray)[1]);
        i += 1;
      }
      blocks.push({ kind: listPattern === bullet ? "ul" : "ol", items });
      continue;
    }
    const paragraph: string[] = [];
    while (i < lines.length && lines[i].trim() && !lines[i].trim().startsWith("```") && !bullet.test(lines[i]) && !numbered.test(lines[i])) paragraph.push(lines[i++]);
    blocks.push({ kind: "p", lines: paragraph });
  }
  return blocks;
}

export default function JarvisMessageText({ text }: { text: string }) {
  return <div className="jarvis-message-text">{parse(text).map((block, index) => {
    const key = `b${index}`;
    if (block.kind === "code") return <pre key={key}><code>{block.lines.join("\n")}</code></pre>;
    if (block.kind === "h") return <p key={key} className="jarvis-message-text__heading">{inline(block.text, key)}</p>;
    if (block.kind === "ul") return <ul key={key}>{block.items.map((item, n) => <li key={n}>{inline(item, `${key}-${n}`)}</li>)}</ul>;
    if (block.kind === "ol") return <ol key={key}>{block.items.map((item, n) => <li key={n}>{inline(item, `${key}-${n}`)}</li>)}</ol>;
    return <p key={key}>{block.lines.flatMap((line, n) => n ? [<br key={`br${n}`} />, ...inline(line, `${key}-${n}`)] : inline(line, `${key}-${n}`))}</p>;
  })}</div>;
}
