import { useState, useEffect } from "react";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";
import { Plus, Edit2, Trash2, CheckCircle, XCircle, RefreshCw } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function ServiceCodes() {
  const [serviceCodes, setServiceCodes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingCode, setEditingCode] = useState(null);
  const [formData, setFormData] = useState({
    service_name: "",
    service_code_internal: "",
    payer: "ODM",
    payer_program: "SP",
    procedure_code: "",
    modifier1: "",
    modifier2: "",
    service_description: "",
    service_category: "Personal Care",
    effective_start_date: new Date().toISOString().split('T')[0],
    is_active: true,
    notes: ""
  });

  const payers = ["ODM", "ODA"];
  const payerPrograms = {
    ODM: ["SP", "OHCW", "MYCARE"],
    ODA: ["PASSPORT", "ASSISTED_LIVING", "HOME_FIRST"]
  };
  const serviceCategories = [
    "Personal Care",
    "Nursing",
    "Therapy",
    "Assessment",
    "Other"
  ];

  useEffect(() => {
    loadServiceCodes();
  }, []);

  const loadServiceCodes = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/service-codes`);
      setServiceCodes(response.data);
    } catch (error) {
      toast.error("Failed to load service codes");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      setLoading(true);
      
      if (editingCode) {
        // Update existing
        await axios.put(`${API}/service-codes/${editingCode.id}`, formData);
        toast.success("Service code updated successfully");
      } else {
        // Create new
        await axios.post(`${API}/service-codes`, formData);
        toast.success("Service code created successfully");
      }
      
      // Reset form and reload
      setShowAddForm(false);
      setEditingCode(null);
      setFormData({
        service_name: "",
        service_code_internal: "",
        payer: "ODM",
        payer_program: "SP",
        procedure_code: "",
        modifier1: "",
        modifier2: "",
        service_description: "",
        service_category: "Personal Care",
        effective_start_date: new Date().toISOString().split('T')[0],
        is_active: true,
        notes: ""
      });
      
      await loadServiceCodes();
    } catch (error) {
      toast.error(editingCode ? "Failed to update service code" : "Failed to create service code");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (code) => {
    setEditingCode(code);
    setFormData({
      service_name: code.service_name,
      service_code_internal: code.service_code_internal,
      payer: code.payer,
      payer_program: code.payer_program,
      procedure_code: code.procedure_code,
      modifier1: code.modifier1 || "",
      modifier2: code.modifier2 || "",
      service_description: code.service_description,
      service_category: code.service_category,
      effective_start_date: code.effective_start_date,
      is_active: code.is_active,
      notes: code.notes || ""
    });
    setShowAddForm(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this service code?")) {
      return;
    }
    
    try {
      await axios.delete(`${API}/service-codes/${id}`);
      toast.success("Service code deleted successfully");
      await loadServiceCodes();
    } catch (error) {
      toast.error("Failed to delete service code");
      console.error(error);
    }
  };

  const handleCancel = () => {
    setShowAddForm(false);
    setEditingCode(null);
    setFormData({
      service_name: "",
      service_code_internal: "",
      payer: "ODM",
      payer_program: "SP",
      procedure_code: "",
      modifier1: "",
      modifier2: "",
      service_description: "",
      service_category: "Personal Care",
      effective_start_date: new Date().toISOString().split('T')[0],
      is_active: true,
      notes: ""
    });
  };

  const groupedCodes = serviceCodes.reduce((acc, code) => {
    const key = `${code.payer} - ${code.payer_program}`;
    if (!acc[key]) {
      acc[key] = [];
    }
    acc[key].push(code);
    return acc;
  }, {});

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Service Code Management</h1>
          <p className="mt-2 text-sm text-gray-600">
            Manage valid service codes for Sandata EVV submission
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={loadServiceCodes} variant="outline" disabled={loading}>
            <RefreshCw className="mr-2" size={16} />
            Refresh
          </Button>
          <Button 
            onClick={() => setShowAddForm(!showAddForm)}
            disabled={loading}
          >
            <Plus className="mr-2" size={16} />
            Add Service Code
          </Button>
        </div>
      </div>

      {/* Add/Edit Form */}
      {showAddForm && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>{editingCode ? "Edit Service Code" : "Add New Service Code"}</CardTitle>
            <CardDescription>
              Enter the service code details. The Payer, Payer Program, and Procedure Code combination must be unique.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Service Name *
                  </label>
                  <input
                    type="text"
                    value={formData.service_name}
                    onChange={(e) => setFormData({...formData, service_name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    required
                    placeholder="e.g., Home Health Aide - State Plan"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Internal Code *
                  </label>
                  <input
                    type="text"
                    value={formData.service_code_internal}
                    onChange={(e) => setFormData({...formData, service_code_internal: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    required
                    placeholder="e.g., HHA_SP"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Payer *
                  </label>
                  <select
                    value={formData.payer}
                    onChange={(e) => setFormData({...formData, payer: e.target.value, payer_program: payerPrograms[e.target.value][0]})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    required
                  >
                    {payers.map(p => (
                      <option key={p} value={p}>{p}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Payer Program *
                  </label>
                  <select
                    value={formData.payer_program}
                    onChange={(e) => setFormData({...formData, payer_program: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    required
                  >
                    {payerPrograms[formData.payer].map(pp => (
                      <option key={pp} value={pp}>{pp}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Procedure Code (HCPCS) *
                  </label>
                  <input
                    type="text"
                    value={formData.procedure_code}
                    onChange={(e) => setFormData({...formData, procedure_code: e.target.value.toUpperCase()})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    required
                    placeholder="e.g., G0156, T1019"
                    maxLength="5"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Service Category *
                  </label>
                  <select
                    value={formData.service_category}
                    onChange={(e) => setFormData({...formData, service_category: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    required
                  >
                    {serviceCategories.map(cat => (
                      <option key={cat} value={cat}>{cat}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Modifier 1
                  </label>
                  <input
                    type="text"
                    value={formData.modifier1}
                    onChange={(e) => setFormData({...formData, modifier1: e.target.value.toUpperCase()})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    maxLength="4"
                    placeholder="Optional"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Modifier 2
                  </label>
                  <input
                    type="text"
                    value={formData.modifier2}
                    onChange={(e) => setFormData({...formData, modifier2: e.target.value.toUpperCase()})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    maxLength="4"
                    placeholder="Optional"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Effective Start Date *
                  </label>
                  <input
                    type="date"
                    value={formData.effective_start_date}
                    onChange={(e) => setFormData({...formData, effective_start_date: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    required
                  />
                </div>

                <div className="flex items-center">
                  <label className="flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.is_active}
                      onChange={(e) => setFormData({...formData, is_active: e.target.checked})}
                      className="mr-2"
                    />
                    <span className="text-sm font-medium text-gray-700">Active</span>
                  </label>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Service Description *
                </label>
                <textarea
                  value={formData.service_description}
                  onChange={(e) => setFormData({...formData, service_description: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  rows="2"
                  required
                  placeholder="Full description of the service"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Notes
                </label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({...formData, notes: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                  rows="2"
                  placeholder="Additional notes or comments"
                />
              </div>

              <div className="flex gap-2">
                <Button type="submit" disabled={loading}>
                  {editingCode ? "Update" : "Create"} Service Code
                </Button>
                <Button type="button" onClick={handleCancel} variant="outline" disabled={loading}>
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Service Codes List */}
      <div className="space-y-6">
        {Object.entries(groupedCodes).map(([groupKey, codes]) => (
          <div key={groupKey}>
            <h2 className="text-xl font-semibold text-gray-900 mb-3">{groupKey}</h2>
            <div className="grid gap-4">
              {codes.map((code) => (
                <Card key={code.id} className={!code.is_active ? "opacity-60" : ""}>
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <div>
                        <CardTitle className="text-lg flex items-center gap-2">
                          {code.service_name}
                          {code.is_active ? (
                            <CheckCircle className="text-green-600" size={20} />
                          ) : (
                            <XCircle className="text-gray-400" size={20} />
                          )}
                        </CardTitle>
                        <CardDescription className="mt-1">
                          {code.service_description}
                        </CardDescription>
                      </div>
                      <div className="flex gap-2">
                        <Button
                          onClick={() => handleEdit(code)}
                          variant="outline"
                          size="sm"
                        >
                          <Edit2 size={16} />
                        </Button>
                        <Button
                          onClick={() => handleDelete(code.id)}
                          variant="outline"
                          size="sm"
                        >
                          <Trash2 size={16} />
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="font-semibold">Internal Code:</span>
                        <p className="text-gray-700 font-mono">{code.service_code_internal}</p>
                      </div>
                      <div>
                        <span className="font-semibold">Procedure Code:</span>
                        <p className="text-gray-700 font-mono">{code.procedure_code}</p>
                      </div>
                      <div>
                        <span className="font-semibold">Category:</span>
                        <p className="text-gray-700">{code.service_category}</p>
                      </div>
                      <div>
                        <span className="font-semibold">Effective Date:</span>
                        <p className="text-gray-700">{code.effective_start_date}</p>
                      </div>
                      {(code.modifier1 || code.modifier2) && (
                        <div>
                          <span className="font-semibold">Modifiers:</span>
                          <p className="text-gray-700 font-mono">
                            {[code.modifier1, code.modifier2].filter(Boolean).join(", ")}
                          </p>
                        </div>
                      )}
                    </div>
                    {code.notes && (
                      <div className="mt-3 pt-3 border-t text-sm">
                        <span className="font-semibold">Notes: </span>
                        <span className="text-gray-700">{code.notes}</span>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        ))}

        {serviceCodes.length === 0 && !loading && (
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-gray-500">No service codes found. Click "Add Service Code" to create one.</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
