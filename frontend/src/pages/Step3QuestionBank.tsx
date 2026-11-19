import React, { useState } from 'react';
import { HelpCircle, Filter, CheckCircle, AlertTriangle, ArrowRight, ChevronDown, ChevronUp } from 'lucide-react';
import { QuestionBank, QuestionBankItem } from '../types';
import { Badge } from '../components/Badge';

interface Step3QuestionBankProps {
  questionBank: QuestionBank | null;
  onNextStep: () => void;
}

const CATEGORIES = [
  'All',
  'Technical Deep-Dive',
  'Problem Solving',
  'Behavioral STAR',
  'Resume Challenge',
  'Gap Mitigation',
];

export const Step3QuestionBank: React.FC<Step3QuestionBankProps> = ({
  questionBank,
  onNextStep,
}) => {
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (!questionBank || !questionBank.questions) {
    return (
      <div className="neuro-card p-12 text-center space-y-3">
        <p className="text-sm font-semibold text-muted">No Question Bank generated yet.</p>
        <p className="text-xs text-muted">Please complete Step 1 and Step 2 first.</p>
      </div>
    );
  }

  const checklist = questionBank.topic_checklist || [];
  const questions = questionBank.questions || [];

  const filteredQuestions =
    selectedCategory === 'All'
      ? questions
      : questions.filter((q) => q.category === selectedCategory);

  const toggleExpand = (id: string) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="neuro-card p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Badge label="Curated Interview Bank" variant="primary" />
            <Badge label="Step 3 of 6" variant="slate" />
          </div>
          <h2 className="text-xl font-extrabold text-heading">
            Step 3: 100% Checklist-Covered Question Bank
          </h2>
          <p className="text-xs text-muted mt-1">
            Questions synthesized across 5 analytical dimensions targeting candidate strengths and identified resume gaps.
          </p>
        </div>

        <button
          onClick={onNextStep}
          className="px-5 py-2.5 bg-primary hover:bg-primary-dark text-white rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-2 shadow-sm flex-shrink-0"
        >
          <span>Take Scored Online Test</span>
          <ArrowRight size={15} />
        </button>
      </div>

      {/* 100% Topic Checklist Pill Grid */}
      {checklist.length > 0 && (
        <div className="neuro-card p-5 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-muted">
              100% Job Description Topic Checklist Coverage
            </span>
            <span className="text-xs text-muted font-medium">
              {checklist.length} core topics evaluated
            </span>
          </div>

          <div className="flex flex-wrap gap-2 pt-1">
            {checklist.map((item, idx) => {
              const isGap = item.coverage_status === 'Gap';
              const isClaimed = item.coverage_status === 'Claimed';

              return (
                <span
                  key={idx}
                  className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${
                    isGap
                      ? 'bg-danger-light text-danger-dark border-danger/20'
                      : isClaimed
                      ? 'bg-success-light text-success-dark border-success/20'
                      : 'bg-inset text-body border-border'
                  }`}
                >
                  {isGap ? (
                    <AlertTriangle size={11} className="text-danger" />
                  ) : (
                    <CheckCircle size={11} className="text-success" />
                  )}
                  <span>{item.topic}</span>
                  <span className="text-[10px] opacity-75">({item.coverage_status})</span>
                </span>
              );
            })}
          </div>
        </div>
      )}

      {/* Category Filter Pills */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1">
        {CATEGORIES.map((cat) => {
          const isSelected = selectedCategory === cat;
          return (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3.5 py-1.5 rounded-full text-xs font-bold transition-all whitespace-nowrap ${
                isSelected
                  ? 'bg-primary text-white shadow-sm'
                  : 'bg-surface border border-border text-muted hover:text-heading hover:bg-inset'
              }`}
            >
              {cat}
            </button>
          );
        })}
      </div>

      {/* Question Accordion List */}
      <div className="space-y-3">
        {filteredQuestions.map((q, idx) => {
          const isExpanded = expandedId === q.id || expandedId === String(idx);
          const qId = q.id || String(idx);

          return (
            <div
              key={qId}
              className="neuro-card p-4 transition-all hover:border-primary/40 cursor-pointer"
              onClick={() => toggleExpand(qId)}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="space-y-1 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge label={q.category} variant="primary" />
                    <span className="text-[11px] font-bold text-muted uppercase">
                      Topic: {q.topic}
                    </span>
                    {q.difficulty && (
                      <Badge
                        label={q.difficulty}
                        variant={
                          q.difficulty === 'Hard'
                            ? 'danger'
                            : q.difficulty === 'Medium'
                            ? 'warning'
                            : 'success'
                        }
                      />
                    )}
                  </div>
                  <h4 className="text-sm font-bold text-heading pt-1 leading-snug">
                    {q.question}
                  </h4>
                </div>

                <button className="text-muted p-1 hover:text-primary transition-colors flex-shrink-0">
                  {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                </button>
              </div>

              {isExpanded && (
                <div className="mt-3 pt-3 border-t border-border space-y-2 text-xs">
                  <div className="bg-inset p-3 rounded-lg">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-muted block mb-1">
                      Expected Signal & Evaluation Rubric:
                    </span>
                    <p className="text-body leading-relaxed">{q.expected_signal}</p>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Proceed */}
      <div className="flex justify-end pt-2">
        <button
          onClick={onNextStep}
          className="px-6 py-3 bg-primary hover:bg-primary-dark text-white rounded-xl text-xs font-bold transition-all flex items-center gap-2 shadow-sm"
        >
          <span>Continue to Scored Online Test & Voice Simulator</span>
          <ArrowRight size={15} />
        </button>
      </div>
    </div>
  );
};
