'use client';

import React, { useState, useEffect } from 'react';
import {
  ChevronDown,
  ChevronRight,
  Loader2,
  Check,
  AlertCircle,
  FileCode,
  Search,
  FolderTree,
  GitBranch,
  BookOpen,
  ArrowRight,
  Sparkles,
} from 'lucide-react';
import { ToolCallItem, PlanGoal, ReflectionItem } from '../types';

interface ThoughtProcessProps {
  isInvestigating?: boolean;
  currentNode?: string;
  toolCalls?: ToolCallItem[];
  plan?: PlanGoal[];
  reflections?: ReflectionItem[];
}

export const ThoughtProcess: React.FC<ThoughtProcessProps> = ({
  isInvestigating = false,
  currentNode,
  toolCalls = [],
  plan = [],
  reflections = [],
}) => {
  const [isOpen, setIsOpen] = useState<boolean>(isInvestigating);
  const [expandedSteps, setExpandedSteps] = useState<Record<string, boolean>>({});

  // Automatically expand parent dropdown while actively investigating
  useEffect(() => {
    if (isInvestigating) {
      setIsOpen(true);
    }
  }, [isInvestigating]);

  const toggleStep = (id: string) => {
    setExpandedSteps((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const latestTool = toolCalls.length > 0 ? toolCalls[toolCalls.length - 1] : null;

  // Dynamic verb selection (like Claude, Gemini, ChatGPT)
  const getActiveVerb = (): string => {
    if (currentNode === 'synthesize') return 'Cooking answer...';
    if (currentNode === 'verify') return 'Verifying citations...';
    if (currentNode === 'reflect') return 'Reflecting on findings...';
    if (currentNode === 'reconcile') return 'Reconciling code vs docs...';
    if (currentNode === 'plan') return 'Planning investigation...';
    if (currentNode === 'classify') return 'Analyzing query...';

    if (latestTool) {
      const { tool, arguments: args, status } = latestTool;
      if (status === 'PENDING') {
        if (tool === 'explore_tree') {
          return args?.subpath && args.subpath !== '.'
            ? `Exploring ${args.subpath}...`
            : 'Exploring directory...';
        }
        if (tool === 'search_code') {
          return args?.query ? `Searching code for "${args.query}"...` : 'Searching codebase...';
        }
        if (tool === 'search_symbols') {
          return args?.query ? `Searching symbols for "${args.query}"...` : 'Searching symbols...';
        }
        if (tool === 'get_symbol') {
          return args?.symbol_name ? `Inspecting symbol ${args.symbol_name}...` : 'Inspecting symbol...';
        }
        if (tool === 'read_file') {
          const fileName = args?.file_path ? args.file_path.split('/').pop() : '';
          return fileName ? `Reading ${fileName}...` : 'Reading source code...';
        }
        if (tool === 'trace_calls') {
          return args?.entry_symbol ? `Tracing ${args.entry_symbol} calls...` : 'Tracing call graph...';
        }
        if (tool === 'semantic_search') {
          return 'Searching semantic concepts...';
        }
        if (tool === 'search_docs') {
          return 'Reading documentation...';
        }
        if (tool === 'get_relationships') {
          return 'Mapping dependencies...';
        }
        if (tool === 'get_history') {
          return 'Checking git history...';
        }
      }
    }

    if (currentNode === 'execute_tool') return 'Running tool...';
    if (currentNode === 'observe') return 'Observing results...';
    if (currentNode === 'evaluate') return 'Evaluating evidence...';

    return 'Thinking...';
  };

  const getToolIcon = (tool: string) => {
    switch (tool) {
      case 'explore_tree':
        return <FolderTree className="w-3.5 h-3.5 text-slate-400 shrink-0" />;
      case 'read_file':
        return <FileCode className="w-3.5 h-3.5 text-slate-400 shrink-0" />;
      case 'search_code':
      case 'search_symbols':
      case 'get_symbol':
      case 'semantic_search':
        return <Search className="w-3.5 h-3.5 text-slate-400 shrink-0" />;
      case 'search_docs':
        return <BookOpen className="w-3.5 h-3.5 text-slate-400 shrink-0" />;
      case 'trace_calls':
      case 'get_relationships':
        return <GitBranch className="w-3.5 h-3.5 text-slate-400 shrink-0" />;
      default:
        return <Sparkles className="w-3.5 h-3.5 text-slate-400 shrink-0" />;
    }
  };

  // Fallback human-readable title when rationale is absent
  const getDefaultStepTitle = (tc: ToolCallItem) => {
    const args = tc.arguments || {};
    if (tc.tool === 'read_file') {
      const file = args.file_path || 'file';
      const lines = args.start_line ? ` (lines ${args.start_line}–${args.end_line || ''})` : '';
      return `Read ${file}${lines}`;
    }
    if (tc.tool === 'search_code') {
      return `Search codebase for "${args.query || ''}"`;
    }
    if (tc.tool === 'search_symbols') {
      return `Search symbol definitions for "${args.query || ''}"`;
    }
    if (tc.tool === 'get_symbol') {
      return `Look up definition of ${args.symbol_name || 'symbol'}`;
    }
    if (tc.tool === 'explore_tree') {
      return `Explore directory structure at "${args.subpath || '.'}"`;
    }
    if (tc.tool === 'semantic_search') {
      return `Semantic search: "${args.query || ''}"`;
    }
    if (tc.tool === 'search_docs') {
      return `Search architectural documentation for "${args.query || ''}"`;
    }
    if (tc.tool === 'trace_calls') {
      return `Trace execution call graph from ${args.entry_symbol || 'entry'}`;
    }
    if (tc.tool === 'get_relationships') {
      return `Map import relationships for ${args.file_path || 'module'}`;
    }
    if (tc.tool === 'get_history') {
      return `Inspect git history for ${args.file_path || 'repo'}`;
    }
    return `Execute ${tc.tool}`;
  };

  // Clean raw summary and parse structured payload if available
  const parseToolOutput = (summary: string = '') => {
    const cleaned = summary
      .replace(/<<<UNTRUSTED_REPOSITORY_DATA[^>]*>>>/g, '')
      .replace(/<<<END_UNTRUSTED_REPOSITORY_DATA>>>/g, '')
      .trim();

    if (!cleaned) return { text: 'No output recorded.', data: null };

    try {
      const parsed = JSON.parse(cleaned);
      return { text: cleaned, data: parsed };
    } catch {
      return { text: cleaned, data: null };
    }
  };

  const totalSteps = toolCalls.length;
  const hasThoughts = totalSteps > 0 || plan.length > 0 || reflections.length > 0 || isInvestigating;

  if (!hasThoughts) {
    return null;
  }

  const activeVerb = getActiveVerb();

  return (
    <div className="my-2 select-none">
      {/* Parent Thinking Dropdown Header */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="group flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-800 transition-colors py-1 cursor-pointer font-sans"
      >
        <span className="text-slate-400 group-hover:text-slate-600 transition-colors">
          {isOpen ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
        </span>

        {isInvestigating ? (
          <span className="flex items-center gap-1.5 font-medium text-slate-600 animate-pulse">
            <Loader2 className="w-3 h-3 animate-spin text-slate-400" />
            <span>{activeVerb}</span>
            {totalSteps > 0 && (
              <span className="text-[10px] font-mono text-slate-400 font-normal">
                ({totalSteps} {totalSteps === 1 ? 'step' : 'steps'})
              </span>
            )}
          </span>
        ) : (
          <span className="flex items-center gap-1.5 text-slate-400 font-medium">
            <span>Thinking Process</span>
            {totalSteps > 0 && (
              <span className="text-[10px] font-mono text-slate-400">
                · {totalSteps} {totalSteps === 1 ? 'step' : 'steps'}
              </span>
            )}
          </span>
        )}
      </button>

      {/* Chained Thoughts Timeline */}
      {isOpen && (
        <div className="border-l border-slate-200/90 ml-2 pl-3 py-1 space-y-2.5 mt-1 mb-2 font-sans text-xs">
          {/* Plan formulated step */}
          {plan.length > 0 && (
            <div className="relative flex items-start gap-2 text-slate-500">
              <span className="w-1.5 h-1.5 rounded-full bg-slate-300 mt-1.5 shrink-0" />
              <div className="space-y-0.5">
                <div className="text-slate-600 font-medium text-[11px]">
                  Formulated investigation plan ({plan.length} goals)
                </div>
                <div className="space-y-0.5 text-[11px] text-slate-400 font-mono">
                  {plan.map((g, idx) => (
                    <div key={g.id || idx} className="truncate max-w-lg">
                      {idx + 1}. {g.description}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Tool Calls with Rationale as Title and Interactive Sub-Dropdown */}
          {toolCalls.map((tc, idx) => {
            const stepId = tc.id || `step_${idx}`;
            const isExpanded = !!expandedSteps[stepId];
            const isPending = tc.status === 'PENDING' || !tc.status;
            const stepTitle = tc.rationale || getDefaultStepTitle(tc);
            const { text: cleanText, data: parsedJson } = parseToolOutput(tc.summary);
            const args = tc.arguments || {};

            return (
              <div key={stepId} className="relative flex items-start gap-2">
                {/* Timeline connector dot */}
                <span
                  className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${
                    isPending
                      ? 'bg-blue-500 animate-pulse'
                      : tc.status === 'ERROR'
                      ? 'bg-amber-400'
                      : 'bg-slate-300'
                  }`}
                />

                <div className="min-w-0 max-w-2xl flex-1 space-y-1">
                  {/* Step Title Row (Clickable sub-dropdown header) */}
                  <div
                    onClick={() => toggleStep(stepId)}
                    className="group cursor-pointer flex items-center justify-between gap-2 p-1 -m-1 rounded-md hover:bg-slate-100/70 transition-colors"
                    title="Click to view tool inputs and output"
                  >
                    <div className="flex items-center gap-1.5 min-w-0">
                      <span className="text-slate-400 group-hover:text-slate-600 transition-colors shrink-0">
                        {isExpanded ? (
                          <ChevronDown className="w-3 h-3" />
                        ) : (
                          <ChevronRight className="w-3 h-3" />
                        )}
                      </span>
                      {getToolIcon(tc.tool)}

                      {/* Rationale as the title */}
                      <span className="text-xs text-slate-700 font-medium group-hover:text-slate-900 transition-colors truncate">
                        {stepTitle}
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5 shrink-0">
                      {/* Tool identifier pill */}
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded-md bg-slate-100 text-slate-500 border border-slate-200/80 font-normal">
                        {tc.tool}
                      </span>

                      {/* Status indicator */}
                      {tc.status === 'SUCCESS' && (
                        <span className="text-[10px] text-emerald-600 flex items-center gap-0.5" title="Success">
                          <Check className="w-3 h-3" />
                        </span>
                      )}
                      {tc.status === 'ERROR' && (
                        <span className="text-[10px] text-amber-600 flex items-center gap-0.5" title="Execution error">
                          <AlertCircle className="w-3 h-3" />
                        </span>
                      )}
                      {isPending && (
                        <span className="text-[10px] text-blue-500 flex items-center gap-0.5" title="Running">
                          <Loader2 className="w-3 h-3 animate-spin" />
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Sub-Dropdown Details: Query and Output */}
                  {isExpanded && (
                    <div className="mt-1.5 p-2.5 rounded-xl bg-slate-50/90 border border-slate-200/90 space-y-2 text-xs font-sans shadow-2xs">
                      {/* Query / Arguments Section */}
                      <div className="space-y-1">
                        <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-slate-400 block">
                          Query / Arguments
                        </span>
                        <div className="p-2 bg-white rounded-lg border border-slate-200/80 font-mono text-[11px] text-slate-700 space-y-0.5 overflow-x-auto">
                          {tc.tool === 'read_file' && (
                            <>
                              <div>file: <span className="font-semibold text-slate-900">{args.file_path || '–'}</span></div>
                              {args.start_line && (
                                <div className="text-slate-500">lines: {args.start_line} – {args.end_line || 'end'}</div>
                              )}
                            </>
                          )}
                          {tc.tool === 'search_code' && (
                            <>
                              <div>query: <span className="font-semibold text-slate-900">"{args.query || ''}"</span></div>
                              {args.path_scope && <div className="text-slate-500">scope: {args.path_scope}</div>}
                              {args.is_regex && <div className="text-slate-500">regex: true</div>}
                            </>
                          )}
                          {tc.tool === 'explore_tree' && (
                            <>
                              <div>subpath: <span className="font-semibold text-slate-900">{args.subpath || '.'}</span></div>
                              {args.depth && <div className="text-slate-500">depth: {args.depth}</div>}
                              {args.glob_pattern && <div className="text-slate-500">glob: {args.glob_pattern}</div>}
                            </>
                          )}
                          {tc.tool === 'search_symbols' && (
                            <>
                              <div>query: <span className="font-semibold text-slate-900">"{args.query || ''}"</span></div>
                              {args.kind && <div className="text-slate-500">kind: {args.kind}</div>}
                            </>
                          )}
                          {tc.tool === 'get_symbol' && (
                            <>
                              <div>symbol: <span className="font-semibold text-slate-900">{args.symbol_name || ''}</span></div>
                              {args.file_path && <div className="text-slate-500">file: {args.file_path}</div>}
                            </>
                          )}
                          {!['read_file', 'search_code', 'explore_tree', 'search_symbols', 'get_symbol'].includes(tc.tool) && (
                            <div className="whitespace-pre-wrap text-slate-700">
                              {Object.keys(args).length > 0 ? JSON.stringify(args, null, 2) : 'No arguments provided'}
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Tool Output Section */}
                      <div className="space-y-1">
                        <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-slate-400 block">
                          Tool Output
                        </span>

                        {isPending ? (
                          <div className="p-2 rounded-lg bg-blue-50/60 border border-blue-200/70 text-blue-600 font-mono text-[11px] flex items-center gap-1.5">
                            <Loader2 className="w-3 h-3 animate-spin shrink-0" />
                            <span>Tool executing in repository...</span>
                          </div>
                        ) : parsedJson && Array.isArray(parsedJson.matches) && parsedJson.matches.length > 0 ? (
                          /* Search matches table */
                          <div className="overflow-x-auto max-h-52 rounded-lg border border-slate-200 bg-white">
                            <table className="w-full text-left font-mono text-[11px]">
                              <thead>
                                <tr className="bg-slate-100/70 border-b border-slate-200 text-slate-600 text-[10px]">
                                  <th className="p-1.5 px-2">File</th>
                                  <th className="p-1.5 px-2">Line</th>
                                  <th className="p-1.5 px-2">Match</th>
                                </tr>
                              </thead>
                              <tbody>
                                {parsedJson.matches.map((m: any, mIdx: number) => (
                                  <tr key={mIdx} className="border-b border-slate-100 hover:bg-slate-50/70 last:border-0">
                                    <td className="p-1.5 px-2 font-semibold text-slate-800 whitespace-nowrap">{m.file_path}</td>
                                    <td className="p-1.5 px-2 text-slate-500">{m.line_number}</td>
                                    <td className="p-1.5 px-2 text-slate-900 font-sans">{m.line}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        ) : parsedJson && typeof parsedJson.content === 'string' ? (
                          /* File content output */
                          <div className="overflow-x-auto max-h-56 rounded-lg border border-slate-200 bg-white p-2 text-[11px] font-mono text-slate-800 whitespace-pre leading-relaxed">
                            {parsedJson.content}
                          </div>
                        ) : parsedJson && Array.isArray(parsedJson.entries) && parsedJson.entries.length > 0 ? (
                          /* Directory tree output */
                          <div className="overflow-x-auto max-h-52 rounded-lg border border-slate-200 bg-white p-2 text-[11px] font-mono text-slate-800 space-y-0.5">
                            {parsedJson.entries.map((entry: any, eIdx: number) => (
                              <div key={eIdx} className="flex items-center gap-1.5">
                                <span className="text-slate-400">{entry.is_dir ? '📁' : '📄'}</span>
                                <span className={entry.is_dir ? 'font-semibold text-slate-800' : 'text-slate-700'}>
                                  {entry.path}
                                </span>
                              </div>
                            ))}
                          </div>
                        ) : (
                          /* Raw text output fallback */
                          <div className="overflow-x-auto max-h-52 rounded-lg border border-slate-200 bg-white p-2 font-mono text-[11px] text-slate-800 whitespace-pre-wrap leading-relaxed">
                            {cleanText || 'Completed with empty result.'}
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}

          {/* Reflections */}
          {reflections.map((ref, idx) => (
            <div key={ref.id || idx} className="relative flex items-start gap-2 text-slate-500">
              <span className="w-1.5 h-1.5 rounded-full bg-purple-400 mt-1.5 shrink-0" />
              <div className="space-y-0.5 text-[11px]">
                <div className="text-purple-700 font-medium">Reflecting on approach</div>
                <p className="text-slate-500 font-mono text-[10px]">{ref.diagnosis}</p>
                {ref.next_approach && (
                  <p className="text-slate-400 text-[10px] flex items-center gap-1">
                    <ArrowRight className="w-2.5 h-2.5" /> Next: {ref.next_approach}
                  </p>
                )}
              </div>
            </div>
          ))}

          {/* Active bottom node indicator when investigating */}
          {isInvestigating && (!latestTool || latestTool.status !== 'PENDING') && (
            <div className="relative flex items-center gap-2 text-slate-400 text-[11px]">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse shrink-0" />
              <span className="flex items-center gap-1.5 font-medium text-slate-500">
                <Loader2 className="w-2.5 h-2.5 animate-spin" />
                {activeVerb}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
