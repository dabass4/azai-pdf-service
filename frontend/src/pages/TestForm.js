import React, { useState, useMemo } from "react";
import MultiStepForm from "@/components/MultiStepForm";

const TestForm = () => {
  const [formData, setFormData] = useState({
    field1: "",
    field2: "",
    field3: "",
    field4: ""
  });

  // Memoize steps to prevent recreation on every render
  const steps = useMemo(() => [
    {
      title: "Step 1: Basic Info",
      description: "First step - enter field 1",
      requiredFields: ["field1"],
      render: ({ formData, onFormDataChange, errors }) => (
        <div className="p-4 bg-gray-50 rounded-lg">
          <h2 className="text-xl font-bold mb-4 text-blue-600">STEP 1 CONTENT</h2>
          <input 
            value={formData.field1 || ""} 
            onChange={(e) => onFormDataChange(prev => ({...prev, field1: e.target.value}))}
            placeholder="Field 1 (required)"
            className={`w-full p-2 border rounded ${errors?.field1 ? 'border-red-500' : 'border-gray-300'}`}
          />
          {errors?.field1 && <p className="text-red-500 text-sm mt-1">{errors.field1}</p>}
        </div>
      )
    },
    {
      title: "Step 2: Additional Info",
      description: "Second step - enter field 2",
      requiredFields: ["field2"],
      render: ({ formData, onFormDataChange, errors }) => (
        <div className="p-4 bg-green-50 rounded-lg">
          <h2 className="text-xl font-bold mb-4 text-green-600">STEP 2 CONTENT</h2>
          <input 
            value={formData.field2 || ""} 
            onChange={(e) => onFormDataChange(prev => ({...prev, field2: e.target.value}))}
            placeholder="Field 2 (required)"
            className={`w-full p-2 border rounded ${errors?.field2 ? 'border-red-500' : 'border-gray-300'}`}
          />
          {errors?.field2 && <p className="text-red-500 text-sm mt-1">{errors.field2}</p>}
        </div>
      )
    },
    {
      title: "Step 3: More Details",
      description: "Third step - enter field 3",
      requiredFields: ["field3"],
      render: ({ formData, onFormDataChange, errors }) => (
        <div className="p-4 bg-yellow-50 rounded-lg">
          <h2 className="text-xl font-bold mb-4 text-yellow-600">STEP 3 CONTENT</h2>
          <input 
            value={formData.field3 || ""} 
            onChange={(e) => onFormDataChange(prev => ({...prev, field3: e.target.value}))}
            placeholder="Field 3 (required)"
            className={`w-full p-2 border rounded ${errors?.field3 ? 'border-red-500' : 'border-gray-300'}`}
          />
          {errors?.field3 && <p className="text-red-500 text-sm mt-1">{errors.field3}</p>}
        </div>
      )
    },
    {
      title: "Step 4: Final Step",
      description: "Fourth step - optional field 4",
      requiredFields: [],
      render: ({ formData, onFormDataChange }) => (
        <div className="p-6 bg-purple-600 text-white rounded-lg">
          <h2 className="text-2xl font-bold mb-4">STEP 4 - THIS SHOULD STAY VISIBLE</h2>
          <p className="mb-4">If you can see this purple box, Step 4 is working correctly!</p>
          <input 
            value={formData.field4 || ""} 
            onChange={(e) => onFormDataChange(prev => ({...prev, field4: e.target.value}))}
            placeholder="Field 4 (optional)"
            className="w-full p-2 border rounded text-black"
          />
        </div>
      )
    }
  ], []);

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Test Form - 4 Steps</h1>
      <p className="mb-4 text-gray-600">This is a test page to verify the MultiStepForm component works correctly.</p>
      <MultiStepForm
        steps={steps}
        formData={formData}
        onFormDataChange={setFormData}
        onSubmit={(data) => alert("Submitted: " + JSON.stringify(data))}
        onCancel={() => alert("Cancelled")}
        submitLabel="Test Submit"
      />
    </div>
  );
};

export default TestForm;
