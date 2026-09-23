import { useState } from "react";
import { searchLocations } from "../services/locationApi";

export default function LocationSearch({ onSelect }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [message, setMessage] = useState("");
  const [isSearching, setIsSearching] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    const normalizedQuery = query.trim();

    if (normalizedQuery.length < 2) {
      setResults([]);
      setMessage("Enter at least 2 characters.");
      return;
    }

    setIsSearching(true);
    setMessage("");

    try {
      const nextResults = await searchLocations(normalizedQuery);
      setResults(nextResults);
      setMessage(nextResults.length === 0 ? "No Bangladesh locations found." : "");
    } catch (error) {
      setResults([]);
      setMessage(error.message);
    } finally {
      setIsSearching(false);
    }
  };

  const handleSelect = (result) => {
    onSelect({
      lat: result.lat,
      lon: result.lon,
      source: "search",
    });
    setQuery(result.name);
    setResults([]);
    setMessage(`Selected ${result.display_name}`);
  };

  return (
    <div className="location-search">
      <form className="search-form" onSubmit={handleSubmit}>
        <label htmlFor="location-query">Search for a place in Bangladesh</label>
        <div className="search-fields">
          <input
            id="location-query"
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Dhanmondi, Dhaka"
            maxLength={100}
            autoComplete="off"
          />
          <button type="submit" disabled={isSearching}>
            {isSearching ? "Searching..." : "Search"}
          </button>
        </div>
      </form>

      {message && <p className="search-message" aria-live="polite">{message}</p>}

      {results.length > 0 && (
        <ul className="search-results" aria-label="Location search results">
          {results.map((result) => (
            <li key={result.id}>
              <button type="button" onClick={() => handleSelect(result)}>
                <strong>{result.name}</strong>
                <span>{result.display_name}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
