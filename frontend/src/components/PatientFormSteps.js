import React from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { AlertCircle } from "lucide-react";
import ICD10Lookup from "@/components/ICD10Lookup";
import PhysicianLookup from "@/components/PhysicianLookup";

const US_STATES = [
  "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
  "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
  "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
  "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
  "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
];

/**
 * Patient Form Steps Configuration
 * Returns an array of 4 steps for the MultiStepForm component
 */
export const getPatientFormSteps = () => [
  // STEP 1: Basic Information
  {
    title: "Step 1: Basic Information",
    description: "Enter patient's personal and identification details",
    requiredFields: ["first_name", "last_name", "sex", "date_of_birth", "medicaid_number"],
    render: ({ formData, onFormDataChange, errors }) => (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <Label htmlFor="first_name">First Name *</Label>
          <Input
            id="first_name"
            value={formData.first_name || ""}
            onChange={(e) => onFormDataChange(prev => ({...prev, first_name: e.target.value}))}
            className={errors.first_name ? "border-red-500" : ""}
          />
          {errors.first_name && <p className="text-xs text-red-500 mt-1">{errors.first_name}</p>}
        </div>
        <div>
          <Label htmlFor="last_name">Last Name *</Label>
          <Input
            id="last_name"
            value={formData.last_name || ""}
            onChange={(e) => onFormDataChange(prev => ({...prev, last_name: e.target.value}))}
            className={errors.last_name ? "border-red-500" : ""}
          />
          {errors.last_name && <p className="text-xs text-red-500 mt-1">{errors.last_name}</p>}
        </div>
        <div>
          <Label htmlFor="sex">Sex *</Label>
          <Select
            value={formData.sex || ""}
            onValueChange={(value) => onFormDataChange(prev => ({...prev, sex: value}))}
          >
            <SelectTrigger className={errors.sex ? "border-red-500" : ""}>
              <SelectValue placeholder="Select sex" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Male">Male</SelectItem>
              <SelectItem value="Female">Female</SelectItem>
            </SelectContent>
          </Select>
          {errors.sex && <p className="text-xs text-red-500 mt-1">{errors.sex}</p>}
        </div>
        <div>
          <Label htmlFor="date_of_birth">Date of Birth *</Label>
          <Input
            id="date_of_birth"
            type="date"
            value={formData.date_of_birth || ""}
            onChange={(e) => onFormDataChange(prev => ({...prev, date_of_birth: e.target.value}))}
            className={errors.date_of_birth ? "border-red-500" : ""}
          />
          {errors.date_of_birth && <p className="text-xs text-red-500 mt-1">{errors.date_of_birth}</p>}
        </div>
        <div className="md:col-span-2">
          <Label htmlFor="medicaid_number">Medicaid Number (12 digits) *</Label>
          <Input
            id="medicaid_number"
            value={formData.medicaid_number || ""}
            onChange={(e) => onFormDataChange(prev => ({...prev, medicaid_number: e.target.value.replace(/\D/g, '').slice(0, 12)}))}
            maxLength="12"
            placeholder="123456789012"
            className={`font-mono ${errors.medicaid_number ? "border-red-500" : ""}`}
          />
          {errors.medicaid_number && <p className="text-xs text-red-500 mt-1">{errors.medicaid_number}</p>}
        </div>
      </div>
    )
  },

  // STEP 2: Address & Medical Information
  {
    title: "Step 2: Address & Medical Information",
    description: "Enter address and medical details required for claims",
    requiredFields: ["address_street", "address_city", "address_state", "address_zip", "icd10_code"],
    render: ({ formData, onFormDataChange, errors }) => (
      <div className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-2">
            <Label htmlFor="address_street">Street Address *</Label>
            <Input
              id="address_street"
              value={formData.address_street || ""}
              onChange={(e) => onFormDataChange(prev => ({...prev, address_street: e.target.value}))}
              className={errors.address_street ? "border-red-500" : ""}
            />
            {errors.address_street && <p className="text-xs text-red-500 mt-1">{errors.address_street}</p>}
          </div>
          <div>
            <Label htmlFor="address_city">City *</Label>
            <Input
              id="address_city"
              value={formData.address_city || ""}
              onChange={(e) => onFormDataChange(prev => ({...prev, address_city: e.target.value}))}
              className={errors.address_city ? "border-red-500" : ""}
            />
            {errors.address_city && <p className="text-xs text-red-500 mt-1">{errors.address_city}</p>}
          </div>
          <div>
            <Label htmlFor="address_state">State *</Label>
            <Select
              value={formData.address_state || ""}
              onValueChange={(value) => onFormDataChange(prev => ({...prev, address_state: value}))}
            >
              <SelectTrigger className={errors.address_state ? "border-red-500" : ""}>
                <SelectValue placeholder="Select state" />
              </SelectTrigger>
              <SelectContent>
                {US_STATES.map(state => (
                  <SelectItem key={state} value={state}>{state}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.address_state && <p className="text-xs text-red-500 mt-1">{errors.address_state}</p>}
          </div>
          <div>
            <Label htmlFor="address_zip">ZIP Code *</Label>
            <Input
              id="address_zip"
              value={formData.address_zip || ""}
              onChange={(e) => onFormDataChange(prev => ({...prev, address_zip: e.target.value}))}
              maxLength="10"
              className={errors.address_zip ? "border-red-500" : ""}
            />
            {errors.address_zip && <p className="text-xs text-red-500 mt-1">{errors.address_zip}</p>}
          </div>
          <div>
            <Label htmlFor="prior_auth_number">Prior Authorization Number (Optional)</Label>
            <Input
              id="prior_auth_number"
              value={formData.prior_auth_number || ""}
              onChange={(e) => onFormDataChange(prev => ({...prev, prior_auth_number: e.target.value}))}
              placeholder="Optional"
            />
          </div>
          <div className="md:col-span-2">
            <ICD10Lookup
              value={formData.icd10_code || ""}
              onChange={(code) => onFormDataChange(prev => ({...prev, icd10_code: code}))}
              onDescriptionChange={(desc) => onFormDataChange(prev => ({...prev, icd10_description: desc}))}
              description={formData.icd10_description || ""}
              error={errors.icd10_code}
            />
          </div>
          <div className="md:col-span-2">
            <Label htmlFor="icd10_description">ICD-10 Description (Auto-filled or Manual)</Label>
            <Input
              id="icd10_description"
              value={formData.icd10_description || ""}
              onChange={(e) => onFormDataChange(prev => ({...prev, icd10_description: e.target.value}))}
              placeholder="Description auto-fills from lookup"
            />
          </div>
        </div>
      </div>
    )
  },

  // STEP 3: Physician Information
  {
    title: "Step 3: Physician Information",
    description: "Search by name or enter NPI number directly",
    requiredFields: ["physician_name", "physician_npi"],
    render: ({ formData, onFormDataChange, errors }) => (
      <div className="max-w-md">
        <PhysicianLookup
          npiValue={formData.physician_npi || ""}
          nameValue={formData.physician_name || ""}
          onNpiChange={(npi) => onFormDataChange(prev => ({...prev, physician_npi: npi}))}
          onNameChange={(name) => onFormDataChange(prev => ({...prev, physician_name: name}))}
          npiError={errors.physician_npi}
          nameError={errors.physician_name}
        />
      </div>
    )
  },

  // STEP 4: Other Insurance (TPL)
  {
    title: "Step 4: Other Insurance (TPL)",
    description: "Third Party Liability information for Medicaid audits",
    requiredFields: [],
    render: ({ formData, onFormDataChange }) => (
      <div className="space-y-6">
        {/* Header Banner */}
        <div className="bg-purple-600 text-white p-4 rounded-lg text-center">
          <h3 className="text-xl font-bold">OTHER INSURANCE INFORMATION</h3>
          <p className="text-sm">Ohio patients may change insurance monthly - please keep this updated</p>
        </div>

        {/* Primary Other Insurance */}
        <div className="p-4 border rounded-lg bg-gray-50">
          <div className="flex items-center gap-3 mb-4">
            <Checkbox
              id="has_other_insurance_checkbox"
              checked={formData.has_other_insurance || false}
              onCheckedChange={(checked) => onFormDataChange(prev => ({...prev, has_other_insurance: checked}))}
            />
            <Label htmlFor="has_other_insurance_checkbox" className="font-medium cursor-pointer">
              Is there other insurance covering this patient (besides the plan being billed)?
            </Label>
          </div>

          {formData.has_other_insurance && (
            <div className="space-y-4 pl-6 border-l-2 border-blue-200 mt-4">
              <div>
                <Label htmlFor="primary_ins_name">Insurance Name</Label>
                <Input
                  id="primary_ins_name"
                  value={formData.other_insurance?.insurance_name || ""}
                  onChange={(e) => onFormDataChange(prev => ({
                    ...prev,
                    other_insurance: {...(prev.other_insurance || {}), insurance_name: e.target.value}
                  }))}
                  placeholder="e.g., Blue Cross Blue Shield"
                />
              </div>

              <div>
                <Label className="mb-2 block">Subscriber Type</Label>
                <div className="flex gap-4">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="primary_sub_type"
                      value="Person"
                      checked={(formData.other_insurance?.subscriber_type || "Person") === "Person"}
                      onChange={(e) => onFormDataChange(prev => ({
                        ...prev,
                        other_insurance: {...(prev.other_insurance || {}), subscriber_type: e.target.value}
                      }))}
                      className="w-4 h-4"
                    />
                    Person
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="primary_sub_type"
                      value="Non-Person Entity"
                      checked={formData.other_insurance?.subscriber_type === "Non-Person Entity"}
                      onChange={(e) => onFormDataChange(prev => ({
                        ...prev,
                        other_insurance: {...(prev.other_insurance || {}), subscriber_type: e.target.value}
                      }))}
                      className="w-4 h-4"
                    />
                    Non-Person Entity
                  </label>
                </div>
              </div>

              <div>
                <Label htmlFor="primary_relationship">Relationship to Patient</Label>
                <Select
                  value={formData.other_insurance?.relationship_to_patient || ""}
                  onValueChange={(value) => onFormDataChange(prev => ({
                    ...prev,
                    other_insurance: {...(prev.other_insurance || {}), relationship_to_patient: value}
                  }))}
                >
                  <SelectTrigger id="primary_relationship">
                    <SelectValue placeholder="Select relationship" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Self">Self</SelectItem>
                    <SelectItem value="Spouse">Spouse</SelectItem>
                    <SelectItem value="Child">Child</SelectItem>
                    <SelectItem value="Other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="primary_group_num">Group Number</Label>
                  <Input
                    id="primary_group_num"
                    value={formData.other_insurance?.group_number || ""}
                    onChange={(e) => onFormDataChange(prev => ({
                      ...prev,
                      other_insurance: {...(prev.other_insurance || {}), group_number: e.target.value}
                    }))}
                  />
                </div>
                <div>
                  <Label htmlFor="primary_policy_num">Policy Number</Label>
                  <Input
                    id="primary_policy_num"
                    value={formData.other_insurance?.policy_number || ""}
                    onChange={(e) => onFormDataChange(prev => ({
                      ...prev,
                      other_insurance: {...(prev.other_insurance || {}), policy_number: e.target.value}
                    }))}
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="primary_policy_type">Policy Type</Label>
                <Select
                  value={formData.other_insurance?.policy_type || ""}
                  onValueChange={(value) => onFormDataChange(prev => ({
                    ...prev,
                    other_insurance: {...(prev.other_insurance || {}), policy_type: value}
                  }))}
                >
                  <SelectTrigger id="primary_policy_type">
                    <SelectValue placeholder="Select policy type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Primary">Primary</SelectItem>
                    <SelectItem value="Secondary">Secondary</SelectItem>
                    <SelectItem value="Tertiary">Tertiary</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          )}
        </div>

        {/* Second Other Insurance - Only show if first insurance is enabled */}
        {formData.has_other_insurance && (
          <div className="p-4 border rounded-lg bg-gray-50">
            <div className="flex items-center gap-3 mb-4">
              <Checkbox
                id="has_second_insurance_checkbox"
                checked={formData.has_second_other_insurance || false}
                onCheckedChange={(checked) => onFormDataChange(prev => ({...prev, has_second_other_insurance: checked}))}
              />
              <Label htmlFor="has_second_insurance_checkbox" className="font-medium cursor-pointer">
                Is there a second other insurance policy?
              </Label>
            </div>

            {formData.has_second_other_insurance && (
              <div className="space-y-4 pl-6 border-l-2 border-blue-200 mt-4">
                <div>
                  <Label htmlFor="second_ins_name">Insurance Name</Label>
                  <Input
                    id="second_ins_name"
                    value={formData.second_other_insurance?.insurance_name || ""}
                    onChange={(e) => onFormDataChange(prev => ({
                      ...prev,
                      second_other_insurance: {...(prev.second_other_insurance || {}), insurance_name: e.target.value}
                    }))}
                    placeholder="e.g., Aetna"
                  />
                </div>

                <div>
                  <Label className="mb-2 block">Subscriber Type</Label>
                  <div className="flex gap-4">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        name="second_sub_type"
                        value="Person"
                        checked={(formData.second_other_insurance?.subscriber_type || "Person") === "Person"}
                        onChange={(e) => onFormDataChange(prev => ({
                          ...prev,
                          second_other_insurance: {...(prev.second_other_insurance || {}), subscriber_type: e.target.value}
                        }))}
                        className="w-4 h-4"
                      />
                      Person
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        name="second_sub_type"
                        value="Non-Person Entity"
                        checked={formData.second_other_insurance?.subscriber_type === "Non-Person Entity"}
                        onChange={(e) => onFormDataChange(prev => ({
                          ...prev,
                          second_other_insurance: {...(prev.second_other_insurance || {}), subscriber_type: e.target.value}
                        }))}
                        className="w-4 h-4"
                      />
                      Non-Person Entity
                    </label>
                  </div>
                </div>

                <div>
                  <Label htmlFor="second_relationship">Relationship to Patient</Label>
                  <Select
                    value={formData.second_other_insurance?.relationship_to_patient || ""}
                    onValueChange={(value) => onFormDataChange(prev => ({
                      ...prev,
                      second_other_insurance: {...(prev.second_other_insurance || {}), relationship_to_patient: value}
                    }))}
                  >
                    <SelectTrigger id="second_relationship">
                      <SelectValue placeholder="Select relationship" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Self">Self</SelectItem>
                      <SelectItem value="Spouse">Spouse</SelectItem>
                      <SelectItem value="Child">Child</SelectItem>
                      <SelectItem value="Other">Other</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="second_group_num">Group Number</Label>
                    <Input
                      id="second_group_num"
                      value={formData.second_other_insurance?.group_number || ""}
                      onChange={(e) => onFormDataChange(prev => ({
                        ...prev,
                        second_other_insurance: {...(prev.second_other_insurance || {}), group_number: e.target.value}
                      }))}
                    />
                  </div>
                  <div>
                    <Label htmlFor="second_policy_num">Policy Number</Label>
                    <Input
                      id="second_policy_num"
                      value={formData.second_other_insurance?.policy_number || ""}
                      onChange={(e) => onFormDataChange(prev => ({
                        ...prev,
                        second_other_insurance: {...(prev.second_other_insurance || {}), policy_number: e.target.value}
                      }))}
                    />
                  </div>
                </div>

                <div>
                  <Label htmlFor="second_policy_type">Policy Type</Label>
                  <Select
                    value={formData.second_other_insurance?.policy_type || ""}
                    onValueChange={(value) => onFormDataChange(prev => ({
                      ...prev,
                      second_other_insurance: {...(prev.second_other_insurance || {}), policy_type: value}
                    }))}
                  >
                    <SelectTrigger id="second_policy_type">
                      <SelectValue placeholder="Select policy type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Primary">Primary</SelectItem>
                      <SelectItem value="Secondary">Secondary</SelectItem>
                      <SelectItem value="Tertiary">Tertiary</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Info Note */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start gap-2">
            <AlertCircle className="h-5 w-5 text-blue-600 mt-0.5 shrink-0" />
            <p className="text-sm text-blue-800">
              <strong>Note:</strong> Other insurance information is required for Medicaid audit documentation.
              If the patient has coverage through another insurance plan (e.g., employer-sponsored, Medicare),
              please provide the details above.
            </p>
          </div>
        </div>
      </div>
    )
  }
];

export default getPatientFormSteps;
