"use client";

import { useEffect } from "react";
import { CircleMarker, MapContainer, Polygon, Polyline, TileLayer, useMap, useMapEvents } from "react-leaflet";
import "leaflet/dist/leaflet.css";

export type LatLng = [number, number];
export type MapMode = "pin" | "boundary";

const PUNJAB_CENTER: LatLng = [30.6, 75.6];
const FIELD_COLOR = "#f5c518";

function ClickHandler({ mode, onPin, onVertex }: { mode: MapMode; onPin: (p: LatLng) => void; onVertex: (p: LatLng) => void }) {
  useMapEvents({
    click(e) {
      const p: LatLng = [e.latlng.lat, e.latlng.lng];
      if (mode === "pin") onPin(p);
      else onVertex(p);
    },
  });
  return null;
}

function FlyTo({ target }: { target: { center: LatLng; zoom: number; key: number } | null }) {
  const map = useMap();
  useEffect(() => {
    if (target) map.flyTo(target.center, target.zoom, { duration: 1.2 });
  }, [map, target]);
  return null;
}

export default function FieldMap({
  mode,
  pin,
  vertices,
  onPin,
  onVertex,
  flyTarget,
}: {
  mode: MapMode;
  pin: LatLng | null;
  vertices: LatLng[];
  onPin: (p: LatLng) => void;
  onVertex: (p: LatLng) => void;
  flyTarget: { center: LatLng; zoom: number; key: number } | null;
}) {
  return (
    <MapContainer center={PUNJAB_CENTER} zoom={8} maxZoom={19} className="h-full w-full" zoomControl={false} attributionControl>
      <TileLayer
        url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        attribution="Imagery &copy; Esri, Maxar, Earthstar Geographics"
        maxNativeZoom={17}
        maxZoom={19}
      />
      <TileLayer
        url="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}"
        maxNativeZoom={17}
        maxZoom={19}
      />
      <ClickHandler mode={mode} onPin={onPin} onVertex={onVertex} />
      <FlyTo target={flyTarget} />
      {mode === "pin" && pin && (
        <>
          <CircleMarker center={pin} radius={22} pathOptions={{ color: FIELD_COLOR, weight: 2, fillOpacity: 0.15 }} />
          <CircleMarker center={pin} radius={7} pathOptions={{ color: "#111", weight: 2, fillColor: FIELD_COLOR, fillOpacity: 1 }} />
        </>
      )}
      {mode === "boundary" && vertices.length >= 3 && (
        <Polygon positions={vertices} pathOptions={{ color: FIELD_COLOR, weight: 3, fillOpacity: 0.2 }} />
      )}
      {mode === "boundary" && vertices.length === 2 && (
        <Polyline positions={vertices} pathOptions={{ color: FIELD_COLOR, weight: 3 }} />
      )}
      {mode === "boundary" &&
        vertices.map((v, i) => (
          <CircleMarker key={i} center={v} radius={6} pathOptions={{ color: "#111", weight: 2, fillColor: FIELD_COLOR, fillOpacity: 1 }} />
        ))}
    </MapContainer>
  );
}
