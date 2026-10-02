import { useEffect, useRef, useState } from "react";
import type uPlot from "uplot";
import type { ProfileValues } from "./types";
import { CHANNEL_LABELS, displayUnit, displayValue } from "./types";

const COLORS = ["#246b45", "#24729b", "#c56825", "#7256a3", "#9a4a55", "#5e7775", "#b18a14", "#287c82"];

type Props = {
  profile: ProfileValues;
  timezone: string;
  resolutionUsed: number | null;
  onRange: (start: string, end: string) => void;
};

function siteTime(value: number, timezone: string): string {
  return new Intl.DateTimeFormat("en-GB", {
    timeZone: timezone,
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).format(new Date(value * 1000));
}

async function loadUPlot() {
  const originalNumberFormat = Intl.NumberFormat;
  if (!navigator.language.includes("@")) return import("uplot");

  // uPlot builds its numeric formatter at module load and reads navigator.language
  // directly, so its options cannot repair the host's nonstandard "en-US@posix" tag.
  // Normalize only locale strings containing the host modifier, then restore the global.
  const LocaleSafeNumberFormat = class extends originalNumberFormat {
    constructor(locales?: Intl.LocalesArgument, options?: Intl.NumberFormatOptions) {
      const normalized = typeof locales === "string" ? locales.split("@")[0] : locales;
      super(normalized, options);
    }
  };
  Intl.NumberFormat = LocaleSafeNumberFormat as unknown as typeof Intl.NumberFormat;
  try {
    return await import("uplot");
  } finally {
    Intl.NumberFormat = originalNumberFormat;
  }
}

export function ProfileChart({ profile, timezone, resolutionUsed, onRange }: Props) {
  const root = useRef<HTMLDivElement>(null);
  const chart = useRef<InstanceType<typeof uPlot> | null>(null);
  const [hidden, setHidden] = useState<Set<string>>(new Set());
  const [chartError, setChartError] = useState("");

  useEffect(() => {
    let active = true;
    let observer: ResizeObserver | undefined;
    setChartError("");
    void loadUPlot().then(({ default: UPlot }) => {
      if (!active || !root.current) return;
      const series = Object.entries(profile.channels).filter(([, values]) => values.some((value) => value !== null));
      if (series.length === 0) return;
      const times = profile.timestamps.map((stamp) => new Date(stamp).getTime() / 1000);
      const units = [...new Set(series.map(([name]) => displayUnit(name, profile.units[name])))];
      const data = ([
        times,
        ...series.map(([name, values]) => values.map((value) => displayValue(name, value))),
      ] as uPlot.AlignedData);
      const scales = Object.fromEntries(units.map((unit) => [unit, {}]));
      chart.current?.destroy();
      chart.current = new UPlot({
        width: Math.max(320, root.current.clientWidth),
        height: 260,
        legend: { show: false },
        scales: { x: { time: true }, ...scales },
        cursor: { drag: { x: true, y: false, setScale: true } },
        hooks: { setScale: [(plot, key) => {
          if (key !== "x" || plot.scales.x.min === undefined || plot.scales.x.max === undefined) return;
          const start = new Date(plot.scales.x.min * 1000).toISOString();
          const end = new Date(plot.scales.x.max * 1000).toISOString();
          onRange(start, end);
        }] },
        series: [{}, ...series.map(([name], index) => ({
          label: CHANNEL_LABELS[name] ?? name,
          scale: displayUnit(name, profile.units[name]),
          show: !hidden.has(name),
          stroke: COLORS[index % COLORS.length],
          width: 2,
        }))],
        axes: [
          {
            label: `Site time (${timezone})`,
            values: (_plot, values) => values.map((value) => siteTime(value, timezone)),
          },
          ...units.map((unit, index) => ({
            scale: unit,
            label: unit,
            side: index === 0 ? 3 : 1,
            grid: { show: index === 0 },
          })),
        ],
      }, data, root.current);
      observer = new ResizeObserver(() => chart.current?.setSize({
        width: Math.max(320, root.current?.clientWidth ?? 320), height: 260,
      }));
      observer.observe(root.current);
    }).catch((reason: unknown) => {
      if (active) setChartError(reason instanceof Error ? reason.message : "The chart could not be rendered.");
    });
    return () => {
      active = false;
      observer?.disconnect();
      chart.current?.destroy();
      chart.current = null;
    };
  }, [profile.digest, profile.timestamps, profile.channels, profile.units, timezone, resolutionUsed, onRange]);

  useEffect(() => {
    if (!chart.current) return;
    Object.keys(profile.channels).forEach((channel, index) => {
      chart.current?.setSeries(index + 1, { show: !hidden.has(channel) });
    });
  }, [hidden, profile.channels]);

  return (
    <section aria-label="Environment chart">
      {chartError && <p className="environment-error" role="alert">Chart unavailable: {chartError}</p>}
      <div ref={root} className="environment-plot" role="img" aria-label={`Environment profile chart. Time axis uses ${timezone}.`} />
      <p className="environment-help">Chart resolution: {resolutionUsed ? `${resolutionUsed} minutes` : "source timestamps"}.
        Drag across the chart to inspect matching table values.</p>
      <div className="environment-legend" role="group" aria-label="Chart series">
        {Object.keys(profile.channels).map((channel, index) => <button
          type="button"
          key={channel}
          aria-pressed={!hidden.has(channel)}
          onClick={() => setHidden((current) => {
            const next = new Set(current);
            if (next.has(channel)) next.delete(channel);
            else next.add(channel);
            return next;
          })}
        ><span className="environment-swatch" style={{ backgroundColor: COLORS[index % COLORS.length] }} />
          {CHANNEL_LABELS[channel] ?? channel} · {displayUnit(channel, profile.units[channel])}
        </button>)}
      </div>
    </section>
  );
}
