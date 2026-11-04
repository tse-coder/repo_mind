'use client';

import React, { useState } from 'react';
import { Terminal, ChevronDown, ChevronRight, CheckCircle2, XCircle, AlertCircle, ShieldAlert } from 'lucide-react';
import { ToolCallItem, ReflectionItem } from '../types';
import { ToolOutputViewer } from './ToolOutputViewer';

interface ToolActivityFeedProps {
  toolCalls: ToolCallItem[];
  reflections: ReflectionItem[];
}

export const ToolActivityFeed: React.FC<ToolActivityFeedProps> = ({ toolCalls, reflections }) => {
  const [expandedItems, setExpandedItems] = useState<Record<string, boolean>>({});

  const toggleExpand = (id: string) => {
    setExpandedItems((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const getToolStatusBadge = (status?: string) => {
    switch (status) {
      case 'SUCCESS':
        return (
          <span className="flex items-center gap-1 text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded-none bg-emerald-50 text-emerald-700 border border-emerald-300">
            <CheckCircle2 className="w-3 h-3 text-emerald-600" /> SUCCESS
          </span>
        );
      case 'ERROR':
        return (
          <span className="flex items-center gap-1 text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded-none bg-red-50 text-red-700 border border-red-300">
            <XCircle className="w-3 h-3 text-red-600" /> ERROR
          </span>
        );
      case 'POLICY_DENIED':
        return (
          <span className="flex items-center gap-1 text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded-none bg-purple-50 text-purple-700 border border-purple-300">
            <ShieldAlert className="w-3 h-3 text-purple-600" /> BLOCKED
          </span>
        );
      case 'TIMEOUT':
        return (
          <span className="flex items-center gap-1 text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded-none bg-amber-50 text-amber-700 border border-amber-300">
            <AlertCircle className="w-3 h-3 text-amber-600" /> TIMEOUT
          </span>
        );
      default:
        return (
          <span className="text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded-none bg-slate-100 text-slate-600 border border-slate-300">
            PENDING
          </span>
        );
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-none p-4 flex flex-col h-full shadow-sm">
      <div className="flex items-center justify-between pb-3 border-b border-slate-200 mb-3">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-slate-700" />
          <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-800">
            Tool Activity Feed
          </h2>
        </div>
        <span className="text-xs font-mono text-slate-500">
          {toolCalls.length} executed
        </span>
      </div>

      {toolCalls.length === 0 && reflections.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center text-center p-6 text-slate-400 text-xs font-mono">
          <Terminal className="w-6 h-6 mb-2 stroke-1 text-slate-300" />
          <span>No tools executed yet. Activity logs stream here.</span>
        </div>
      ) : (
        <div className="space-y-2.5 overflow-y-auto flex-1 min-h-0 pr-1">
          {toolCalls.map((tc, idx) => {
            const isExpanded = expandedItems[tc.id] ?? (idx === toolCalls.length - 1);
            return (
              <div
                key={tc.id}
                className="rounded-none border border-slate-200 bg-slate-50 overflow-hidden transition-all"
              >
                {/* Header */}
                <button
                  type="button"
                  onClick={() => toggleExpand(tc.id)}
                  className="w-full text-left p-2.5 flex items-center justify-between hover:bg-slate-100 transition"
                >
                  <div className="flex items-center gap-2 min-w-0">
                    {isExpanded ? (
                      <ChevronDown className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                    ) : (
                      <ChevronRight className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                    )}
                    <span className="text-xs font-mono font-bold text-slate-900">
                      {tc.tool}
                    </span>
                    <span className="text-xs text-slate-600 truncate max-w-[260px] sm:max-w-[340px]">
                      {tc.rationale}
                    </span>
                  </div>
                  <div>{getToolStatusBadge(tc.status)}</div>
                </button>

                {/* Collapsible Details */}
                {isExpanded && (
                  <div className="p-3 border-t border-slate-200 bg-white space-y-2 text-xs">
                    {/* Rationale */}
                    {tc.rationale && (
                      <div>
                        <span className="text-slate-500 font-mono text-[11px] block mb-0.5">
                          Rationale:
                        </span>
                        <p className="text-slate-800 text-xs">{tc.rationale}</p>
                      </div>
                    )}

                    {/* Arguments */}
                    {tc.arguments && Object.keys(tc.arguments).length > 0 && (
                      <div>
                        <span className="text-slate-500 font-mono text-[11px] block mb-0.5">
                          Arguments:
                        </span>
                        <pre className="p-2 rounded-none bg-slate-100 border border-slate-200 text-[11px] font-mono text-slate-800 overflow-x-auto">
                          {JSON.stringify(tc.arguments, null, 2)}
                        </pre>
                      </div>
                    )}

                    {/* Output / Summary */}
                    {tc.summary && (
                      <ToolOutputViewer tool={tc.tool} summary={tc.summary} />
                    )}
                  </div>
                )}
              </div>
            );
          })}

          {/* Reflexion self-critiques */}
          {reflections.map((ref) => (
            <div
              key={ref.id}
              className="p-3 rounded-none border border-amber-300 bg-amber-50 space-y-1 text-xs font-mono"
            >
              <div className="flex items-center gap-1.5 text-amber-800 font-bold text-xs">
                <AlertCircle className="w-3.5 h-3.5" />
                <span>Reflexion Diagnosis</span>
              </div>
              <p className="text-slate-700 text-xs">
                <span className="text-slate-500">Trigger:</span> {ref.trigger}
              </p>
              <p className="text-slate-700 text-xs">
                <span className="text-slate-500">Diagnosis:</span> {ref.diagnosis}
              </p>
              <p className="text-emerald-800 text-xs font-medium">
                <span className="text-slate-500">Adjustment:</span> {ref.next_approach}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
