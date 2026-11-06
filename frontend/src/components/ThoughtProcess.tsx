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

  // Automatically expand while actively investigating
  useEffect(() => {
    if (isInvestigating) {
      setIsOpen(true);
    }
  }, [isInvestigating]);

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
        return <FolderTree className="w-3 h-3 text-slate-400 shrink-0" />;
      case 'read_file':
        return <FileCode className="w-3 h-3 text-slate-400 shrink-0" />;
      case 'search_code':
      case 'search_symbols':
      case 'get_symbol':
      case 'semantic_search':
        return <Search className="w-3 h-3 text-slate-400 shrink-0" />;
      case 'search_docs':
        return <BookOpen className="w-3 h-3 text-slate-400 shrink-0" />;
      case 'trace_calls':
      case 'get_relationships':
        return <GitBranch className="w-3 h-3 text-slate-400 shrink-0" />;
      default:
        return <Sparkles className="w-3 h-3 text-slate-400 shrink-0" />;
    }
  };

  const formatToolCall = (tc: ToolCallItem) => {
    const args = tc.arguments || {};
    if (tc.tool === 'read_file') {
      const path = args.file_path || '';
      const lines = args.start_line ? `:${args.start_line}-${args.end_line || ''}` : '';
      return `read_file(${path}${lines})`;
    }
    if (tc.tool === 'search_code') {
      return `search_code("${args.query || ''}")`;
    }
    if (tc.tool === 'search_symbols') {
      return `search_symbols("${args.query || ''}")`;
    }
    if (tc.tool === 'get_symbol') {
      return `get_symbol("${args.symbol_name || ''}")`;
    }
    if (tc.tool === 'explore_tree') {
      return `explore_tree("${args.subpath || '.'}")`;
    }
    if (tc.tool === 'semantic_search') {
      return `semantic_search("${args.query || ''}")`;
    }
    if (tc.tool === 'search_docs') {
      return `search_docs("${args.query || ''}")`;
    }
    if (tc.tool === 'trace_calls') {
      return `trace_calls("${args.entry_symbol || ''}")`;
    }
    return `${tc.tool}()`;
  };

  const totalSteps = toolCalls.length;
  const hasThoughts = totalSteps > 0 || plan.length > 0 || reflections.length > 0 || isInvestigating;

  if (!hasThoughts) {
    return null;
  }

  const activeVerb = getActiveVerb();

  return (
    <div className="my-2 select-none">
      {/* Dropdown Header */}
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

          {/* Tool Calls & Outputs */}
          {toolCalls.map((tc, idx) => {
            const isLatest = idx === toolCalls.length - 1;
            const isPending = tc.status === 'PENDING' || !tc.status;

            return (
              <div key={tc.id || idx} className="relative flex items-start gap-2">
                <span
                  className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${
                    isPending
                      ? 'bg-blue-500 animate-pulse'
                      : tc.status === 'ERROR'
                      ? 'bg-amber-400'
                      : 'bg-slate-300'
                  }`}
                />
                <div className="space-y-1 min-w-0 max-w-2xl">
                  {/* Tool signature & status */}
                  <div className="flex items-center gap-1.5 flex-wrap">
                    {getToolIcon(tc.tool)}
                    <span className="font-mono text-[11px] font-semibold text-slate-700">
                      {formatToolCall(tc)}
                    </span>
                    {tc.status === 'SUCCESS' && (
                      <span className="text-[10px] text-emerald-600 flex items-center gap-0.5">
                        <Check className="w-2.5 h-2.5" />
                      </span>
                    )}
                    {tc.status === 'ERROR' && (
                      <span className="text-[10px] text-amber-600 flex items-center gap-0.5">
                        <AlertCircle className="w-2.5 h-2.5" /> error
                      </span>
                    )}
                    {isPending && (
                      <span className="text-[10px] text-blue-500 flex items-center gap-1">
                        <Loader2 className="w-2.5 h-2.5 animate-spin" /> running
                      </span>
                    )}
                  </div>

                  {/* Rationale if present */}
                  {tc.rationale && (
                    <p className="text-[11px] text-slate-400 italic font-sans leading-tight">
                      {tc.rationale}
                    </p>
                  )}

                  {/* Summary / Result preview */}
                  {tc.summary && (
                    <p className="text-[11px] text-slate-500 font-mono bg-slate-100/70 rounded px-1.5 py-0.5 max-w-xl truncate">
                      {tc.summary.replace(/<<<UNTRUSTED_REPOSITORY_DATA[^>]*>>>/g, '').replace(/<<<END_UNTRUSTED_REPOSITORY_DATA>>>/g, '').trim()}
                    </p>
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

          {/* Active bottom node when investigating and no active pending tool */}
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
