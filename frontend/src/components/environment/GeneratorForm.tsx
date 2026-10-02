import { useState } from "react";

export type GenerateRequest = {
  name: string;
  kind: "clear_sky" | "synthetic_day";
  parameters: Record<string, number | string>;
};

type Props = { onGenerate: (request: GenerateRequest) => void; disabled: boolean };

export function GeneratorForm({ onGenerate, disabled }: Props) {
  const [name, setName] = useState("Clear sky · 3 days");
  const [start, setStart] = useState(() => new Date().toISOString().slice(0, 16));
  const [resolution, setResolution] = useState(15);
  const [days, setDays] = useState(3);
  const [kind, setKind] = useState<GenerateRequest["kind"]>("clear_sky");
  const [clearness, setClearness] = useState(1);
  const [photoperiod, setPhotoperiod] = useState(12);
  const [peakPar, setPeakPar] = useState(1500);
  const [temperatureMean, setTemperatureMean] = useState(293.15);
  const [temperatureAmplitude, setTemperatureAmplitude] = useState(5);

  const generate = () => {
    const startDate = new Date(/[zZ]|[+-]\d{2}:?\d{2}$/.test(start) ? start : `${start}Z`);
    if (!Number.isFinite(startDate.getTime())) return;
    const parameters: GenerateRequest["parameters"] = {
      start: startDate.toISOString(),
      count: (days * 24 * 60) / resolution,
      resolution_minutes: resolution,
    };
    if (kind === "clear_sky") parameters.clearness_factor = clearness;
    else Object.assign(parameters, {
      photoperiod, peak_par: peakPar, temperature_mean: temperatureMean,
      temperature_amplitude: temperatureAmplitude,
    });
    onGenerate({ name, kind, parameters });
  };

  return (
    <section className="environment-card">
      <h3>Create profile</h3>
      <label>Profile name<input value={name} onChange={(e) => setName(e.target.value)} /></label>
      <label>First interval end (UTC)<input value={start} onChange={(e) => setStart(e.target.value)} /></label>
      <p className="environment-help">The first value is stamped one interval after this start time.</p>
      <div className="environment-form-row">
        <label>Resolution<select value={resolution} onChange={(e) => setResolution(Number(e.target.value))}>
          {[5, 10, 15, 30, 60, 1440].map((step) => <option key={step} value={step}>
            {step === 1440 ? "Daily · 1440 min" : `${step} min`}
          </option>)}
        </select></label>
        <label>Days<input type="number" min="1" max="730" value={days} onChange={(e) => setDays(Number(e.target.value))} /></label>
      </div>
      <label>Generator<select value={kind} onChange={(e) => setKind(e.target.value as GenerateRequest["kind"])}>
        <option value="clear_sky">Clear sky</option><option value="synthetic_day">Synthetic day</option>
      </select></label>
      {kind === "clear_sky" ? (
        <label>Clearness factor<input type="number" min="0" max="1" step="0.05"
          value={clearness} onChange={(e) => setClearness(Number(e.target.value))} /></label>
      ) : (
        <div className="environment-form-row">
          <label>Photoperiod (h)<input type="number" min="0.1" max="24" step="0.1"
            value={photoperiod} onChange={(e) => setPhotoperiod(Number(e.target.value))} /></label>
          <label>Peak PAR (µmol/(m²·s))<input type="number" min="0" value={peakPar}
            onChange={(e) => setPeakPar(Number(e.target.value))} /></label>
          <label>Mean air temperature (K)<input type="number" min="200" max="350" step="0.1"
            value={temperatureMean} onChange={(e) => setTemperatureMean(Number(e.target.value))} /></label>
          <label>Temperature amplitude (K)<input type="number" min="0" step="0.1"
            value={temperatureAmplitude} onChange={(e) => setTemperatureAmplitude(Number(e.target.value))} /></label>
        </div>
      )}
      <button type="button" disabled={disabled} onClick={generate}>Generate</button>
    </section>
  );
}
