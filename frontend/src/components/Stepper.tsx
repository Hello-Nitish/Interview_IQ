import React from 'react';
import { Check } from 'lucide-react';

interface StepperProps {
  currentStep: number; // 1 to 6
  onStepClick?: (stepNumber: number) => void;
}

const STEPS = [
  { num: 1, label: 'Onboarding', page: '01_upload' },
  { num: 2, label: 'Fit Report', page: '02_fit_report' },
  { num: 3, label: 'Question Bank', page: '03_question_bank' },
  { num: 4, label: 'Online Test', page: '04_online_test' },
  { num: 5, label: 'Diagnostics', page: '05_results' },
  { num: 6, label: 'Curriculum', page: '06_curriculum' },
];

export const Stepper: React.FC<StepperProps> = ({ currentStep, onStepClick }) => {
  return (
    <div className="ent-card px-4 py-3 mb-6 flex items-center justify-between overflow-x-auto gap-2">
      {STEPS.map((step, idx) => {
        const isCompleted = step.num < currentStep;
        const isActive = step.num === currentStep;

        return (
          <React.Fragment key={step.num}>
            <div
              onClick={() => onStepClick && onStepClick(step.num)}
              className={`flex items-center gap-2 cursor-pointer transition-all flex-shrink-0 ${
                isActive ? 'opacity-100' : isCompleted ? 'opacity-90' : 'opacity-60'
              }`}
            >
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                  isCompleted
                    ? 'bg-success text-white'
                    : isActive
                    ? 'bg-primary text-white shadow-sm ring-2 ring-primary/20'
                    : 'bg-inset text-muted border border-border'
                }`}
              >
                {isCompleted ? <Check size={14} strokeWidth={3} /> : step.num}
              </div>
              <span
                className={`text-xs font-bold whitespace-nowrap hidden sm:inline-block ${
                  isActive
                    ? 'text-primary'
                    : isCompleted
                    ? 'text-heading'
                    : 'text-muted'
                }`}
              >
                {step.label}
              </span>
            </div>

            {idx < STEPS.length - 1 && (
              <div
                className={`h-0.5 flex-1 min-w-3 sm:min-w-6 transition-all ${
                  isCompleted ? 'bg-success' : 'bg-border'
                }`}
              />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
};
