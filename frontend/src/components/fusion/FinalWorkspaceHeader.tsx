import AppLink, { type Navigate } from "../../app/AppLink";

type WorkspaceGroup = "memory" | "development" | "coding";

type Props = Readonly<{
  group: WorkspaceGroup;
  active: string;
  navigate: Navigate;
}>;

const groups = {
  memory: {
    eyebrow: "Memory",
    title: "Project knowledge",
    description: "Authoritative project basis, versioned engineering models and cited literature.",
    tabs: [
      ["Project Basis", "/memory/project-basis", "project-basis"],
      ["Models", "/memory/models", "models"],
      ["Literature", "/memory/literature", "literature"]
    ]
  },
  development: {
    eyebrow: "JarvisOS operator workspace",
    title: "Development",
    description: "Plan, sequence and trace engineering work without obscuring the technical dependencies behind it.",
    tabs: [
      ["Roadmap", "/development/roadmap/timeline", "roadmap"],
      ["Brainstorm", "/development/brainstorm", "brainstorm"]
    ]
  },
  coding: {
    eyebrow: "JarvisOS operator workspace",
    title: "Coding",
    description: "Inspect repository truth and the actually observed runtime without conflating remote and local state.",
    tabs: [
      ["Repository", "/coding/repository", "repository"],
      ["Runtime", "/coding/runtime", "runtime"]
    ]
  }
} as const;

export default function FinalWorkspaceHeader({ group, active, navigate }: Props) {
  const config = groups[group];
  return (
    <header className="final-fusion__workspace-head">
      <p className="eyebrow">{config.eyebrow}</p>
      <h1>{config.title}</h1>
      <p>{config.description}</p>
      <nav className="final-fusion__peer-tabs" aria-label={`${config.title} destinations`}>
        {config.tabs.map(([label, href, id]) => (
          <AppLink key={href} href={href} navigate={navigate} className={active === id ? "is-active" : ""} aria-current={active === id ? "page" : undefined}>
            {label}
          </AppLink>
        ))}
      </nav>
    </header>
  );
}
