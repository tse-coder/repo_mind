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
      <div className="flex border-b border-slate-200 shrink-0">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`flex-1 flex items-center justify-center gap-1.5 px-2 py-2.5 text-[11px] font-mono font-semibold uppercase tracking-wider ${
              tab === t.id
                ? 'text-slate-900 border-b-2 border-slate-900 bg-slate-50'
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
