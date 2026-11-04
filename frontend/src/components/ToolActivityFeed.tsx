'use client';

import React, { useState } from 'react';
import { ChevronDown, ChevronRight, CheckCircle2, XCircle, AlertCircle, ShieldAlert } from 'lucide-react';
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
          <span title="Success" className="flex items-center">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          </span>
        );
      case 'ERROR':
        return (
          <span title="Error" className="flex items-center">
            <XCircle className="w-4 h-4 text-red-600 shrink-0" />
          </span>
        );
      case 'POLICY_DENIED':
        return (
          <span title="Blocked" className="flex items-center">
            <ShieldAlert className="w-4 h-4 text-purple-600 shrink-0" />
          </span>
        );
      case 'TIMEOUT':
        return (
          <span title="Timeout" className="flex items-center">
            <AlertCircle className="w-4 h-4 text-amber-600 shrink-0" />
          </span>
        );
      default:
        return (
          <span title="Pending" className="flex items-center">
            <span className="w-2.5 h-2.5 rounded-full bg-slate-300 animate-pulse inline-block" />
          </span>
        );
    }
  };

  return (
    <div className="p-3 flex flex-col h-full bg-white overflow-hidden">
      {toolCalls.length === 0 && reflections.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center text-center p-6 text-slate-400 text-xs font-mono">
          <span>No tools executed yet. Activity logs stream here.</span>
        </div>
      ) : (
        <div className="space-y-2 overflow-y-auto flex-1 min-h-0 pr-1">
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
                    <span className="text-xs font-mono font-bold text-slate-900 truncate">
                      {tc.tool}
                    </span>
                  </div>
                  <div className="shrink-0 ml-2">{getToolStatusBadge(tc.status)}</div>
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

          {/* Reflections */}
          {reflections.map((ref) => (
            <div
              key={ref.id}
              className="p-3 rounded-none bg-amber-50 border border-amber-200 space-y-1 text-xs"
            >
              <div className="flex items-center gap-1.5 font-mono font-bold text-amber-800">
                <AlertCircle className="w-3.5 h-3.5" />
                <span>Reflexion Diagnostic: {ref.trigger}</span>
              </div>
              <p className="text-amber-900 font-sans">
                <strong>Diagnosis:</strong> {ref.diagnosis}
              </p>
              <p className="text-amber-900 font-sans">
                <strong>Next Approach:</strong> {ref.next_approach}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
