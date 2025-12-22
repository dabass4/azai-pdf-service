import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ChevronLeft, ChevronRight, Check } from "lucide-react";

/**
 * SimpleMultiStepForm - A minimal multi-step form component
 * Created to debug Step 4 disappearing issue
 */
const SimpleMultiStepForm = ({ 
  steps, 
  formData, 
  onFormDataChange, 
  onSubmit, 
  onCancel,
  submitLabel = "Submit"
}) => {
  const [step, setStep] = useState(0);
  const [validationErrors, setValidationErrors] = useState({});
  
  const totalSteps = steps.length;
  const currentConfig = steps[step];
  const isFirst = step === 0;
  const isLast = step === totalSteps - 1;

  const validate = () => {
    const required = currentConfig.requiredFields || [];
    const errs = {};
    for (const field of required) {
      if (!formData[field] || formData[field].toString().trim() === "") {
        errs[field] = "Required";
      }
    }
    setValidationErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const goNext = () => {
    if (validate() && step < totalSteps - 1) {
      setStep(s => s + 1);
      setValidationErrors({});
    }
  };

  const goPrev = () => {
    if (step > 0) {
      setStep(s => s - 1);
      setValidationErrors({});
    }
  };

  const doSubmit = (e) => {
    e.preventDefault();
    if (validate()) {
      onSubmit(formData);
    }
  };

  return (
    <Card className="border-2 border-blue-200 shadow-lg">
      <CardHeader className="bg-blue-50">
        <CardTitle>{currentConfig.title}</CardTitle>
        <CardDescription>{currentConfig.description}</CardDescription>
        
        {/* Progress */}
        <div className="mt-4">
          <div className="flex justify-between text-sm mb-2">
            <span>Step {step + 1} of {totalSteps}</span>
            <span>{Math.round(((step + 1) / totalSteps) * 100)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all"
              style={{ width: `${((step + 1) / totalSteps) * 100}%` }}
            />
          </div>
        </div>

        {/* Step indicators */}
        <div className="flex justify-center gap-2 mt-4">
          {steps.map((_, i) => (
            <div
              key={i}
              className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold
                ${i < step ? 'bg-green-500 text-white' : 
                  i === step ? 'bg-blue-600 text-white' : 
                  'bg-gray-300 text-gray-600'}`}
            >
              {i < step ? <Check size={16} /> : i + 1}
            </div>
          ))}
        </div>
      </CardHeader>

      <CardContent className="p-6">
        <form onSubmit={doSubmit}>
          {/* Step Content */}
          <div className="mb-6">
            {currentConfig.render({ 
              formData, 
              onFormDataChange, 
              errors: validationErrors 
            })}
          </div>

          {/* Buttons */}
          <div className="flex justify-between pt-4 border-t">
            <Button type="button" variant="outline" onClick={onCancel}>
              Cancel
            </Button>
            
            <div className="flex gap-2">
              {!isFirst && (
                <Button type="button" variant="outline" onClick={goPrev}>
                  <ChevronLeft size={18} /> Previous
                </Button>
              )}
              
              {!isLast ? (
                <Button type="button" onClick={goNext} className="bg-blue-600 hover:bg-blue-700">
                  Next <ChevronRight size={18} />
                </Button>
              ) : (
                <Button type="submit" className="bg-green-600 hover:bg-green-700">
                  <Check size={18} /> {submitLabel}
                </Button>
              )}
            </div>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};

export default SimpleMultiStepForm;
