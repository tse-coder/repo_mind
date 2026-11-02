'use client';

import React, { useState } from 'react';
import { Terminal, ChevronDown, ChevronRight, CheckCircle2, XCircle, AlertCircle, ShieldAlert, Sparkles } from 'lucide-react';
import { ToolCallItem, ReflectionItem } from '../types';

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
          <span className="flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <CheckCircle2 className="w-3 h-3" /> SUCCESS
          </span>
        );
      case 'ERROR':
        return (
          <span className="flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/30">
            <XCircle className="w-3 h-3" /> ERROR
          </span>
        );
      case 'POLICY_DENIED':
        return (
          <span className="flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded bg-purple-500/10 text-purple-300 border border-purple-500/30">
            <ShieldAlert className="w-3 h-3" /> POLICY DENIED
          </span>
        );
      case 'TIMEOUT':
        return (
          <span className="flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30">
            <AlertCircle className="w-3 h-3" /> TIMEOUT
          </span>
        );
      default:
        return (
          <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-gray-800 text-gray-400 border border-gray-700">
            PENDING
          </span>
        );
    }
  };

  return (
    <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-4 flex flex-col h-full shadow-lg">
      <div className="flex items-center justify-between pb-3 border-b border-gray-800 mb-3">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-blue-400" />
          <h2 className="text-xs font-bold uppercase tracking-wider text-gray-200">
            Tool Execution & Activity Feed
          </h2>
        </div>
        <span className="text-xs font-mono text-gray-400">
          {toolCalls.length} actions executed
        </span>
      </div>

      {toolCalls.length === 0 && reflections.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center text-center p-6 text-gray-500 text-xs">
          <Terminal className="w-8 h-8 mb-2 stroke-1 text-gray-600" />
          <span>No tools dispatched yet. Activity and outputs will stream here in real time.</span>
        </div>
      ) : (
        <div className="space-y-3 overflow-y-auto max-h-[500px] pr-1">
          {/* Interleave or show tool calls */}
          {toolCalls.map((tc, idx) => {
            const isExpanded = expandedItems[tc.id] ?? (idx === toolCalls.length - 1);
            return (
              <div
                key={tc.id}
                className="rounded-lg border border-gray-800 bg-[#090d16] overflow-hidden transition-all"
              >
                {/* Header */}
                <button
                  type="button"
                  onClick={() => toggleExpand(tc.id)}
                  className="w-full text-left p-3 flex items-center justify-between hover:bg-gray-850 transition"
                >
                  <div className="flex items-center gap-2 min-w-0">
                    {isExpanded ? (
                      <ChevronDown className="w-4 h-4 text-gray-400 shrink-0" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-gray-400 shrink-0" />
                    )}
                    <span className="text-xs font-mono font-bold text-blue-400">
                      {tc.tool}
                    </span>
                    <span className="text-xs text-gray-400 truncate max-w-[260px] sm:max-w-[340px]">
                      {tc.rationale}
                    </span>
                  </div>
                  <div>{getToolStatusBadge(tc.status)}</div>
                </button>

                {/* Collapsible Details */}
                {isExpanded && (
                  <div className="p-3 border-t border-gray-800/80 bg-black/40 space-y-2 text-xs">
                    {/* Rationale */}
                    {tc.rationale && (
                      <div>
                        <span className="text-gray-500 font-semibold block text-[11px] mb-0.5">
                          Rationale:
                        </span>
                        <p className="text-gray-300 italic">{tc.rationale}</p>
                      </div>
                    )}

                    {/* Arguments */}
                    {tc.arguments && Object.keys(tc.arguments).length > 0 && (
                      <div>
                        <span className="text-gray-500 font-semibold block text-[11px] mb-0.5">
                          Parameters:
                        </span>
                        <pre className="p-2 rounded bg-[#090d16] border border-gray-800 text-[11px] font-mono text-gray-300 overflow-x-auto">
                          {JSON.stringify(tc.arguments, null, 2)}
                        </pre>
                      </div>
                    )}

                    {/* Output / Summary */}
                    {tc.summary && (
                      <div>
                        <span className="text-gray-500 font-semibold block text-[11px] mb-0.5">
                          Output Snippet:
                        </span>
                        <pre className="p-2.5 rounded bg-[#090d16] border border-gray-800 text-[11px] font-mono text-gray-300 overflow-x-auto max-h-48 whitespace-pre-wrap">
                          {tc.summary}
                        </pre>
                      </div>
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
              className="p-3 rounded-lg border border-amber-500/30 bg-amber-500/5 space-y-1.5 text-xs"
            >
              <div className="flex items-center gap-1.5 text-amber-400 font-semibold text-xs">
                <Sparkles className="w-3.5 h-3.5" />
                <span>Reflexion Diagnosis</span>
              </div>
              <p className="text-gray-300 text-xs">
                <strong className="text-gray-400">Trigger:</strong> {ref.trigger}
              </p>
              <p className="text-gray-300 text-xs">
                <strong className="text-gray-400">Diagnosis:</strong> {ref.diagnosis}
              </p>
              <p className="text-emerald-300 text-xs">
                <strong className="text-emerald-400">Adjustment:</strong> {ref.next_approach}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

