import React, { useState } from 'react';
import {
  Key,
  Shield,
  Activity,
  Database,
  CheckCircle,
  AlertTriangle,
  ChevronRight,
  Zap,
} from 'lucide-react';
import { Badge } from './Badge';
import { TelemetryStats } from '../types';

interface SidebarProps {
  currentPage: string;
  onNavigate: (pageId: any) => void;
  apiKey: string;
  isKeyValid: boolean;
  onValidateKey: (key: string) => Promise<boolean>;
  telemetry: TelemetryStats | null;
  savedSessions: Array<any>;
  onLoadSession: (sessionId: string) => void;
}

const NAV_ITEMS = [
  { id: '01_upload', label: '1. Candidate Onboarding' },
  { id: '02_fit_report', label: '2. Strategic Fit Report' },
  { id: '03_question_bank', label: '3. Targeted Question Bank' },
  { id: '04_online_test', label: '4. Scored Online Test & Voice' },
  { id: '05_results', label: '5. Unified Diagnostics' },
  { id: '06_curriculum', label: '6. 7-Day Prep Curriculum' },
];

export const Sidebar: React.FC<SidebarProps> = ({
  currentPage,
  onNavigate,
  apiKey,
  isKeyValid,
  onValidateKey,
  telemetry,
  savedSessions,
  onLoadSession,
}) => {
  const [keyInput, setKeyInput] = useState(apiKey || '');
  const [isValidating, setIsValidating] = useState(false);
  const [keyError, setKeyError] = useState('');

  const handleKeySubmit = async () => {
    if (!keyInput.trim()) {
      setKeyError('Please enter an API key');
      return;
    }
    setIsValidating(true);
    setKeyError('');
    try {
      const ok = await onValidateKey(keyInput.trim());
      if (!ok) {
        setKeyError('Validation failed. Check your API key.');
      }
    } catch (e: any) {
      setKeyError(e.message || 'Validation error');
    } finally {
      setIsValidating(false);
    }
  };

  return (
    <aside className="w-72 bg-surface border-r border-border p-4 flex flex-col justify-between overflow-y-auto">
      <div className="space-y-6">
        {/* Navigation Menu */}
        <div>
          <div className="text-[11px] font-bold uppercase tracking-wider text-muted mb-2 px-2">
            Assessment Pipeline
          </div>
          <div className="space-y-1">
            {NAV_ITEMS.map((item) => {
              const isActive = currentPage === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onNavigate(item.id)}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-bold transition-all text-left ${
                    isActive
                      ? 'bg-primary text-white shadow-sm'
                      : 'text-heading hover:bg-inset hover:text-primary'
                  }`}
                >
                  <span className="truncate">{item.label}</span>
                  {isActive && <ChevronRight size={14} />}
                </button>
              );
            })}
          </div>
        </div>

        {/* API Key Gatekeeper Section */}
        <div className="pt-4 border-t border-border">
          <div className="flex items-center justify-between mb-2 px-1">
            <span className="text-[11px] font-bold uppercase tracking-wider text-muted flex items-center gap-1.5">
              <Key size={13} className="text-primary" /> Gemini API Key
            </span>
            {isKeyValid ? (
              <Badge label="Active" variant="success" icon={<CheckCircle size={10} />} />
            ) : (
              <Badge label="Required" variant="danger" icon={<AlertTriangle size={10} />} />
            )}
          </div>

          <div className="space-y-2">
            <input
              type="password"
              placeholder="Paste Google AI Studio key..."
              value={keyInput}
              onChange={(e) => setKeyInput(e.target.value)}
              className="w-full px-3 py-2 text-xs rounded-lg border border-border bg-canvas focus:outline-none focus:border-primary font-mono"
            />
            <button
              onClick={handleKeySubmit}
              disabled={isValidating}
              className="w-full py-2 bg-primary hover:bg-primary-dark disabled:opacity-50 text-white rounded-lg text-xs font-bold transition-colors"
            >
              {isValidating ? 'Validating Key...' : 'Activate API Key'}
            </button>
            {keyError && <p className="text-[11px] text-danger font-medium">{keyError}</p>}
          </div>
        </div>

        {/* Live API Quota & Telemetry Meter */}
        <div className="pt-4 border-t border-border">
          <div className="text-[11px] font-bold uppercase tracking-wider text-muted mb-2 px-1 flex items-center gap-1.5">
            <Activity size={13} className="text-primary" /> API Quota Meter
          </div>
          <div className="bg-inset p-3 rounded-xl border border-border space-y-2 text-xs">
            <div className="flex justify-between font-semibold">
              <span className="text-muted">Session Calls:</span>
              <span className="text-heading">{telemetry?.session_calls ?? 0}</span>
            </div>
            <div className="flex justify-between font-semibold">
              <span className="text-muted">Cache Hits:</span>
              <span className="text-success">{telemetry?.session_cache_hits ?? 0}</span>
            </div>
            <div className="flex justify-between font-semibold">
              <span className="text-muted">Peak RPM:</span>
              <span className="text-heading">{telemetry?.current_rpm ?? 0}/15</span>
            </div>
            <div className="text-[11px] font-bold text-success flex items-center gap-1 pt-1 border-t border-border/50">
              <Zap size={11} /> {telemetry?.cache_savings_pct ?? 0}% served at 0ms (0 tokens)
            </div>
          </div>
        </div>

        {/* SQLite Saved Sessions */}
        {savedSessions && savedSessions.length > 0 && (
          <div className="pt-4 border-t border-border">
            <div className="text-[11px] font-bold uppercase tracking-wider text-muted mb-2 px-1 flex items-center gap-1.5">
              <Database size={13} className="text-primary" /> Past Sessions
            </div>
            <select
              onChange={(e) => e.target.value && onLoadSession(e.target.value)}
              className="w-full text-xs px-2.5 py-2 rounded-lg border border-border bg-canvas text-heading font-medium focus:outline-none"
              defaultValue=""
            >
              <option value="" disabled>
                Load Saved Session...
              </option>
              {savedSessions.slice(0, 10).map((s) => (
                <option key={s.session_id} value={s.session_id}>
                  {s.candidate_name || 'Candidate'} (R{s.current_round || 1})
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Footer Attribution */}
      <div className="pt-4 border-t border-border text-[11px] text-muted text-center">
        <p className="font-semibold text-heading">InterviewIQ Native Desktop</p>
        <p className="mt-0.5">Developed by your frd Nitish and Jeevana</p>
      </div>
    </aside>
  );
};
