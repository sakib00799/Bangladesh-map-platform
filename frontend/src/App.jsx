import { useEffect, useState } from "react";
import LocationSearch from "./components/LocationSearch";
import NearbySearch from "./components/NearbySearch";
import BangladeshMap from "./map/BangladeshMap";
import { getMapConfig, reverseGeocode } from "./services/locationApi";

const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function App() {
  const [status, setStatus] = useState("Checking backend...");
  const [isHealthy, setIsHealthy] = useState(false);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [userLocation, setUserLocation] = useState(null);
  const [locationError, setLocationError] = useState("");
  const [isLocating, setIsLocating] = useState(false);
  const [address, setAddress] = useState("");
  const [addressStatus, setAddressStatus] = useState("idle");
  const [mapConfig, setMapConfig] = useState(null);
  const [mapConfigError, setMapConfigError] = useState("");

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch(`${apiUrl}/health`);
        if (!response.ok) {
          throw new Error(`Backend returned ${response.status}`);
        }

        const data = await response.json();
        setIsHealthy(data.status === "ok");
        setStatus(data.status === "ok" ? "Backend is healthy" : "Backend status is unknown");
      } catch {
        setIsHealthy(false);
        setStatus("Backend is unavailable");
      }
    };

    checkHealth();

    getMapConfig()
      .then(setMapConfig)
      .catch(() => setMapConfigError("Map configuration is unavailable."));
  }, []);

  useEffect(() => {
    if (!selectedLocation) {
      setAddress("");
      setAddressStatus("idle");
      return undefined;
    }

    const controller = new AbortController();
    setAddress("");
    setAddressStatus("loading");

    reverseGeocode(
      selectedLocation.lat,
      selectedLocation.lon,
      controller.signal,
    )
      .then((result) => {
        setAddress(result.display_name);
        setAddressStatus("success");
      })
      .catch((error) => {
        if (error.name !== "AbortError") {
          setAddressStatus("unavailable");
        }
      });

    return () => controller.abort();
  }, [selectedLocation]);

  const useMyLocation = () => {
    setLocationError("");

    if (!("geolocation" in navigator)) {
      setLocationError("Location is unavailable in this browser.");
      return;
    }

    setIsLocating(true);

    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        const detectedLocation = {
          lat: coords.latitude,
          lon: coords.longitude,
          source: "browser",
        };
        setUserLocation(detectedLocation);
        setSelectedLocation(detectedLocation);
        setIsLocating(false);
      },
      (error) => {
        const messages = {
          [error.PERMISSION_DENIED]:
            "Location permission was denied. Allow location access and try again.",
          [error.POSITION_UNAVAILABLE]:
            "Your location is currently unavailable. Please try again.",
          [error.TIMEOUT]: "Location request timed out. Please try again.",
        };

        setLocationError(messages[error.code] || "Unable to get your location.");
        setIsLocating(false);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0,
      },
    );
  };

  const selectMapLocation = (location) => {
    setLocationError("");
    setSelectedLocation(location);
  };

  return (
    <main className="page-shell">
      <header className="page-header">
        <div>
          <p className="eyebrow">Standalone platform</p>
          <h1>Bangladesh Map Platform</h1>
          <p className="intro">Explore Bangladesh using an open-source interactive map.</p>
        </div>
        <div className={`health-status ${isHealthy ? "healthy" : "unhealthy"}`}>
          <span aria-hidden="true" />
          {status}
        </div>
      </header>

      <section className="map-card" aria-labelledby="map-heading">
        <LocationSearch onSelect={selectMapLocation} />

        <div className="map-card-header">
          <div>
            <h2 id="map-heading">Bangladesh map</h2>
            <p>Click the map to select a location, or use your current location.</p>
          </div>
          <button
            type="button"
            className="location-button"
            onClick={useMyLocation}
            disabled={isLocating}
          >
            {isLocating ? "Finding location..." : "Use My Location"}
          </button>
        </div>

        {(selectedLocation || locationError) && (
          <div className="location-feedback" aria-live="polite">
            {selectedLocation && !locationError && (
              <p>
                {selectedLocation.source === "browser"
                  ? "Current location"
                  : "Selected location"}
                : {selectedLocation.lat.toFixed(6)}, {" "}
                {selectedLocation.lon.toFixed(6)}
              </p>
            )}
            {locationError && <p className="location-error">{locationError}</p>}
            {selectedLocation && addressStatus === "loading" && (
              <p className="address-status">Finding address...</p>
            )}
            {selectedLocation && addressStatus === "success" && (
              <p className="selected-address">{address}</p>
            )}
            {selectedLocation && addressStatus === "unavailable" && (
              <p className="address-status">
                Address unavailable. The selected coordinates are still usable.
              </p>
            )}
          </div>
        )}

        <NearbySearch userLocation={userLocation} />

        {mapConfig ? (
          <BangladeshMap
            selectedLocation={selectedLocation}
            onLocationSelect={selectMapLocation}
            styleUrl={mapConfig.style_url}
            defaultCenter={mapConfig.default_center}
            defaultZoom={mapConfig.default_zoom}
          />
        ) : (
          <div className="bangladesh-map" role="status">
            {mapConfigError || "Loading map configuration..."}
          </div>
        )}
      </section>
    </main>
  );
}
