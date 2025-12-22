import React, { useState } from "react";
import MultiStepForm from "@/components/MultiStepForm";

const TestForm = () => {
  const [formData, setFormData] = useState({
    field1: "",
    field2: "",
    field3: "",
    field4: ""
  });

  const steps = [
    {
      title: "Step 1",
      description: "First step",
      requiredFields: ["field1"],
      render: ({ formData, onFormDataChange, errors }) => (
        <div>
          <h2>STEP 1 CONTENT</h2>
          <input 
            value={formData.field1 || ""} 
            onChange={(e) => onFormDataChange(prev => ({...prev, field1: e.target.value}))}
            placeholder="Field 1"
            style={{border: "1px solid black", padding: "8px"}}
          />
        </div>
      )
    },
    {
      title: "Step 2",
      description: "Second step",
      requiredFields: ["field2"],
      render: ({ formData, onFormDataChange, errors }) => (
        <div>
          <h2>STEP 2 CONTENT</h2>
          <input 
            value={formData.field2 || ""} 
            onChange={(e) => onFormDataChange(prev => ({...prev, field2: e.target.value}))}
            placeholder="Field 2"
            style={{border: "1px solid black", padding: "8px"}}
          />
        </div>
      )
    },
    {
      title: "Step 3",
      description: "Third step",
      requiredFields: ["field3"],
      render: ({ formData, onFormDataChange, errors }) => (
        <div>
          <h2>STEP 3 CONTENT</h2>
          <input 
            value={formData.field3 || ""} 
            onChange={(e) => onFormDataChange(prev => ({...prev, field3: e.target.value}))}
            placeholder="Field 3"
            style={{border: "1px solid black", padding: "8px"}}
          />
        </div>
      )
    },
    {
      title: "Step 4",
      description: "Fourth step",
      requiredFields: [],
      render: ({ formData, onFormDataChange, errors }) => (
        <div style={{background: "purple", color: "white", padding: "20px"}}>
          <h2>STEP 4 CONTENT - THIS SHOULD STAY VISIBLE</h2>
          <input 
            value={formData.field4 || ""} 
            onChange={(e) => onFormDataChange(prev => ({...prev, field4: e.target.value}))}
            placeholder="Field 4"
            style={{border: "1px solid black", padding: "8px", color: "black"}}
          />
        </div>
      )
    }
  ];

  return (
    <div style={{padding: "20px"}}>
      <h1>Test Form - 4 Steps</h1>
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
