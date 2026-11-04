'use client';

import React from 'react';
import { InvestigationState } from '../types';
import { InvestigationTrace } from './InvestigationTrace';

interface DetailsPanelProps {
  state: InvestigationState;
}

export const DetailsPanel: React.FC<DetailsPanelProps> = ({ state }) => {
  return (
    <div className="h-full flex flex-col min-h-0 bg-white border-l border-slate-200">
      {/* Unified Step-by-Step Trace Timeline */}
      <div className="flex-1 min-h-0 overflow-hidden">
        <InvestigationTrace
          toolCalls={state.toolCalls}
          plan={state.plan}
          planVersion={state.plan_version}
          evidenceStore={state.evidenceStore}
          findings={state.findings}
          reflections={state.reflections}
        />
      </div>
    </div>
  );
};

