const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function readErrorMessage(response, fallback) {
  try {
    const body = await response.json();
    if (typeof body?.error?.message === "string") {
      return body.error.message;
    }
  } catch {
    // Use the endpoint-specific fallback when the response is not JSON.
  }

  return fallback;
}

export async function getMapConfig() {
  const response = await fetch(`${apiUrl}/map/config`);

  if (!response.ok) {
    throw new Error(
      await readErrorMessage(response, "Map configuration is unavailable."),
    );
  }

  const config = await response.json();
  return {
    ...config,
    style_url: new URL(config.style_url, apiUrl).toString(),
  };
}

export async function searchLocations(query) {
  const response = await fetch(
    `${apiUrl}/search-location?q=${encodeURIComponent(query)}`,
  );

  if (!response.ok) {
    throw new Error(
      await readErrorMessage(response, "Location search failed. Please try again."),
    );
  }

  const body = await response.json();
  return Array.isArray(body.results) ? body.results : [];
}

export async function reverseGeocode(lat, lon, signal) {
  const params = new URLSearchParams({ lat: String(lat), lon: String(lon) });
  const response = await fetch(`${apiUrl}/reverse-geocode?${params}`, { signal });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response, "Address lookup failed."));
  }

  return response.json();
}

export async function findNearbyDonors(lat, lon, radius, signal) {
  const params = new URLSearchParams({
    lat: String(lat),
    lon: String(lon),
    radius: String(radius),
    type: "donor",
  });
  const response = await fetch(`${apiUrl}/nearby?${params}`, { signal });

  if (!response.ok) {
    throw new Error(
      await readErrorMessage(response, "Nearby donor search failed. Please try again."),
    );
  }

  return response.json();
}
