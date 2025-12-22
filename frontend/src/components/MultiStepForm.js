import { useState, useEffect, useRef } from "react";
import { ChevronLeft, ChevronRight, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

/**
 * Reusable Multi-Step Form Component
 * 
 * @param {Array} steps - Array of step objects with { title, description, fields, render }
 * @param {Object} formData - Current form data
 * @param {Function} onFormDataChange - Callback when form data changes
 * @param {Function} onSubmit - Callback when form is submitted
 * @param {Function} onCancel - Callback when form is cancelled
 * @param {string} submitLabel - Label for submit button (default: "Submit")
 * @param {string} storageKey - LocalStorage key for auto-save (optional)
 */
const MultiStepForm = ({ 
  steps, 
  formData, 
  onFormDataChange, 
  onSubmit, 
  onCancel,
  submitLabel = "Submit",
  storageKey = null
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [errors, setErrors] = useState({});
  
  // Ensure currentStep is always valid
  const safeCurrentStep = Math.min(currentStep, steps.length - 1);
  if (safeCurrentStep !== currentStep) {
    setCurrentStep(safeCurrentStep);
  }

  // DISABLED: Auto-save to localStorage - was causing Step 4 flash issue
  // useEffect(() => {
  //   if (storageKey && formData && Object.keys(formData).length > 0) {
  //     localStorage.setItem(storageKey, JSON.stringify({ formData, currentStep }));
  //   }
  // }, [formData, currentStep, storageKey]);

  // DISABLED: Restore from localStorage - was causing Step 4 flash issue
  // const hasRestoredRef = useRef(false);
  // useEffect(() => { ... }, []);

  // Clear localStorage when form is submitted or cancelled
  const clearStorage = () => {
    if (storageKey) {
      localStorage.removeItem(storageKey);
    }
  };

  const validateStep = () => {
    const currentStepConfig = steps[currentStep];
    const requiredFields = currentStepConfig.requiredFields || [];
    const newErrors = {};

    requiredFields.forEach(field => {
      if (!formData[field] || formData[field].toString().trim() === "") {
        newErrors[field] = "This field is required";
      }
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateStep()) {
      if (currentStep < steps.length - 1) {
        setCurrentStep(prev => prev + 1);
        setErrors({});
      }
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1);
      setErrors({});
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (validateStep()) {
      clearStorage();
      onSubmit(formData);
    }
  };

  const handleCancel = () => {
    clearStorage();
    onCancel();
  };

  const currentStepConfig = steps[currentStep];
  const isLastStep = currentStep === steps.length - 1;
  const isFirstStep = currentStep === 0;

  return (
    <Card className="border-2 border-blue-200 shadow-lg">
      <CardHeader className="bg-blue-50">
        <CardTitle>{currentStepConfig.title}</CardTitle>
        <CardDescription>{currentStepConfig.description}</CardDescription>
        
        {/* Progress Indicator */}
        <div className="mt-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">
              Step {currentStep + 1} of {steps.length}
            </span>
            <span className="text-sm text-gray-500">
              {Math.round(((currentStep + 1) / steps.length) * 100)}% Complete
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
            />
          </div>
          
          {/* Step Indicators */}
          <div className="flex justify-between mt-3">
            {steps.map((step, index) => (
              <div key={index} className="flex items-center">
                <div className={`
                  flex items-center justify-center w-8 h-8 rounded-full text-sm font-semibold
                  ${index < currentStep ? 'bg-green-500 text-white' : 
                    index === currentStep ? 'bg-blue-600 text-white' : 
                    'bg-gray-300 text-gray-600'}
                `}>
                  {index < currentStep ? <Check size={16} /> : index + 1}
                </div>
                {index < steps.length - 1 && (
                  <div className={`h-0.5 w-8 mx-1 ${index < currentStep ? 'bg-green-500' : 'bg-gray-300'}`} />
                )}
              </div>
            ))}
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="pt-6">
        <form onSubmit={handleSubmit}>
          {/* Render current step */}
          <div className="space-y-6">
            {currentStepConfig.render({ formData, onFormDataChange, errors })}
          </div>

          {/* Navigation Buttons */}
          <div className="flex justify-between gap-3 pt-6 mt-6 border-t">
            <Button 
              type="button" 
              variant="outline" 
              onClick={handleCancel}
            >
              Cancel
            </Button>
            
            <div className="flex gap-3">
              {!isFirstStep && (
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={handlePrevious}
                  className="flex items-center gap-2"
                >
                  <ChevronLeft size={18} />
                  Previous
                </Button>
              )}
              
              {!isLastStep ? (
                <Button 
                  type="button" 
                  onClick={handleNext}
                  className="bg-blue-600 hover:bg-blue-700 flex items-center gap-2"
                >
                  Next
                  <ChevronRight size={18} />
                </Button>
              ) : (
                <Button 
                  type="submit"
                  className="bg-green-600 hover:bg-green-700 flex items-center gap-2"
                >
                  <Check size={18} />
                  {submitLabel}
                </Button>
              )}
            </div>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};

export default MultiStepForm;
