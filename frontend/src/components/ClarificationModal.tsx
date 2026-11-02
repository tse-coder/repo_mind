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
  investigationId,
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
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-[#111827] border border-blue-500/40 rounded-xl max-w-lg w-full p-6 shadow-2xl space-y-4 animate-in fade-in zoom-in-95 duration-200">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center shrink-0 border border-blue-500/30">
            <HelpCircle className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">Agent Clarification Request</h3>
            <p className="text-xs text-gray-400">
              The agent needs human guidance to proceed with this investigation.
            </p>
          </div>
        </div>

        {/* Question Prompt */}
        <div className="p-3.5 rounded-lg bg-[#090d16] border border-gray-800 text-sm text-gray-200 leading-relaxed font-sans">
          {prompt.question}
        </div>

        {/* User Response Form */}
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">
              Your Guidance / Clarification:
            </label>
            <textarea
              value={response}
              onChange={(e) => setResponse(e.target.value)}
              placeholder="e.g., Focus specifically on the FastAPI auth routers in /api and JWT handling."
              rows={3}
              className="w-full bg-[#090d16] border border-gray-800 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 resize-none"
              autoFocus
              required
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="submit"
              disabled={isSubmitting || !response.trim()}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:bg-gray-800 disabled:text-gray-500 text-white text-xs font-semibold transition cursor-pointer disabled:cursor-not-allowed"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Resuming...</span>
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5" />
                  <span>Submit Guidance & Resume</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

