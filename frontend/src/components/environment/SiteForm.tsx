import type { Site } from "./types";

export type SiteDraft = Omit<Site, "latitude" | "longitude" | "elevation_m"> & {
  latitude: string;
  longitude: string;
  elevation_m: string;
};

export function toSiteDraft(site: Site | null): SiteDraft {
  return {
    name: site?.name ?? "",
    latitude: site ? String(site.latitude) : "",
    longitude: site ? String(site.longitude) : "",
    elevation_m: site ? String(site.elevation_m) : "",
    timezone: site?.timezone ?? "UTC",
    water_body: site?.water_body ?? "",
    revision: site?.revision ?? 0,
  };
}

export function sitePayload(draft: SiteDraft): Site {
  return {
    ...draft,
    latitude: Number(draft.latitude),
    longitude: Number(draft.longitude),
    elevation_m: Number(draft.elevation_m),
    water_body: draft.water_body || null,
  };
}

type Props = {
  value: SiteDraft;
  onChange: (site: SiteDraft) => void;
  onSave: () => void;
  disabled: boolean;
};

export function SiteForm({ value, onChange, onSave, disabled }: Props) {
  const update = (key: keyof SiteDraft, next: string) => onChange({ ...value, [key]: next });
  return (
    <section className="environment-card">
      <h3>Site</h3>
      <div className="environment-site-grid">
        <label>Site name<input value={value.name} maxLength={120} onChange={(e) => update("name", e.target.value)} /></label>
        <label>Latitude (°)<input type="number" min="-90" max="90" step="any"
          value={value.latitude} onChange={(e) => update("latitude", e.target.value)} /></label>
        <label>Longitude (°)<input type="number" min="-180" max="180" step="any"
          value={value.longitude} onChange={(e) => update("longitude", e.target.value)} /></label>
        <label>Elevation (m)<input type="number" min="-500" max="9000" step="any"
          value={value.elevation_m} onChange={(e) => update("elevation_m", e.target.value)} /></label>
        <label>IANA timezone<input value={value.timezone} onChange={(e) => update("timezone", e.target.value)} /></label>
        <label>Water body<input value={value.water_body ?? ""} maxLength={120}
          onChange={(e) => update("water_body", e.target.value)} /></label>
      </div>
      <button type="button" disabled={disabled} onClick={onSave}>Save site</button>
    </section>
  );
}
