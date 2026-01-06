import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { Save, X, Plus, Trash2, AlertCircle, CheckCircle, Users, Link, Wand2, ChevronDown, Clock, FileText } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const convertTo24Hour = (time12h) => {
  if (!time12h) return "";
  if (time12h.match(/^\d{2}:\d{2}$/)) return time12h;
  const match = time12h.match(/^(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)?$/i);
  if (!match) return time12h;
  let hours = parseInt(match[1], 10);
  const minutes = match[2];
  const period = (match[3] || "").toUpperCase();
  if (period === "AM") { if (hours === 12) hours = 0; }
  else if (period === "PM") { if (hours !== 12) hours += 12; }
  return `${hours.toString().padStart(2, "0")}:${minutes}`;
};

const convertTo12Hour = (time24h) => {
  if (!time24h) return "";
  if (time24h.match(/AM|PM/i)) return time24h;
  const match = time24h.match(/^(\d{1,2}):(\d{2})$/);
  if (!match) return time24h;
  let hours = parseInt(match[1], 10);
  const minutes = match[2];
  const period = hours >= 12 ? "PM" : "AM";
  if (hours === 0) hours = 12;
  else if (hours > 12) hours -= 12;
  return `${hours.toString().padStart(2, "0")}:${minutes} ${period}`;
};

const formatDateForInput = (dateStr) => {
  if (!dateStr) return "";
  if (dateStr.match(/^\d{4}-\d{2}-\d{2}$/)) return dateStr;
  const match = dateStr.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
  if (match) {
    const month = match[1].padStart(2, "0");
    const day = match[2].padStart(2, "0");
    const year = match[3];
    return `${year}-${month}-${day}`;
  }
  return dateStr;
};

const DEFAULT_BILLING_CODES = [
  { code: "T1019", name: "Personal Care Aide" },
  { code: "T1020", name: "Personal Care (per diem)" },
  { code: "T1021", name: "Home Health Aide (per visit)" },
  { code: "G0156", name: "Home Health Aide" },
  { code: "G0299", name: "RN Direct Skilled Nursing" },
  { code: "G0300", name: "LPN Direct Skilled Nursing" },
  { code: "T1000", name: "Private Duty Nursing" },
  { code: "T1001", name: "Nursing Assessment" },
  { code: "S5125", name: "Attendant Care Services" },
];

const TimesheetEditor = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [timesheet, setTimesheet] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [similarEmployees, setSimilarEmployees] = useState({});
  const [loadingSimilar, setLoadingSimilar] = useState({});
  const [showSuggestions, setShowSuggestions] = useState({});
  const [showNameCorrection, setShowNameCorrection] = useState({});
  const [correctingName, setCorrectingName] = useState(null);
  const [employeeBillingCodes, setEmployeeBillingCodes] = useState({});
  const [showCodeDropdown, setShowCodeDropdown] = useState({});

  useEffect(() => {
    fetchTimesheet();
  }, [id]);

  const fetchTimesheet = async () => {
    try {
      const response = await axios.get(`${API}/timesheets/${id}`);
      setTimesheet(response.data);
      setLoading(false);
    } catch (e) {
      console.error("Error fetching timesheet:", e);
      toast.error("Failed to load timesheet");
      setLoading(false);
    }
  };

  const handleClientNameChange = (value) => {
    setTimesheet(prev => ({
      ...prev,
      extracted_data: { ...prev.extracted_data, client_name: value }
    }));
  };

  const handleEmployeeFieldChange = (empIndex, field, value) => {
    setTimesheet(prev => {
      const newEmployees = [...prev.extracted_data.employee_entries];
      newEmployees[empIndex] = { ...newEmployees[empIndex], [field]: value };
      return { ...prev, extracted_data: { ...prev.extracted_data, employee_entries: newEmployees } };
    });
    if (field === 'employee_name' && value && value.length >= 2) {
      fetchSimilarEmployees(empIndex, value);
      fetchEmployeeBillingCodes(empIndex, value);
    }
  };

  const fetchSimilarEmployees = async (empIndex, name) => {
    if (!name || name.length < 2) return;
    setLoadingSimilar(prev => ({ ...prev, [empIndex]: true }));
    try {
      const response = await axios.get(`${API}/employees/similar/${encodeURIComponent(name)}`);
      setSimilarEmployees(prev => ({ ...prev, [empIndex]: response.data }));
      if (response.data.similar_employees?.length > 0) {
        setShowSuggestions(prev => ({ ...prev, [empIndex]: true }));
      }
    } catch (e) {
      console.error("Error fetching similar employees:", e);
    } finally {
      setLoadingSimilar(prev => ({ ...prev, [empIndex]: false }));
    }
  };

  const fetchEmployeeBillingCodes = async (empIndex, name) => {
    if (!name || name.length < 2) return;
    try {
      const response = await axios.get(`${API}/employees/by-name/${encodeURIComponent(name)}/billing-codes`);
      setEmployeeBillingCodes(prev => ({ ...prev, [empIndex]: response.data }));
    } catch (e) {
      setEmployeeBillingCodes(prev => ({ ...prev, [empIndex]: { billing_codes: DEFAULT_BILLING_CODES.map(c => c.code), employee_found: false } }));
    }
  };

  const getAvailableBillingCodes = (empIndex) => {
    const empCodes = employeeBillingCodes[empIndex];
    if (empCodes?.billing_codes?.length > 0) {
      return empCodes.billing_codes.map(code => {
        const defaultCode = DEFAULT_BILLING_CODES.find(c => c.code === code);
        return { code, name: defaultCode?.name || code };
      });
    }
    return DEFAULT_BILLING_CODES;
  };

  const applySuggestedEmployee = (empIndex, employee) => {
    handleEmployeeFieldChange(empIndex, 'employee_name', employee.full_name);
    setShowSuggestions(prev => ({ ...prev, [empIndex]: false }));
    fetchEmployeeBillingCodes(empIndex, employee.full_name);
    toast.success(`Applied: ${employee.full_name}`);
  };

  const applyNameCorrectionToAll = async (empIndex, incorrectName, correctName) => {
    if (!correctName || correctName.trim() === '') {
      toast.error("Please enter the correct name");
      return;
    }
    setCorrectingName(empIndex);
    try {
      const response = await axios.post(`${API}/employees/name-corrections`, null, {
        params: { incorrect_name: incorrectName, correct_name: correctName.trim(), apply_to_all: true }
      });
      handleEmployeeFieldChange(empIndex, 'employee_name', correctName.trim());
      setShowNameCorrection(prev => ({ ...prev, [empIndex]: false }));
      toast.success(response.data.message);
    } catch (e) {
      toast.error("Failed to apply name correction");
    } finally {
      setCorrectingName(null);
    }
  };

  const handleTimeEntryChange = (empIndex, entryIndex, field, value) => {
    setTimesheet(prev => {
      const newEmployees = [...prev.extracted_data.employee_entries];
      const newTimeEntries = [...newEmployees[empIndex].time_entries];
      newTimeEntries[entryIndex] = { ...newTimeEntries[entryIndex], [field]: value };
      newEmployees[empIndex] = { ...newEmployees[empIndex], time_entries: newTimeEntries };
      return { ...prev, extracted_data: { ...prev.extracted_data, employee_entries: newEmployees } };
    });
  };

  const addTimeEntry = (empIndex) => {
    setTimesheet(prev => {
      const newEmployees = [...prev.extracted_data.employee_entries];
      newEmployees[empIndex] = {
        ...newEmployees[empIndex],
        time_entries: [...newEmployees[empIndex].time_entries, { date: "", time_in: "", time_out: "", hours_worked: "" }]
      };
      return { ...prev, extracted_data: { ...prev.extracted_data, employee_entries: newEmployees } };
    });
  };

  const removeTimeEntry = (empIndex, entryIndex) => {
    setTimesheet(prev => {
      const newEmployees = [...prev.extracted_data.employee_entries];
      const newTimeEntries = newEmployees[empIndex].time_entries.filter((_, idx) => idx !== entryIndex);
      newEmployees[empIndex] = { ...newEmployees[empIndex], time_entries: newTimeEntries };
      return { ...prev, extracted_data: { ...prev.extracted_data, employee_entries: newEmployees } };
    });
  };

  const addEmployee = () => {
    setTimesheet(prev => ({
      ...prev,
      extracted_data: {
        ...prev.extracted_data,
        employee_entries: [
          ...prev.extracted_data.employee_entries,
          { employee_name: "", service_code: "", signature: "No", time_entries: [{ date: "", time_in: "", time_out: "", hours_worked: "" }] }
        ]
      }
    }));
  };

  const removeEmployee = (empIndex) => {
    setTimesheet(prev => ({
      ...prev,
      extracted_data: {
        ...prev.extracted_data,
        employee_entries: prev.extracted_data.employee_entries.filter((_, idx) => idx !== empIndex)
      }
    }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/timesheets/${id}`, timesheet);
      toast.success("Timesheet updated successfully");
      navigate("/");
    } catch (e) {
      toast.error("Failed to save timesheet");
      setSaving(false);
    }
  };

  const handleResubmit = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/timesheets/${id}`, timesheet);
      const response = await axios.post(`${API}/timesheets/${id}/resubmit`);
      if (response.data.status === "success") {
        toast.success("Timesheet saved and resubmitted to Sandata");
        navigate("/");
      } else if (response.data.status === "blocked") {
        toast.error(`Submission blocked: ${response.data.message}`);
        setSaving(false);
      } else {
        toast.error(`Resubmission failed: ${response.data.message}`);
        setSaving(false);
      }
    } catch (e) {
      toast.error("Failed to resubmit timesheet");
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen healthcare-pattern flex items-center justify-center">
        <div className="glass-card p-8 rounded-2xl text-center">
          <div className="w-12 h-12 border-2 border-teal-400/30 border-t-teal-400 rounded-full animate-spin mx-auto"></div>
          <p className="mt-4 text-gray-400">Loading timesheet...</p>
        </div>
      </div>
    );
  }

  if (!timesheet) {
    return (
      <div className="min-h-screen healthcare-pattern flex items-center justify-center">
        <div className="glass-card p-8 rounded-2xl text-center">
          <FileText className="w-12 h-12 text-gray-600 mx-auto mb-4" />
          <p className="text-gray-400">Timesheet not found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen healthcare-pattern" data-testid="timesheet-editor">
      <div className="animated-bg"></div>
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8 animate-fade-in">
          <div className="flex items-center gap-4">
            <div className="icon-container">
              <FileText className="w-6 h-6 text-teal-400" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white" style={{ fontFamily: 'Manrope, sans-serif' }}>
                Edit Timesheet
              </h1>
              <p className="text-gray-400">Review and correct extracted data</p>
              <p className="text-sm text-gray-500 mt-1">File: {timesheet.filename}</p>
            </div>
          </div>
          <div className="flex gap-3">
            <button onClick={() => navigate("/")} className="btn-secondary flex items-center gap-2" data-testid="cancel-edit-btn">
              <X size={18} /> Cancel
            </button>
            <button onClick={handleSave} disabled={saving} className="btn-primary flex items-center gap-2" data-testid="save-timesheet-btn">
              <Save size={18} /> Save Changes
            </button>
            <button onClick={handleResubmit} disabled={saving} className="btn-primary flex items-center gap-2" style={{ background: 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)' }} data-testid="resubmit-timesheet-btn">
              <CheckCircle size={18} /> Save & Resubmit
            </button>
          </div>
        </div>

        {/* Alert */}
        <div className="glass-card rounded-2xl p-4 mb-6 border border-amber-500/30 bg-amber-500/5 animate-slide-up">
          <div className="flex items-start gap-3">
            <AlertCircle className="text-amber-400 mt-0.5" size={20} />
            <div>
              <p className="font-semibold text-amber-400">Manual Review Mode</p>
              <p className="text-sm text-amber-300/80">Review all extracted data carefully. Units are automatically calculated from time in/out (1 unit = 15 minutes).</p>
            </div>
          </div>
        </div>

        {/* Patient/Client Name */}
        <div className="glass-card rounded-2xl p-6 mb-6 animate-slide-up">
          <div className="flex items-center gap-3 mb-4">
            <div className="icon-container-sm">
              <Users className="w-5 h-5 text-teal-400" />
            </div>
            <h2 className="text-lg font-bold text-white">Patient/Client Information</h2>
          </div>
          <div>
            <Label className="text-gray-300">Patient/Client Name</Label>
            <Input
              value={timesheet.extracted_data?.client_name || ""}
              onChange={(e) => handleClientNameChange(e.target.value)}
              placeholder="Enter patient name"
              className="modern-input mt-1"
              data-testid="client-name-input"
            />
          </div>
        </div>

        {/* Employee Entries */}
        <div className="space-y-6">
          {timesheet.extracted_data?.employee_entries?.map((employee, empIndex) => (
            <div key={empIndex} className="glass-card rounded-2xl overflow-hidden animate-slide-up" data-testid={`employee-${empIndex}`}>
              <div className="p-6 border-b border-white/10 flex justify-between items-center">
                <h3 className="text-lg font-bold text-white">Employee {empIndex + 1}</h3>
                <button
                  onClick={() => removeEmployee(empIndex)}
                  className="p-2 rounded-lg hover:bg-red-500/20 text-gray-400 hover:text-red-400 transition-all"
                  data-testid={`remove-employee-${empIndex}`}
                >
                  <Trash2 size={18} />
                </button>
              </div>
              <div className="p-6 space-y-6">
                {/* Employee Details */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="relative">
                    <Label className="text-gray-300">Employee Name</Label>
                    <div className="flex gap-2 mt-1">
                      <Input
                        value={employee.employee_name || ""}
                        onChange={(e) => handleEmployeeFieldChange(empIndex, "employee_name", e.target.value)}
                        placeholder="Enter name"
                        className="modern-input flex-1"
                        data-testid={`employee-name-${empIndex}`}
                      />
                      <button
                        type="button"
                        onClick={() => fetchSimilarEmployees(empIndex, employee.employee_name)}
                        disabled={loadingSimilar[empIndex]}
                        className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-gray-400 hover:text-teal-400 transition-all"
                        title="Find similar employees"
                      >
                        <Users size={16} />
                      </button>
                      <button
                        type="button"
                        onClick={() => setShowNameCorrection(prev => ({ ...prev, [empIndex]: !prev[empIndex] }))}
                        className="p-2 rounded-lg bg-white/5 hover:bg-purple-500/20 text-gray-400 hover:text-purple-400 transition-all"
                        title="Apply name correction"
                      >
                        <Wand2 size={16} />
                      </button>
                    </div>
                    
                    {/* Name Correction Panel */}
                    {showNameCorrection[empIndex] && (
                      <div className="absolute z-20 w-80 mt-1 glass-card border border-purple-500/30 rounded-xl p-3">
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-sm font-semibold text-purple-400 flex items-center gap-1">
                            <Wand2 size={14} />
                            Apply to All Timesheets
                          </span>
                          <button onClick={() => setShowNameCorrection(prev => ({ ...prev, [empIndex]: false }))} className="text-gray-500 hover:text-gray-300">
                            <X size={14} />
                          </button>
                        </div>
                        <p className="text-xs text-gray-400 mb-2">Type the correct name. This will update ALL timesheets with this name.</p>
                        <div className="space-y-2">
                          <div>
                            <Label className="text-xs text-gray-500">Current (incorrect):</Label>
                            <Input value={employee.employee_name || ""} disabled className="modern-input mt-1 text-sm opacity-60" />
                          </div>
                          <div>
                            <Label className="text-xs text-gray-500">Correct name:</Label>
                            <Input id={`correct_name_${empIndex}`} placeholder="Enter correct name" className="modern-input mt-1 text-sm" />
                          </div>
                          <button
                            type="button"
                            className="w-full btn-primary text-sm py-2"
                            style={{ background: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)' }}
                            disabled={correctingName === empIndex}
                            onClick={() => {
                              const correctName = document.getElementById(`correct_name_${empIndex}`).value;
                              applyNameCorrectionToAll(empIndex, employee.employee_name, correctName);
                            }}
                          >
                            {correctingName === empIndex ? "Applying..." : "Apply to All Timesheets"}
                          </button>
                        </div>
                      </div>
                    )}
                    
                    {/* Similar Employee Suggestions */}
                    {showSuggestions[empIndex] && similarEmployees[empIndex]?.similar_employees?.length > 0 && (
                      <div className="absolute z-10 w-full mt-1 glass-card border border-white/10 rounded-xl max-h-60 overflow-y-auto">
                        <div className="p-2 border-b border-white/10 flex justify-between items-center">
                          <span className="text-xs font-semibold text-teal-400 flex items-center gap-1">
                            <Users size={12} />
                            Similar Employees ({similarEmployees[empIndex].similar_employees.length})
                          </span>
                          <button onClick={() => setShowSuggestions(prev => ({ ...prev, [empIndex]: false }))} className="text-gray-500 hover:text-gray-300">
                            <X size={14} />
                          </button>
                        </div>
                        {similarEmployees[empIndex].similar_employees.map((emp, idx) => (
                          <div
                            key={idx}
                            className="p-3 hover:bg-white/5 cursor-pointer border-b border-white/5 last:border-b-0 flex justify-between items-center"
                            onClick={() => applySuggestedEmployee(empIndex, emp)}
                          >
                            <div>
                              <p className="font-medium text-sm text-white">{emp.full_name}</p>
                              <p className="text-xs text-gray-500">
                                {emp.categories?.length > 0 ? emp.categories.join(", ") : "No category"} 
                                {emp.is_complete ? " • Complete" : " • Incomplete"}
                              </p>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className={`text-xs px-2 py-0.5 rounded ${
                                emp.similarity_score >= 0.95 ? 'bg-green-500/20 text-green-400' :
                                emp.similarity_score >= 0.85 ? 'bg-amber-500/20 text-amber-400' :
                                'bg-gray-500/20 text-gray-400'
                              }`}>
                                {Math.round(emp.similarity_score * 100)}% match
                              </span>
                              <Link size={14} className="text-teal-400" />
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  
                  <div className="relative">
                    <Label className="text-gray-300">Service Code</Label>
                    <div className="relative mt-1">
                      <button
                        type="button"
                        onClick={() => {
                          setShowCodeDropdown(prev => ({ ...prev, [empIndex]: !prev[empIndex] }));
                          if (!employeeBillingCodes[empIndex]) {
                            fetchEmployeeBillingCodes(empIndex, employee.employee_name);
                          }
                        }}
                        className="w-full modern-input text-left flex items-center justify-between"
                        data-testid={`service-code-${empIndex}`}
                      >
                        <span className={employee.service_code ? "text-white" : "text-gray-500"}>
                          {employee.service_code || "Select code..."}
                        </span>
                        <ChevronDown size={16} className="text-gray-400" />
                      </button>
                      
                      {showCodeDropdown[empIndex] && (
                        <div className="absolute z-30 w-full mt-1 glass-card border border-white/10 rounded-xl max-h-60 overflow-y-auto">
                          <div className="p-2 border-b border-white/10 text-xs text-teal-400 font-medium">
                            {employeeBillingCodes[empIndex]?.employee_found 
                              ? `Codes for ${employeeBillingCodes[empIndex]?.employee_name || 'employee'}`
                              : "Default billing codes"
                            }
                          </div>
                          {getAvailableBillingCodes(empIndex).map((bc) => (
                            <div
                              key={bc.code}
                              className={`px-3 py-2 cursor-pointer hover:bg-white/5 flex items-center justify-between ${
                                employee.service_code === bc.code ? 'bg-teal-500/20' : ''
                              }`}
                              onClick={() => {
                                handleEmployeeFieldChange(empIndex, "service_code", bc.code);
                                setShowCodeDropdown(prev => ({ ...prev, [empIndex]: false }));
                              }}
                            >
                              <div>
                                <span className="font-mono font-semibold text-teal-400">{bc.code}</span>
                                <span className="text-sm text-gray-400 ml-2">{bc.name}</span>
                              </div>
                              {employee.service_code === bc.code && (
                                <CheckCircle size={16} className="text-teal-400" />
                              )}
                            </div>
                          ))}
                          <div className="p-2 border-t border-white/10">
                            <Input
                              placeholder="Or enter custom code..."
                              className="modern-input text-sm"
                              onKeyDown={(e) => {
                                if (e.key === 'Enter' && e.target.value) {
                                  handleEmployeeFieldChange(empIndex, "service_code", e.target.value);
                                  setShowCodeDropdown(prev => ({ ...prev, [empIndex]: false }));
                                }
                              }}
                            />
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div>
                    <Label className="text-gray-300">Signature</Label>
                    <select
                      value={employee.signature || "No"}
                      onChange={(e) => handleEmployeeFieldChange(empIndex, "signature", e.target.value)}
                      className="w-full modern-input mt-1"
                      data-testid={`signature-${empIndex}`}
                    >
                      <option value="Yes">Yes</option>
                      <option value="No">No</option>
                    </select>
                  </div>
                </div>

                {/* Time Entries */}
                <div>
                  <div className="flex justify-between items-center mb-3">
                    <h4 className="text-sm font-semibold text-teal-400 uppercase flex items-center gap-2">
                      <Clock size={14} />
                      Time Entries
                    </h4>
                    <button
                      onClick={() => addTimeEntry(empIndex)}
                      className="btn-primary text-sm py-1.5"
                      style={{ background: 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)' }}
                      data-testid={`add-time-entry-${empIndex}`}
                    >
                      <Plus className="mr-1" size={16} />
                      Add Entry
                    </button>
                  </div>

                  <div className="space-y-3">
                    {employee.time_entries?.map((entry, entryIndex) => (
                      <div key={entryIndex} className="glass-card rounded-xl p-4" data-testid={`time-entry-${empIndex}-${entryIndex}`}>
                        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
                          <div>
                            <Label className="text-xs text-gray-500">Date</Label>
                            <Input
                              type="date"
                              value={formatDateForInput(entry.date) || ""}
                              onChange={(e) => handleTimeEntryChange(empIndex, entryIndex, "date", e.target.value)}
                              className="modern-input mt-1"
                              data-testid={`date-${empIndex}-${entryIndex}`}
                            />
                          </div>
                          <div>
                            <Label className="text-xs text-gray-500">Time In</Label>
                            <Input
                              type="time"
                              value={convertTo24Hour(entry.time_in) || ""}
                              onChange={(e) => handleTimeEntryChange(empIndex, entryIndex, "time_in", convertTo12Hour(e.target.value))}
                              className="modern-input mt-1"
                              data-testid={`time-in-${empIndex}-${entryIndex}`}
                            />
                          </div>
                          <div>
                            <Label className="text-xs text-gray-500">Time Out</Label>
                            <Input
                              type="time"
                              value={convertTo24Hour(entry.time_out) || ""}
                              onChange={(e) => handleTimeEntryChange(empIndex, entryIndex, "time_out", convertTo12Hour(e.target.value))}
                              className="modern-input mt-1"
                              data-testid={`time-out-${empIndex}-${entryIndex}`}
                            />
                          </div>
                          <div>
                            <Label className="text-xs text-gray-500">Hours</Label>
                            <Input
                              value={entry.formatted_hours || entry.hours_worked || ""}
                              onChange={(e) => handleTimeEntryChange(empIndex, entryIndex, "hours_worked", e.target.value)}
                              placeholder="8:30"
                              readOnly
                              className="modern-input mt-1 opacity-60"
                              data-testid={`hours-${empIndex}-${entryIndex}`}
                            />
                          </div>
                          <div className="flex items-end">
                            <button
                              onClick={() => removeTimeEntry(empIndex, entryIndex)}
                              className="p-2 rounded-lg hover:bg-red-500/20 text-gray-400 hover:text-red-400 transition-all"
                              data-testid={`remove-entry-${empIndex}-${entryIndex}`}
                            >
                              <Trash2 size={16} />
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ))}

          {/* Add Employee Button */}
          <button
            onClick={addEmployee}
            className="w-full btn-primary py-3"
            data-testid="add-employee-btn"
          >
            <Plus className="mr-2" size={18} />
            Add Another Employee
          </button>
        </div>

        {/* Action Buttons at Bottom */}
        <div className="flex justify-end gap-3 mt-8 pt-6 border-t border-white/10">
          <button onClick={() => navigate("/")} disabled={saving} className="btn-secondary">
            Cancel
          </button>
          <button onClick={handleSave} disabled={saving} className="btn-primary flex items-center gap-2">
            <Save size={18} />
            Save Changes
          </button>
          <button onClick={handleResubmit} disabled={saving} className="btn-primary flex items-center gap-2" style={{ background: 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)' }}>
            <CheckCircle size={18} />
            Save & Resubmit to Sandata
          </button>
        </div>
      </div>
    </div>
  );
};

export default TimesheetEditor;
