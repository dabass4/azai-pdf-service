import React, { useState } from "react";
import axios from "axios";
import { CheckCircle, AlertCircle, ExternalLink, Loader2 } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

/**
 * ICD-10 Code Badge Component
 * Displays ICD-10 code with billability status on click
 */
const ICD10Badge = ({ code, description, className }) => {
  const [lookupResult, setLookupResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showPopover, setShowPopover] = useState(false);

  const lookupCode = async () => {
    if (!code || lookupResult) {
      setShowPopover(true);
      return;
    }

    setIsLoading(true);
    setShowPopover(true);

    try {
      const response = await axios.get(`${API}/icd10/lookup/${encodeURIComponent(code)}`);
      setLookupResult(response.data);
    } catch (err) {
      console.error("ICD-10 lookup error:", err);
      setLookupResult({
        code: code,
        description: description || "Unknown",
        is_billable: null,
        billable_text: "Unable to verify",
        error: true
      });
    } finally {
      setIsLoading(false);
    }
  };

  if (!code) return <span className="text-gray-400">N/A</span>;

  return (
    <div className={`relative inline-block ${className || ""}`}>
      <button
        type="button"
        onClick={lookupCode}
        className="font-mono text-blue-600 hover:text-blue-800 hover:underline focus:outline-none flex items-center gap-1"
        title="Click to verify billability"
      >
        {code}
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
                <span className="text-sm">Verifying code...</span>
              </div>
            ) : lookupResult ? (
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="font-mono font-bold text-lg">{lookupResult.code}</span>
                  {lookupResult.is_billable === true && (
                    <span className="flex items-center gap-1 text-xs px-2 py-0.5 bg-green-100 text-green-700 rounded-full">
                      <CheckCircle size={12} />
                      Billable
                    </span>
                  )}
                  {lookupResult.is_billable === false && (
                    <span className="flex items-center gap-1 text-xs px-2 py-0.5 bg-red-100 text-red-700 rounded-full">
                      <AlertCircle size={12} />
                      Not Billable
                    </span>
                  )}
                  {lookupResult.is_billable === null && (
                    <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full">
                      Unable to verify
                    </span>
                  )}
                </div>
                
                <p className="text-sm text-gray-700 mb-2">{lookupResult.description}</p>
                
                {lookupResult.is_billable === false && (
                  <p className="text-xs text-red-600 mb-2 p-2 bg-red-50 rounded">
                    ⚠️ This code is not billable per ICD10data.com. Consider using a more specific code.
                  </p>
                )}

                <div className="flex items-center justify-between pt-2 border-t">
                  {lookupResult.source_url && (
                    <a 
                      href={lookupResult.source_url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-xs text-blue-600 hover:underline flex items-center gap-1"
                    >
                      View on ICD10data.com
                      <ExternalLink size={10} />
                    </a>
                  )}
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

export default ICD10Badge;
