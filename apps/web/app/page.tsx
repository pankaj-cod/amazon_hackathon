"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import dynamic from "next/dynamic";
import clsx from "clsx";
import { Crosshair, Hexagon, Loader2, MapPin, Undo2, X } from "lucide-react";
import Results from "@/components/Results";
import type { LatLng, MapMode } from "@/components/FieldMap";
import { analyzeField, type FieldGeometry, type FieldReport } from "@/lib/api";
import { LANG_LABEL, T, type Lang } from "@/lib/i18n";

const FieldMap = dynamic(() => import("@/components/FieldMap"), {
  ssr: false,
  loading: () => <div className="h-full w-full animate-pulse bg-[var(--unknown-bg)]" />,
});

const SAMPLE_FIELD: { pin: LatLng; acres: number } = { pin: [30.1613, 75.6816], acres: 2 };
const ACRES_PER_M2 = 1 / 4046.86;

function polygonAcres(vertices: LatLng[]): number {
  if (vertices.length < 3) return 0;
  const lat0 = (vertices.reduce((s, v) => s + v[0], 0) / vertices.length) * (Math.PI / 180);
  const R = 6371008.8;
  const pts = vertices.map(([lat, lng]) => [R * (lng * Math.PI / 180) * Math.cos(lat0), R * (lat * Math.PI / 180)]);
  let a = 0;
  for (let i = 0; i < pts.length; i++) {
    const [x1, y1] = pts[i];
    const [x2, y2] = pts[(i + 1) % pts.length];
    a += x1 * y2 - x2 * y1;
  }
  return (Math.abs(a) / 2) * ACRES_PER_M2;
}

function loadLang(): Lang {
  try {
    const v = localStorage.getItem("lang");
    if (v === "pa" || v === "hi" || v === "en") return v;
  } catch {}
  return "pa";
}

export default function Home() {
  const [lang, setLang] = useState<Lang>("pa");
  const [mode, setMode] = useState<MapMode>("pin");
  const [pin, setPin] = useState<LatLng | null>(null);
  const [vertices, setVertices] = useState<LatLng[]>([]);
  const [acres, setAcres] = useState("2");
  const [flyTarget, setFlyTarget] = useState<{ center: LatLng; zoom: number; key: number } | null>(null);
  const [phase, setPhase] = useState<"pick" | "loading" | "result">("pick");
  const [report, setReport] = useState<FieldReport | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [loadingStep, setLoadingStep] = useState(0);
  const abortRef = useRef<AbortController | null>(null);
  const t = T[lang];

  useEffect(() => setLang(loadLang()), []);
  useEffect(() => {
    document.documentElement.lang = lang;
    try { localStorage.setItem("lang", lang); } catch {}
  }, [lang]);

  useEffect(() => {
    if (phase !== "loading") return;
    setLoadingStep(0);
    const id = setInterval(() => setLoadingStep((s) => Math.min(s + 1, 3)), 9000);
    return () => clearInterval(id);
  }, [phase]);

  const boundaryAcres = useMemo(() => polygonAcres(vertices), [vertices]);

  const geometry: FieldGeometry | null = useMemo(() => {
    if (mode === "pin" && pin) return { type: "Point", coordinates: [pin[1], pin[0]] };
    if (mode === "boundary" && vertices.length >= 3) {
      const ring = vertices.map(([lat, lng]) => [lng, lat] as [number, number]);
      return { type: "Polygon", coordinates: [[...ring, ring[0]]] };
    }
    return null;
  }, [mode, pin, vertices]);

  function locate() {
    if (!("geolocation" in navigator)) {
      setMessage(t.locationFailed);
      return;
    }
    setMessage(t.locating);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const p: LatLng = [pos.coords.latitude, pos.coords.longitude];
        setFlyTarget({ center: p, zoom: 17, key: Date.now() });
        if (mode === "pin") setPin(p);
        setMessage(null);
      },
      () => setMessage(t.locationFailed),
      { enableHighAccuracy: true, timeout: 15000 },
    );
  }

  async function run(geom: FieldGeometry, areaAcres?: number) {
    abortRef.current?.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    setMessage(null);
    setPhase("loading");
    try {
      const r = await analyzeField(geom, lang, areaAcres, ctrl.signal);
      setReport(r);
      setPhase("result");
      window.scrollTo({ top: 0 });
    } catch (e) {
      if (ctrl.signal.aborted) return;
      setMessage(e instanceof Error && e.message ? `${t.error} (${e.message})` : t.error);
      setPhase("pick");
    }
  }

  function check() {
    if (!geometry) {
      setMessage(t.pickFirst);
      return;
    }
    const a = mode === "pin" ? Number(acres) || 2 : undefined;
    run(geometry, a);
  }

  function trySample() {
    setMode("pin");
    setPin(SAMPLE_FIELD.pin);
    setAcres(String(SAMPLE_FIELD.acres));
    setFlyTarget({ center: SAMPLE_FIELD.pin, zoom: 17, key: Date.now() });
    run({ type: "Point", coordinates: [SAMPLE_FIELD.pin[1], SAMPLE_FIELD.pin[0]] }, SAMPLE_FIELD.acres);
  }

  function changeLang(l: Lang) {
    setLang(l);
    if (phase === "result" && report) {
      const sameField = report.field.input_type === "pin"
        ? { type: "Point" as const, coordinates: report.field.centroid }
        : geometry;
      if (sameField) run(sameField, report.field.area_acres);
    }
  }

  return (
    <div className="mx-auto flex min-h-dvh max-w-xl flex-col px-4">
      <header className="flex items-center justify-between gap-2 py-3">
        <div>
          <h1 className="text-2xl font-extrabold text-[var(--accent)]">{t.appName}</h1>
          <p className="text-sm text-[var(--muted)]">{t.tagline}</p>
        </div>
        <div className="flex shrink-0 rounded-full bg-[var(--surface)] p-1 ring-1 ring-[var(--line)]" role="group" aria-label="Language">
          {(Object.keys(LANG_LABEL) as Lang[]).map((l) => (
            <button
              key={l}
              type="button"
              onClick={() => changeLang(l)}
              aria-pressed={lang === l}
              className={clsx(
                "min-h-10 rounded-full px-3 text-sm font-semibold",
                lang === l ? "bg-[var(--accent)] text-white" : "text-[var(--ink)]",
              )}
            >
              {LANG_LABEL[l]}
            </button>
          ))}
        </div>
      </header>

      {phase === "result" && report ? (
        <Results report={report} lang={lang} onReset={() => { setPhase("pick"); setReport(null); }} />
      ) : (
        <main className="flex flex-1 flex-col gap-3 pb-6">
          <div className="flex rounded-2xl bg-[var(--surface)] p-1 ring-1 ring-[var(--line)]">
            {([["pin", MapPin, t.pinMode], ["boundary", Hexagon, t.boundaryMode]] as const).map(([m, Icon, label]) => (
              <button
                key={m}
                type="button"
                onClick={() => setMode(m)}
                aria-pressed={mode === m}
                className={clsx(
                  "flex min-h-11 flex-1 items-center justify-center gap-2 rounded-xl text-sm font-semibold",
                  mode === m ? "bg-[var(--accent)] text-white" : "text-[var(--ink)]",
                )}
              >
                <Icon size={18} aria-hidden /> {label}
              </button>
            ))}
          </div>

          <p className="text-center font-medium">{mode === "pin" ? t.pickField : t.boundaryHint}</p>

          <div className="relative h-[52dvh] min-h-72 overflow-hidden rounded-2xl ring-1 ring-[var(--line)]">
            <FieldMap
              mode={mode}
              pin={pin}
              vertices={vertices}
              onPin={setPin}
              onVertex={(p) => setVertices((v) => [...v, p])}
              flyTarget={flyTarget}
            />
            <div className="absolute right-2 top-2 z-[1000] flex flex-col gap-2">
              <button
                type="button"
                onClick={locate}
                className="flex min-h-11 items-center gap-2 rounded-full bg-white px-3 text-sm font-semibold text-[var(--ink)] shadow"
              >
                <Crosshair size={18} aria-hidden /> {t.myLocation}
              </button>
              {mode === "boundary" && vertices.length > 0 && (
                <div className="flex gap-2 self-end">
                  <button type="button" onClick={() => setVertices((v) => v.slice(0, -1))} aria-label={t.undo}
                    className="flex h-11 w-11 items-center justify-center rounded-full bg-white text-[var(--ink)] shadow">
                    <Undo2 size={18} aria-hidden />
                  </button>
                  <button type="button" onClick={() => setVertices([])} aria-label={t.clear}
                    className="flex h-11 w-11 items-center justify-center rounded-full bg-white text-[var(--ink)] shadow">
                    <X size={18} aria-hidden />
                  </button>
                </div>
              )}
            </div>
            {phase === "loading" && (
              <div className="absolute inset-0 z-[1001] flex flex-col items-center justify-center gap-3 bg-black/60 p-6 text-center text-white" role="status" aria-live="polite">
                <Loader2 size={40} className="animate-spin" aria-hidden />
                <p className="text-lg font-semibold">{t.loadingSteps[loadingStep]}</p>
                <p className="text-sm opacity-80">{t.loadingNote}</p>
              </div>
            )}
          </div>

          {mode === "pin" ? (
            <label className="flex items-center justify-between gap-3 rounded-2xl bg-[var(--surface)] px-4 py-2 ring-1 ring-[var(--line)]">
              <span className="font-medium">{t.areaLabel}</span>
              <input
                type="number"
                inputMode="decimal"
                min="0.25"
                max="100"
                step="0.25"
                value={acres}
                onChange={(e) => setAcres(e.target.value)}
                className="min-h-11 w-24 rounded-xl border border-[var(--line)] bg-white px-3 text-right text-lg font-semibold"
              />
            </label>
          ) : (
            <div className="flex items-center justify-between rounded-2xl bg-[var(--surface)] px-4 py-3 ring-1 ring-[var(--line)]">
              <span className="font-medium">{t.areaFromBoundary}</span>
              <span className="text-lg font-semibold tabular-nums">{boundaryAcres.toFixed(2)} {t.acres}</span>
            </div>
          )}

          {message && <p className="rounded-xl bg-[var(--partly-bg)] px-4 py-3 text-sm text-[var(--ink)]" role="alert">{message}</p>}

          <button
            type="button"
            onClick={check}
            disabled={phase === "loading"}
            className="min-h-14 w-full rounded-2xl bg-[var(--accent)] text-lg font-bold text-white shadow disabled:opacity-60"
          >
            {t.check}
          </button>
          <button
            type="button"
            onClick={trySample}
            disabled={phase === "loading"}
            className="min-h-12 w-full rounded-2xl border-2 border-[var(--accent)] font-semibold text-[var(--accent)] disabled:opacity-60"
          >
            {t.sample}
          </button>
        </main>
      )}

      <footer className="py-4 text-center text-xs text-[var(--muted)]">
        Sentinel-2 · AWS Open Data · Amazon Bedrock · Amazon Polly
      </footer>
    </div>
  );
}
