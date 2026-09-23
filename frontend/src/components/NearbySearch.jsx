import { useEffect, useState } from "react";
import { findNearbyDonors } from "../services/locationApi";

const RADIUS_OPTIONS = [
  { label: "15 km", value: 15000 },
  { label: "30 km", value: 30000 },
  { label: "45 km", value: 45000 },
];

function formatDistance(distanceM) {
  if (distanceM < 1000) {
    return `${Math.round(distanceM)} m`;
  }

  return `${(distanceM / 1000).toFixed(1)} km`;
}

export default function NearbySearch({ userLocation }) {
  const [radius, setRadius] = useState(15000);
  const [results, setResults] = useState([]);
  const [message, setMessage] = useState("");
  const [isSearching, setIsSearching] = useState(false);

  useEffect(() => {
    setResults([]);
    setMessage("");
  }, [userLocation]);

  const searchNearby = async () => {
    if (!userLocation) {
      setMessage("Detect your current location before searching for donors.");
      return;
    }

    const controller = new AbortController();
    setIsSearching(true);
    setMessage("");

    try {
      const response = await findNearbyDonors(
        userLocation.lat,
        userLocation.lon,
        radius,
        controller.signal,
      );
      setResults(response.results);
      setMessage(
        response.count === 0
          ? `No donors found within ${radius / 1000} km.`
          : `${response.count} donor${response.count === 1 ? "" : "s"} found.`,
      );
    } catch (error) {
      setResults([]);
      setMessage(error.message);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <section className="nearby-panel" aria-labelledby="nearby-heading">
      <div className="nearby-heading-row">
        <div>
          <h2 id="nearby-heading">Find nearby donors</h2>
          <p>
            {userLocation
              ? "Your detected location will be used as the search origin."
              : "Use My Location first to set the search origin."}
          </p>
        </div>

        <div className="nearby-controls">
          <label htmlFor="nearby-radius">Radius</label>
          <select
            id="nearby-radius"
            value={radius}
            onChange={(event) => setRadius(Number(event.target.value))}
          >
            {RADIUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={searchNearby}
            disabled={!userLocation || isSearching}
          >
            {isSearching ? "Searching..." : "Find Donors"}
          </button>
        </div>
      </div>

      {userLocation && (
        <p className="origin-coordinates">
          Search origin: {userLocation.lat.toFixed(6)}, {" "}
          {userLocation.lon.toFixed(6)}
        </p>
      )}

      {message && <p className="nearby-message" aria-live="polite">{message}</p>}

      {results.length > 0 && (
        <ol className="nearby-results">
          {results.map((result) => (
            <li key={result.id}>
              <div>
                <strong>{result.name}</strong>
                <span>Nearby donor</span>
              </div>
              <span className="distance">{formatDistance(result.distance_m)}</span>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
