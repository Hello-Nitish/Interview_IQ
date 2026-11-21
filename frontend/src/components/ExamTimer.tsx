import React, { useState, useEffect } from 'react';
import { Clock, AlertTriangle, ShieldCheck } from 'lucide-react';

interface ExamTimerProps {
  initialMinutes?: number;
  onTimeExpired: () => void;
  onCheatingViolation?: (count: number) => void;
}

export const ExamTimer: React.FC<ExamTimerProps> = ({
  initialMinutes = 30,
  onTimeExpired,
  onCheatingViolation,
}) => {
  const [secondsRemaining, setSecondsRemaining] = useState(initialMinutes * 60);
  const [blurViolations, setBlurViolations] = useState(0);

  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        setBlurViolations((prev) => {
          const updated = prev + 1;
          if (onCheatingViolation) onCheatingViolation(updated);
          return updated;
        });
      }
    };

    window.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('blur', handleVisibilityChange);

    return () => {
      window.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('blur', handleVisibilityChange);
    };
  }, [onCheatingViolation]);

  useEffect(() => {
    if (secondsRemaining <= 0) {
      onTimeExpired();
      return;
    }

    const interval = setInterval(() => {
      setSecondsRemaining((prev) => prev - 1);
    }, 1000);

    return () => clearInterval(interval);
  }, [secondsRemaining, onTimeExpired]);

  const minutes = Math.floor(secondsRemaining / 60);
  const seconds = secondsRemaining % 60;
  const isUrgent = secondsRemaining < 300; // < 5 mins

  return (
    <div className="flex items-center gap-3">
      {/* Timer Pill */}
      <div
        className={`flex items-center gap-2 px-3 py-1.5 rounded-xl border font-mono font-bold text-xs transition-colors ${
          isUrgent
            ? 'bg-danger-light text-danger-dark border-danger/40'
            : 'bg-inset text-heading border-border'
        }`}
      >
        <Clock size={14} className={isUrgent ? 'text-danger' : 'text-primary'} />
        <span className="num-tnum">
          {String(minutes).padStart(2, '0')}:{String(seconds).padStart(2, '0')}
        </span>
      </div>

      {/* Anti-Cheating Monitor */}
      <div
        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-semibold ${
          blurViolations > 0
            ? 'bg-warning-light text-warning-dark border-warning/30'
            : 'bg-inset text-muted border-border'
        }`}
      >
        {blurViolations > 0 ? (
          <>
            <AlertTriangle size={13} className="text-warning-dark" />
            <span>Tab Blur Violations: {blurViolations}</span>
          </>
        ) : (
          <>
            <ShieldCheck size={13} className="text-success" />
            <span>Anti-Cheat Proctored</span>
          </>
        )}
      </div>
    </div>
  );
};
