import { useState, useEffect } from "react";
import axios from "axios";
import { DollarSign, Plus, Edit, Trash2, X, ChevronDown, ChevronRight, MapPin, Phone, Globe, Building2, FileText, Calendar, CheckCircle, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const PAYER_TYPES = ["State", "Managed Care", "MyCare Ohio", "Medicare", "Private"];
const INSURANCE_TYPES = ["Medicaid", "Medicare", "Private", "Workers Comp", "Other"];

const COMMON_BILLING_CODES = [
  { code: "T1019", name: "Personal Care Aide" },
  { code: "T1020", name: "Personal Care (per diem)" },
  { code: "T1021", name: "Home Health Aide" },
  { code: "G0156", name: "Home Health Aide" },
  { code: "G0299", name: "RN Direct Skilled Nursing" },
  { code: "G0300", name: "LPN Direct Skilled Nursing" },
  { code: "T1000", name: "Private Duty Nursing" },
  { code: "T1001", name: "Nursing Assessment" },
  { code: "T1002", name: "RN Waiver Nursing" },
  { code: "T1003", name: "LPN Waiver Nursing" },
  { code: "G0151", name: "Physical Therapy" },
  { code: "G0152", name: "Occupational Therapy" },
  { code: "G0153", name: "Speech Therapy" },
];

const Payers = () => {
  const [payers, setPayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedPayers, setExpandedPayers] = useState({});
  
  const [showPayerForm, setShowPayerForm] = useState(false);
  const [editingPayer, setEditingPayer] = useState(null);
  const [payerFormData, setPayerFormData] = useState({
    name: "",
    short_name: "",
    payer_type: "",
    insurance_type: "",
    edi_payer_id: "",
    address: "",
    city: "",
    state: "",
    zip_code: "",
    phone: "",
    website: "",
    notes: "",
    is_active: true
  });
  
  const [showContractForm, setShowContractForm] = useState(false);
  const [editingContract, setEditingContract] = useState(null);
  const [contractPayerId, setContractPayerId] = useState(null);
  const [contractFormData, setContractFormData] = useState({
    contract_name: "",
    contract_number: "",
    start_date: "",
    end_date: "",
    contact_person: "",
    contact_phone: "",
    contact_email: "",
    notes: "",
    billable_services: [],
    is_active: true
  });

  useEffect(() => {
    fetchPayers();
  }, []);

  const fetchPayers = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/payers`);
      setPayers(response.data);
    } catch (e) {
      console.error("Error fetching payers:", e);
      toast.error("Failed to load payers");
    } finally {
      setLoading(false);
    }
  };

  const handleSeedOhioPayers = async () => {
    try {
      const response = await axios.post(`${API}/payers/seed-ohio`);
      toast.success(`Ohio payers added: ${response.data.added} new, ${response.data.skipped} already exist`);
      fetchPayers();
    } catch (e) {
      console.error("Error seeding payers:", e);
      toast.error("Failed to seed Ohio payers");
    }
  };

  const toggleExpanded = (payerId) => {
    setExpandedPayers(prev => ({ ...prev, [payerId]: !prev[payerId] }));
  };

  const handlePayerSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingPayer) {
        await axios.put(`${API}/payers/${editingPayer.id}`, payerFormData);
        toast.success("Payer updated");
      } else {
        await axios.post(`${API}/payers`, payerFormData);
        toast.success("Payer created");
      }
      setShowPayerForm(false);
      setEditingPayer(null);
      resetPayerForm();
      fetchPayers();
    } catch (e) {
      console.error("Error saving payer:", e);
      toast.error("Failed to save payer");
    }
  };

  const handleEditPayer = (payer) => {
    setEditingPayer(payer);
    setPayerFormData({
      name: payer.name || "",
      short_name: payer.short_name || "",
      payer_type: payer.payer_type || "",
      insurance_type: payer.insurance_type || "",
      edi_payer_id: payer.edi_payer_id || "",
      address: payer.address || "",
      city: payer.city || "",
      state: payer.state || "",
      zip_code: payer.zip_code || "",
      phone: payer.phone || "",
      website: payer.website || "",
      notes: payer.notes || "",
      is_active: payer.is_active !== false
    });
    setShowPayerForm(true);
  };

  const handleDeletePayer = async (payerId) => {
    if (!window.confirm("Delete this payer and ALL its contracts?")) return;
    try {
      await axios.delete(`${API}/payers/${payerId}`);
      toast.success("Payer deleted");
      fetchPayers();
    } catch (e) {
      toast.error("Failed to delete payer");
    }
  };

  const resetPayerForm = () => {
    setPayerFormData({
      name: "", short_name: "", payer_type: "", insurance_type: "",
      edi_payer_id: "", address: "", city: "", state: "", zip_code: "",
      phone: "", website: "", notes: "", is_active: true
    });
  };

  const handleContractSubmit = async (e) => {
    e.preventDefault();
    try {
      const payerIdToExpand = contractPayerId;
      
      if (editingContract) {
        await axios.put(`${API}/payers/${contractPayerId}/contracts/${editingContract.id}`, contractFormData);
        toast.success("Contract updated");
      } else {
        await axios.post(`${API}/payers/${contractPayerId}/contracts`, contractFormData);
        toast.success("Contract created successfully!");
      }
      setShowContractForm(false);
      setEditingContract(null);
      setContractPayerId(null);
      resetContractForm();
      
      await fetchPayers();
      setExpandedPayers(prev => ({ ...prev, [payerIdToExpand]: true }));
    } catch (e) {
      console.error("Error saving contract:", e);
      toast.error("Failed to save contract");
    }
  };

  const handleAddContract = (payerId) => {
    setContractPayerId(payerId);
    setEditingContract(null);
    resetContractForm();
    setShowContractForm(true);
  };

  const handleEditContract = (payerId, contract) => {
    setContractPayerId(payerId);
    setEditingContract(contract);
    setContractFormData({
      contract_name: contract.contract_name || "",
      contract_number: contract.contract_number || "",
      start_date: contract.start_date || "",
      end_date: contract.end_date || "",
      contact_person: contract.contact_person || "",
      contact_phone: contract.contact_phone || "",
      contact_email: contract.contact_email || "",
      notes: contract.notes || "",
      billable_services: contract.billable_services || [],
      is_active: contract.is_active !== false
    });
    setShowContractForm(true);
  };

  const handleDeleteContract = async (payerId, contractId) => {
    if (!window.confirm("Delete this contract?")) return;
    try {
      await axios.delete(`${API}/payers/${payerId}/contracts/${contractId}`);
      toast.success("Contract deleted");
      fetchPayers();
    } catch (e) {
      toast.error("Failed to delete contract");
    }
  };

  const resetContractForm = () => {
    setContractFormData({
      contract_name: "", contract_number: "", start_date: "", end_date: "",
      contact_person: "", contact_phone: "", contact_email: "",
      notes: "", billable_services: [], is_active: true
    });
  };

  const handleServiceToggle = (code) => {
    setContractFormData(prev => {
      const existing = prev.billable_services.find(s => s.service_code === code);
      if (existing) {
        return {
          ...prev,
          billable_services: prev.billable_services.filter(s => s.service_code !== code)
        };
      } else {
        return {
          ...prev,
          billable_services: [...prev.billable_services, { service_code: code, is_active: true }]
        };
      }
    });
  };

  const isServiceSelected = (code) => {
    return contractFormData.billable_services.some(s => s.service_code === code);
  };

  const groupedPayers = payers.reduce((acc, payer) => {
    const type = payer.payer_type || "Other";
    if (!acc[type]) acc[type] = [];
    acc[type].push(payer);
    return acc;
  }, {});

  const getTypeColor = (type) => {
    const colors = {
      'State': 'bg-purple-500',
      'Managed Care': 'bg-blue-500',
      'MyCare Ohio': 'bg-green-500',
      'Medicare': 'bg-teal-500',
      'Private': 'bg-orange-500'
    };
    return colors[type] || 'bg-gray-500';
  };

  return (
    <div className="min-h-screen healthcare-pattern" data-testid="payers-page">
      <div className="animated-bg"></div>
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8 animate-fade-in">
          <div className="flex items-center gap-4">
            <div className="icon-container">
              <DollarSign className="w-6 h-6 text-teal-400" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white" style={{ fontFamily: 'Manrope, sans-serif' }}>
                Payers & Contracts
              </h1>
              <p className="text-gray-400">Manage payers and their time-bound contracts</p>
            </div>
          </div>
          <div className="flex gap-3">
            <button onClick={handleSeedOhioPayers} className="btn-secondary flex items-center gap-2">
              <MapPin size={18} />
              Load Ohio Payers
            </button>
            <button onClick={() => { setShowPayerForm(true); setEditingPayer(null); resetPayerForm(); }} className="btn-primary flex items-center gap-2">
              <Plus size={18} />
              Add Payer
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8 stagger-children">
          <div className="stat-card card-lift">
            <div className="flex items-center justify-between mb-3">
              <div className="icon-container-sm">
                <Building2 className="w-5 h-5 text-teal-400" />
              </div>
              <span className="text-xs text-gray-500 uppercase">Total</span>
            </div>
            <p className="text-3xl font-bold text-white">{payers.length}</p>
            <p className="text-sm text-gray-400">Payers</p>
          </div>
          <div className="stat-card card-lift">
            <div className="flex items-center justify-between mb-3">
              <div className="icon-container-sm">
                <CheckCircle className="w-5 h-5 text-green-400" />
              </div>
              <span className="text-xs text-gray-500 uppercase">Active</span>
            </div>
            <p className="text-3xl font-bold text-white">{payers.filter(p => p.is_active).length}</p>
            <p className="text-sm text-gray-400">Payers</p>
          </div>
          <div className="stat-card card-lift">
            <div className="flex items-center justify-between mb-3">
              <div className="icon-container-sm">
                <FileText className="w-5 h-5 text-purple-400" />
              </div>
              <span className="text-xs text-gray-500 uppercase">Total</span>
            </div>
            <p className="text-3xl font-bold text-white">{payers.reduce((sum, p) => sum + (p.contracts?.length || 0), 0)}</p>
            <p className="text-sm text-gray-400">Contracts</p>
          </div>
          <div className="stat-card card-lift">
            <div className="flex items-center justify-between mb-3">
              <div className="icon-container-sm">
                <DollarSign className="w-5 h-5 text-amber-400" />
              </div>
              <span className="text-xs text-gray-500 uppercase">Types</span>
            </div>
            <p className="text-3xl font-bold text-white">{Object.keys(groupedPayers).length}</p>
            <p className="text-sm text-gray-400">Categories</p>
          </div>
        </div>

        {/* Payer Form Modal */}
        {showPayerForm && (
          <div className="mb-8 glass-card rounded-2xl overflow-hidden animate-slide-up">
            <div className="p-6 border-b border-white/10 flex justify-between items-center">
              <h2 className="text-xl font-bold text-white">{editingPayer ? "Edit Payer" : "Add New Payer"}</h2>
              <button onClick={() => { setShowPayerForm(false); setEditingPayer(null); }} className="p-2 rounded-lg hover:bg-white/10 text-gray-400">
                <X size={20} />
              </button>
            </div>
            <div className="p-6">
              <form onSubmit={handlePayerSubmit} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="md:col-span-2">
                    <Label className="text-gray-300">Payer Name *</Label>
                    <Input value={payerFormData.name} onChange={(e) => setPayerFormData({...payerFormData, name: e.target.value})} required className="modern-input mt-1" />
                  </div>
                  <div>
                    <Label className="text-gray-300">Short Name</Label>
                    <Input value={payerFormData.short_name} onChange={(e) => setPayerFormData({...payerFormData, short_name: e.target.value})} placeholder="e.g., ODM" className="modern-input mt-1" />
                  </div>
                  <div>
                    <Label className="text-gray-300">Payer Type *</Label>
                    <Select value={payerFormData.payer_type} onValueChange={(v) => setPayerFormData({...payerFormData, payer_type: v})}>
                      <SelectTrigger className="modern-input mt-1"><SelectValue placeholder="Select type" /></SelectTrigger>
                      <SelectContent>
                        {PAYER_TYPES.map(t => <SelectItem key={t} value={t}>{t}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label className="text-gray-300">Insurance Type *</Label>
                    <Select value={payerFormData.insurance_type} onValueChange={(v) => setPayerFormData({...payerFormData, insurance_type: v})}>
                      <SelectTrigger className="modern-input mt-1"><SelectValue placeholder="Select type" /></SelectTrigger>
                      <SelectContent>
                        {INSURANCE_TYPES.map(t => <SelectItem key={t} value={t}>{t}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label className="text-gray-300">EDI Payer ID</Label>
                    <Input value={payerFormData.edi_payer_id} onChange={(e) => setPayerFormData({...payerFormData, edi_payer_id: e.target.value})} placeholder="e.g., 35374" className="modern-input mt-1" />
                  </div>
                </div>
                
                <div className="border-t border-white/10 pt-4">
                  <h4 className="font-semibold text-teal-400 text-sm uppercase mb-3 flex items-center gap-2"><MapPin size={16} /> Claims Mailing Address</h4>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="md:col-span-2">
                      <Label className="text-gray-300">Address / P.O. Box</Label>
                      <Input value={payerFormData.address} onChange={(e) => setPayerFormData({...payerFormData, address: e.target.value})} className="modern-input mt-1" />
                    </div>
                    <div>
                      <Label className="text-gray-300">City</Label>
                      <Input value={payerFormData.city} onChange={(e) => setPayerFormData({...payerFormData, city: e.target.value})} className="modern-input mt-1" />
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <Label className="text-gray-300">State</Label>
                        <Input value={payerFormData.state} onChange={(e) => setPayerFormData({...payerFormData, state: e.target.value})} className="modern-input mt-1" />
                      </div>
                      <div>
                        <Label className="text-gray-300">ZIP</Label>
                        <Input value={payerFormData.zip_code} onChange={(e) => setPayerFormData({...payerFormData, zip_code: e.target.value})} className="modern-input mt-1" />
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label className="text-gray-300">Phone</Label>
                    <Input value={payerFormData.phone} onChange={(e) => setPayerFormData({...payerFormData, phone: e.target.value})} placeholder="1-800-XXX-XXXX" className="modern-input mt-1" />
                  </div>
                  <div>
                    <Label className="text-gray-300">Website</Label>
                    <Input value={payerFormData.website} onChange={(e) => setPayerFormData({...payerFormData, website: e.target.value})} placeholder="example.com" className="modern-input mt-1" />
                  </div>
                </div>
                
                <div>
                  <Label className="text-gray-300">Notes</Label>
                  <Input value={payerFormData.notes} onChange={(e) => setPayerFormData({...payerFormData, notes: e.target.value})} placeholder="Disputes address, special instructions..." className="modern-input mt-1" />
                </div>
                
                <div className="flex items-center gap-2">
                  <Switch checked={payerFormData.is_active} onCheckedChange={(c) => setPayerFormData({...payerFormData, is_active: c})} />
                  <Label className="text-gray-300">Payer Active</Label>
                </div>
                
                <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
                  <button type="button" onClick={() => { setShowPayerForm(false); setEditingPayer(null); }} className="btn-secondary">Cancel</button>
                  <button type="submit" className="btn-primary">{editingPayer ? "Update Payer" : "Create Payer"}</button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Contract Form Modal */}
        {showContractForm && (
          <div className="mb-8 glass-card rounded-2xl overflow-hidden animate-slide-up">
            <div className="p-6 border-b border-white/10 flex justify-between items-center">
              <h2 className="text-xl font-bold text-white">{editingContract ? "Edit Contract" : "Add New Contract"}</h2>
              <button onClick={() => { setShowContractForm(false); setEditingContract(null); }} className="p-2 rounded-lg hover:bg-white/10 text-gray-400">
                <X size={20} />
              </button>
            </div>
            <div className="p-6">
              <form onSubmit={handleContractSubmit} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label className="text-gray-300">Contract Name</Label>
                    <Input value={contractFormData.contract_name} onChange={(e) => setContractFormData({...contractFormData, contract_name: e.target.value})} placeholder="e.g., 2025 Rate Agreement" className="modern-input mt-1" />
                  </div>
                  <div>
                    <Label className="text-gray-300">Contract Number</Label>
                    <Input value={contractFormData.contract_number} onChange={(e) => setContractFormData({...contractFormData, contract_number: e.target.value})} className="modern-input mt-1" />
                  </div>
                  <div>
                    <Label className="text-gray-300">Start Date *</Label>
                    <Input type="date" value={contractFormData.start_date} onChange={(e) => setContractFormData({...contractFormData, start_date: e.target.value})} required className="modern-input mt-1" />
                  </div>
                  <div>
                    <Label className="text-gray-300">End Date</Label>
                    <Input type="date" value={contractFormData.end_date} onChange={(e) => setContractFormData({...contractFormData, end_date: e.target.value})} className="modern-input mt-1" />
                  </div>
                </div>
                
                <div className="border-t border-white/10 pt-4">
                  <h4 className="font-semibold text-teal-400 text-sm uppercase mb-3">Your Contact (Internal)</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <Label className="text-gray-300">Contact Person</Label>
                      <Input value={contractFormData.contact_person} onChange={(e) => setContractFormData({...contractFormData, contact_person: e.target.value})} className="modern-input mt-1" />
                    </div>
                    <div>
                      <Label className="text-gray-300">Phone</Label>
                      <Input value={contractFormData.contact_phone} onChange={(e) => setContractFormData({...contractFormData, contact_phone: e.target.value})} className="modern-input mt-1" />
                    </div>
                    <div>
                      <Label className="text-gray-300">Email</Label>
                      <Input type="email" value={contractFormData.contact_email} onChange={(e) => setContractFormData({...contractFormData, contact_email: e.target.value})} className="modern-input mt-1" />
                    </div>
                  </div>
                </div>
                
                <div className="border-t border-white/10 pt-4">
                  <h4 className="font-semibold text-teal-400 text-sm uppercase mb-3">Billable Services ({contractFormData.billable_services.length} selected)</h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2 max-h-48 overflow-y-auto p-2 glass-card rounded-xl">
                    {COMMON_BILLING_CODES.map(bc => (
                      <label key={bc.code} className={`flex items-center p-2 rounded-lg cursor-pointer text-sm transition-all ${isServiceSelected(bc.code) ? 'bg-teal-500/20 border border-teal-500/30' : 'bg-white/5 border border-white/10'}`}>
                        <input type="checkbox" checked={isServiceSelected(bc.code)} onChange={() => handleServiceToggle(bc.code)} className="mr-2" />
                        <span className="font-mono text-teal-400 font-semibold">{bc.code}</span>
                      </label>
                    ))}
                  </div>
                </div>
                
                <div>
                  <Label className="text-gray-300">Notes</Label>
                  <Input value={contractFormData.notes} onChange={(e) => setContractFormData({...contractFormData, notes: e.target.value})} placeholder="Contract-specific notes..." className="modern-input mt-1" />
                </div>
                
                <div className="flex items-center gap-2">
                  <Switch checked={contractFormData.is_active} onCheckedChange={(c) => setContractFormData({...contractFormData, is_active: c})} />
                  <Label className="text-gray-300">Contract Active</Label>
                </div>
                
                <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
                  <button type="button" onClick={() => { setShowContractForm(false); setEditingContract(null); }} className="btn-secondary">Cancel</button>
                  <button type="submit" className="btn-primary">{editingContract ? "Update Contract" : "Create Contract"}</button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Payers List */}
        {loading ? (
          <div className="glass-card rounded-2xl p-12 text-center">
            <div className="w-12 h-12 border-2 border-teal-400/30 border-t-teal-400 rounded-full animate-spin mx-auto"></div>
            <p className="mt-4 text-gray-400">Loading payers...</p>
          </div>
        ) : payers.length === 0 ? (
          <div className="glass-card rounded-2xl p-12 text-center">
            <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-white/5 flex items-center justify-center">
              <Building2 className="w-10 h-10 text-gray-600" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">No Payers Yet</h3>
            <p className="text-gray-400 mb-4">Add your first payer or load Ohio Medicaid payers</p>
            <button onClick={handleSeedOhioPayers} className="btn-secondary">
              <MapPin className="mr-2" size={18} />
              Load Ohio Payers
            </button>
          </div>
        ) : (
          <div className="space-y-6">
            {Object.entries(groupedPayers).map(([type, payerList]) => (
              <div key={type} className="animate-fade-in">
                <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <span className={`w-3 h-3 rounded-full ${getTypeColor(type)}`}></span>
                  {type} <span className="text-gray-500 font-normal">({payerList.length})</span>
                </h2>
                <div className="space-y-3">
                  {payerList.map(payer => (
                    <div key={payer.id} className="glass-card rounded-xl overflow-hidden">
                      {/* Payer Header */}
                      <div 
                        className="p-4 cursor-pointer hover:bg-white/5 flex items-center justify-between transition-all"
                        onClick={() => toggleExpanded(payer.id)}
                      >
                        <div className="flex items-center gap-4 flex-1">
                          {expandedPayers[payer.id] ? <ChevronDown size={20} className="text-gray-400" /> : <ChevronRight size={20} className="text-gray-400" />}
                          <div>
                            <div className="flex items-center gap-2">
                              <h3 className="font-bold text-lg text-white">{payer.name}</h3>
                              {payer.short_name && <span className="text-sm text-gray-500">({payer.short_name})</span>}
                              <span className={`status-badge ${payer.is_active ? 'status-completed' : 'bg-gray-500/20 text-gray-400 border-gray-500/30'}`}>
                                {payer.is_active ? 'Active' : 'Inactive'}
                              </span>
                            </div>
                            <div className="flex items-center gap-4 text-sm text-gray-400 mt-1">
                              {payer.phone && (
                                <span className="flex items-center gap-1">
                                  <Phone size={14} />
                                  <a href={`tel:${payer.phone}`} className="text-teal-400 hover:underline" onClick={e => e.stopPropagation()}>{payer.phone}</a>
                                </span>
                              )}
                              {payer.edi_payer_id && <span className="font-mono">ID: {payer.edi_payer_id}</span>}
                              {payer.address && (
                                <span className="flex items-center gap-1 text-xs">
                                  <MapPin size={12} />
                                  {payer.address}, {payer.city}, {payer.state} {payer.zip_code}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2" onClick={e => e.stopPropagation()}>
                          <button onClick={() => handleAddContract(payer.id)} className="btn-primary text-sm py-2">
                            <Plus size={14} className="mr-1" /> Add Contract
                          </button>
                          <span className="text-sm text-gray-500 mx-2">{payer.contracts?.length || 0} contract(s)</span>
                          <button onClick={() => handleEditPayer(payer)} className="p-2 rounded-lg hover:bg-white/10 text-gray-400 hover:text-teal-400 transition-all">
                            <Edit size={16} />
                          </button>
                          <button onClick={() => handleDeletePayer(payer.id)} className="p-2 rounded-lg hover:bg-white/10 text-gray-400 hover:text-red-400 transition-all">
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </div>
                      
                      {/* Expanded: Contracts */}
                      {expandedPayers[payer.id] && (
                        <div className="border-t border-white/10 p-4 bg-white/5">
                          {payer.notes && (
                            <p className="text-sm text-amber-400/80 mb-4 p-2 bg-amber-500/10 rounded-lg border border-amber-500/20">{payer.notes}</p>
                          )}
                          
                          <div className="flex justify-between items-center mb-3">
                            <h4 className="font-semibold text-gray-300">Contracts</h4>
                            <button onClick={() => handleAddContract(payer.id)} className="btn-primary text-sm py-1.5">
                              <Plus size={16} className="mr-1" /> Add Contract
                            </button>
                          </div>
                          
                          {(!payer.contracts || payer.contracts.length === 0) ? (
                            <p className="text-sm text-gray-500 italic">No contracts yet. Click "Add Contract" to create one.</p>
                          ) : (
                            <div className="space-y-2">
                              {payer.contracts.map(contract => (
                                <div key={contract.id} className="glass-card-hover rounded-lg p-3 flex justify-between items-center">
                                  <div>
                                    <div className="flex items-center gap-2">
                                      <FileText size={16} className="text-teal-400" />
                                      <span className="font-semibold text-white">{contract.contract_name || contract.contract_number || "Unnamed Contract"}</span>
                                      <span className={`status-badge ${contract.is_active ? 'status-completed' : 'bg-gray-500/20 text-gray-400 border-gray-500/30'}`}>
                                        {contract.is_active ? 'Active' : 'Inactive'}
                                      </span>
                                    </div>
                                    <div className="text-sm text-gray-400 flex items-center gap-4 mt-1">
                                      <span className="flex items-center gap-1">
                                        <Calendar size={14} />
                                        {contract.start_date} - {contract.end_date || "Ongoing"}
                                      </span>
                                      <span>{contract.billable_services?.length || 0} services</span>
                                    </div>
                                  </div>
                                  <div className="flex gap-1">
                                    <button onClick={() => handleEditContract(payer.id, contract)} className="p-2 rounded-lg hover:bg-white/10 text-gray-400 hover:text-teal-400 transition-all">
                                      <Edit size={14} />
                                    </button>
                                    <button onClick={() => handleDeleteContract(payer.id, contract.id)} className="p-2 rounded-lg hover:bg-white/10 text-gray-400 hover:text-red-400 transition-all">
                                      <Trash2 size={14} />
                                    </button>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Payers;
