'use client';

import React, { useState } from 'react';
import { Terminal, ListOrdered, BookOpen } from 'lucide-react';
import { InvestigationState } from '../types';
import { ToolActivityFeed } from './ToolActivityFeed';
import { PlanChecklist } from './PlanChecklist';
import { EvidencePanel } from './EvidencePanel';

interface DetailsPanelProps {
  state: InvestigationState;
}

type TabId = 'tools' | 'plan' | 'evidence';

function getStatusBadge(s: string) {
  switch (s) {
    case 'RUNNING':
      return 'bg-blue-50 text-blue-700 border-blue-200';
    case 'PAUSED':
      return 'bg-amber-50 text-amber-700 border-amber-200';
    case 'COMPLETED':
    case 'SUFFICIENT':
      return 'bg-emerald-50 text-emerald-700 border-emerald-200';
    case 'PARTIAL':
      return 'bg-yellow-50 text-yellow-800 border-yellow-200';
    case 'FAILED':
      return 'bg-red-50 text-red-700 border-red-200';
    default:
      return 'bg-slate-100 text-slate-600 border-slate-200';
  }
}

export const DetailsPanel: React.FC<DetailsPanelProps> = ({ state }) => {
  const [tab, setTab] = useState<TabId>('tools');

  const tabs: { id: TabId; label: string; icon: React.ReactNode; count?: number }[] = [
    { id: 'tools', label: 'Tools', icon: <Terminal className="w-3.5 h-3.5" />, count: state.toolCalls.length },
    { id: 'plan', label: 'Plan', icon: <ListOrdered className="w-3.5 h-3.5" />, count: state.plan.length },
    {
      id: 'evidence',
      label: 'Evidence',
      icon: <BookOpen className="w-3.5 h-3.5" />,
      count: state.evidenceStore.length,
    },
  ];

  return (
    <div className="h-full flex flex-col min-h-0 bg-white border-l border-slate-200">
      {/* Panel Sub-header with Trace label & Status badge */}
      <div className="flex items-center justify-between border-b border-slate-200 px-3 py-2 bg-slate-50">
        <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-slate-700">
          Trace & Evidence
        </span>
        {state.status && state.status !== 'IDLE' && (
          <span
            className={`text-[10px] font-mono font-semibold px-2 py-0.5 uppercase tracking-wider border rounded-none ${getStatusBadge(
              state.status
            )}`}
          >
            {state.status}
          </span>
        )}
      </div>

      <div className="flex border-b border-slate-200 shrink-0">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`flex-1 flex items-center justify-center gap-1.5 px-2 py-2 text-[11px] font-mono font-semibold uppercase tracking-wider ${
              tab === t.id
                ? 'text-slate-900 border-b-2 border-slate-900 bg-white'
                : 'text-slate-500 hover:text-slate-800 hover:bg-slate-50'
            }`}
          >
            {t.icon}
            {t.label}
            {typeof t.count === 'number' && t.count > 0 && (
              <span className="text-[10px] font-normal text-slate-500">{t.count}</span>
            )}
          </button>
        ))}
      </div>
      <div className="flex-1 min-h-0 overflow-hidden [&>div]:h-full [&>div]:border-0 [&>div]:shadow-none [&>div]:rounded-none">
        {tab === 'tools' && (
          <ToolActivityFeed toolCalls={state.toolCalls} reflections={state.reflections} />
        )}
        {tab === 'plan' && <PlanChecklist plan={state.plan} planVersion={state.plan_version} />}
        {tab === 'evidence' && (
          <EvidencePanel evidenceStore={state.evidenceStore} findings={state.findings} />
        )}
      </div>
    </div>
  );
};
