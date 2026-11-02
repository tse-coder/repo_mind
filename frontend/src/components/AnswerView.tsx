'use client';

import React, { useState } from 'react';
import { Award, ShieldCheck, AlertCircle, Copy, Check, Sparkles } from 'lucide-react';
import { FindingItem } from '../types';

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

  const displayText = answer || (streamingTokens.length > 0 ? streamingTokens.join('') : '');

  const copyAnswer = () => {
    if (!displayText) return;
    navigator.clipboard.writeText(displayText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-5 shadow-lg flex flex-col space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-gray-800">
        <div className="flex items-center gap-2">
          <Award className="w-5 h-5 text-emerald-400" />
          <h2 className="text-sm font-bold uppercase tracking-wider text-gray-200">
            Investigation Synthesized Answer
          </h2>
        </div>
        {displayText && (
          <button
            type="button"
            onClick={copyAnswer}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-gray-800 hover:bg-gray-700 text-xs text-gray-300 border border-gray-700 transition"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-400" />
                <span>Copied</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5" />
                <span>Copy Answer</span>
              </>
            )}
          </button>
        )}
      </div>

      {/* Main Answer Area */}
      {!displayText ? (
        <div className="py-12 flex flex-col items-center justify-center text-center text-gray-500 text-xs">
          <Sparkles className="w-8 h-8 mb-2 stroke-1 text-gray-600" />
          <span>The synthesized final answer with verified line citations will render here.</span>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Answer Text */}
          <div className="p-4 rounded-lg bg-[#090d16] border border-gray-800 text-sm text-gray-200 font-sans leading-relaxed whitespace-pre-wrap">
            {displayText}
          </div>

          {/* Finding Confidence Ratings */}
          {findings.length > 0 && (
            <div className="p-3.5 rounded-lg bg-gray-900/60 border border-gray-800 space-y-2">
              <span className="text-xs font-semibold text-gray-300 uppercase tracking-wider block flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" /> Verified Claim Confidence:
              </span>
              <div className="space-y-1.5">
                {findings.map((f, i) => (
                  <div key={i} className="flex items-start gap-2 text-xs">
                    <span
                      className={`text-[10px] font-mono px-1.5 py-0.5 rounded uppercase font-semibold shrink-0 ${
                        f.confidence === 'CONFIRMED'
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          : f.confidence === 'INFERRED'
                          ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                          : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                      }`}
                    >
                      {f.confidence}
                    </span>
                    <span className="text-gray-300">{f.claim}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Limitations and Knowledge Gaps */}
          {limitations.length > 0 && (
            <div className="p-3.5 rounded-lg bg-amber-500/5 border border-amber-500/20 space-y-1.5">
              <span className="text-xs font-semibold text-amber-400 uppercase tracking-wider block flex items-center gap-1.5">
                <AlertCircle className="w-3.5 h-3.5 text-amber-400" /> Explicit Limitations & Unanswerable Slots:
              </span>
              <ul className="list-disc list-inside text-xs text-gray-300 space-y-1">
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

