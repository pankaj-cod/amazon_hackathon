import type { Lang } from "./i18n";

const BASE_URL = (process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000").replace(/\/$/, "");

export type Range = { low: number; high: number };

export type SeasonStatus = "burned" | "partly_burned" | "not_burned" | "no_harvest" | "no_data";

export type Season = {
  year: number;
  status: SeasonStatus;
  burned_fraction: number;
  burn_date: string | null;
  active_fire_seen: boolean;
  clear_observations: number;
  max_gap_days: number | null;
  confidence: "high" | "medium" | "low";
};

export type Impact = {
  straw_burned_t: Range;
  co2_t: Range;
  non_co2_tco2e: Range;
  pm25_kg: Range;
  nutrients_lost_kg: Record<"N" | "P2O5" | "K2O" | "S", Range>;
  nutrient_value_inr: Range;
  soil_carbon_foregone_t_c: Range;
};

export type FieldReport = {
  field: { input_type: "pin" | "polygon"; area_acres: number; area_ha: number; centroid: [number, number] };
  summary: {
    seasons_checked: number;
    seasons_burned: number;
    seasons_unclear: number;
    last_burn_year: number | null;
    burned_season_equivalent: number;
  };
  burn_history: Season[];
  soil: {
    soc_g_per_kg: number;
    bulk_density_g_cm3: number;
    soc_stock_t_per_ha: number;
    source: string;
    share_of_stock_lost_pct: Range;
  };
  impact: { per_burn: Impact; cumulative: Impact };
  carbon_credits: {
    credits_t_co2e_per_acre_per_year: Range;
    income_inr_per_acre_per_year: Range;
    income_inr_field_per_year: Range;
    includes_avoided_burning: boolean;
    assumptions: string[];
  };
  advice: { language: Lang; headline: string; steps: string[]; money_note: string; source: "bedrock" | "template" };
  data_sources: string[];
  cached: boolean;
};

export type FieldGeometry =
  | { type: "Point"; coordinates: [number, number] }
  | { type: "Polygon"; coordinates: [number, number][][] };

async function errorDetail(res: Response): Promise<string> {
  try {
    const body = await res.json();
    return typeof body.detail === "string" ? body.detail : res.statusText;
  } catch {
    return res.statusText;
  }
}

export async function analyzeField(
  geometry: FieldGeometry,
  language: Lang,
  fieldAreaAcres?: number,
  signal?: AbortSignal,
): Promise<FieldReport> {
  const res = await fetch(`${BASE_URL}/compute/direct`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ geometry, language, field_area_acres: fieldAreaAcres }),
    signal,
  });
  if (!res.ok) throw new Error(await errorDetail(res));
  return res.json();
}

export async function fetchVoice(text: string, language: Lang): Promise<Blob> {
  const res = await fetch(`${BASE_URL}/advice/voice`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, language }),
  });
  if (!res.ok) throw new Error(await errorDetail(res));
  return res.blob();
}
