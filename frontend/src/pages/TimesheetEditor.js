import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { Save, X, Plus, Trash2, AlertCircle, CheckCircle, Users, Link, Wand2, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Default billing codes if employee has none assigned
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
  
  // Similar employee suggestions state
  const [similarEmployees, setSimilarEmployees] = useState({});
  const [loadingSimilar, setLoadingSimilar] = useState({});
  const [showSuggestions, setShowSuggestions] = useState({});
  
  // Name correction state
  const [showNameCorrection, setShowNameCorrection] = useState({});
  const [correctingName, setCorrectingName] = useState(null);
  
  // Employee billing codes state
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
      extracted_data: {
        ...prev.extracted_data,
        client_name: value
      }
    }));
  };

  const handleEmployeeFieldChange = (empIndex, field, value) => {
    setTimesheet(prev => {
      const newEmployees = [...prev.extracted_data.employee_entries];
      newEmployees[empIndex] = {
        ...newEmployees[empIndex],
        [field]: value
      };
      return {
        ...prev,
        extracted_data: {
          ...prev.extracted_data,
          employee_entries: newEmployees
        }
      };
    });
    
    // If employee name changed, fetch similar employees
    if (field === 'employee_name' && value && value.length >= 2) {
      fetchSimilarEmployees(empIndex, value);
    }
  };

  const fetchSimilarEmployees = async (empIndex, name) => {
    if (!name || name.length < 2) return;
    
    setLoadingSimilar(prev => ({ ...prev, [empIndex]: true }));
    try {
      const response = await axios.get(`${API}/employees/similar/${encodeURIComponent(name)}`);
      setSimilarEmployees(prev => ({ ...prev, [empIndex]: response.data }));
      
      // Auto-show suggestions if we found matches
      if (response.data.similar_employees?.length > 0) {
        setShowSuggestions(prev => ({ ...prev, [empIndex]: true }));
      }
    } catch (e) {
      console.error("Error fetching similar employees:", e);
    } finally {
      setLoadingSimilar(prev => ({ ...prev, [empIndex]: false }));
    }
  };

  const applySuggestedEmployee = (empIndex, employee) => {
    handleEmployeeFieldChange(empIndex, 'employee_name', employee.full_name);
    setShowSuggestions(prev => ({ ...prev, [empIndex]: false }));
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
        params: {
          incorrect_name: incorrectName,
          correct_name: correctName.trim(),
          apply_to_all: true
        }
      });
      
      // Update the current timesheet's display
      handleEmployeeFieldChange(empIndex, 'employee_name', correctName.trim());
      setShowNameCorrection(prev => ({ ...prev, [empIndex]: false }));
      
      toast.success(response.data.message);
    } catch (e) {
      console.error("Error applying name correction:", e);
      toast.error("Failed to apply name correction");
    } finally {
      setCorrectingName(null);
    }
  };

  const handleTimeEntryChange = (empIndex, entryIndex, field, value) => {
    setTimesheet(prev => {
      const newEmployees = [...prev.extracted_data.employee_entries];
      const newTimeEntries = [...newEmployees[empIndex].time_entries];
      newTimeEntries[entryIndex] = {
        ...newTimeEntries[entryIndex],
        [field]: value
      };
      newEmployees[empIndex] = {
        ...newEmployees[empIndex],
        time_entries: newTimeEntries
      };
      return {
        ...prev,
        extracted_data: {
          ...prev.extracted_data,
          employee_entries: newEmployees
        }
      };
    });
  };

  const addTimeEntry = (empIndex) => {
    setTimesheet(prev => {
      const newEmployees = [...prev.extracted_data.employee_entries];
      newEmployees[empIndex] = {
        ...newEmployees[empIndex],
        time_entries: [
          ...newEmployees[empIndex].time_entries,
          { date: "", time_in: "", time_out: "", hours_worked: "" }
        ]
      };
      return {
        ...prev,
        extracted_data: {
          ...prev.extracted_data,
          employee_entries: newEmployees
        }
      };
    });
  };

  const removeTimeEntry = (empIndex, entryIndex) => {
    setTimesheet(prev => {
      const newEmployees = [...prev.extracted_data.employee_entries];
      const newTimeEntries = newEmployees[empIndex].time_entries.filter((_, idx) => idx !== entryIndex);
      newEmployees[empIndex] = {
        ...newEmployees[empIndex],
        time_entries: newTimeEntries
      };
      return {
        ...prev,
        extracted_data: {
          ...prev.extracted_data,
          employee_entries: newEmployees
        }
      };
    });
  };

  const addEmployee = () => {
    setTimesheet(prev => ({
      ...prev,
      extracted_data: {
        ...prev.extracted_data,
        employee_entries: [
          ...prev.extracted_data.employee_entries,
          {
            employee_name: "",
            service_code: "",
            signature: "No",
            time_entries: [{ date: "", time_in: "", time_out: "", hours_worked: "" }]
          }
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
      console.error("Save error:", e);
      toast.error("Failed to save timesheet");
      setSaving(false);
    }
  };

  const handleResubmit = async () => {
    setSaving(true);
    try {
      // Update the timesheet first
      await axios.put(`${API}/timesheets/${id}`, timesheet);
      
      // Resubmit to Sandata with validation
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
      console.error("Resubmit error:", e);
      toast.error("Failed to resubmit timesheet");
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-green-50 flex items-center justify-center">
        <p className="text-gray-600">Loading timesheet...</p>
      </div>
    );
  }

  if (!timesheet) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-green-50 flex items-center justify-center">
        <p className="text-gray-600">Timesheet not found</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-green-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-2" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Edit Timesheet
            </h1>
            <p className="text-gray-600">Review and correct extracted data</p>
            <p className="text-sm text-gray-500 mt-1">File: {timesheet.filename}</p>
          </div>
          <div className="flex gap-3">
            <Button variant="outline" onClick={() => navigate("/")} data-testid="cancel-edit-btn">
              <X className="mr-2" size={18} />
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={saving} className="bg-blue-600 hover:bg-blue-700" data-testid="save-timesheet-btn">
              <Save className="mr-2" size={18} />
              Save Changes
            </Button>
            <Button onClick={handleResubmit} disabled={saving} className="bg-green-600 hover:bg-green-700" data-testid="resubmit-timesheet-btn">
              <CheckCircle className="mr-2" size={18} />
              Save & Resubmit
            </Button>
          </div>
        </div>

        {/* Alert */}
        <Card className="mb-6 border-l-4 border-l-yellow-500 bg-yellow-50">
          <CardContent className="py-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="text-yellow-600 mt-0.5" size={20} />
              <div>
                <p className="font-semibold text-yellow-900">Manual Review Mode</p>
                <p className="text-sm text-yellow-800">Review all extracted data carefully. Units are automatically calculated from time in/out (1 unit = 15 minutes). Time periods over 35 minutes are rounded up to 3 units.</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Patient/Client Name */}
        <Card className="mb-6 shadow-lg">
          <CardHeader className="bg-blue-50">
            <CardTitle>Patient/Client Information</CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            <div>
              <Label htmlFor="client_name">Patient/Client Name</Label>
              <Input
                id="client_name"
                value={timesheet.extracted_data?.client_name || ""}
                onChange={(e) => handleClientNameChange(e.target.value)}
                placeholder="Enter patient name"
                data-testid="client-name-input"
              />
            </div>
          </CardContent>
        </Card>

        {/* Employee Entries */}
        <div className="space-y-6">
          {timesheet.extracted_data?.employee_entries?.map((employee, empIndex) => (
            <Card key={empIndex} className="shadow-lg" data-testid={`employee-${empIndex}`}>
              <CardHeader className="bg-gray-50">
                <div className="flex justify-between items-center">
                  <CardTitle className="text-lg">Employee {empIndex + 1}</CardTitle>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => removeEmployee(empIndex)}
                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                    data-testid={`remove-employee-${empIndex}`}
                  >
                    <Trash2 size={18} />
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="pt-6 space-y-6">
                {/* Employee Details */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="relative">
                    <Label htmlFor={`emp_name_${empIndex}`}>Employee Name</Label>
                    <div className="flex gap-2">
                      <Input
                        id={`emp_name_${empIndex}`}
                        value={employee.employee_name || ""}
                        onChange={(e) => handleEmployeeFieldChange(empIndex, "employee_name", e.target.value)}
                        placeholder="Enter name"
                        data-testid={`employee-name-${empIndex}`}
                        className="flex-1"
                      />
                      <Button
                        type="button"
                        variant="outline"
                        size="icon"
                        onClick={() => fetchSimilarEmployees(empIndex, employee.employee_name)}
                        disabled={loadingSimilar[empIndex]}
                        title="Find similar employees"
                      >
                        <Users size={16} />
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        size="icon"
                        onClick={() => setShowNameCorrection(prev => ({ ...prev, [empIndex]: !prev[empIndex] }))}
                        title="Apply name correction to all timesheets"
                        className="text-purple-600 hover:bg-purple-50"
                      >
                        <Wand2 size={16} />
                      </Button>
                    </div>
                    
                    {/* Name Correction Panel */}
                    {showNameCorrection[empIndex] && (
                      <div className="absolute z-20 w-80 mt-1 bg-white border-2 border-purple-200 rounded-lg shadow-xl p-3">
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-sm font-semibold text-purple-800">
                            <Wand2 size={14} className="inline mr-1" />
                            Apply to All Timesheets
                          </span>
                          <button
                            onClick={() => setShowNameCorrection(prev => ({ ...prev, [empIndex]: false }))}
                            className="text-gray-500 hover:text-gray-700"
                          >
                            <X size={14} />
                          </button>
                        </div>
                        <p className="text-xs text-gray-600 mb-2">
                          Type the correct name below. This will update ALL timesheets with "{employee.employee_name || 'this name'}".
                        </p>
                        <div className="space-y-2">
                          <div>
                            <Label className="text-xs">Current (incorrect):</Label>
                            <Input 
                              value={employee.employee_name || ""} 
                              disabled 
                              className="bg-gray-100 text-sm"
                            />
                          </div>
                          <div>
                            <Label className="text-xs">Correct name:</Label>
                            <Input
                              id={`correct_name_${empIndex}`}
                              placeholder="Enter correct name"
                              className="text-sm"
                              defaultValue=""
                            />
                          </div>
                          <Button
                            type="button"
                            size="sm"
                            className="w-full bg-purple-600 hover:bg-purple-700"
                            disabled={correctingName === empIndex}
                            onClick={() => {
                              const correctName = document.getElementById(`correct_name_${empIndex}`).value;
                              applyNameCorrectionToAll(empIndex, employee.employee_name, correctName);
                            }}
                          >
                            {correctingName === empIndex ? "Applying..." : "Apply to All Timesheets"}
                          </Button>
                        </div>
                      </div>
                    )}
                    
                    {/* Similar Employee Suggestions */}
                    {showSuggestions[empIndex] && similarEmployees[empIndex]?.similar_employees?.length > 0 && (
                      <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                        <div className="p-2 bg-blue-50 border-b flex justify-between items-center">
                          <span className="text-xs font-semibold text-blue-800">
                            <Users size={12} className="inline mr-1" />
                            Similar Employees Found ({similarEmployees[empIndex].similar_employees.length})
                          </span>
                          <button
                            onClick={() => setShowSuggestions(prev => ({ ...prev, [empIndex]: false }))}
                            className="text-gray-500 hover:text-gray-700"
                          >
                            <X size={14} />
                          </button>
                        </div>
                        {similarEmployees[empIndex].similar_employees.map((emp, idx) => (
                          <div
                            key={idx}
                            className="p-2 hover:bg-gray-50 cursor-pointer border-b last:border-b-0 flex justify-between items-center"
                            onClick={() => applySuggestedEmployee(empIndex, emp)}
                          >
                            <div>
                              <p className="font-medium text-sm">{emp.full_name}</p>
                              <p className="text-xs text-gray-500">
                                {emp.categories?.length > 0 ? emp.categories.join(", ") : "No category"} 
                                {emp.is_complete ? " • Complete" : " • Incomplete"}
                              </p>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className={`text-xs px-2 py-0.5 rounded ${
                                emp.similarity_score >= 0.95 ? 'bg-green-100 text-green-800' :
                                emp.similarity_score >= 0.85 ? 'bg-yellow-100 text-yellow-800' :
                                'bg-gray-100 text-gray-800'
                              }`}>
                                {Math.round(emp.similarity_score * 100)}% match
                              </span>
                              <Link size={14} className="text-blue-600" />
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  <div>
                    <Label htmlFor={`service_code_${empIndex}`}>Service Code</Label>
                    <Input
                      id={`service_code_${empIndex}`}
                      value={employee.service_code || ""}
                      onChange={(e) => handleEmployeeFieldChange(empIndex, "service_code", e.target.value)}
                      placeholder="Enter code"
                      data-testid={`service-code-${empIndex}`}
                    />
                  </div>
                  <div>
                    <Label htmlFor={`signature_${empIndex}`}>Signature</Label>
                    <select
                      id={`signature_${empIndex}`}
                      value={employee.signature || "No"}
                      onChange={(e) => handleEmployeeFieldChange(empIndex, "signature", e.target.value)}
                      className="w-full h-10 px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                    <h4 className="text-sm font-semibold text-gray-700 uppercase">Time Entries</h4>
                    <Button
                      size="sm"
                      onClick={() => addTimeEntry(empIndex)}
                      className="bg-green-600 hover:bg-green-700"
                      data-testid={`add-time-entry-${empIndex}`}
                    >
                      <Plus className="mr-1" size={16} />
                      Add Entry
                    </Button>
                  </div>

                  <div className="space-y-3">
                    {employee.time_entries?.map((entry, entryIndex) => (
                      <div key={entryIndex} className="border border-gray-200 rounded-lg p-4 bg-gray-50" data-testid={`time-entry-${empIndex}-${entryIndex}`}>
                        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
                          <div>
                            <Label htmlFor={`date_${empIndex}_${entryIndex}`} className="text-xs">Date</Label>
                            <Input
                              id={`date_${empIndex}_${entryIndex}`}
                              type="date"
                              value={entry.date || ""}
                              onChange={(e) => handleTimeEntryChange(empIndex, entryIndex, "date", e.target.value)}
                              data-testid={`date-${empIndex}-${entryIndex}`}
                            />
                          </div>
                          <div>
                            <Label htmlFor={`time_in_${empIndex}_${entryIndex}`} className="text-xs">Time In</Label>
                            <Input
                              id={`time_in_${empIndex}_${entryIndex}`}
                              type="time"
                              value={entry.time_in || ""}
                              onChange={(e) => handleTimeEntryChange(empIndex, entryIndex, "time_in", e.target.value)}
                              placeholder="HH:MM AM/PM"
                              data-testid={`time-in-${empIndex}-${entryIndex}`}
                            />
                          </div>
                          <div>
                            <Label htmlFor={`time_out_${empIndex}_${entryIndex}`} className="text-xs">Time Out</Label>
                            <Input
                              id={`time_out_${empIndex}_${entryIndex}`}
                              type="time"
                              value={entry.time_out || ""}
                              onChange={(e) => handleTimeEntryChange(empIndex, entryIndex, "time_out", e.target.value)}
                              placeholder="HH:MM AM/PM"
                              data-testid={`time-out-${empIndex}-${entryIndex}`}
                            />
                          </div>
                          <div>
                            <Label htmlFor={`hours_${empIndex}_${entryIndex}`} className="text-xs">Hours</Label>
                            <Input
                              id={`hours_${empIndex}_${entryIndex}`}
                              value={entry.formatted_hours || entry.hours_worked || ""}
                              onChange={(e) => handleTimeEntryChange(empIndex, entryIndex, "hours_worked", e.target.value)}
                              placeholder="8:30"
                              readOnly
                              className="bg-gray-100"
                              data-testid={`hours-${empIndex}-${entryIndex}`}
                            />
                          </div>
                          <div className="flex items-end">
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => removeTimeEntry(empIndex, entryIndex)}
                              className="text-red-600 hover:text-red-700 hover:bg-red-50"
                              data-testid={`remove-entry-${empIndex}-${entryIndex}`}
                            >
                              <Trash2 size={16} />
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}

          {/* Add Employee Button */}
          <Button
            onClick={addEmployee}
            className="w-full bg-blue-600 hover:bg-blue-700"
            data-testid="add-employee-btn"
          >
            <Plus className="mr-2" size={18} />
            Add Another Employee
          </Button>
        </div>

        {/* Action Buttons at Bottom */}
        <div className="flex justify-end gap-3 mt-8 pt-6 border-t">
          <Button variant="outline" onClick={() => navigate("/")} disabled={saving}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={saving} className="bg-blue-600 hover:bg-blue-700">
            <Save className="mr-2" size={18} />
            Save Changes
          </Button>
          <Button onClick={handleResubmit} disabled={saving} className="bg-green-600 hover:bg-green-700">
            <CheckCircle className="mr-2" size={18} />
            Save & Resubmit to Sandata
          </Button>
        </div>
      </div>
    </div>
  );
};

export default TimesheetEditor;
