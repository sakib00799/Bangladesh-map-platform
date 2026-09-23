import { useEffect, useRef } from "react";
import * as maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

export default function BangladeshMap({
  className = "",
  selectedLocation = null,
  onLocationSelect,
  styleUrl,
  defaultCenter,
  defaultZoom,
}) {
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const markerRef = useRef(null);
  const onLocationSelectRef = useRef(onLocationSelect);

  useEffect(() => {
    onLocationSelectRef.current = onLocationSelect;
  }, [onLocationSelect]);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) {
      return undefined;
    }

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: styleUrl,
      center: defaultCenter,
      zoom: defaultZoom,
      attributionControl: false,
    });

    map.addControl(new maplibregl.NavigationControl(), "top-right");
    map.addControl(
      new maplibregl.AttributionControl({ compact: false }),
      "bottom-right",
    );

    const handleMapClick = ({ lngLat }) => {
      onLocationSelectRef.current?.({
        lat: lngLat.lat,
        lon: lngLat.lng,
        source: "map",
      });
    };

    map.on("click", handleMapClick);

    mapRef.current = map;

    return () => {
      map.off("click", handleMapClick);
      markerRef.current?.remove();
      markerRef.current = null;
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;

    if (!map || !selectedLocation) {
      return;
    }

    const coordinates = [selectedLocation.lon, selectedLocation.lat];

    if (!markerRef.current) {
      markerRef.current = new maplibregl.Marker({
        color: "#d92d3e",
        draggable: true,
      })
        .setLngLat(coordinates)
        .addTo(map);

      markerRef.current.on("dragend", () => {
        const position = markerRef.current?.getLngLat();

        if (position) {
          onLocationSelectRef.current?.({
            lat: position.lat,
            lon: position.lng,
            source: "marker",
          });
        }
      });
    } else {
      markerRef.current.setLngLat(coordinates);
    }

    if (["browser", "search"].includes(selectedLocation.source)) {
      map.flyTo({
        center: coordinates,
        zoom: 14,
        essential: true,
      });
    }
  }, [selectedLocation]);

  return (
    <div
      ref={containerRef}
      className={`bangladesh-map ${className}`.trim()}
      aria-label="Interactive map of Bangladesh"
    />
  );
}
