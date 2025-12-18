import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import { Search, CheckCircle, AlertCircle, ExternalLink, Loader2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

/**
 * ICD-10 Code Lookup Component
 * Fetches ICD-10 code information from icd10data.com and displays billability status
 */
const ICD10Lookup = ({ 
  value, 
  onChange, 
  onDescriptionChange,
  description,
  error,
  className 
}) => {
  const [lookupResult, setLookupResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [lookupError, setLookupError] = useState(null);
  const [showDropdown, setShowDropdown] = useState(false);
  const [searchResults, setSearchResults] = useState([]);

  // Debounce timer ref
  const searchTimeoutRef = useRef(null);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, []);

  // Look up a specific ICD-10 code
  const lookupCode = async (code) => {
    if (!code || code.length < 3) {
      setLookupResult(null);
      return;
    }

    setIsLoading(true);
    setLookupError(null);

    try {
      const response = await axios.get(`${API}/icd10/lookup/${encodeURIComponent(code)}`);
      setLookupResult(response.data);
      
      // Auto-fill description if empty
      if (onDescriptionChange && !description && response.data.description) {
        onDescriptionChange(response.data.description);
      }
    } catch (err) {
      console.error("ICD-10 lookup error:", err);
      setLookupError(err.response?.data?.detail || "Failed to look up code");
      setLookupResult(null);
    } finally {
      setIsLoading(false);
    }
  };

  // Search ICD-10 codes
  const searchCodes = async (query) => {
    if (!query || query.length < 2) {
      setSearchResults([]);
      setShowDropdown(false);
      return;
    }

    try {
      const response = await axios.get(`${API}/icd10/search?q=${encodeURIComponent(query)}`);
      setSearchResults(response.data.results || []);
      setShowDropdown(response.data.results?.length > 0);
    } catch (err) {
      console.error("ICD-10 search error:", err);
      setSearchResults([]);
    }
  };

  // Debounced search
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const debouncedSearch = useCallback(debounce(searchCodes, 300), []);

  // Handle input change
  const handleInputChange = (e) => {
    const newValue = e.target.value.toUpperCase();
    onChange(newValue);
    setLookupResult(null);
    debouncedSearch(newValue);
  };

  // Handle code selection from dropdown
  const handleSelectCode = (result) => {
    onChange(result.code);
    if (onDescriptionChange) {
      onDescriptionChange(result.description);
    }
    setLookupResult({
      code: result.code,
      description: result.description,
      is_billable: result.is_billable,
      billable_text: result.is_billable ? "Billable/Specific Code" : "Non-Billable/Non-Specific Code",
      source_url: result.url
    });
    setShowDropdown(false);
    setSearchResults([]);
  };

  // Handle lookup button click
  const handleLookup = () => {
    if (value) {
      lookupCode(value);
      setShowDropdown(false);
    }
  };

  // Clear the lookup result
  const handleClear = () => {
    setLookupResult(null);
    setLookupError(null);
  };

  return (
    <div className={`space-y-2 ${className || ""}`}>
      <Label htmlFor="icd10_code">ICD-10 Code *</Label>
      
      <div className="relative">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Input
              id="icd10_code"
              value={value || ""}
              onChange={handleInputChange}
              onFocus={() => searchResults.length > 0 && setShowDropdown(true)}
              placeholder="e.g., F32.9 or search by keyword"
              className={`${error ? "border-red-500" : ""} pr-10`}
            />
            {isLoading && (
              <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-gray-400" />
            )}
          </div>
          <Button 
            type="button" 
            variant="outline" 
            onClick={handleLookup}
            disabled={!value || isLoading}
            className="shrink-0"
          >
            <Search size={16} className="mr-1" />
            Verify
          </Button>
        </div>

        {/* Search Results Dropdown */}
        {showDropdown && searchResults.length > 0 && (
          <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-60 overflow-y-auto">
            <div className="p-2 border-b bg-gray-50">
              <span className="text-xs text-gray-500">{searchResults.length} result(s) found</span>
            </div>
            {searchResults.map((result, idx) => (
              <button
                key={idx}
                type="button"
                className="w-full px-3 py-2 text-left hover:bg-gray-100 flex items-center justify-between border-b last:border-b-0"
                onClick={() => handleSelectCode(result)}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-semibold text-blue-600">{result.code}</span>
                    {result.is_billable ? (
                      <span className="text-xs px-1.5 py-0.5 bg-green-100 text-green-700 rounded">Billable</span>
                    ) : (
                      <span className="text-xs px-1.5 py-0.5 bg-red-100 text-red-700 rounded">Non-Billable</span>
                    )}
                  </div>
                  <p className="text-sm text-gray-600 truncate">{result.description}</p>
                </div>
              </button>
            ))}
            <button
              type="button"
              className="w-full px-3 py-2 text-center text-xs text-gray-500 hover:bg-gray-50"
              onClick={() => setShowDropdown(false)}
            >
              Close
            </button>
          </div>
        )}
      </div>

      {/* Lookup Result Display */}
      {lookupResult && (
        <div className={`p-3 rounded-md border ${lookupResult.is_billable ? "bg-green-50 border-green-200" : "bg-red-50 border-red-200"}`}>
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-2">
              {lookupResult.is_billable ? (
                <CheckCircle className="h-5 w-5 text-green-600 shrink-0 mt-0.5" />
              ) : (
                <AlertCircle className="h-5 w-5 text-red-600 shrink-0 mt-0.5" />
              )}
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold">{lookupResult.code}</span>
                  <span className={`text-xs px-2 py-0.5 rounded font-medium ${
                    lookupResult.is_billable 
                      ? "bg-green-200 text-green-800" 
                      : "bg-red-200 text-red-800"
                  }`}>
                    {lookupResult.is_billable ? "BILLABLE" : "NOT BILLABLE"}
                  </span>
                </div>
                <p className="text-sm mt-1">{lookupResult.description}</p>
                {!lookupResult.is_billable && (
                  <p className="text-xs text-red-700 mt-2 font-medium">
                    ⚠️ This code is not billable per ICD10data.com&apos;s recommendation. 
                    Consider using a more specific billable code.
                  </p>
                )}
              </div>
            </div>
            <div className="flex items-center gap-1">
              <a 
                href={lookupResult.source_url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-800"
                title="View on ICD10data.com"
              >
                <ExternalLink size={16} />
              </a>
              <button 
                type="button"
                onClick={handleClear}
                className="text-gray-400 hover:text-gray-600 ml-1"
                title="Clear"
              >
                <X size={16} />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Lookup Error */}
      {lookupError && (
        <div className="p-3 rounded-md bg-yellow-50 border border-yellow-200">
          <div className="flex items-center gap-2 text-yellow-800">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">{lookupError}</span>
          </div>
        </div>
      )}

      {/* External link to search */}
      <a 
        href="https://www.icd10data.com" 
        target="_blank" 
        rel="noopener noreferrer" 
        className="text-xs text-blue-600 hover:underline flex items-center gap-1"
      >
        Search ICD-10 codes on icd10data.com
        <ExternalLink size={12} />
      </a>

      {/* Validation Error */}
      {error && <p className="text-xs text-red-500">{error}</p>}
    </div>
  );
};

export default ICD10Lookup;
