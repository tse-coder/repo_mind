'use client';

import React, { useState } from 'react';
import { BookOpen, FileCode, Hash, Check, Copy } from 'lucide-react';
import { EvidenceItem, FindingItem } from '../types';

interface EvidencePanelProps {
  evidenceStore: EvidenceItem[];
  findings: FindingItem[];
}

export const EvidencePanel: React.FC<EvidencePanelProps> = ({ evidenceStore, findings }) => {
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const getConfidenceBadge = (confidence: string) => {
    switch (confidence) {
      case 'CONFIRMED':
        return 'bg-emerald-50 text-emerald-700 border-emerald-300';
      case 'INFERRED':
        return 'bg-amber-50 text-amber-700 border-amber-300';
      case 'NOT_FOUND':
        return 'bg-red-50 text-red-700 border-red-300';
      default:
        return 'bg-slate-100 text-slate-600 border-slate-300';
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-none p-4 flex flex-col h-full shadow-sm">
      <div className="flex items-center justify-between pb-3 border-b border-slate-200 mb-3">
        <div className="flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-slate-700" />
          <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-800">
            Evidence Store & Line Citations
          </h2>
        </div>
        <span className="text-xs font-mono text-slate-500">
          {evidenceStore.length} verified
        </span>
      </div>

      {evidenceStore.length === 0 && findings.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center text-center p-6 text-slate-400 text-xs font-mono">
          <FileCode className="w-6 h-6 mb-2 stroke-1 text-slate-300" />
          <span>No evidence verified yet. Line citations will appear here.</span>
        </div>
      ) : (
        <div className="space-y-3 overflow-y-auto max-h-[500px] pr-1">
          {/* Findings */}
          {findings.length > 0 && (
            <div className="space-y-2 mb-3">
              <span className="text-[11px] font-mono font-semibold text-slate-500 uppercase tracking-wider block">
                Derived Claims ({findings.length}):
              </span>
              {findings.map((f, idx) => (
                <div
                  key={f.id || idx}
                  className="p-2.5 rounded-none border border-slate-200 bg-slate-50 text-xs space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span
                      className={`text-[9px] font-mono font-semibold px-1.5 py-0.2 rounded-none border uppercase tracking-wider ${getConfidenceBadge(
                        f.confidence
                      )}`}
                    >
                      {f.confidence}
                    </span>
                    {f.slot_id && (
                      <span className="text-[10px] text-slate-500 font-mono">
                        slot: <span className="text-slate-800 font-semibold">{f.slot_id}</span>
                      </span>
                    )}
                  </div>
                  <p className="text-slate-800 text-xs pt-0.5 leading-snug">{f.claim}</p>
                </div>
              ))}
            </div>
          )}

          {/* Raw Evidence Items */}
          <span className="text-[11px] font-mono font-semibold text-slate-500 uppercase tracking-wider block">
            Verified Citations ({evidenceStore.length}):
          </span>

          {evidenceStore.map((ev) => (
            <div
              key={ev.id}
              className="p-2.5 rounded-none border border-slate-200 bg-slate-50 text-xs space-y-1.5"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 font-mono text-slate-900 font-semibold text-xs truncate max-w-[240px]">
                  <FileCode className="w-3.5 h-3.5 shrink-0 text-slate-500" />
                  <span title={ev.file_path}>{ev.file_path}</span>
                </div>
                <span className="font-mono text-[10px] text-slate-700 px-1.5 py-0.2 rounded-none bg-slate-200 border border-slate-300">
                  L{ev.start_line}{ev.end_line !== ev.start_line ? `-${ev.end_line}` : ''}
                </span>
              </div>

              {/* Hash and Tool source */}
              <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono">
                <span className="flex items-center gap-1">
                  <Hash className="w-3 h-3 text-slate-400" />
                  <span>{ev.content_hash ? ev.content_hash.slice(0, 8) : 'hash'}</span>
                </span>
                <span className="text-slate-500">via {ev.tool_source}</span>
              </div>

              {/* Snippet preview */}
              {ev.snippet && (
                <div className="relative">
                  <pre className="p-2 rounded-none bg-slate-900 border border-slate-800 font-mono text-[11px] text-slate-100 overflow-x-auto max-h-24 whitespace-pre-wrap">
                    {ev.snippet}
                  </pre>
                  <button
                    type="button"
                    onClick={() => copyToClipboard(ev.snippet, ev.id)}
                    className="absolute top-1.5 right-1.5 p-1 rounded-none bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
                    title="Copy snippet"
                  >
                    {copiedId === ev.id ? (
                      <Check className="w-3 h-3 text-emerald-400" />
                    ) : (
                      <Copy className="w-3 h-3" />
                    )}
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
