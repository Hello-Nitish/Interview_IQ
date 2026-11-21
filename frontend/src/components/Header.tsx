import React from 'react';
import { Target, Cpu, Sparkles, RotateCcw } from 'lucide-react';
import { Badge } from './Badge';

interface HeaderProps {
  directmlInfo?: {
    directml_available: boolean;
    device_name: string;
  };
  activeModel?: string;
  onResetSession: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  directmlInfo,
  activeModel = 'gemini-2.5-flash',
  onResetSession,
}) => {
  return (
    <header className="bg-surface border-b border-border px-6 py-3 flex items-center justify-between sticky top-0 z-40 shadow-sm">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center text-white shadow-sm">
          <Target size={22} strokeWidth={2.5} />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-extrabold text-heading tracking-tight leading-none">
              InterviewIQ
            </h1>
            <span className="text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded bg-primary-light text-primary border border-primary/20">
              Desktop Pro
            </span>
          </div>
          <p className="text-xs text-muted font-medium mt-0.5">
            Don't Practice Questions. Experience the Assessment.
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* DirectML Hardware Acceleration Badge */}
        <div className="hidden md:flex items-center gap-1.5 px-3 py-1 rounded-full bg-inset border border-border text-xs font-semibold text-muted">
          <Cpu size={14} className="text-primary" />
          <span>
            {directmlInfo?.directml_available
              ? `${directmlInfo.device_name} (DirectML)`
              : 'Host CPU (DirectML Inactive)'}
          </span>
        </div>

        {/* Gemini Active Model */}
        <Badge
          label={activeModel}
          variant="primary"
          icon={<Sparkles size={12} />}
          className="hidden sm:inline-flex"
        />

        {/* Reset Session Button */}
        <button
          onClick={onResetSession}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-border hover:bg-inset text-xs font-bold text-muted hover:text-heading transition-colors"
          title="Reset current candidate session"
        >
          <RotateCcw size={14} />
          <span className="hidden sm:inline">New Session</span>
        </button>
      </div>
    </header>
  );
};
