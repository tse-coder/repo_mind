'use client';

import React, { useState } from 'react';
import {
  ChevronDown,
  ChevronRight,
  CheckCircle2,
  XCircle,
  AlertCircle,
  ShieldAlert,
  CircleDashed,
  Clock,
  FileCode,
  Check,
  Copy,
  AlertTriangle,
  RefreshCw,
} from 'lucide-react';
import { ToolCallItem, PlanGoal, EvidenceItem, FindingItem, ReflectionItem } from '../types';
import { ToolOutputViewer } from './ToolOutputViewer';
import { MarkdownRenderer } from './MarkdownRenderer';

interface InvestigationTraceProps {
  toolCalls: ToolCallItem[];
  plan: PlanGoal[];
  planVersion: number;
  evidenceStore: EvidenceItem[];
  findings: FindingItem[];
  reflections: ReflectionItem[];
}

export const InvestigationTrace: React.FC<InvestigationTraceProps> = ({
  toolCalls,
  plan,
  planVersion,
  evidenceStore,
  findings,
  reflections,
}) => {
  const [expandedSteps, setExpandedSteps] = useState<Record<string, boolean>>({});
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const toggleStep = (id: string) => {
    setExpandedSteps((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const getToolStatusIcon = (status?: string) => {
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
            <span className="w-2.5 h-2.5 rounded-full bg-blue-500 animate-pulse inline-block" />
          </span>
        );
    }
  };

  const getConfidenceBadge = (confidence: string) => {
    switch (confidence) {
      case 'CONFIRMED':
        return 'bg-emerald-50 text-emerald-700 border-emerald-300';
      case 'INFERRED':
        return 'bg-amber-50 text-amber-700 border-amber-300';
      default:
        return 'bg-slate-100 text-slate-600 border-slate-300';
    }
  };

  return (
    <div className="flex flex-col h-full bg-white min-h-0 overflow-y-auto">
      {/* 1. Goals Summary (Compact Checklist) */}
      {plan.length > 0 && (
        <div className="m-2.5 p-3 rounded-xl border border-slate-200/80 bg-slate-50/70 space-y-1.5 shrink-0 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-500">
              Investigation Goals ({plan.filter((g) => g.status === 'COMPLETED').length}/{plan.length})
            </span>
            {planVersion > 1 && (
              <span className="flex items-center gap-1 text-[9px] font-mono px-2 py-0.5 rounded-full bg-amber-50 text-amber-800 border border-amber-200">
                <RefreshCw className="w-2.5 h-2.5" /> v{planVersion}
              </span>
            )}
          </div>
          <div className="space-y-1">
            {plan.map((goal, idx) => (
              <div key={goal.id || idx} className="flex items-center gap-1.5 text-xs text-slate-800">
                {goal.status === 'COMPLETED' ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                ) : goal.status === 'IN_PROGRESS' ? (
                  <CircleDashed className="w-3.5 h-3.5 text-blue-600 animate-spin shrink-0" />
                ) : goal.status === 'BLOCKED' ? (
                  <AlertTriangle className="w-3.5 h-3.5 text-red-600 shrink-0" />
                ) : (
                  <Clock className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                )}
                <span
                  className={`truncate text-xs ${
                    goal.status === 'COMPLETED' ? 'line-through text-slate-400' : ''
                  }`}
                  title={goal.description}
                >
                  {goal.description}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 2. Step-by-Step Execution Trace */}
      {toolCalls.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center text-center p-6 text-slate-400 text-xs font-mono">
          <CircleDashed className="w-5 h-5 mb-2 stroke-1 text-slate-300 animate-spin" />
          <span>Awaiting execution steps...</span>
        </div>
      ) : (
        <div className="divide-y divide-slate-100 flex-1 min-h-0 px-2 py-1">
          {toolCalls.map((tc, idx) => {
            const stepNum = String(idx + 1).padStart(2, '0');
            const isExpanded = expandedSteps[tc.id] ?? (idx === toolCalls.length - 1);

            // Find evidence items discovered by this tool or file
            const targetFile = tc.arguments?.file_path || tc.arguments?.subpath || '';
            const stepEvidence = evidenceStore.filter((ev) => {
              if (ev.tool_source === tc.tool) {
                if (!targetFile) return true;
                return ev.file_path === targetFile || ev.file_path.includes(targetFile);
              }
              return false;
            });

            // Find findings linked to this step's evidence
            const stepEvIds = new Set(stepEvidence.map((e) => e.id));
            const stepFindings = findings.filter((f) =>
              f.evidence_ids.some((id) => stepEvIds.has(id))
            );

            // Find reflection corresponding to this tool failure (if any)
            const stepReflection = tc.status === 'ERROR' || tc.status === 'POLICY_DENIED'
              ? reflections[reflections.length - 1]
              : null;

            return (
              <div key={tc.id} className="py-0.5">
                {/* Step Header (Clickable Dropdown Row) */}
                <button
                  type="button"
                  onClick={() => toggleStep(tc.id)}
                  className={`w-full text-left px-2.5 py-2 flex items-center justify-between rounded-lg transition cursor-pointer ${
                    isExpanded ? 'bg-slate-50 text-slate-900 font-medium' : 'hover:bg-slate-50 text-slate-700'
                  }`}
                >
                  <div className="flex items-center gap-2 min-w-0">
                    {isExpanded ? (
                      <ChevronDown className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    ) : (
                      <ChevronRight className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    )}
                    <span className="font-mono text-[11px] font-semibold text-slate-400">
                      {stepNum}
                    </span>
                    <span className="font-mono text-xs font-bold text-slate-900 truncate">
                      {tc.tool}
                    </span>
                  </div>

                  <div className="flex items-center gap-2 shrink-0 ml-2">
                    {stepEvidence.length > 0 && (
                      <span className="text-[10px] font-mono text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                        +{stepEvidence.length}
                      </span>
                    )}
                    {getToolStatusIcon(tc.status)}
                  </div>
                </button>

                {/* Step Dropdown Details (Plain, Border-Reduced, Visible) */}
                {isExpanded && (
                  <div className="mx-1 my-1 px-3 py-2.5 space-y-3 text-xs rounded-lg border border-slate-100 bg-slate-50/30">
                    {/* Rationale */}
                    {tc.rationale && (
                      <div>
                        <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-slate-400 block mb-0.5">
                          Rationale
                        </span>
                        <p className="text-slate-700 text-xs leading-relaxed">{tc.rationale}</p>
                      </div>
                    )}

                    {/* Arguments (clean plain inline list) */}
                    {tc.arguments && Object.keys(tc.arguments).length > 0 && (
                      <div>
                        <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-slate-400 block mb-1">
                          Parameters
                        </span>
                        <div className="space-y-0.5 font-mono text-[11px] text-slate-700 pl-2 border-l border-slate-200">
                          {Object.entries(tc.arguments).map(([key, val]) => (
                            <div key={key} className="flex gap-1.5 py-0.5">
                              <span className="text-slate-400">{key}:</span>
                              <span className="text-slate-800 font-medium break-all">
                                {typeof val === 'object' ? JSON.stringify(val) : String(val)}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Tool Result Preview */}
                    {tc.summary && (
                      <div>
                        <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-slate-400 block mb-1">
                          Execution Output
                        </span>
                        <ToolOutputViewer tool={tc.tool} summary={tc.summary} />
                      </div>
                    )}

                    {/* Evidence & Line Citations Discovered */}
                    {stepEvidence.length > 0 && (
                      <div className="space-y-2 pt-1 border-t border-slate-100">
                        <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-emerald-700 flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                          Verified Citations ({stepEvidence.length})
                        </span>
                        <div className="space-y-2">
                          {stepEvidence.map((ev) => (
                            <div
                              key={ev.id}
                              className="py-1 space-y-1 border-l-2 border-emerald-500/70 pl-2.5"
                            >
                              <div className="flex items-center justify-between font-mono text-[11px]">
                                <span className="font-semibold text-slate-800 truncate">
                                  {ev.file_path}
                                </span>
                                <span className="text-slate-400 shrink-0 text-[10px]">
                                  L{ev.start_line}{ev.end_line !== ev.start_line ? `-${ev.end_line}` : ''}
                                </span>
                              </div>
                              {ev.snippet && (
                                <div className="relative">
                                  {ev.file_path.endsWith('.md') ? (
                                    <div className="text-xs max-h-28 overflow-y-auto">
                                      <MarkdownRenderer content={ev.snippet} />
                                    </div>
                                  ) : (
                                    <pre className="p-1.5 bg-slate-50 font-mono text-[10px] text-slate-700 whitespace-pre-wrap max-h-24 overflow-y-auto">
                                      {ev.snippet}
                                    </pre>
                                  )}
                                  <button
                                    type="button"
                                    onClick={() => copyToClipboard(ev.snippet, ev.id)}
                                    className="absolute top-1 right-1 p-0.5 text-slate-400 hover:text-slate-700"
                                    title="Copy snippet"
                                  >
                                    {copiedId === ev.id ? (
                                      <Check className="w-3 h-3 text-emerald-600" />
                                    ) : (
                                      <Copy className="w-3 h-3" />
                                    )}
                                  </button>
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Findings Discovered */}
                    {stepFindings.length > 0 && (
                      <div className="space-y-1.5 pt-1 border-t border-slate-100">
                        <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-slate-400 block">
                          Derived Findings
                        </span>
                        <div className="space-y-2">
                          {stepFindings.map((f, fIdx) => (
                            <div
                              key={f.id || fIdx}
                              className="py-1 text-xs space-y-1 border-l-2 border-slate-300 pl-2.5"
                            >
                              <span
                                className={`text-[9px] font-mono font-semibold px-1 py-0.2 uppercase border ${getConfidenceBadge(
                                  f.confidence
                                )}`}
                              >
                                {f.confidence}
                              </span>
                              <p className="text-slate-700 leading-snug">{f.claim}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Reflexion Self-Critique (only if failed) */}
                    {stepReflection && (
                      <div className="py-1 space-y-1 text-xs border-l-2 border-amber-500 pl-2.5">
                        <div className="flex items-center gap-1 font-mono font-bold text-amber-800 text-[10px] uppercase">
                          <AlertCircle className="w-3 h-3" />
                          Reflexion Diagnosis
                        </div>
                        <p className="text-slate-800 text-xs">
                          <span className="text-slate-500">Diagnosis:</span> {stepReflection.diagnosis}
                        </p>
                        <p className="text-slate-800 text-xs">
                          <span className="text-slate-500">Next approach:</span> {stepReflection.next_approach}
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

