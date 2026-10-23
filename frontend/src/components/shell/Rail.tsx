import AppLink, { type Navigate } from "../../app/AppLink";
import { PEER_NAV_ITEMS, PRIMARY_NAV_ITEMS, type PrimaryNavId } from "../../app/routes";

type RailProps = Readonly<{
  current: PrimaryNavId | undefined;
  currentPath: string;
  navigate: Navigate;
}>;

// Spec 213: the Process / BlueCad / Studio switcher lives in the rail under Design, so it keeps the same
// screen position on all three surfaces whatever each surface's header or navigator does.
function Rail({ current, currentPath, navigate }: RailProps) {
  return (
    <nav className="shell-rail" aria-label="Primary navigation">
      <div className="shell-rail__identity" aria-label="JarvisOS">
        <strong>JarvisOS</strong>
        <span>Engineering workspace</span>
      </div>
      <div className="shell-rail__links">
        {PRIMARY_NAV_ITEMS.map((item) => (
          <div key={item.id} className="shell-rail__group">
            <AppLink
              href={item.href}
              navigate={navigate}
              className="shell-nav-link"
              aria-current={current === item.id ? (item.id === "design" ? "true" : "page") : undefined}
            >
              {item.label}
            </AppLink>
            {item.id === "design" && current === "design" ? (
              <ul className="shell-rail__switcher" aria-label="Design workspaces">
                {PEER_NAV_ITEMS.design.map((peer) => (
                  <li key={peer.href}>
                    <AppLink href={peer.href} navigate={navigate} aria-current={currentPath === peer.href ? "page" : undefined}>
                      {peer.label}
                    </AppLink>
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
        ))}
      </div>
    </nav>
  );
}

export default Rail;
