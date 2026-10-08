import type { SeasonStatus } from "./api";

export type Lang = "pa" | "hi" | "en";

export const LANG_LABEL: Record<Lang, string> = { pa: "ਪੰਜਾਬੀ", hi: "हिंदी", en: "English" };

type Dict = {
  appName: string;
  tagline: string;
  pickField: string;
  myLocation: string;
  pinMode: string;
  boundaryMode: string;
  boundaryHint: string;
  undo: string;
  clear: string;
  areaLabel: string;
  areaFromBoundary: string;
  check: string;
  sample: string;
  pickFirst: string;
  locating: string;
  locationFailed: string;
  loadingSteps: string[];
  loadingNote: string;
  burnHistory: string;
  status: Record<SeasonStatus, string>;
  fertPerBurn: string;
  fertTotal: (n: number) => string;
  soilCarbon: string;
  soilShare: (a: number, b: number) => string;
  smoke: string;
  credits: string;
  perAcreYear: string;
  fieldYear: string;
  howEstimated: string;
  advice: string;
  checkAnother: string;
  error: string;
  estimateNote: string;
  dataSources: string;
  acres: string;
  lowConfidence: string;
  aiAdvice: string;
  months: string[];
};

export const T: Record<Lang, Dict> = {
  pa: {
    appName: "ਪਰਾਲੀ ਮਿੱਤਰ",
    tagline: "ਆਪਣੇ ਖੇਤ ਦੀ ਪਰਾਲੀ ਦਾ ਹਿਸਾਬ ਦੇਖੋ",
    pickField: "ਨਕਸ਼ੇ 'ਤੇ ਆਪਣੇ ਖੇਤ 'ਤੇ ਟੈਪ ਕਰੋ",
    myLocation: "ਮੇਰੀ ਲੋਕੇਸ਼ਨ",
    pinMode: "ਪਿੰਨ",
    boundaryMode: "ਖੇਤ ਦੀ ਹੱਦ",
    boundaryHint: "ਖੇਤ ਦੇ ਕੋਨਿਆਂ 'ਤੇ ਇੱਕ-ਇੱਕ ਕਰਕੇ ਟੈਪ ਕਰੋ",
    undo: "ਪਿੱਛੇ",
    clear: "ਮਿਟਾਓ",
    areaLabel: "ਖੇਤ ਦਾ ਰਕਬਾ (ਏਕੜ)",
    areaFromBoundary: "ਹੱਦ ਤੋਂ ਰਕਬਾ",
    check: "ਮੇਰਾ ਖੇਤ ਜਾਂਚੋ",
    sample: "ਨਮੂਨਾ ਖੇਤ ਦੇਖੋ",
    pickFirst: "ਪਹਿਲਾਂ ਨਕਸ਼ੇ 'ਤੇ ਖੇਤ ਚੁਣੋ",
    locating: "ਲੋਕੇਸ਼ਨ ਲੱਭ ਰਹੇ ਹਾਂ…",
    locationFailed: "ਲੋਕੇਸ਼ਨ ਨਹੀਂ ਮਿਲੀ। ਨਕਸ਼ੇ 'ਤੇ ਖੇਤ ਲੱਭੋ।",
    loadingSteps: [
      "ਸੈਟੇਲਾਈਟ ਤਸਵੀਰਾਂ ਲੱਭ ਰਹੇ ਹਾਂ…",
      "ਹਰ ਸੀਜ਼ਨ ਵਿੱਚ ਅੱਗ ਦੇ ਨਿਸ਼ਾਨ ਦੇਖ ਰਹੇ ਹਾਂ…",
      "ਮਿੱਟੀ ਦਾ ਕਾਰਬਨ ਗਿਣ ਰਹੇ ਹਾਂ…",
      "ਸਲਾਹ ਤਿਆਰ ਕਰ ਰਹੇ ਹਾਂ…",
    ],
    loadingNote: "ਪਹਿਲੀ ਵਾਰ 1 ਮਿੰਟ ਤੱਕ ਲੱਗ ਸਕਦਾ ਹੈ",
    burnHistory: "ਪਰਾਲੀ ਸਾੜਨ ਦਾ ਇਤਿਹਾਸ",
    status: { burned: "ਸਾੜੀ", partly_burned: "ਕੁਝ ਹਿੱਸਾ", not_burned: "ਨਹੀਂ ਸਾੜੀ", no_harvest: "ਫ਼ਸਲ ਖੜ੍ਹੀ", no_data: "ਪਤਾ ਨਹੀਂ" },
    fertPerBurn: "ਹਰ ਵਾਰ ਸਾੜਨ 'ਤੇ ਸੜੀ ਖਾਦ (ਤੁਹਾਡਾ ਖੇਤ)",
    fertTotal: (n) => `${n} ਵਾਰ ਸਾੜਨ ਨਾਲ ਕੁੱਲ ਨੁਕਸਾਨ`,
    soilCarbon: "ਮਿੱਟੀ ਦਾ ਕਾਰਬਨ ਗੁਆਇਆ (ਤੁਹਾਡਾ ਖੇਤ)",
    soilShare: (a, b) => `ਤੁਹਾਡੀ ਮਿੱਟੀ ਦੇ ਕਾਰਬਨ ਦਾ ${a}–${b}%`,
    smoke: "ਹਰ ਵਾਰ ਹਵਾ ਵਿੱਚ ਧੂੰਆਂ PM2.5 (ਤੁਹਾਡਾ ਖੇਤ)",
    credits: "ਨਾ ਸਾੜਨ 'ਤੇ ਕਾਰਬਨ ਕ੍ਰੈਡਿਟ ਕਮਾਈ",
    perAcreYear: "ਪ੍ਰਤੀ ਏਕੜ / ਸਾਲ",
    fieldYear: "ਤੁਹਾਡਾ ਖੇਤ / ਸਾਲ",
    howEstimated: "ਇਹ ਅੰਦਾਜ਼ਾ ਕਿਵੇਂ ਲਗਾਇਆ",
    advice: "ਤੁਸੀਂ ਕੀ ਕਰ ਸਕਦੇ ਹੋ",
    checkAnother: "ਹੋਰ ਖੇਤ ਜਾਂਚੋ",
    error: "ਕੁਝ ਗਲਤ ਹੋ ਗਿਆ। ਦੁਬਾਰਾ ਕੋਸ਼ਿਸ਼ ਕਰੋ।",
    estimateNote: "ਇਹ ਸੈਟੇਲਾਈਟ ਅਧਾਰਿਤ ਅੰਦਾਜ਼ੇ ਹਨ, ਪੱਕੇ ਅੰਕੜੇ ਨਹੀਂ।",
    dataSources: "ਡਾਟਾ ਸਰੋਤ",
    acres: "ਏਕੜ",
    lowConfidence: "ਘੱਟ ਸਾਫ਼ ਤਸਵੀਰਾਂ",
    aiAdvice: "Amazon Bedrock AI ਦੀ ਸਲਾਹ",
    months: ["ਜਨ", "ਫ਼ਰ", "ਮਾਰ", "ਅਪ੍ਰੈ", "ਮਈ", "ਜੂਨ", "ਜੁਲਾ", "ਅਗ", "ਸਤੰ", "ਅਕਤੂ", "ਨਵੰ", "ਦਸੰ"],
  },
  hi: {
    appName: "पराली मित्र",
    tagline: "अपने खेत की पराली का हिसाब देखें",
    pickField: "नक्शे पर अपने खेत पर टैप करें",
    myLocation: "मेरी लोकेशन",
    pinMode: "पिन",
    boundaryMode: "खेत की सीमा",
    boundaryHint: "खेत के कोनों पर एक-एक करके टैप करें",
    undo: "पीछे",
    clear: "मिटाएँ",
    areaLabel: "खेत का रकबा (एकड़)",
    areaFromBoundary: "सीमा से रकबा",
    check: "मेरा खेत जाँचें",
    sample: "नमूना खेत देखें",
    pickFirst: "पहले नक्शे पर खेत चुनें",
    locating: "लोकेशन ढूँढ रहे हैं…",
    locationFailed: "लोकेशन नहीं मिली। नक्शे पर खेत ढूँढें।",
    loadingSteps: [
      "सैटेलाइट तस्वीरें ढूँढ रहे हैं…",
      "हर सीज़न में आग के निशान देख रहे हैं…",
      "मिट्टी का कार्बन गिन रहे हैं…",
      "सलाह तैयार कर रहे हैं…",
    ],
    loadingNote: "पहली बार 1 मिनट तक लग सकता है",
    burnHistory: "पराली जलाने का इतिहास",
    status: { burned: "जलाई", partly_burned: "आंशिक", not_burned: "नहीं जलाई", no_harvest: "फ़सल खड़ी", no_data: "पता नहीं" },
    fertPerBurn: "हर बार जलाने पर जली खाद (आपका खेत)",
    fertTotal: (n) => `${n} बार जलाने से कुल नुकसान`,
    soilCarbon: "मिट्टी का कार्बन खोया (आपका खेत)",
    soilShare: (a, b) => `आपकी मिट्टी के कार्बन का ${a}–${b}%`,
    smoke: "हर बार हवा में धुआँ PM2.5 (आपका खेत)",
    credits: "न जलाने पर कार्बन क्रेडिट कमाई",
    perAcreYear: "प्रति एकड़ / साल",
    fieldYear: "आपका खेत / साल",
    howEstimated: "यह अनुमान कैसे लगाया",
    advice: "आप क्या कर सकते हैं",
    checkAnother: "दूसरा खेत जाँचें",
    error: "कुछ गड़बड़ हुई। फिर से कोशिश करें।",
    estimateNote: "ये सैटेलाइट पर आधारित अनुमान हैं, पक्के आँकड़े नहीं।",
    dataSources: "डेटा स्रोत",
    acres: "एकड़",
    lowConfidence: "कम साफ़ तस्वीरें",
    aiAdvice: "Amazon Bedrock AI की सलाह",
    months: ["जन", "फ़र", "मार्च", "अप्रै", "मई", "जून", "जुला", "अग", "सितं", "अक्टू", "नवं", "दिसं"],
  },
  en: {
    appName: "Parali Mitra",
    tagline: "See what stubble burning costs your field",
    pickField: "Tap your field on the map",
    myLocation: "My location",
    pinMode: "Pin",
    boundaryMode: "Boundary",
    boundaryHint: "Tap each corner of your field",
    undo: "Undo",
    clear: "Clear",
    areaLabel: "Field size (acres)",
    areaFromBoundary: "Area from boundary",
    check: "Check my field",
    sample: "Try a sample field",
    pickFirst: "Pick your field on the map first",
    locating: "Finding your location…",
    locationFailed: "Couldn't get location. Find your field on the map.",
    loadingSteps: [
      "Finding satellite images…",
      "Checking each season for burn scars…",
      "Calculating soil carbon…",
      "Preparing advice…",
    ],
    loadingNote: "The first check can take up to a minute",
    burnHistory: "Burn history",
    status: { burned: "Burned", partly_burned: "Partly", not_burned: "Not burned", no_harvest: "Crop standing", no_data: "Unclear" },
    fertPerBurn: "Fertiliser burned each time (your field)",
    fertTotal: (n) => `Total lost over ${n} burns`,
    soilCarbon: "Soil carbon lost (your field)",
    soilShare: (a, b) => `${a}–${b}% of your soil's carbon`,
    smoke: "Smoke (PM2.5) per burn (your field)",
    credits: "Carbon-credit income if you stop burning",
    perAcreYear: "per acre / year",
    fieldYear: "your field / year",
    howEstimated: "How this is estimated",
    advice: "What you can do",
    checkAnother: "Check another field",
    error: "Something went wrong. Please try again.",
    estimateNote: "These are satellite-based estimates, not exact figures.",
    dataSources: "Data sources",
    acres: "acres",
    lowConfidence: "few clear images",
    aiAdvice: "Advice by Amazon Bedrock AI",
    months: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
  },
};

export function inr(n: number): string {
  return "₹" + Math.round(n).toLocaleString("en-IN");
}

export function inrRange(r: { low: number; high: number }): string {
  return `${inr(r.low)} – ${inr(r.high)}`;
}
