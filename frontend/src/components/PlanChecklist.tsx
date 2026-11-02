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
        return <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />;
      case 'IN_PROGRESS':
        return <CircleDashed className="w-4 h-4 text-blue-400 animate-spin shrink-0" />;
      case 'BLOCKED':
        return <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />;
      case 'PENDING':
      default:
        return <Clock className="w-4 h-4 text-gray-500 shrink-0" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'IN_PROGRESS':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/30';
      case 'BLOCKED':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
      case 'PENDING':
      default:
        return 'bg-gray-800 text-gray-400 border-gray-700';
    }
  };

  return (
    <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-4 flex flex-col h-full shadow-lg">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-gray-800 mb-3">
        <div className="flex items-center gap-2">
          <ListOrdered className="w-4 h-4 text-blue-400" />
          <h2 className="text-xs font-bold uppercase tracking-wider text-gray-200">
            Investigation Plan
          </h2>
        </div>
        <div className="flex items-center gap-2">
          {planVersion > 1 && (
            <span className="flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <RefreshCw className="w-2.5 h-2.5 animate-spin" /> Replanned
            </span>
          )}
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-gray-800 text-gray-300 border border-gray-700">
            v{planVersion}
          </span>
        </div>
      </div>

      {/* Checklist Items */}
      {plan.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center text-center p-6 text-gray-500 text-xs">
          <Clock className="w-8 h-8 mb-2 stroke-1 text-gray-600" />
          <span>No plan generated yet. Start an investigation to observe sub-goals.</span>
        </div>
      ) : (
        <div className="space-y-2.5 overflow-y-auto max-h-[380px] pr-1">
          {plan.map((goal, index) => (
            <div
              key={goal.id || index}
              className={`p-3 rounded-lg border transition-all ${
                goal.status === 'IN_PROGRESS'
                  ? 'bg-blue-950/20 border-blue-500/40'
                  : goal.status === 'COMPLETED'
                  ? 'bg-emerald-950/10 border-emerald-900/30'
                  : 'bg-[#090d16]/70 border-gray-800/80'
              }`}
            >
              <div className="flex items-start gap-2.5">
                <div className="mt-0.5">{getStatusIcon(goal.status)}</div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-gray-200 leading-snug break-words">
                    {goal.description}
                  </p>
                  <div className="flex items-center gap-2 mt-2">
                    <span
                      className={`text-[10px] font-semibold px-2 py-0.5 rounded border uppercase tracking-wider ${getStatusBadge(
                        goal.status
                      )}`}
                    >
                      {goal.status}
                    </span>
                    {goal.evidence_slot && (
                      <span className="text-[10px] text-gray-400 font-mono">
                        slot: <span className="text-blue-300">{goal.evidence_slot}</span>
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

