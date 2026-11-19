import React from 'react';
import { Download, Award, AlertTriangle, CheckCircle2, XCircle, ArrowRight, BookOpen, Clock } from 'lucide-react';
import { FeedbackDiagnostics, TestScoreResult } from '../types';
import { Badge } from '../components/Badge';
import { MetricCard } from '../components/MetricCard';

interface Step5ResultsProps {
  feedback: FeedbackDiagnostics | null;
  testResults: TestScoreResult | null;
  candidateName?: string;
  roleTitle?: string;
  onExportDossierPdf: () => void;
  onNextStep: () => void;
}

export const Step5Results: React.FC<Step5ResultsProps> = ({
  feedback,
  testResults,
  candidateName = 'Candidate',
  roleTitle = 'Target Role',
  onExportDossierPdf,
  onNextStep,
}) => {
  if (!feedback && !testResults) {
    return (
      <div className="neuro-card p-12 text-center space-y-3">
        <p className="text-sm font-semibold text-muted">No Diagnostic Results generated yet.</p>
        <p className="text-xs text-muted">Please complete and submit the Online Test in Step 4.</p>
      </div>
    );
  }

  const compositePct = feedback?.composite_readiness_pct ?? testResults?.percentage ?? 0;
  const structFit = feedback?.structural_fit_score ?? 0;
  const empTest = feedback?.empirical_test_score ?? testResults?.percentage ?? 0;
  const verdict = feedback?.overall_verdict || (compositePct >= 70 ? 'Recommended for Interview' : 'Requires Preparation');

  return (
    <div className="space-y-6">
      {/* Header & Export Action */}
      <div className="neuro-card p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Badge label="Unified Placement Diagnostics" variant="primary" />
            <Badge label="Step 5 of 6" variant="slate" />
          </div>
          <h2 className="text-xl font-extrabold text-heading">
            Step 5: Composite Readiness & Diagnostic Matrix
          </h2>
          <p className="text-xs text-muted mt-1">
            Synthesized evaluation fusing 45% structural resume fit and 55% empirical examination performance.
          </p>
        </div>

        <button
          onClick={onExportDossierPdf}
          className="px-4 py-2.5 bg-primary hover:bg-primary-dark text-white rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-2 shadow-sm flex-shrink-0"
        >
          <Download size={15} /> Export Complete Dossier (PDF)
        </button>
      </div>

      {/* 4-Metric Deck */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Composite Readiness"
          value={`${compositePct}%`}
          delta="45% Fit + 55% Test"
          icon={<Award size={18} />}
          variant={compositePct >= 70 ? 'success' : 'warning'}
        />
        <MetricCard
          label="Structural Fit Score"
          value={`${structFit}%`}
          delta="Resume vs JD"
          icon={<Award size={18} />}
          variant="primary"
        />
        <MetricCard
          label="Empirical Test Score"
          value={`${empTest}%`}
          delta={testResults ? `${testResults.total_score}/${testResults.max_score} MCQs` : ''}
          icon={<Award size={18} />}
          variant={empTest >= 70 ? 'success' : 'danger'}
        />
        <div className="neuro-card p-4 border-l-4 border-l-primary flex flex-col justify-between">
          <div className="text-[10px] font-bold uppercase tracking-wider text-muted">
            Diagnostic Verdict
          </div>
          <div className="text-sm font-extrabold text-heading my-1">{verdict}</div>
          <div className="text-[11px] text-muted">Automated Placement Verdict</div>
        </div>
      </div>

      {/* Prioritized Weakness / Dual-Gap Alert */}
      {feedback?.prioritized_topics_for_next_round &&
        feedback.prioritized_topics_for_next_round.length > 0 && (
          <div className="neuro-card p-4 border-l-4 border-l-danger bg-danger-light/20 space-y-2">
            <div className="flex items-center gap-2 text-danger-dark font-extrabold text-xs uppercase tracking-wider">
              <AlertTriangle size={15} /> 🚨 High Priority Focus Topics (Dual Weakness Diagnosed)
            </div>
            <p className="text-xs text-muted">
              The following topics were identified as resume gaps AND showed sub-optimal performance in the online examination:
            </p>
            <div className="flex flex-wrap gap-2 pt-1">
              {feedback.prioritized_topics_for_next_round.map((t, idx) => (
                <span
                  key={idx}
                  className="px-2.5 py-1 rounded-full text-xs font-bold bg-danger text-white flex items-center gap-1 shadow-sm"
                >
                  {t}
                </span>
              ))}
            </div>
          </div>
        )}

      {/* Topic-Wise Accuracy Table */}
      {testResults?.topic_accuracies && testResults.topic_accuracies.length > 0 && (
        <div className="neuro-card p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-extrabold text-heading">
              Topic-Wise Examination Accuracy Breakdown
            </h3>
            <span className="text-xs text-muted font-medium">Empirical test telemetry</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-border text-muted uppercase text-[10px] font-bold tracking-wider">
                  <th className="py-2.5 px-3">Evaluation Topic</th>
                  <th className="py-2.5 px-3">Accuracy</th>
                  <th className="py-2.5 px-3">Score Breakdown</th>
                  <th className="py-2.5 px-3">Readiness Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {testResults.topic_accuracies.map((item, idx) => (
                  <tr key={idx} className="hover:bg-inset/50 transition-colors">
                    <td className="py-3 px-3 font-bold text-heading">{item.topic}</td>
                    <td className="py-3 px-3">
                      <div className="flex items-center gap-2">
                        <div className="w-24 h-2 rounded-full bg-inset overflow-hidden">
                          <div
                            className={`h-full ${
                              item.pct >= 70 ? 'bg-success' : item.pct >= 50 ? 'bg-warning' : 'bg-danger'
                            }`}
                            style={{ width: `${item.pct}%` }}
                          />
                        </div>
                        <span className="font-bold text-heading">{item.pct}%</span>
                      </div>
                    </td>
                    <td className="py-3 px-3 text-muted">
                      {item.correct} / {item.total} correct
                    </td>
                    <td className="py-3 px-3">
                      <Badge
                        label={item.status}
                        variant={item.status === 'Strong' ? 'success' : item.status === 'Adequate' ? 'warning' : 'danger'}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 48-Hour Revision Roadmap */}
      {feedback?.revision_roadmap_48h && feedback.revision_roadmap_48h.length > 0 && (
        <div className="neuro-card p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-extrabold text-heading flex items-center gap-2">
              <Clock size={16} className="text-primary" /> 48-Hour Sprint Revision Roadmap
            </h3>
            <span className="text-xs text-muted font-medium">Prioritized candidate coaching</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {feedback.revision_roadmap_48h.map((block, idx) => (
              <div key={idx} className="neuro-inset p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-bold text-primary uppercase tracking-wide">
                    {block.hour_block}
                  </span>
                  <Badge label={block.focus_topic} variant="slate" />
                </div>
                <h4 className="text-xs font-bold text-heading">{block.action_item}</h4>
                <p className="text-xs text-muted leading-relaxed">{block.concrete_exercise}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Next Step */}
      <div className="flex justify-end pt-2">
        <button
          onClick={onNextStep}
          className="px-6 py-3 bg-primary hover:bg-primary-dark text-white rounded-xl text-xs font-bold transition-all flex items-center gap-2 shadow-sm"
        >
          <span>Unlock 7-Day Personalized Micro-Curriculum</span>
          <ArrowRight size={15} />
        </button>
      </div>
    </div>
  );
};
