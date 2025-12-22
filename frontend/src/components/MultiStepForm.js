import React, { useState, useCallback } from "react";
import { ChevronLeft, ChevronRight, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

/**
 * MultiStepForm - A simple, robust multi-step form component
 * 
 * COMPLETELY REWRITTEN to fix the "Step 4 flash and disappear" bug.
 * Uses a straightforward approach with minimal state.
 * 
 * @param {Array} steps - Array of step objects with { title, description, requiredFields, render }
 * @param {Object} formData - Current form data (controlled externally)
 * @param {Function} onFormDataChange - Callback when form data changes
 * @param {Function} onSubmit - Callback when form is submitted
 * @param {Function} onCancel - Callback when form is cancelled
 * @param {string} submitLabel - Label for submit button (default: "Submit")
 */
const MultiStepForm = ({ 
  steps = [], 
  formData = {}, 
  onFormDataChange, 
  onSubmit, 
  onCancel,
  submitLabel = "Submit"
}) => {
  // Single source of truth for current step
  const [currentStep, setCurrentStep] = useState(0);
  const [errors, setErrors] = useState({});

  // Safely get total steps - defensive coding
  const totalSteps = Array.isArray(steps) ? steps.length : 0;
  
  // Debug logging
  console.log('[MultiStepForm] Render - currentStep:', currentStep, 'totalSteps:', totalSteps, 'steps array length:', steps?.length);
  
  // Get current step config safely
  const getCurrentStepConfig = useCallback(() => {
    if (!Array.isArray(steps) || steps.length === 0) return null;
    if (currentStep < 0 || currentStep >= steps.length) return null;
    return steps[currentStep];
  }, [steps, currentStep]);

  const stepConfig = getCurrentStepConfig();

  // Validation function
  const validateCurrentStep = useCallback(() => {
    if (!stepConfig) return true;
    
    const requiredFields = stepConfig.requiredFields || [];
    const newErrors = {};

    requiredFields.forEach(field => {
      const value = formData[field];
      if (value === undefined || value === null || value.toString().trim() === "") {
        newErrors[field] = "This field is required";
      }
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [stepConfig, formData]);

  // Navigation handlers - using functional updates to avoid stale state
  const goToNextStep = useCallback(() => {
    console.log('[MultiStepForm] goToNextStep called, currentStep:', currentStep, 'totalSteps:', totalSteps);
    if (!validateCurrentStep()) {
      console.log('[MultiStepForm] Validation failed');
      return;
    }
    
    // Use setTimeout to ensure the click event completes before state change
    // This prevents the click from propagating to the newly rendered submit button
    setTimeout(() => {
      setCurrentStep(prevStep => {
        const nextStep = prevStep + 1;
        console.log('[MultiStepForm] Transitioning from step', prevStep, 'to', nextStep);
        // Ensure we don't go beyond the last step
        if (nextStep >= totalSteps) {
          console.log('[MultiStepForm] Already at last step, staying at', prevStep);
          return prevStep;
        }
        console.log('[MultiStepForm] Moving to step', nextStep);
        return nextStep;
      });
      setErrors({});
    }, 0);
  }, [validateCurrentStep, totalSteps, currentStep]);

  const goToPreviousStep = useCallback(() => {
    setCurrentStep(prevStep => {
      const nextStep = prevStep - 1;
      // Ensure we don't go below 0
      if (nextStep < 0) return prevStep;
      return nextStep;
    });
    setErrors({});
  }, []);

  // Submit handler
  const handleSubmit = useCallback((e) => {
    e.preventDefault();
    console.log('[MultiStepForm] handleSubmit called! currentStep:', currentStep, 'isLastStep:', currentStep === totalSteps - 1);
    if (!validateCurrentStep()) {
      console.log('[MultiStepForm] Submit validation failed');
      return;
    }
    
    console.log('[MultiStepForm] Calling onSubmit with formData');
    if (typeof onSubmit === 'function') {
      onSubmit(formData);
    }
  }, [validateCurrentStep, onSubmit, formData, currentStep, totalSteps]);

  // Cancel handler
  const handleCancel = useCallback(() => {
    if (typeof onCancel === 'function') {
      onCancel();
    }
  }, [onCancel]);

  // Error state - no valid steps
  if (totalSteps === 0 || !stepConfig) {
    return (
      <Card className="border-2 border-red-200">
        <CardContent className="p-6">
          <p className="text-red-600">Error: No form steps configured</p>
        </CardContent>
      </Card>
    );
  }

  const isFirstStep = currentStep === 0;
  const isLastStep = currentStep === totalSteps - 1;
  const progressPercent = Math.round(((currentStep + 1) / totalSteps) * 100);

  return (
    <Card className="border-2 border-blue-200 shadow-lg">
      <CardHeader className="bg-blue-50">
        <CardTitle>{stepConfig.title}</CardTitle>
        <CardDescription>{stepConfig.description}</CardDescription>
        
        {/* Progress Bar */}
        <div className="mt-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">
              Step {currentStep + 1} of {totalSteps}
            </span>
            <span className="text-sm text-gray-500">
              {progressPercent}% Complete
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
          
          {/* Step Indicators */}
          <div className="flex justify-between mt-3">
            {steps.map((step, index) => (
              <div key={`step-indicator-${index}`} className="flex items-center">
                <div className={`
                  flex items-center justify-center w-8 h-8 rounded-full text-sm font-semibold
                  ${index < currentStep ? 'bg-green-500 text-white' : 
                    index === currentStep ? 'bg-blue-600 text-white' : 
                    'bg-gray-300 text-gray-600'}
                `}>
                  {index < currentStep ? <Check size={16} /> : index + 1}
                </div>
                {index < totalSteps - 1 && (
                  <div className={`h-0.5 w-8 mx-1 ${index < currentStep ? 'bg-green-500' : 'bg-gray-300'}`} />
                )}
              </div>
            ))}
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="pt-6">
        <form onSubmit={handleSubmit}>
          {/* Render current step content */}
          <div className="space-y-6 min-h-[200px]">
            {stepConfig.render && typeof stepConfig.render === 'function' 
              ? stepConfig.render({ formData, onFormDataChange, errors })
              : <p className="text-gray-500">No content for this step</p>
            }
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
                  onClick={goToPreviousStep}
                  className="flex items-center gap-2"
                >
                  <ChevronLeft size={18} />
                  Previous
                </Button>
              )}
              
              {!isLastStep ? (
                <Button 
                  type="button" 
                  onClick={goToNextStep}
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
