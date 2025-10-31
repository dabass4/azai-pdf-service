import { useState, useEffect } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";
import { CheckCircle, XCircle, Clock, Download, Upload, AlertCircle, MapPin, Phone } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function EVVManagement() {
  const [activeTab, setActiveTab] = useState("visits");
  const [visits, setVisits] = useState([]);
  const [transmissions, setTransmissions] = useState([]);
  const [businessEntity, setBusinessEntity] = useState(null);
  const [loading, setLoading] = useState(false);
  const [referenceData, setReferenceData] = useState({
    payers: [],
    programs: {},
    procedureCodes: {},
    exceptionCodes: {}
  });

  // Tabs configuration
  const tabs = [
    { id: "visits", label: "EVV Visits" },
    { id: "export", label: "Export Data" },
    { id: "submit", label: "Submit to EVV" },
    { id: "transmissions", label: "Transmission History" },
    { id: "config", label: "Configuration" }
  ];

  useEffect(() => {
    loadBusinessEntity();
    loadReferenceData();
    if (activeTab === "visits") {
      loadVisits();
    } else if (activeTab === "transmissions") {
      loadTransmissions();
    }
  }, [activeTab]);

  const loadBusinessEntity = async () => {
    try {
      const response = await axios.get(`${API}/evv/business-entity/active`);
      setBusinessEntity(response.data);
    } catch (error) {
      console.error("Error loading business entity:", error);
    }
  };

  const loadReferenceData = async () => {
    try {
      const [payersRes, programsRes, codesRes, exceptionsRes] = await Promise.all([
        axios.get(`${API}/evv/reference/payers`),
        axios.get(`${API}/evv/reference/programs`),
        axios.get(`${API}/evv/reference/procedure-codes`),
        axios.get(`${API}/evv/reference/exception-codes`)
      ]);
      
      setReferenceData({
        payers: payersRes.data.payers || [],
        programs: programsRes.data.programs || {},
        procedureCodes: codesRes.data.procedure_codes || {},
        exceptionCodes: exceptionsRes.data.exception_codes || {}
      });
    } catch (error) {
      console.error("Error loading reference data:", error);
    }
  };

  const loadVisits = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/evv/visits`);
      setVisits(response.data);
    } catch (error) {
      toast.error("Failed to load EVV visits");
    } finally {
      setLoading(false);
    }
  };

  const loadTransmissions = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/evv/transmissions`);
      setTransmissions(response.data);
    } catch (error) {
      toast.error("Failed to load transmission history");
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (recordType) => {
    try {
      setLoading(true);
      let endpoint = "";
      if (recordType === "individuals") {
        endpoint = `${API}/evv/export/individuals`;
      } else if (recordType === "dcw") {
        endpoint = `${API}/evv/export/direct-care-workers`;
      } else if (recordType === "visits") {
        endpoint = `${API}/evv/export/visits`;
      }

      const response = await axios.get(endpoint);
      
      // Download as JSON file
      const blob = new Blob([JSON.stringify(response.data.data, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `evv_${recordType}_${new Date().toISOString()}.json`;
      a.click();
      window.URL.revokeObjectURL(url);
      
      toast.success(`Exported ${response.data.record_count} ${recordType} records`);
    } catch (error) {
      toast.error(`Failed to export ${recordType}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (recordType) => {
    try {
      setLoading(true);
      let endpoint = "";
      if (recordType === "individuals") {
        endpoint = `${API}/evv/submit/individuals`;
      } else if (recordType === "dcw") {
        endpoint = `${API}/evv/submit/direct-care-workers`;
      } else if (recordType === "visits") {
        endpoint = `${API}/evv/submit/visits`;
      }

      const response = await axios.post(endpoint);
      
      if (response.data.status === "success") {
        toast.success(`Submitted successfully! Transaction ID: ${response.data.transaction_id}`);
        if (response.data.has_rejections) {
          toast.warning(`${response.data.rejected_count} records were rejected`);
        }
        if (recordType === "visits") {
          loadVisits();
        }
      } else {
        toast.error(response.data.message || "Submission failed");
      }
    } catch (error) {
      toast.error(`Failed to submit ${recordType}`);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      draft: { color: "bg-gray-100 text-gray-800", icon: Clock },
      ready: { color: "bg-blue-100 text-blue-800", icon: CheckCircle },
      submitted: { color: "bg-green-100 text-green-800", icon: Upload },
      accepted: { color: "bg-green-100 text-green-800", icon: CheckCircle },
      rejected: { color: "bg-red-100 text-red-800", icon: XCircle },
      partial: { color: "bg-yellow-100 text-yellow-800", icon: AlertCircle }
    };

    const config = statusConfig[status] || statusConfig.draft;
    const Icon = config.icon;

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.color}`}>
        <Icon className="mr-1" size={12} />
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Ohio Medicaid EVV Management</h1>
        <p className="mt-2 text-sm text-gray-600">
          Electronic Visit Verification - Data export and submission to Ohio Department of Medicaid
        </p>
      </div>

      {/* Business Entity Status */}
      {businessEntity && (
        <Card className="mb-6 bg-blue-50 border-blue-200">
          <CardHeader>
            <CardTitle className="text-sm">Active Business Entity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div>
                <span className="font-semibold">Agency:</span> {businessEntity.agency_name}
              </div>
              <div>
                <span className="font-semibold">Entity ID:</span> {businessEntity.business_entity_id}
              </div>
              <div>
                <span className="font-semibold">Medicaid ID:</span> {businessEntity.business_entity_medicaid_id}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* EVV Visits Tab */}
      {activeTab === "visits" && (
        <div>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">EVV Visit Records</h2>
            <Button onClick={loadVisits} disabled={loading}>
              {loading ? "Loading..." : "Refresh"}
            </Button>
          </div>

          {visits.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <p className="text-gray-500">No EVV visits found. Create visits from timesheet data.</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {visits.map((visit) => (
                <Card key={visit.id}>
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <div>
                        <CardTitle className="text-lg">Visit {visit.visit_other_id}</CardTitle>
                        <CardDescription className="mt-1">
                          Patient: {visit.patient_other_id} | Employee: {visit.staff_other_id}
                        </CardDescription>
                      </div>
                      {getStatusBadge(visit.evv_status)}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="font-semibold">Payer:</span> {visit.payer}
                      </div>
                      <div>
                        <span className="font-semibold">Program:</span> {visit.payer_program}
                      </div>
                      <div>
                        <span className="font-semibold">Service:</span> {visit.procedure_code}
                      </div>
                      {visit.adj_in_datetime && (
                        <div>
                          <span className="font-semibold">Check In:</span> {new Date(visit.adj_in_datetime).toLocaleString()}
                        </div>
                      )}
                      {visit.adj_out_datetime && (
                        <div>
                          <span className="font-semibold">Check Out:</span> {new Date(visit.adj_out_datetime).toLocaleString()}
                        </div>
                      )}
                      {visit.units_to_bill && (
                        <div>
                          <span className="font-semibold">Units:</span> {visit.units_to_bill}
                        </div>
                      )}
                    </div>
                    
                    {visit.calls && visit.calls.length > 0 && (
                      <div className="mt-4 pt-4 border-t">
                        <span className="font-semibold text-sm">Calls: </span>
                        <span className="text-sm text-gray-600">{visit.calls.length} call(s) recorded</span>
                      </div>
                    )}
                    
                    {visit.transaction_id && (
                      <div className="mt-2">
                        <span className="font-semibold text-sm">Transaction ID: </span>
                        <span className="text-sm text-gray-600 font-mono">{visit.transaction_id}</span>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Export Tab */}
      {activeTab === "export" && (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold mb-4">Export EVV Data</h2>
          
          <Card>
            <CardHeader>
              <CardTitle>Export Individuals (Patients)</CardTitle>
              <CardDescription>
                Export patient records in Ohio Medicaid EVV Individual format
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button onClick={() => handleExport("individuals")} disabled={loading || !businessEntity}>
                <Download className="mr-2" size={16} />
                Export Individuals
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Export Direct Care Workers (Employees)</CardTitle>
              <CardDescription>
                Export employee records in Ohio Medicaid EVV DirectCareWorker format
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button onClick={() => handleExport("dcw")} disabled={loading || !businessEntity}>
                <Download className="mr-2" size={16} />
                Export Direct Care Workers
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Export Visits</CardTitle>
              <CardDescription>
                Export visit records in Ohio Medicaid EVV Visit format
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button onClick={() => handleExport("visits")} disabled={loading || !businessEntity}>
                <Download className="mr-2" size={16} />
                Export Visits
              </Button>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Submit Tab */}
      {activeTab === "submit" && (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold mb-4">Submit to Ohio EVV Aggregator</h2>
          
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
            <div className="flex items-start">
              <AlertCircle className="mr-2 text-yellow-600 mt-0.5" size={20} />
              <div>
                <h3 className="font-semibold text-yellow-800">Mock Submission Environment</h3>
                <p className="text-sm text-yellow-700 mt-1">
                  This is a mock EVV aggregator for testing. In production, this would submit to the actual
                  Ohio Department of Medicaid Sandata Aggregator API.
                </p>
              </div>
            </div>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Submit Individuals</CardTitle>
              <CardDescription>
                Submit all patient records to EVV aggregator
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button onClick={() => handleSubmit("individuals")} disabled={loading || !businessEntity}>
                <Upload className="mr-2" size={16} />
                Submit Individuals
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Submit Direct Care Workers</CardTitle>
              <CardDescription>
                Submit all employee records to EVV aggregator
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button onClick={() => handleSubmit("dcw")} disabled={loading || !businessEntity}>
                <Upload className="mr-2" size={16} />
                Submit Direct Care Workers
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Submit Visits</CardTitle>
              <CardDescription>
                Submit all draft and ready visits to EVV aggregator
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button onClick={() => handleSubmit("visits")} disabled={loading || !businessEntity}>
                <Upload className="mr-2" size={16} />
                Submit Visits
              </Button>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Transmissions Tab */}
      {activeTab === "transmissions" && (
        <div>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">Transmission History</h2>
            <Button onClick={loadTransmissions} disabled={loading}>
              {loading ? "Loading..." : "Refresh"}
            </Button>
          </div>

          {transmissions.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <p className="text-gray-500">No transmission history found.</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {transmissions.map((trans) => (
                <Card key={trans.id}>
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <div>
                        <CardTitle className="text-lg font-mono">{trans.transaction_id}</CardTitle>
                        <CardDescription className="mt-1">
                          {trans.record_type} - {trans.record_count} record(s)
                        </CardDescription>
                      </div>
                      {getStatusBadge(trans.status)}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="font-semibold">Submitted:</span>{" "}
                        {new Date(trans.transmission_datetime).toLocaleString()}
                      </div>
                      <div>
                        <span className="font-semibold">Business Entity:</span> {trans.business_entity_id}
                      </div>
                    </div>
                    
                    {trans.acknowledgement && (
                      <div className="mt-4 p-3 bg-gray-50 rounded border text-xs">
                        <pre className="whitespace-pre-wrap overflow-x-auto">
                          {typeof trans.acknowledgement === 'string' 
                            ? trans.acknowledgement 
                            : JSON.stringify(JSON.parse(trans.acknowledgement), null, 2)}
                        </pre>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Configuration Tab */}
      {activeTab === "config" && (
        <div className="space-y-6">
          <h2 className="text-xl font-semibold mb-4">EVV Configuration</h2>
          
          <Card>
            <CardHeader>
              <CardTitle>Business Entity Configuration</CardTitle>
              <CardDescription>
                Configure your agency's business entity for EVV submissions
              </CardDescription>
            </CardHeader>
            <CardContent>
              {businessEntity ? (
                <div className="space-y-3 text-sm">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <span className="font-semibold">Agency Name:</span>
                      <p className="text-gray-700">{businessEntity.agency_name}</p>
                    </div>
                    <div>
                      <span className="font-semibold">Business Entity ID:</span>
                      <p className="text-gray-700 font-mono">{businessEntity.business_entity_id}</p>
                    </div>
                    <div>
                      <span className="font-semibold">Medicaid Identifier:</span>
                      <p className="text-gray-700 font-mono">{businessEntity.business_entity_medicaid_id}</p>
                    </div>
                    <div>
                      <span className="font-semibold">Status:</span>
                      <p className="text-gray-700">{businessEntity.is_active ? "Active" : "Inactive"}</p>
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-gray-500">No business entity configured. Please contact administrator.</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Reference Data</CardTitle>
              <CardDescription>
                Valid Ohio Medicaid EVV payers, programs, and service codes
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <h4 className="font-semibold text-sm mb-2">Valid Payers</h4>
                  <div className="flex gap-2 flex-wrap">
                    {referenceData.payers.map((payer) => (
                      <span key={payer} className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-xs">
                        {payer}
                      </span>
                    ))}
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold text-sm mb-2">Procedure Codes</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                    {Object.entries(referenceData.procedureCodes).map(([code, description]) => (
                      <div key={code} className="p-2 bg-gray-50 rounded">
                        <span className="font-mono font-semibold">{code}</span> - {description}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
