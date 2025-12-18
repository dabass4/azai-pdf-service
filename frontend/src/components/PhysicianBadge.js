import React, { useState } from "react";
import axios from "axios";
import { CheckCircle, XCircle, Loader2, User } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

/**
 * Physician Badge Component
 * Displays physician NPI with click-to-verify PECOS status
 */
const PhysicianBadge = ({ npi, name, className }) => {
  const [lookupResult, setLookupResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showPopover, setShowPopover] = useState(false);

  const lookupNPI = async () => {
    if (!npi || lookupResult) {
      setShowPopover(true);
      return;
    }

    setIsLoading(true);
    setShowPopover(true);

    try {
      const response = await axios.get(`${API}/npi/lookup/${npi}`);
      setLookupResult(response.data);
    } catch (err) {
      console.error("NPI lookup error:", err);
      setLookupResult({
        npi: npi,
        name: name || "Unknown",
        is_pecos_certified: false,
        pecos_status: err.response?.status === 404 ? "NPI not found" : "Unable to verify",
        error: true
      });
    } finally {
      setIsLoading(false);
    }
  };

  if (!npi) return <span className="text-gray-400">N/A</span>;

  return (
    <div className={`relative inline-block ${className || ""}`}>
      <button
        type="button"
        onClick={lookupNPI}
        className="font-mono text-blue-600 hover:text-blue-800 hover:underline focus:outline-none flex items-center gap-1"
        title="Click to verify PECOS status"
      >
        {npi}
        {isLoading && <Loader2 className="h-3 w-3 animate-spin" />}
      </button>

      {/* Popover */}
      {showPopover && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 z-40" 
            onClick={() => setShowPopover(false)}
          />
          
          {/* Popover content */}
          <div className="absolute z-50 left-0 top-full mt-1 w-72 p-3 bg-white border border-gray-200 rounded-lg shadow-xl">
            {isLoading ? (
              <div className="flex items-center gap-2 text-gray-600">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm">Verifying physician...</span>
              </div>
            ) : lookupResult ? (
              <div>
                <div className="flex items-start gap-2 mb-2">
                  <User className="h-5 w-5 text-gray-400 mt-0.5" />
                  <div>
                    <div className="font-medium">{lookupResult.name || name}</div>
                    <div className="text-xs text-gray-500 font-mono">NPI: {lookupResult.npi}</div>
                    {lookupResult.specialty && (
                      <div className="text-xs text-gray-500">{lookupResult.specialty}</div>
                    )}
                  </div>
                </div>
                
                {/* PECOS Status */}
                <div className="mt-3 pt-3 border-t">
                  <div className="text-xs text-gray-500 mb-1">Medicare Enrollment (PECOS)</div>
                  {lookupResult.is_pecos_certified ? (
                    <div className="flex items-center gap-1 text-green-700">
                      <CheckCircle className="h-4 w-4" />
                      <span className="text-sm font-medium">PECOS Certified</span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-1 text-amber-700">
                      <XCircle className="h-4 w-4" />
                      <span className="text-sm font-medium">{lookupResult.pecos_status || "Not Certified"}</span>
                    </div>
                  )}
                </div>

                {!lookupResult.is_pecos_certified && !lookupResult.error && (
                  <p className="text-xs text-amber-600 mt-2 p-2 bg-amber-50 rounded">
                    ⚠️ Verify Medicare enrollment before submitting claims
                  </p>
                )}

                <div className="flex justify-end pt-2 mt-2 border-t">
                  <button
                    type="button"
                    onClick={() => setShowPopover(false)}
                    className="text-xs text-gray-500 hover:text-gray-700"
                  >
                    Close
                  </button>
                </div>
              </div>
            ) : null}
          </div>
        </>
      )}
    </div>
  );
};

export default PhysicianBadge;
