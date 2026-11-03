'use client';

import React, { useState } from 'react';
import { FileText, ShieldCheck, AlertCircle, Copy, Check, Eye, Code } from 'lucide-react';
import { FindingItem } from '../types';
import { MarkdownRenderer } from './MarkdownRenderer';

interface AnswerViewProps {
  answer?: string;
  streamingTokens: string[];
  findings: FindingItem[];
  limitations: string[];
  status: string;
}

export const AnswerView: React.FC<AnswerViewProps> = ({
  answer,
  streamingTokens,
  findings,
  limitations,
  status,
}) => {
  const [copied, setCopied] = useState(false);
  const [viewMode, setViewMode] = useState<'preview' | 'raw'>('preview');

  const displayText = answer || (streamingTokens.length > 0 ? streamingTokens.join('') : '');

  const copyAnswer = () => {
    if (!displayText) return;
    navigator.clipboard.writeText(displayText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-white border border-slate-200 rounded-none p-5 shadow-sm flex flex-col space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-200">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-slate-700" />
          <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-800">
            Synthesized Investigation Result
          </h2>
        </div>
        {displayText && (
          <div className="flex items-center gap-2">
            {/* View Mode Toggle: Preview / Raw */}
            <div className="inline-flex border border-slate-300 rounded-none bg-slate-100 p-0.5">
              <button
                type="button"
                onClick={() => setViewMode('preview')}
                className={`flex items-center gap-1 px-2 py-0.5 text-xs font-mono transition ${
                  viewMode === 'preview'
                    ? 'bg-white text-slate-900 font-semibold shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
                title="Render formatted Markdown"
              >
                <Eye className="w-3 h-3" />
                <span>Preview</span>
              </button>
              <button
                type="button"
                onClick={() => setViewMode('raw')}
                className={`flex items-center gap-1 px-2 py-0.5 text-xs font-mono transition ${
                  viewMode === 'raw'
                    ? 'bg-white text-slate-900 font-semibold shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
                title="View raw Markdown source"
              >
                <Code className="w-3 h-3" />
                <span>Raw</span>
              </button>
            </div>

            <button
              type="button"
              onClick={copyAnswer}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-none bg-slate-100 hover:bg-slate-200 text-xs font-mono text-slate-700 border border-slate-300 transition"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  <span>Copy</span>
                </>
              )}
            </button>
          </div>
        )}
      </div>

      {/* Main Answer Area */}
      {!displayText ? (
        <div className="py-12 flex flex-col items-center justify-center text-center text-slate-400 text-xs font-mono">
          <FileText className="w-6 h-6 mb-2 stroke-1 text-slate-300" />
          <span>The verified final answer with line citations will render here upon completion.</span>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Answer Content */}
          <div className="p-4 rounded-none bg-slate-50 border border-slate-200 text-sm text-slate-900 font-sans leading-relaxed">
            {viewMode === 'preview' ? (
              <MarkdownRenderer content={displayText} />
            ) : (
              <pre className="p-3 bg-slate-900 text-slate-100 font-mono text-xs whitespace-pre-wrap overflow-x-auto rounded-none border border-slate-800">
                {displayText}
              </pre>
            )}
          </div>

          {/* Finding Confidence Ratings */}
          {findings.length > 0 && (
            <div className="p-3.5 rounded-none bg-slate-50 border border-slate-200 space-y-2">
              <span className="text-xs font-mono font-semibold text-slate-700 uppercase tracking-wider block flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-slate-600" /> Claim Verification Breakdown:
              </span>
              <div className="space-y-1.5">
                {findings.map((f, i) => (
                  <div key={i} className="flex items-start gap-2 text-xs">
                    <span
                      className={`text-[9px] font-mono px-1.5 py-0.2 rounded-none uppercase font-semibold shrink-0 border ${
                        f.confidence === 'CONFIRMED'
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-300'
                          : f.confidence === 'INFERRED'
                          ? 'bg-amber-50 text-amber-700 border-amber-300'
                          : 'bg-red-50 text-red-700 border-red-300'
                      }`}
                    >
                      {f.confidence}
                    </span>
                    <span className="text-slate-800">{f.claim}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Limitations and Knowledge Gaps */}
          {limitations.length > 0 && (
            <div className="p-3.5 rounded-none bg-amber-50 border border-amber-200 space-y-1.5">
              <span className="text-xs font-mono font-semibold text-amber-800 uppercase tracking-wider block flex items-center gap-1.5">
                <AlertCircle className="w-3.5 h-3.5 text-amber-700" /> Knowledge Gaps & Unanswerable Slots:
              </span>
              <ul className="list-disc list-inside text-xs text-slate-700 space-y-1">
                {limitations.map((lim, i) => (
                  <li key={i}>{lim}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
