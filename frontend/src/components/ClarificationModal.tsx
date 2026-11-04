'use client';

import React, { useState } from 'react';
import { HelpCircle, Send, Loader2 } from 'lucide-react';
import { ClarificationPrompt } from '../types';

interface ClarificationModalProps {
  prompt: ClarificationPrompt | null;
  investigationId: string;
  onResume: (response: string) => Promise<void>;
}

export const ClarificationModal: React.FC<ClarificationModalProps> = ({
  prompt,
  onResume,
}) => {
  const [response, setResponse] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!prompt) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!response.trim() || isSubmitting) return;
    setIsSubmitting(true);
    try {
      await onResume(response.trim());
      setResponse('');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white border border-slate-200 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-slate-100 text-slate-800 flex items-center justify-center shrink-0 border border-slate-200 shadow-xs">
            <HelpCircle className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-mono font-bold text-slate-900">Clarification Required</h3>
            <p className="text-xs text-slate-500">
              Agent execution paused for user input.
            </p>
          </div>
        </div>

        {/* Question Prompt */}
        <div className="p-3.5 bg-slate-50 border border-slate-200 text-xs text-slate-800 leading-relaxed font-sans rounded-xl">
          {prompt.question}
        </div>

        {/* User Response Form */}
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block text-xs font-mono font-semibold text-slate-600 uppercase tracking-wider mb-1">
              Your Input:
            </label>
            <textarea
              value={response}
              onChange={(e) => setResponse(e.target.value)}
              placeholder="e.g. Focus on auth_service.py"
              rows={3}
              className="w-full bg-white border border-slate-300 rounded-xl px-3.5 py-2.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900/10 focus:border-slate-800 resize-none font-sans"
              autoFocus
              required
            />
          </div>

          <div className="flex justify-end gap-2 pt-1">
            <button
              type="submit"
              disabled={isSubmitting || !response.trim()}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 disabled:bg-slate-200 disabled:text-slate-400 text-white text-xs font-mono font-medium transition cursor-pointer disabled:cursor-not-allowed border border-slate-900 shadow-xs"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>RESUMING...</span>
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5" />
                  <span>SUBMIT & RESUME</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
