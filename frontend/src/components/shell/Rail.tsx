import AppLink, { type Navigate } from "../../app/AppLink";
import { PRIMARY_NAV_ITEMS, type PrimaryNavId } from "../../app/routes";

type RailProps = Readonly<{
  current: PrimaryNavId | undefined;
  navigate: Navigate;
}>;

function Rail({ current, navigate }: RailProps) {
  return (
    <nav className="shell-rail" aria-label="Primary navigation">
      <div className="shell-rail__identity" aria-label="JarvisOS">
        <strong>JarvisOS</strong>
        <span>Engineering workspace</span>
      </div>
      <div className="shell-rail__links">
        {PRIMARY_NAV_ITEMS.map((item) => (
          <AppLink
            key={item.id}
            href={item.href}
            navigate={navigate}
            className="shell-nav-link"
            aria-current={current === item.id ? "page" : undefined}
          >
            {item.label}
          </AppLink>
        ))}
      </div>
    </nav>
  );
}

export default Rail;
