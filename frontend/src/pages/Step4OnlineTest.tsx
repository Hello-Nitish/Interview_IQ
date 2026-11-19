import React, { useState } from 'react';
import { Award, CheckCircle2, XCircle, ArrowRight, RefreshCw, Send, AlertCircle } from 'lucide-react';
import { MCQQuestion } from '../types';
import { Badge } from '../components/Badge';
import { ExamTimer } from '../components/ExamTimer';
import { AudioRecorder } from '../components/AudioRecorder';

interface Step4OnlineTestProps {
  onlineTest: { questions: MCQQuestion[]; total_questions: number } | null;
  onSubmitTest: (userAnswers: Record<string, string>) => Promise<void>;
  isSubmitting: boolean;
  onNextStep: () => void;
  hasResults: boolean;
}

export const Step4OnlineTest: React.FC<Step4OnlineTestProps> = ({
  onlineTest,
  onSubmitTest,
  isSubmitting,
  onNextStep,
  hasResults,
}) => {
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [voiceTranscripts, setVoiceTranscripts] = useState<Record<string, string>>({});

  if (!onlineTest || !onlineTest.questions || onlineTest.questions.length === 0) {
    return (
      <div className="neuro-card p-12 text-center space-y-3">
        <p className="text-sm font-semibold text-muted">No Online Test generated yet.</p>
        <p className="text-xs text-muted">Please complete Step 1 through Step 3 first.</p>
      </div>
    );
  }

  const questions = onlineTest.questions;
  const answeredCount = Object.keys(answers).length;
  const progressPct = Math.round((answeredCount / questions.length) * 100);

  const handleSelectOption = (qId: string | number, optKey: string) => {
    setAnswers((prev) => ({ ...prev, [String(qId)]: optKey }));
  };

  const handleVoiceAnswer = (qId: string | number, result: any) => {
    setVoiceTranscripts((prev) => ({ ...prev, [String(qId)]: result.transcript }));
  };

  const handleSubmit = async () => {
    if (answeredCount < questions.length) {
      const confirmSubmit = window.confirm(
        `You have answered ${answeredCount} of ${questions.length} questions. Are you sure you want to submit?`
      );
      if (!confirmSubmit) return;
    }
    await onSubmitTest(answers);
  };

  return (
    <div className="space-y-6">
      {/* Header & Proctor Bar */}
      <div className="neuro-card p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Badge label="Timed Assessment" variant="primary" />
            <Badge label="Step 4 of 6" variant="slate" />
          </div>
          <h2 className="text-xl font-extrabold text-heading">
            Step 4: Scored Online Examination & Voice Simulator
          </h2>
          <p className="text-xs text-muted mt-1">
            {questions.length} Multiple Choice Questions covering 100% of the Job Description topic checklist.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <ExamTimer
            initialMinutes={30}
            onTimeExpired={handleSubmit}
            onCheatingViolation={(count) => console.warn(`Proctor blur violation: ${count}`)}
          />
        </div>
      </div>

      {/* Progress Bar Strip */}
      <div className="neuro-card p-4 space-y-2">
        <div className="flex justify-between text-xs font-bold text-muted">
          <span>
            Completion: {answeredCount} / {questions.length} Questions Answered
          </span>
          <span className="text-primary">{progressPct}%</span>
        </div>
        <div className="w-full h-2 rounded-full bg-inset overflow-hidden">
          <div
            className="h-full bg-primary transition-all duration-300"
            style={{ width: `${progressPct}%` }}
          />
        </div>
      </div>

      {/* Questions List */}
      <div className="space-y-4">
        {questions.map((q, idx) => {
          const qId = String(q.id || idx);
          const selectedKey = answers[qId];

          return (
            <div key={qId} className="neuro-card p-5 space-y-4">
              <div className="flex items-start justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="w-6 h-6 rounded-lg bg-inset border border-border flex items-center justify-center text-xs font-bold text-heading">
                      {idx + 1}
                    </span>
                    <Badge label={q.topic} variant="slate" />
                  </div>
                  <h4 className="text-sm font-bold text-heading pt-1 leading-relaxed">
                    {q.question}
                  </h4>
                </div>
              </div>

              {/* Options Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-1">
                {q.options.map((opt) => {
                  const isSelected = selectedKey === opt.key;
                  return (
                    <button
                      key={opt.key}
                      onClick={() => handleSelectOption(qId, opt.key)}
                      className={`p-3 rounded-xl border text-left text-xs font-medium transition-all flex items-start gap-3 ${
                        isSelected
                          ? 'bg-primary text-white border-primary shadow-sm'
                          : 'bg-surface hover:bg-inset border-border text-heading'
                      }`}
                    >
                      <span
                        className={`w-5 h-5 rounded-md flex items-center justify-center text-xs font-bold flex-shrink-0 ${
                          isSelected ? 'bg-white text-primary' : 'bg-inset text-muted'
                        }`}
                      >
                        {opt.key}
                      </span>
                      <span className="leading-snug">{opt.text}</span>
                    </button>
                  );
                })}
              </div>

              {/* Optional Voice Simulation for Question 1 & Question 5 */}
              {(idx === 0 || idx === 4) && (
                <div className="pt-2">
                  <AudioRecorder
                    questionText={q.question}
                    onTranscriptionComplete={(res) => handleVoiceAnswer(qId, res)}
                  />
                  {voiceTranscripts[qId] && (
                    <div className="mt-2 text-xs text-success font-medium flex items-center gap-1.5">
                      <CheckCircle2 size={13} /> Recorded oral rationale saved.
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Submission Actions */}
      <div className="neuro-card p-4 flex flex-col sm:flex-row items-center justify-between gap-4 bg-surface">
        <div className="text-xs text-muted font-medium">
          Answered <strong className="text-heading">{answeredCount}</strong> of{' '}
          <strong className="text-heading">{questions.length}</strong> questions
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="px-6 py-3 bg-primary hover:bg-primary-dark text-white rounded-xl text-xs font-bold transition-all flex items-center gap-2 shadow-glow disabled:opacity-50"
          >
            {isSubmitting ? (
              <>
                <RefreshCw size={14} className="animate-spin" /> Scoring Examination...
              </>
            ) : (
              <>
                <Send size={14} /> Submit & Evaluate Online Test
              </>
            )}
          </button>

          {hasResults && (
            <button
              onClick={onNextStep}
              className="px-5 py-3 bg-success hover:bg-success-dark text-white rounded-xl text-xs font-bold transition-all flex items-center gap-1.5"
            >
              <span>View Diagnostics</span>
              <ArrowRight size={14} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
