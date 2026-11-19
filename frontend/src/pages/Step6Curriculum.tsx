import React, { useState } from 'react';
import { BookOpen, CheckSquare, Square, ExternalLink, Calendar, Award, CheckCircle2 } from 'lucide-react';
import { MicroCurriculum } from '../types';
import { Badge } from '../components/Badge';
import { API } from '../services/api';

interface Step6CurriculumProps {
  curriculum: MicroCurriculum | null;
  sessionId: string;
}

export const Step6Curriculum: React.FC<Step6CurriculumProps> = ({
  curriculum,
  sessionId,
}) => {
  const [activeDayIdx, setActiveDayIdx] = useState(0);
  const [completedTaskIds, setCompletedTaskIds] = useState<Record<string, boolean>>({});

  if (!curriculum || !curriculum.days || curriculum.days.length === 0) {
    return (
      <div className="neuro-card p-12 text-center space-y-3">
        <p className="text-sm font-semibold text-muted">No Micro-Curriculum generated yet.</p>
        <p className="text-xs text-muted">Please complete Step 1 through Step 5 to generate your personalized 7-day plan.</p>
      </div>
    );
  }

  const days = curriculum.days;
  const currentDay = days[activeDayIdx] || days[0];

  const handleToggleTask = async (dayNum: number, taskId: string, currentVal: boolean) => {
    const newVal = !currentVal;
    setCompletedTaskIds((prev) => ({ ...prev, [taskId]: newVal }));

    try {
      await API.toggleCurriculumTask(sessionId, dayNum, taskId, newVal);
    } catch (err) {
      console.error('Failed to update task progress:', err);
    }
  };

  // Calculate total curriculum completion
  let totalTasks = 0;
  let finishedTasks = 0;
  days.forEach((d) => {
    d.tasks.forEach((t) => {
      totalTasks += 1;
      const isDone = completedTaskIds[t.id] !== undefined ? completedTaskIds[t.id] : t.completed;
      if (isDone) finishedTasks += 1;
    });
  });
  const overallPct = totalTasks > 0 ? Math.round((finishedTasks / totalTasks) * 100) : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="neuro-card p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Badge label="Continuous Placement Preparation" variant="primary" />
            <Badge label="Step 6 of 6" variant="slate" />
          </div>
          <h2 className="text-xl font-extrabold text-heading">
            Step 6: Dynamic 7-Day Personalized Micro-Curriculum
          </h2>
          <p className="text-xs text-muted mt-1">
            Tailored study schedule based on diagnosed weaknesses with curated free courses, interactive checklists, and SQLite progress tracking.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="bg-inset px-4 py-2 rounded-xl border border-border text-xs font-bold text-heading">
            Progress: <span className="text-primary">{finishedTasks} / {totalTasks} Tasks</span> ({overallPct}%)
          </div>
        </div>
      </div>

      {/* Day Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1">
        {days.map((day, idx) => {
          const isSelected = activeDayIdx === idx;
          return (
            <button
              key={day.day_number}
              onClick={() => setActiveDayIdx(idx)}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all whitespace-nowrap flex items-center gap-2 ${
                isSelected
                  ? 'bg-primary text-white shadow-sm'
                  : 'bg-surface border border-border text-muted hover:text-heading hover:bg-inset'
              }`}
            >
              <Calendar size={13} />
              <span>Day {day.day_number}</span>
            </button>
          );
        })}
      </div>

      {/* Active Day Detail Card */}
      <div className="neuro-card p-6 space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-border">
          <div>
            <h3 className="text-base font-extrabold text-heading">
              Day {currentDay.day_number}: {currentDay.day_title}
            </h3>
            <p className="text-xs text-muted font-medium mt-0.5">
              Core Competency: <strong className="text-primary">{currentDay.core_competency}</strong>
            </p>
          </div>
          <Badge label={`${currentDay.tasks.length} Learning Blocks`} variant="primary" />
        </div>

        {/* Task List */}
        <div className="space-y-3">
          {currentDay.tasks.map((task) => {
            const isDone = completedTaskIds[task.id] !== undefined ? completedTaskIds[task.id] : task.completed;

            return (
              <div
                key={task.id}
                className={`p-4 rounded-xl border transition-all flex items-start gap-3.5 ${
                  isDone
                    ? 'bg-success-light/20 border-success/30'
                    : 'bg-surface hover:bg-inset/50 border-border'
                }`}
              >
                <button
                  onClick={() => handleToggleTask(currentDay.day_number, task.id, isDone)}
                  className="mt-0.5 text-primary hover:scale-110 transition-transform flex-shrink-0"
                >
                  {isDone ? (
                    <CheckSquare size={18} className="text-success" />
                  ) : (
                    <Square size={18} className="text-muted" />
                  )}
                </button>

                <div className="flex-1 space-y-1">
                  <div className="flex items-center justify-between gap-2">
                    <h4
                      className={`text-xs font-bold ${
                        isDone ? 'line-through text-muted' : 'text-heading'
                      }`}
                    >
                      {task.title}
                    </h4>
                    <span className="text-[10px] font-bold text-muted bg-inset px-2 py-0.5 rounded-md flex-shrink-0">
                      {task.estimated_minutes} mins
                    </span>
                  </div>

                  <p className="text-xs text-muted leading-relaxed">{task.description}</p>

                  {task.resource_link && (
                    <div className="pt-1.5">
                      <a
                        href={task.resource_link}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1.5 text-xs font-bold text-primary hover:underline"
                      >
                        <ExternalLink size={12} />
                        <span>{task.resource_title || 'Free Course / Documentation Guide'}</span>
                      </a>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
