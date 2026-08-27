import Settings from "../../pages/Settings";
import "../../styles/final-settings.css";

type SettingsSection = "appearance" | "ai" | "system";

type Props = Readonly<{
  section: SettingsSection;
  navigate(path: string): void;
}>;

const SETTINGS_TABS: ReadonlyArray<Readonly<{ id: SettingsSection; label: string; href: string }>> = [
  { id: "appearance", label: "Appearance", href: "/settings/appearance" },
  { id: "ai", label: "AI", href: "/settings/ai" },
  { id: "system", label: "System", href: "/settings/system" }
];

function FinalSettingsSurface({ section, navigate }: Props) {
  return (
    <section className={`final-settings final-settings--${section}`} aria-labelledby="final-settings-title">
      <header className="final-settings__header">
        <div>
          <p className="eyebrow">Operator controls</p>
          <h1 id="final-settings-title">Settings</h1>
          <p>Configure visual preferences, AI access and system diagnostics without mixing operational controls into the engineering workspace.</p>
        </div>
      </header>
      <nav className="final-settings__tabs" aria-label="Settings sections">
        {SETTINGS_TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            className={tab.id === section ? "final-settings__tab is-active" : "final-settings__tab"}
            aria-current={tab.id === section ? "page" : undefined}
            onClick={() => navigate(tab.href)}
          >
            {tab.label}
          </button>
        ))}
      </nav>
      <Settings />
    </section>
  );
}

export default FinalSettingsSurface;
