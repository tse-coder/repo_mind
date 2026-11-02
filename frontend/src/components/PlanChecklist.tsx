'use client';

import React from 'react';
import { CheckCircle2, CircleDashed, Clock, AlertTriangle, RefreshCw, ListOrdered } from 'lucide-react';
import { PlanGoal } from '../types';

interface PlanChecklistProps {
  plan: PlanGoal[];
  planVersion: number;
}

export const PlanChecklist: React.FC<PlanChecklistProps> = ({ plan, planVersion }) => {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />;
      case 'IN_PROGRESS':
        return <CircleDashed className="w-3.5 h-3.5 text-blue-600 animate-spin shrink-0" />;
      case 'BLOCKED':
        return <AlertTriangle className="w-3.5 h-3.5 text-red-600 shrink-0" />;
      case 'PENDING':
      default:
        return <Clock className="w-3.5 h-3.5 text-slate-400 shrink-0" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return 'bg-emerald-50 text-emerald-700 border-emerald-300';
      case 'IN_PROGRESS':
        return 'bg-blue-50 text-blue-700 border-blue-300';
      case 'BLOCKED':
        return 'bg-red-50 text-red-700 border-red-300';
      case 'PENDING':
      default:
        return 'bg-slate-100 text-slate-600 border-slate-300';
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-none p-4 flex flex-col h-full shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-200 mb-3">
        <div className="flex items-center gap-2">
          <ListOrdered className="w-4 h-4 text-slate-700" />
          <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-800">
            Investigation Plan
          </h2>
        </div>
        <div className="flex items-center gap-1.5">
          {planVersion > 1 && (
            <span className="flex items-center gap-1 text-[10px] font-mono px-1.5 py-0.5 rounded-none bg-amber-50 text-amber-700 border border-amber-300">
              <RefreshCw className="w-2.5 h-2.5" /> v{planVersion}
            </span>
          )}
          <span className="text-[11px] font-mono px-2 py-0.5 rounded-none bg-slate-100 text-slate-700 border border-slate-300">
            v{planVersion}
          </span>
        </div>
      </div>

      {/* Checklist Items */}
      {plan.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center text-center p-6 text-slate-400 text-xs font-mono">
          <Clock className="w-6 h-6 mb-2 stroke-1 text-slate-300" />
          <span>No plan generated yet. Goals will appear upon execution.</span>
        </div>
      ) : (
        <div className="space-y-2 overflow-y-auto max-h-[380px] pr-1">
          {plan.map((goal, index) => (
            <div
              key={goal.id || index}
              className={`p-2.5 rounded-none border transition-all ${
                goal.status === 'IN_PROGRESS'
                  ? 'bg-blue-50/50 border-blue-400'
                  : goal.status === 'COMPLETED'
                  ? 'bg-emerald-50/30 border-emerald-300'
                  : 'bg-slate-50 border-slate-200'
              }`}
            >
              <div className="flex items-start gap-2">
                <div className="mt-0.5">{getStatusIcon(goal.status)}</div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-slate-800 leading-snug break-words">
                    {goal.description}
                  </p>
                  <div className="flex items-center gap-2 mt-1.5">
                    <span
                      className={`text-[9px] font-mono font-semibold px-1.5 py-0.2 rounded-none border uppercase tracking-wider ${getStatusBadge(
                        goal.status
                      )}`}
                    >
                      {goal.status}
                    </span>
                    {goal.evidence_slot && (
                      <span className="text-[10px] text-slate-500 font-mono">
                        slot: <span className="text-slate-800">{goal.evidence_slot}</span>
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
