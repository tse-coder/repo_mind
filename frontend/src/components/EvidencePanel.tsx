'use client';

import React, { useState } from 'react';
import { BookOpen, FileCode, Hash, ExternalLink, Check, Copy } from 'lucide-react';
import { EvidenceItem, FindingItem } from '../types';

interface EvidencePanelProps {
  evidenceStore: EvidenceItem[];
  findings: FindingItem[];
}

export const EvidencePanel: React.FC<EvidencePanelProps> = ({ evidenceStore, findings }) => {
  const [selectedSnippet, setSelectedSnippet] = useState<EvidenceItem | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const getConfidenceBadge = (confidence: string) => {
    switch (confidence) {
      case 'CONFIRMED':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'INFERRED':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      case 'NOT_FOUND':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
      default:
        return 'bg-gray-800 text-gray-400 border-gray-700';
    }
  };

  return (
    <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-4 flex flex-col h-full shadow-lg">
      <div className="flex items-center justify-between pb-3 border-b border-gray-800 mb-3">
        <div className="flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-blue-400" />
          <h2 className="text-xs font-bold uppercase tracking-wider text-gray-200">
            Evidence Store & Line Citations
          </h2>
        </div>
        <span className="text-xs font-mono text-gray-400">
          {evidenceStore.length} items verified
        </span>
      </div>

      {evidenceStore.length === 0 && findings.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center text-center p-6 text-gray-500 text-xs">
          <FileCode className="w-8 h-8 mb-2 stroke-1 text-gray-600" />
          <span>No evidence extracted yet. Verified citations will appear here.</span>
        </div>
      ) : (
        <div className="space-y-3 overflow-y-auto max-h-[500px] pr-1">
          {/* Findings */}
          {findings.length > 0 && (
            <div className="space-y-2 mb-3">
              <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider block">
                Derived Claims & Findings ({findings.length}):
              </span>
              {findings.map((f, idx) => (
                <div
                  key={f.id || idx}
                  className="p-2.5 rounded-lg border border-gray-800 bg-[#090d16] text-xs space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span
                      className={`text-[10px] font-semibold px-2 py-0.5 rounded border uppercase tracking-wider ${getConfidenceBadge(
                        f.confidence
                      )}`}
                    >
                      {f.confidence}
                    </span>
                    {f.slot_id && (
                      <span className="text-[10px] text-gray-400 font-mono">
                        slot: <span className="text-blue-300">{f.slot_id}</span>
                      </span>
                    )}
                  </div>
                  <p className="text-gray-200 font-medium text-xs pt-1">{f.claim}</p>
                </div>
              ))}
            </div>
          )}

          {/* Raw Evidence Items */}
          <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider block">
            Line-Level Evidence Items ({evidenceStore.length}):
          </span>

          {evidenceStore.map((ev) => (
            <div
              key={ev.id}
              className="p-3 rounded-lg border border-gray-800 bg-[#090d16] hover:border-gray-700 transition text-xs space-y-2"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 font-mono text-blue-400 font-semibold text-xs truncate max-w-[240px]">
                  <FileCode className="w-3.5 h-3.5 shrink-0" />
                  <span title={ev.file_path}>{ev.file_path}</span>
                </div>
                <span className="font-mono text-[11px] text-gray-400 px-1.5 py-0.5 rounded bg-gray-800 border border-gray-700">
                  L{ev.start_line}{ev.end_line !== ev.start_line ? `-${ev.end_line}` : ''}
                </span>
              </div>

              {/* Hash and Tool source */}
              <div className="flex items-center justify-between text-[10px] text-gray-500 font-mono">
                <span className="flex items-center gap-1">
                  <Hash className="w-3 h-3" />
                  <span>{ev.content_hash ? ev.content_hash.slice(0, 8) : 'hash'}</span>
                </span>
                <span className="text-gray-400">via {ev.tool_source}</span>
              </div>

              {/* Snippet preview */}
              {ev.snippet && (
                <div className="relative">
                  <pre className="p-2 rounded bg-black/60 border border-gray-800/80 font-mono text-[11px] text-gray-300 overflow-x-auto max-h-24 whitespace-pre-wrap">
                    {ev.snippet}
                  </pre>
                  <button
                    type="button"
                    onClick={() => copyToClipboard(ev.snippet, ev.id)}
                    className="absolute top-1.5 right-1.5 p-1 rounded bg-gray-800 hover:bg-gray-700 text-gray-300 transition"
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

