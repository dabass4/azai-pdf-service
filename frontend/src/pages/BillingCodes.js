import { useState, useEffect } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { toast } from "sonner";
import { RefreshCw, Settings, Info, CheckCircle2, AlertCircle } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Pre-defined billing codes from Ohio Medicaid (extracted from RhinoBill)
const DEFAULT_BILLING_CODES = [
  // Therapy Services
  { code: "G0151", description: "Physical Therapy", category: "Therapy", enabled: true },
  { code: "G0152", description: "Occupational Therapy", category: "Therapy", enabled: true },
  { code: "G0153", description: "Speech Therapy", category: "Therapy", enabled: true },
  
  // Nursing Services - LPN/RN
  { code: "G0154", description: "LPN Services", category: "Nursing", modifier: "LPN", enabled: false },
  { code: "G0154", description: "RN Services", category: "Nursing", modifier: "RN", enabled: false },
  { code: "G0156", description: "Aide, Medicare Certified Agency", category: "Nursing", enabled: true },
  { code: "G0299", description: "RN Direct skilled nursing services", category: "Nursing", enabled: true },
  { code: "G0300", description: "LPN Direct skilled nursing services", category: "Nursing", enabled: true },
  
  // Waiver Nursing
  { code: "G0493", description: "Waiver Nursing Delegation/Assessment by a Registered Nurse", category: "Waiver Nursing", modifier: "Assessment", enabled: false },
  { code: "G0493", description: "Waiver Nursing Delegation/Consultation by a Registered Nurse", category: "Waiver Nursing", modifier: "Consultation", enabled: false },
  { code: "G0494", description: "Waiver Nursing Delegation/Consultation by a Licensed Practical Nurse", category: "Waiver Nursing", enabled: false },
  
  // Supplemental Services
  { code: "S0215", description: "Supplemental Transportation", category: "Supplemental", enabled: false },
  { code: "S5101", description: "Day Care Services per ½ day", category: "Day Care", enabled: false },
  { code: "S5102", description: "Day Care Services per full day", category: "Day Care", enabled: false },
  { code: "S5170", description: "Delivered meal services - therapeutic or kosher meal", category: "Meals", modifier: "Therapeutic", enabled: false },
  { code: "S5170", description: "Delivered Meals", category: "Meals", enabled: false },
  
  // PDN Services
  { code: "T1000", description: "PDN - LPN (Private Duty Nursing)", category: "PDN", modifier: "LPN", enabled: true },
  { code: "T1000", description: "PDN - RN (Private Duty Nursing)", category: "PDN", modifier: "RN", enabled: true },
  
  // Assessment & Consultation
  { code: "T1001", description: "RN Assessment", category: "Assessment", modifier: "Assessment", enabled: true },
  { code: "T1001", description: "RN Consultation", category: "Assessment", modifier: "Consultation", enabled: false },
  
  // Waiver Nursing T-Codes
  { code: "T1002", description: "RN Waiver Nursing", category: "Waiver Nursing", enabled: true },
  { code: "T1003", description: "LPN/LVN Waiver Nursing", category: "Waiver Nursing", modifier: "LPN/LVN", enabled: true },
  { code: "T1003", description: "Waiver Nursing LPN", category: "Waiver Nursing", modifier: "LPN", enabled: false },
  
  // Personal Care
  { code: "T1019", description: "Personal Care Aide", category: "Personal Care", enabled: true },
  { code: "T1020", description: "Personal Care Services", category: "Personal Care", enabled: true },
  { code: "T1021", description: "Home Health Aide per visit", category: "Personal Care", enabled: true },
  
  // Additional Common Codes
  { code: "S5125", description: "Attendant Care Services", category: "Personal Care", enabled: true },
  { code: "S5126", description: "Attendant Care Services - per 15 min", category: "Personal Care", enabled: true },
  { code: "S5130", description: "Homemaker Services", category: "Personal Care", enabled: false },
  { code: "S5131", description: "Homemaker Services - per 15 min", category: "Personal Care", enabled: false },
];

export default function BillingCodes() {
  const [billingCodes, setBillingCodes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [eraEnabled, setEraEnabled] = useState(true);
  const [usingOtherService, setUsingOtherService] = useState(false);
  const [filter, setFilter] = useState("all");
  const [hasChanges, setHasChanges] = useState(false);

  // Get unique categories for filtering
  const categories = ["all", ...new Set(DEFAULT_BILLING_CODES.map(c => c.category))];

  useEffect(() => {
    loadBillingCodes();
  }, []);

  const loadBillingCodes = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/billing-codes/config`);
      
      if (response.data && response.data.codes && response.data.codes.length > 0) {
        setBillingCodes(response.data.codes);
        setEraEnabled(response.data.era_enabled ?? true);
        setUsingOtherService(response.data.using_other_service ?? false);
      } else {
        // Use defaults if no saved config
        setBillingCodes(DEFAULT_BILLING_CODES);
      }
    } catch (error) {
      // Use defaults on error
      setBillingCodes(DEFAULT_BILLING_CODES);
      console.log("Using default billing codes");
    } finally {
      setLoading(false);
    }
  };

  const handleToggleCode = (index) => {
    const newCodes = [...billingCodes];
    newCodes[index] = { ...newCodes[index], enabled: !newCodes[index].enabled };
    setBillingCodes(newCodes);
    setHasChanges(true);
  };

  const handleEnableAll = () => {
    const newCodes = billingCodes.map(code => ({ ...code, enabled: true }));
    setBillingCodes(newCodes);
    setHasChanges(true);
  };

  const handleDisableAll = () => {
    const newCodes = billingCodes.map(code => ({ ...code, enabled: false }));
    setBillingCodes(newCodes);
    setHasChanges(true);
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      await axios.post(`${API}/billing-codes/config`, {
        codes: billingCodes,
        era_enabled: eraEnabled,
        using_other_service: usingOtherService
      });
      toast.success("Billing codes configuration saved!");
      setHasChanges(false);
    } catch (error) {
      toast.error("Failed to save billing codes configuration");
      console.error(error);
    } finally {
      setSaving(false);
    }
  };

  const filteredCodes = filter === "all" 
    ? billingCodes 
    : billingCodes.filter(code => code.category === filter);

  const enabledCount = billingCodes.filter(c => c.enabled).length;
  const totalCount = billingCodes.length;

  // Group codes by category for display
  const groupedCodes = filteredCodes.reduce((acc, code, originalIndex) => {
    // Find the original index in the full billingCodes array
    const actualIndex = billingCodes.findIndex(c => 
      c.code === code.code && 
      c.description === code.description && 
      c.modifier === code.modifier
    );
    
    if (!acc[code.category]) {
      acc[code.category] = [];
    }
    acc[code.category].push({ ...code, index: actualIndex });
    return acc;
  }, {});

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Billing Codes Configuration</h1>
        <p className="mt-2 text-gray-600">
          Enable or disable billing codes for Medicaid claims submission
        </p>
      </div>

      {/* Global Settings Card */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings size={20} />
            Global Settings
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between py-2 border-b">
            <div>
              <p className="font-medium">Enable ERAs via RhinoBill</p>
              <p className="text-sm text-gray-500">Receive Electronic Remittance Advice</p>
            </div>
            <Switch 
              checked={eraEnabled} 
              onCheckedChange={(checked) => {
                setEraEnabled(checked);
                setHasChanges(true);
              }}
            />
          </div>
          <div className="flex items-center justify-between py-2">
            <div>
              <p className="font-medium">Currently Using Another Billing Service?</p>
              <p className="text-sm text-gray-500">Toggle if using external billing</p>
            </div>
            <Switch 
              checked={usingOtherService} 
              onCheckedChange={(checked) => {
                setUsingOtherService(checked);
                setHasChanges(true);
              }}
            />
          </div>
        </CardContent>
      </Card>

      {/* Stats & Actions Bar */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-sm">
            <CheckCircle2 className="text-green-600" size={18} />
            <span><strong>{enabledCount}</strong> of {totalCount} codes enabled</span>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button onClick={loadBillingCodes} variant="outline" size="sm" disabled={loading}>
            <RefreshCw className={`mr-2 ${loading ? 'animate-spin' : ''}`} size={16} />
            Refresh
          </Button>
          <Button onClick={handleEnableAll} variant="outline" size="sm">
            Enable All
          </Button>
          <Button onClick={handleDisableAll} variant="outline" size="sm">
            Disable All
          </Button>
          <Button 
            onClick={handleSave} 
            disabled={saving || !hasChanges}
            className={hasChanges ? "bg-green-600 hover:bg-green-700" : ""}
          >
            {saving ? "Saving..." : hasChanges ? "Save Changes" : "Saved"}
          </Button>
        </div>
      </div>

      {/* Category Filter */}
      <div className="mb-6 flex flex-wrap gap-2">
        {categories.map(cat => (
          <Button
            key={cat}
            variant={filter === cat ? "default" : "outline"}
            size="sm"
            onClick={() => setFilter(cat)}
            className="capitalize"
          >
            {cat === "all" ? "All Categories" : cat}
          </Button>
        ))}
      </div>

      {/* Info Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 flex items-start gap-3">
        <Info className="text-blue-600 flex-shrink-0 mt-0.5" size={20} />
        <div className="text-sm text-blue-800">
          <p className="font-medium">Ohio Medicaid HCPCS Codes</p>
          <p className="mt-1">
            Toggle codes to enable/disable them for claims submission. Enabled codes will be available
            when creating claims and EVV submissions. Some codes have modifiers (LPN, RN, etc.) that
            differentiate the service type.
          </p>
        </div>
      </div>

      {/* Billing Codes List - Grouped by Category */}
      <div className="space-y-6">
        {Object.entries(groupedCodes).map(([category, codes]) => (
          <Card key={category}>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">{category}</CardTitle>
              <CardDescription>
                {codes.filter(c => c.enabled).length} of {codes.length} enabled
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="divide-y">
                {codes.map((code) => (
                  <div 
                    key={`${code.code}-${code.description}-${code.modifier || ''}`}
                    className={`flex items-center justify-between py-3 ${!code.enabled ? 'opacity-60' : ''}`}
                  >
                    <div className="flex items-center gap-3">
                      <Switch
                        checked={code.enabled}
                        onCheckedChange={() => handleToggleCode(code.index)}
                      />
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-mono font-semibold text-blue-700">{code.code}</span>
                          {code.modifier && (
                            <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                              {code.modifier}
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-600">{code.description}</p>
                      </div>
                    </div>
                    {code.enabled && (
                      <CheckCircle2 className="text-green-500 flex-shrink-0" size={20} />
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Floating Save Button for Mobile */}
      {hasChanges && (
        <div className="fixed bottom-6 right-6 sm:hidden">
          <Button 
            onClick={handleSave} 
            disabled={saving}
            size="lg"
            className="bg-green-600 hover:bg-green-700 shadow-lg"
          >
            {saving ? "Saving..." : "Save Changes"}
          </Button>
        </div>
      )}
    </div>
  );
}
