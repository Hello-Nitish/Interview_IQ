import React from 'react';
import { Download, Award, Briefcase, CheckCircle2, XCircle, AlertTriangle, ArrowRight } from 'lucide-react';
import { StrategicFitReport } from '../types';
import { Badge } from '../components/Badge';
import { MetricCard } from '../components/MetricCard';

interface Step2FitReportProps {
  fitReport: StrategicFitReport | null;
  candidateName?: string;
  roleTitle?: string;
  onExportPdf: () => void;
  onNextStep: () => void;
}

export const Step2FitReport: React.FC<Step2FitReportProps> = ({
  fitReport,
  candidateName = 'Candidate',
  roleTitle = 'Target Role',
  onExportPdf,
  onNextStep,
}) => {
  if (!fitReport) {
    return (
      <div className="neuro-card p-12 text-center space-y-3">
        <p className="text-sm font-semibold text-muted">No Strategic Fit Report generated yet.</p>
        <p className="text-xs text-muted">Please complete Step 1 Onboarding first.</p>
      </div>
    );
  }

  const techRating = fitReport.technical_rating || { technical_match_pct: 0, mandatory_matched: 0, total_mandatory: 0 };
  const expRating = fitReport.experience_rating || { score_out_of_10: 0, tier_label: 'Entry' };
  const decision = fitReport.overall_fit_decision || 'CONDITIONAL';

  const decisionColor = {
    'STRONG HIRE': 'border-l-success bg-success-light/20 text-success-dark',
    'SHORTLIST': 'border-l-primary bg-primary-light/20 text-primary-dark',
    'CONDITIONAL': 'border-l-warning bg-warning-light/20 text-warning-dark',
    'REJECT': 'border-l-danger bg-danger-light/20 text-danger-dark',
  }[decision] || 'border-l-primary bg-primary-light/20 text-primary-dark';

  return (
    <div className="space-y-6">
      {/* Header & Export Action */}
      <div className="neuro-card p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Badge label="Fit Analytics" variant="primary" />
            <Badge label="Step 2 of 6" variant="slate" />
          </div>
          <h2 className="text-xl font-extrabold text-heading">
            Step 2: Strategic Role Fit & Requirements Matrix
          </h2>
          <p className="text-xs text-muted mt-1">
            Institutional placement evaluation for <strong className="text-heading">{candidateName}</strong> applying for <strong className="text-heading">{roleTitle}</strong>.
          </p>
        </div>

        <button
          onClick={onExportPdf}
          className="px-4 py-2.5 bg-primary hover:bg-primary-dark text-white rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-2 shadow-sm flex-shrink-0"
        >
          <Download size={15} /> Export Standalone Fit Report (PDF)
        </button>
      </div>

      {/* Metric Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <MetricCard
          label="Technical Match Score"
          value={`${techRating.technical_match_pct}%`}
          delta={`${techRating.mandatory_matched}/${techRating.total_mandatory} Mandatory`}
          icon={<Award size={18} />}
          variant={techRating.technical_match_pct >= 70 ? 'success' : 'warning'}
        />
        <MetricCard
          label="Experience Tier Rating"
          value={`${expRating.score_out_of_10}/10`}
          delta={expRating.tier_label}
          icon={<Briefcase size={18} />}
          variant="primary"
        />
        <div className={`neuro-card p-4 border-l-4 ${decisionColor} flex flex-col justify-between sm:col-span-2 lg:col-span-1`}>
          <div className="text-[10px] font-bold uppercase tracking-wider text-muted">
            Recruitment Decision
          </div>
          <div className="text-xl font-extrabold my-1">{decision}</div>
          <div className="text-[11px] text-muted truncate">
            {fitReport.governing_rule_citation || 'Standard Placement Threshold'}
          </div>
        </div>
      </div>

      {/* Decision Card & Justification */}
      <div className="neuro-card p-5 space-y-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-muted">
          Corporate Policy Decision Justification
        </h3>
        {fitReport.decision_rationale && fitReport.decision_rationale.length > 0 ? (
          <ul className="space-y-1.5 text-xs text-body">
            {fitReport.decision_rationale.map((r, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-primary mt-0.5">•</span>
                <span>{r}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-xs text-muted">Standard algorithmic alignment satisfied.</p>
        )}
      </div>

      {/* 4-Column Requirements Matrix */}
      <div className="neuro-card p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-extrabold text-heading">
            4-Column Candidate Evidence & Gap Matrix
          </h3>
          <span className="text-xs text-muted font-medium">
            {fitReport.requirements_matrix?.length ?? 0} requirements evaluated
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-border text-muted uppercase text-[10px] font-bold tracking-wider">
                <th className="py-2.5 px-3">Requirement</th>
                <th className="py-2.5 px-3">Category</th>
                <th className="py-2.5 px-3">Resume Evidence / Gap Findings</th>
                <th className="py-2.5 px-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {fitReport.requirements_matrix?.map((row, idx) => {
                const isMatched = row.status === 'MATCHED';
                const isGap = row.status === 'GAP';

                return (
                  <tr key={idx} className="hover:bg-inset/50 transition-colors">
                    <td className="py-3 px-3 font-bold text-heading whitespace-nowrap">
                      {row.requirement}
                    </td>
                    <td className="py-3 px-3 text-muted">{row.category}</td>
                    <td className="py-3 px-3">
                      {row.evidence_status?.startsWith('Present:') ? (
                        <span className="text-success-dark font-medium flex items-center gap-1.5">
                          <CheckCircle2 size={13} className="text-success flex-shrink-0" />
                          {row.evidence_status}
                        </span>
                      ) : row.evidence_status?.startsWith('Missing:') ? (
                        <span className="text-danger-dark font-medium flex items-center gap-1.5">
                          <XCircle size={13} className="text-danger flex-shrink-0" />
                          {row.evidence_status}
                        </span>
                      ) : (
                        <span>{row.evidence_status || 'Under review'}</span>
                      )}
                    </td>
                    <td className="py-3 px-3">
                      <Badge
                        label={row.status}
                        variant={isMatched ? 'success' : isGap ? 'danger' : 'warning'}
                      />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Navigation Footer */}
      <div className="flex justify-end">
        <button
          onClick={onNextStep}
          className="px-6 py-3 bg-primary hover:bg-primary-dark text-white rounded-xl text-xs font-bold transition-all flex items-center gap-2 shadow-sm"
        >
          <span>Proceed to Targeted Question Bank</span>
          <ArrowRight size={15} />
        </button>
      </div>
    </div>
  );
};
