'use client';

import React from 'react';
import { InvestigationState } from '../types';

interface DetailsPanelProps {
  state: InvestigationState;
}

export const DetailsPanel: React.FC<DetailsPanelProps> = () => {
  return (
    <div className="h-full flex flex-col min-h-0 bg-white border-l border-slate-200" />
  );
};


