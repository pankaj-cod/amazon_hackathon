"use client";

import { useEffect, useRef, useState } from "react";
import clsx from "clsx";
import {
  CloudOff, Coins, Flame, HelpCircle, Leaf, Mountain, Sparkles, Sprout, Volume2, Square, Wind, Wheat,
} from "lucide-react";
import { fetchVoice, type FieldReport, type Season } from "@/lib/api";
import { T, inrRange, type Lang } from "@/lib/i18n";

const STATUS_STYLE: Record<Season["status"], { cls: string; Icon: typeof Flame }> = {
  burned: { cls: "bg-[var(--burn-bg)] text-[var(--burn)] border-[var(--burn)]", Icon: Flame },
  partly_burned: { cls: "bg-[var(--partly-bg)] text-[var(--partly)] border-[var(--partly)]", Icon: Flame },
  not_burned: { cls: "bg-[var(--clean-bg)] text-[var(--clean)] border-[var(--clean)]", Icon: Leaf },
  no_harvest: { cls: "bg-[var(--clean-bg)] text-[var(--clean)] border-[var(--clean)]", Icon: Wheat },
  no_data: { cls: "bg-[var(--unknown-bg)] text-[var(--muted)] border-[var(--line)]", Icon: CloudOff },
};

function Card({ children, className }: { children: React.ReactNode; className?: string }) {
  return <section className={clsx("rounded-2xl bg-[var(--surface)] p-4 shadow-sm ring-1 ring-[var(--line)]", className)}>{children}</section>;
}

function Stat({ icon: Icon, label, value, sub }: { icon: typeof Flame; label: string; value: string; sub?: string }) {
  return (
    <Card>
      <div className="flex items-start gap-3">
        <span className="mt-0.5 rounded-full bg-[var(--accent-bg)] p-2 text-[var(--accent)]"><Icon size={20} aria-hidden /></span>
        <div className="min-w-0">
          <p className="text-sm text-[var(--muted)]">{label}</p>
          <p className="text-xl font-bold tabular-nums">{value}</p>
          {sub && <p className="text-sm text-[var(--muted)]">{sub}</p>}
        </div>
      </div>
    </Card>
  );
}

function shortDate(iso: string, lang: Lang): string {
  const locale = lang === "en" ? "en-IN" : `${lang}-IN`;
  return new Date(iso + "T00:00:00").toLocaleDateString(locale, { day: "numeric", month: "short" });
}

function useSpeech(text: string, lang: Lang) {
  const [state, setState] = useState<"idle" | "loading" | "playing">("idle");
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const browserVoice = () =>
    typeof window !== "undefined" && "speechSynthesis" in window
      ? window.speechSynthesis.getVoices().find((v) => v.lang.toLowerCase().startsWith(lang))
      : undefined;

  const [available, setAvailable] = useState(lang !== "pa");
  useEffect(() => {
    if (lang !== "pa" || typeof window === "undefined" || !("speechSynthesis" in window)) return;
    const update = () => setAvailable(Boolean(browserVoice()));
    update();
    window.speechSynthesis.addEventListener("voiceschanged", update);
    return () => window.speechSynthesis.removeEventListener("voiceschanged", update);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lang]);

  useEffect(() => () => stop(), []); // eslint-disable-line react-hooks/exhaustive-deps

  function speakInBrowser(): boolean {
    const v = browserVoice();
    if (!v) return false;
    const u = new SpeechSynthesisUtterance(text);
    u.voice = v;
    u.lang = v.lang;
    u.onend = () => setState("idle");
    window.speechSynthesis.speak(u);
    setState("playing");
    return true;
  }

  async function play() {
    if (lang === "pa") {
      speakInBrowser();
      return;
    }
    setState("loading");
    try {
      const blob = await fetchVoice(text, lang);
      const audio = new Audio(URL.createObjectURL(blob));
      audioRef.current = audio;
      audio.onended = () => setState("idle");
      await audio.play();
      setState("playing");
    } catch {
      if (!speakInBrowser()) setState("idle");
    }
  }

  function stop() {
    audioRef.current?.pause();
    audioRef.current = null;
    if (typeof window !== "undefined" && "speechSynthesis" in window) window.speechSynthesis.cancel();
    setState("idle");
  }

  return { state, available, play, stop };
}

export default function Results({ report, lang, onReset }: { report: FieldReport; lang: Lang; onReset: () => void }) {
  const t = T[lang];
  const { summary, burn_history, impact, soil, carbon_credits, advice, field } = report;
  const burned = summary.seasons_burned > 0;
  const speechText = [advice.headline, ...advice.steps, advice.money_note].join(" ");
  const speech = useSpeech(speechText, lang);

  return (
    <div className="space-y-3 pb-8">
      <Card className={clsx("border-l-8", burned ? "border-l-[var(--burn)]" : "border-l-[var(--clean)]")}>
        <div className="flex items-start gap-3">
          <span className={clsx("rounded-full p-2", burned ? "bg-[var(--burn-bg)] text-[var(--burn)]" : "bg-[var(--clean-bg)] text-[var(--clean)]")}>
            {burned ? <Flame size={28} aria-hidden /> : <Sprout size={28} aria-hidden />}
          </span>
          <div>
            <h2 className="text-lg font-bold leading-snug">{advice.headline}</h2>
            <p className="mt-1 text-sm text-[var(--muted)]">
              {field.area_acres} {t.acres} · {field.centroid[1].toFixed(4)}, {field.centroid[0].toFixed(4)}
            </p>
          </div>
        </div>
      </Card>

      <Card>
        <h3 className="mb-3 font-semibold">{t.burnHistory}</h3>
        <ol className="grid grid-cols-4 gap-2 sm:grid-cols-7">
          {burn_history.map((s) => {
            const { cls, Icon } = STATUS_STYLE[s.status];
            return (
              <li key={s.year} className={clsx("flex flex-col items-center rounded-xl border-2 px-1 py-2 text-center", cls, s.confidence === "low" && "border-dashed")}>
                <Icon size={20} aria-hidden />
                <span className="mt-1 text-sm font-bold tabular-nums text-[var(--ink)]">{s.year}</span>
                <span className="text-xs font-medium leading-tight">{t.status[s.status]}</span>
                {s.burn_date && <span className="text-[11px] text-[var(--muted)]">{shortDate(s.burn_date, lang)}</span>}
                {s.confidence === "low" && <HelpCircle size={12} className="mt-0.5 text-[var(--muted)]" aria-label={t.lowConfidence} />}
              </li>
            );
          })}
        </ol>
      </Card>

      <div className="grid gap-3 sm:grid-cols-2">
        <Stat
          icon={Coins}
          label={t.fertPerBurn}
          value={inrRange(impact.per_burn.nutrient_value_inr)}
          sub={burned ? `${t.fertTotal(summary.seasons_burned)}: ${inrRange(impact.cumulative.nutrient_value_inr)}` : undefined}
        />
        <Stat
          icon={Mountain}
          label={t.soilCarbon}
          value={`${impact.cumulative.soil_carbon_foregone_t_c.low.toFixed(1)} – ${impact.cumulative.soil_carbon_foregone_t_c.high.toFixed(1)} t C`}
          sub={burned ? t.soilShare(soil.share_of_stock_lost_pct.low, soil.share_of_stock_lost_pct.high) : `${soil.soc_stock_t_per_ha} t C/ha (0–30 cm)`}
        />
        <Stat
          icon={Wind}
          label={t.smoke}
          value={`${Math.round(impact.per_burn.pm25_kg.low)} – ${Math.round(impact.per_burn.pm25_kg.high)} kg`}
        />
        <Card>
          <div className="flex items-start gap-3">
            <span className="mt-0.5 rounded-full bg-[var(--accent-bg)] p-2 text-[var(--accent)]"><Sparkles size={20} aria-hidden /></span>
            <div className="min-w-0">
              <p className="text-sm text-[var(--muted)]">{t.credits}</p>
              <p className="text-xl font-bold tabular-nums">{inrRange(carbon_credits.income_inr_per_acre_per_year)}</p>
              <p className="text-sm text-[var(--muted)]">{t.perAcreYear}</p>
              <p className="mt-1 text-sm tabular-nums">
                {inrRange(carbon_credits.income_inr_field_per_year)} <span className="text-[var(--muted)]">{t.fieldYear}</span>
              </p>
            </div>
          </div>
          <details className="mt-3 text-sm">
            <summary className="cursor-pointer py-2 font-medium text-[var(--accent)]">{t.howEstimated}</summary>
            <ul className="list-disc space-y-1 pl-5 text-[var(--muted)]" lang="en">
              {carbon_credits.assumptions.map((a) => <li key={a}>{a}</li>)}
            </ul>
          </details>
        </Card>
      </div>

      <Card>
        <div className="mb-2 flex items-center justify-between gap-2">
          <h3 className="font-semibold">{t.advice}</h3>
          {speech.available && (
            <button
              type="button"
              onClick={speech.state === "idle" ? speech.play : speech.stop}
              disabled={speech.state === "loading"}
              className="flex min-h-11 items-center gap-2 rounded-full bg-[var(--accent)] px-4 text-sm font-semibold text-white disabled:opacity-60"
            >
              {speech.state === "playing" ? <Square size={16} aria-hidden /> : <Volume2 size={16} aria-hidden />}
              {speech.state === "playing" ? t.stop : t.listen}
            </button>
          )}
        </div>
        <ol className="space-y-2">
          {advice.steps.map((s, i) => (
            <li key={i} className="flex gap-3">
              <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[var(--accent-bg)] text-sm font-bold text-[var(--accent)]">{i + 1}</span>
              <span className="leading-relaxed">{s}</span>
            </li>
          ))}
        </ol>
        <p className="mt-3 rounded-xl bg-[var(--accent-bg)] p-3 text-sm leading-relaxed">{advice.money_note}</p>
        {advice.source === "bedrock" && <p className="mt-2 text-xs text-[var(--muted)]">{t.aiAdvice}</p>}
      </Card>

      <p className="px-1 text-xs text-[var(--muted)]">{t.estimateNote}</p>
      <details className="px-1 text-xs text-[var(--muted)]">
        <summary className="cursor-pointer py-1">{t.dataSources}</summary>
        <ul className="list-disc pl-5" lang="en">
          {report.data_sources.map((d) => <li key={d}>{d}</li>)}
        </ul>
      </details>

      <button
        type="button"
        onClick={onReset}
        className="min-h-12 w-full rounded-2xl border-2 border-[var(--accent)] font-semibold text-[var(--accent)]"
      >
        {t.checkAnother}
      </button>
    </div>
  );
}
