import { MathTree } from "../process/BiologyModelLibrary";
import type { StudioDerived, StudioMathNode, StudioStep } from "../../api/studio";

const inner = (tree: StudioMathNode) => tree.children ?? [];
const equation = (target: StudioMathNode, expr: StudioMathNode): StudioMathNode => ({ tag: "math", children: [{ tag: "mrow", children: [...inner(target), { tag: "mo", text: "=" }, ...inner(expr)] }] });

type Selection = { selectedLine?: number | null; onSelectLine?(line: number): void };
function Steps({ steps, selectedLine, onSelectLine }: { steps: StudioStep[] } & Selection) {
  return <>{steps.map((step, index) => {
    if (step.kind === "equation") return <div className="studio-equation" key={index}>{onSelectLine ? <button type="button" className="studio-equation-link" aria-pressed={selectedLine === step.line} onClick={() => onSelectLine(step.line)} title={`Show Python line ${step.line}`}><MathTree node={equation(step.target, step.expr)} /><span>Line {step.line}</span></button> : <MathTree node={equation(step.target, step.expr)} />}</div>;
    if (step.kind === "code") return <div className="studio-unrendered" key={index}><pre>{step.text}</pre><small>Not rendered: {step.reason} (line {step.line})</small></div>;
    if (step.form === "piecewise") return <div className="studio-piecewise" key={index}>{step.cases.map((item, n) => <div className="studio-equation" key={n}><MathTree node={equation(step.target, item.expr)} /><span>{item.condition ? "if" : "otherwise"}</span>{item.condition ? <MathTree node={item.condition} /> : null}</div>)}</div>;
    return <div className="studio-branches" key={index}>{step.branches.map((branch, n) => <div key={n}><div className="studio-equation"><span>{branch.label}</span>{branch.condition ? <MathTree node={branch.condition} /> : null}</div><div className="studio-branch-steps"><Steps steps={branch.steps} selectedLine={selectedLine} onSelectLine={onSelectLine} /></div></div>)}</div>;
  })}</>;
}

export default function DerivedDocumentation({ derived, selectedLine, onSelectLine, entry = "evaluate" }: { derived: StudioDerived; entry?: "evaluate" | "build" } & Selection) {
  if (derived.status === "syntax_error") return <p className="studio-warning">Python syntax error{derived.error?.line ? ` on line ${derived.error.line}` : ""}: {derived.error?.message}. No equations can be derived until it is fixed.</p>;
  return <>
    {derived.status === "entry_missing" ? <p className="studio-warning">The source does not define <code>{entry}</code>, so no equations can be derived.</p> : null}
    {derived.unrendered_count ? <p className="studio-warning">{derived.unrendered_count} construct{derived.unrendered_count === 1 ? " is" : "s are"} shown as code because {derived.unrendered_count === 1 ? "it" : "they"} cannot be rendered as equations.</p> : null}
    {derived.module_constants.length ? <article><strong>Constants</strong><Steps steps={derived.module_constants} selectedLine={selectedLine} onSelectLine={onSelectLine} /></article> : null}
    {derived.functions.map((item) => <article key={item.name}><strong>{item.name}({item.args.join(", ")})</strong>{item.docstring ? <p className="studio-docstring">{item.docstring}</p> : null}{item.steps.length ? <Steps steps={item.steps} selectedLine={selectedLine} onSelectLine={onSelectLine} /> : <p>No statements to derive.</p>}</article>)}
  </>;
}
