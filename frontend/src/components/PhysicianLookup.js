import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import { CheckCircle, XCircle, Loader2, Search, User } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

/**
 * Physician Lookup Component
 * Silently looks up physician info from NPPES when NPI is entered
 * Displays PECOS certification status
 */
const PhysicianLookup = ({
  npiValue,
  nameValue,
  onNpiChange,
  onNameChange,
  onPhysicianData,
  npiError,
  nameError
}) => {
  const [lookupResult, setLookupResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  
  const npiTimeoutRef = useRef(null);
  const nameTimeoutRef = useRef(null);

  // Cleanup timeouts on unmount
  useEffect(() => {
    return () => {
      if (npiTimeoutRef.current) clearTimeout(npiTimeoutRef.current);
      if (nameTimeoutRef.current) clearTimeout(nameTimeoutRef.current);
    };
  }, []);

  // Look up NPI when it changes (silently in background)
  const lookupNPI = async (npi) => {
    if (!npi || npi.length !== 10 || !/^\d{10}$/.test(npi)) {
      setLookupResult(null);
      return;
    }

    setIsLoading(true);

    try {
      const response = await axios.get(`${API}/npi/lookup/${npi}`);
      setLookupResult(response.data);
      
      // Auto-fill name if empty
      if (onNameChange && !nameValue && response.data.name) {
        onNameChange(response.data.name);
      }
      
      // Pass full data to parent if needed
      if (onPhysicianData) {
        onPhysicianData(response.data);
      }
    } catch (err) {
      console.error("NPI lookup error:", err);
      setLookupResult({
        npi: npi,
        name: nameValue || "",
        is_pecos_certified: false,
        pecos_status: err.response?.status === 404 ? "NPI not found" : "Unable to verify",
        error: true
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Search by name
  const searchByName = async (name) => {
    if (!name || name.length < 3) {
      setSearchResults([]);
      setShowSuggestions(false);
      return;
    }

    try {
      const response = await axios.get(`${API}/npi/search?name=${encodeURIComponent(name)}&limit=5`);
      setSearchResults(response.data.results || []);
      setShowSuggestions(response.data.results?.length > 0);
    } catch (err) {
      console.error("NPI search error:", err);
      setSearchResults([]);
    }
  };

  // Handle NPI input change
  const handleNpiChange = (e) => {
    const value = e.target.value.replace(/\D/g, '').slice(0, 10);
    onNpiChange(value);
    setLookupResult(null);
    
    // Clear previous timeout
    if (npiTimeoutRef.current) {
      clearTimeout(npiTimeoutRef.current);
    }
    
    // Debounced lookup when 10 digits
    if (value.length === 10) {
      npiTimeoutRef.current = setTimeout(() => {
        lookupNPI(value);
      }, 500);
    }
  };

  // Handle name input change
  const handleNameChange = (e) => {
    const value = e.target.value;
    onNameChange(value);
    
    // Clear previous timeout
    if (nameTimeoutRef.current) {
      clearTimeout(nameTimeoutRef.current);
    }
    
    // Debounced search
    nameTimeoutRef.current = setTimeout(() => {
      searchByName(value);
    }, 400);
  };

  // Handle selection from search results
  const handleSelectPhysician = (physician) => {
    onNpiChange(physician.npi);
    onNameChange(physician.name);
    setShowSuggestions(false);
    setSearchResults([]);
    
    // Lookup full details including PECOS
    lookupNPI(physician.npi);
  };

  // PECOS Badge component
  const PECOSBadge = ({ isEnrolled, status }) => {
    if (isLoading) {
      return (
        <span className="inline-flex items-center gap-1 text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded-full">
          <Loader2 className="h-3 w-3 animate-spin" />
          Checking...
        </span>
      );
    }

    if (isEnrolled) {
      return (
        <span className="inline-flex items-center gap-1 text-xs px-2 py-1 bg-green-100 text-green-700 rounded-full">
          <CheckCircle className="h-3 w-3" />
          PECOS Certified
        </span>
      );
    }

    return (
      <span className="inline-flex items-center gap-1 text-xs px-2 py-1 bg-amber-100 text-amber-700 rounded-full">
        <XCircle className="h-3 w-3" />
        {status || "Not PECOS Certified"}
      </span>
    );
  };

  return (
    <div className="space-y-4">
      {/* Physician Name Field */}
      <div className="relative">
        <Label htmlFor="physician_name">Physician Name *</Label>
        <div className="relative">
          <Input
            id="physician_name"
            value={nameValue || ""}
            onChange={handleNameChange}
            onFocus={() => searchResults.length > 0 && setShowSuggestions(true)}
            placeholder="Enter name or search..."
            className={nameError ? "border-red-500" : ""}
          />
          {isLoading && npiValue?.length === 10 && (
            <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-gray-400" />
          )}
        </div>
        {nameError && <p className="text-xs text-red-500 mt-1">{nameError}</p>}
        
        {/* Search Suggestions Dropdown */}
        {showSuggestions && searchResults.length > 0 && (
          <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-60 overflow-y-auto">
            <div className="p-2 border-b bg-gray-50">
              <span className="text-xs text-gray-500">{searchResults.length} physician(s) found</span>
            </div>
            {searchResults.map((physician, idx) => (
              <button
                key={idx}
                type="button"
                className="w-full px-3 py-2 text-left hover:bg-gray-100 flex items-start gap-2 border-b last:border-b-0"
                onClick={() => handleSelectPhysician(physician)}
              >
                <User className="h-4 w-4 mt-0.5 text-gray-400 shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-sm">{physician.name}</div>
                  <div className="text-xs text-gray-500">
                    NPI: {physician.npi} • {physician.specialty || "Specialty N/A"}
                  </div>
                  {physician.city && physician.state && (
                    <div className="text-xs text-gray-400">
                      {physician.city}, {physician.state}
                    </div>
                  )}
                </div>
              </button>
            ))}
            <button
              type="button"
              className="w-full px-3 py-2 text-center text-xs text-gray-500 hover:bg-gray-50"
              onClick={() => setShowSuggestions(false)}
            >
              Close
            </button>
          </div>
        )}
      </div>

      {/* NPI Field */}
      <div>
        <Label htmlFor="physician_npi">NPI Number (10 digits) *</Label>
        <div className="flex gap-2">
          <Input
            id="physician_npi"
            value={npiValue || ""}
            onChange={handleNpiChange}
            maxLength="10"
            placeholder="1234567890"
            className={`font-mono flex-1 ${npiError ? "border-red-500" : ""}`}
          />
        </div>
        {npiError && <p className="text-xs text-red-500 mt-1">{npiError}</p>}
      </div>

      {/* Lookup Result / PECOS Status */}
      {(lookupResult || (npiValue?.length === 10 && isLoading)) && (
        <div className={`p-3 rounded-md border ${
          lookupResult?.error 
            ? "bg-amber-50 border-amber-200" 
            : lookupResult?.is_pecos_certified 
              ? "bg-green-50 border-green-200"
              : "bg-gray-50 border-gray-200"
        }`}>
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1">
              {lookupResult?.name && !lookupResult?.error && (
                <div className="text-sm font-medium mb-1">{lookupResult.name}</div>
              )}
              {lookupResult?.specialty && (
                <div className="text-xs text-gray-600 mb-2">{lookupResult.specialty}</div>
              )}
              <PECOSBadge 
                isEnrolled={lookupResult?.is_pecos_certified} 
                status={lookupResult?.pecos_status}
              />
            </div>
          </div>
          
          {lookupResult && !lookupResult.is_pecos_certified && !lookupResult.error && (
            <p className="text-xs text-amber-700 mt-2">
              ⚠️ This provider may not be enrolled in Medicare PECOS. 
              Verify enrollment before submitting claims.
            </p>
          )}
        </div>
      )}
    </div>
  );
};

export default PhysicianLookup;
