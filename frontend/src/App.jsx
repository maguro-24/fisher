import { useEffect, useRef, useState } from "react";
import L from "leaflet";

const ACRES_PER_KM2 = 247.105;

const formatArea = (km2) => {
  const acres = km2 * ACRES_PER_KM2;
  return acres >= 10
    ? `${Math.round(acres).toLocaleString()} acres`
    : `${acres.toFixed(1)} acres`;
};

// "Lake Harriet, Minneapolis, Hennepin County, Minnesota, United States" -> after the name
const place = (lake) =>
  (lake.display_name || "").split(",").slice(1, 4).join(",").trim();

export default function App() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState(null); // null = nothing searched yet
  const [selected, setSelected] = useState(null);
  const [status, setStatus] = useState("idle"); // idle | loading | error
  const [error, setError] = useState("");

  const mapEl = useRef(null);
  const map = useRef(null);
  const outline = useRef(null);

  // Create the map once.
  useEffect(() => {
    const satellite = L.tileLayer(
      "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
      { maxZoom: 19, attribution: "Imagery &copy; Esri, Maxar, Earthstar Geographics" }
    );
    const streets = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: "&copy; OpenStreetMap contributors",
    });
    map.current = L.map(mapEl.current, { layers: [satellite], zoomControl: true })
      .setView([39.5, -98.35], 4);
    L.control.layers({ Satellite: satellite, Streets: streets }, null, { position: "topright" })
      .addTo(map.current);
    return () => map.current.remove();
  }, []);

  // Draw the selected lake.
  useEffect(() => {
    if (outline.current) outline.current.remove();
    outline.current = null;
    if (!selected) return;
    outline.current = L.geoJSON(selected.geometry, {
      style: { color: "#f2a900", weight: 2.5, fillColor: "#17707f", fillOpacity: 0.18 },
    }).addTo(map.current);
    map.current.fitBounds(outline.current.getBounds(), { padding: [48, 48] });
  }, [selected]);

  async function search(e) {
    e.preventDefault();
    const q = query.trim();
    if (q.length < 2) return;
    setStatus("loading");
    setError("");
    try {
      const res = await fetch(`/api/lakes/search?q=${encodeURIComponent(q)}`);
      if (!res.ok) throw new Error(res.status === 502 ? "The map data service didn't respond. Try again in a moment." : `Search failed (${res.status}).`);
      const data = await res.json();
      setResults(data.results);
      setSelected(data.results[0] ?? null);
      setStatus("idle");
    } catch (err) {
      setStatus("error");
      setError(err.message === "Failed to fetch"
        ? "Can't reach the Fisher backend. Is it running on port 8000?"
        : err.message);
    }
  }

  return (
    <div className="app">
      <aside className="panel">
        <h1>Fisher</h1>
        <p className="lede">Find a lake to see its outline on satellite imagery.</p>

        <form onSubmit={search} className="search">
          <label htmlFor="lake-q">Lake name</label>
          <div className="row">
            <input
              id="lake-q"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Lake Minnetonka"
              autoComplete="off"
            />
            <button type="submit" disabled={status === "loading" || query.trim().length < 2}>
              {status === "loading" ? "Searching" : "Search"}
            </button>
          </div>
        </form>

        <div className="status" role="status" aria-live="polite">
          {status === "error" && <p className="error">{error}</p>}
          {status === "idle" && results && results.length === 0 && (
            <p>No lake outlines found for “{query.trim()}”. Try adding the town or state.</p>
          )}
        </div>

        {results && results.length > 0 && (
          <ul className="results">
            {results.map((lake) => (
              <li key={lake.osm_id}>
                <button
                  className={selected?.osm_id === lake.osm_id ? "lake active" : "lake"}
                  onClick={() => setSelected(lake)}
                >
                  <span className="lake-name">{lake.name}</span>
                  <span className="lake-meta">{formatArea(lake.area_km2)}</span>
                  <span className="lake-place">{place(lake)}</span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </aside>
      <main className="map" ref={mapEl} aria-label="Map" />
    </div>
  );
}
