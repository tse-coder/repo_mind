'use client';

import React, { useEffect, useRef, useState } from 'react';
import { Loader2, Send, AlertCircle } from 'lucide-react';
import { ChatSession } from '../types';
import { RepoSelector } from './RepoSelector';
import { MarkdownRenderer } from './MarkdownRenderer';
import { ThoughtProcess } from './ThoughtProcess';

interface ChatPaneProps {
  chat: ChatSession | null;
  isInvestigating: boolean;
  onStart: (repoPath: string, query: string, maxSteps: number) => void;
}

export const ChatPane: React.FC<ChatPaneProps> = ({ chat, isInvestigating, onStart }) => {
  const [followUp, setFollowUp] = useState('');
  const bottomRef = useRef<HTMLDivElement | null>(null);

  const assistantLive =
    chat && (chat.state.tokens.length > 0 || chat.state.final_answer)
      ? chat.state.final_answer || chat.state.tokens.join('')
      : '';

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chat?.messages.length, assistantLive, chat?.state.status]);

  if (!chat) {
    return (
      <div className="h-full flex flex-col min-h-0 bg-slate-50">
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-2xl mx-auto space-y-4">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Investigate a repository</h2>
              <p className="text-sm text-slate-500 mt-1">
                Ask architectural, flow, or definition questions. Answers cite verified source lines.
              </p>
            </div>
            <RepoSelector onStart={onStart} isLoading={false} />
          </div>
        </div>
      </div>
    );
  }

  const showComposerSetup = chat.messages.length === 0 && chat.state.status === 'IDLE';

  return (
    <div className="h-full flex flex-col min-h-0 bg-slate-50">
      {chat.state.error && (
        <div className="mx-4 mt-3 p-3 bg-red-50 border border-red-200 text-red-800 text-xs font-mono rounded-xl">
          <strong>ERROR:</strong> {chat.state.error}
        </div>
      )}

      <div className="flex-1 overflow-y-auto min-h-0 px-4 py-4 space-y-5">
        {showComposerSetup && (
          <div className="max-w-2xl mx-auto space-y-3">
            <p className="text-sm text-slate-600">
              Select a local repository and ask a question. Tool traces appear in the right pane.
            </p>
            <RepoSelector onStart={onStart} isLoading={isInvestigating} />
          </div>
        )}

        {chat.messages.map((msg, idx) => {
          const isLast = idx === chat.messages.length - 1;
          const body =
            msg.role === 'assistant' && isLast && (isInvestigating || !msg.content)
              ? assistantLive || msg.content
              : msg.content;
          const isUser = msg.role === 'user';

          // Extract thought process data for this message
          const isCurrentInvestigating = isLast && isInvestigating;
          const messageToolCalls =
            (isLast && chat.state.toolCalls.length > 0 ? chat.state.toolCalls : msg.toolCalls) || [];
          const messagePlan =
            (isLast && chat.state.plan.length > 0 ? chat.state.plan : msg.plan) || [];
          const messageReflections =
            (isLast && chat.state.reflections.length > 0 ? chat.state.reflections : msg.reflections) || [];

          return (
            <div key={msg.id} className={`flex ${isUser ? 'justify-end' : 'justify-start'} min-w-0 max-w-full`}>
              {isUser ? (
                /* User request box: subtle light background, light border, rounded */
                <div className="max-w-[80%] px-4 py-2.5 bg-slate-100 border border-slate-200/90 text-slate-900 rounded-2xl rounded-br-sm shadow-xs text-sm">
                  <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                </div>
              ) : (
                /* AI response: plain background, no border, text rendered cleanly */
                <div className="w-full min-w-0 max-w-full text-slate-900 text-sm py-1">
                  <ThoughtProcess
                    isInvestigating={isCurrentInvestigating}
                    currentNode={isCurrentInvestigating ? chat.state.currentNode : undefined}
                    toolCalls={messageToolCalls}
                    plan={messagePlan}
                    reflections={messageReflections}
                  />

                  {body ? (
                    <div className="mt-1">
                      <MarkdownRenderer content={body} />
                    </div>
                  ) : isCurrentInvestigating ? null : (
                    <span className="flex items-center gap-2 text-xs font-mono text-slate-400 py-1">
                      No response generated.
                    </span>
                  )}
                </div>
              )}
            </div>
          );
        })}

        {chat.state.limitations.length > 0 && chat.state.status !== 'RUNNING' && (
          <div className="w-full p-3 bg-amber-50 border border-amber-200 text-xs text-slate-700 space-y-1 rounded-xl">
            <div className="flex items-center gap-1.5 font-mono font-semibold text-amber-800 uppercase tracking-wider">
              <AlertCircle className="w-3.5 h-3.5" />
              Limitations
            </div>
            <ul className="list-disc list-inside">
              {chat.state.limitations.map((lim, i) => (
                <li key={i}>{lim}</li>
              ))}
            </ul>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {!showComposerSetup && (
        <form
          className="border-t border-slate-200 bg-white p-3 space-y-2"
          onSubmit={(e) => {
            e.preventDefault();
            if (!followUp.trim() || isInvestigating || !chat.state.repo_path) return;
            onStart(chat.state.repo_path, followUp.trim(), chat.maxSteps);
            setFollowUp('');
          }}
        >
          {chat.state.repo_path && (
            <div className="text-[10px] font-mono text-slate-500 truncate">
              repo: {chat.state.repo_path}
            </div>
          )}
          <div className="flex items-end gap-2">
            <textarea
              value={followUp}
              onChange={(e) => setFollowUp(e.target.value)}
              placeholder={
                isInvestigating ? 'Investigation in progress...' : 'Ask a follow-up about this repository...'
              }
              rows={2}
              disabled={isInvestigating}
              className="flex-1 bg-white border border-slate-300 rounded-xl px-3.5 py-2 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900/10 focus:border-slate-800 resize-none font-sans"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  (e.currentTarget.form as HTMLFormElement | null)?.requestSubmit();
                }
              }}
            />
            <button
              type="submit"
              disabled={isInvestigating || !followUp.trim() || !chat.state.repo_path}
              className="h-10 w-10 flex items-center justify-center rounded-xl bg-slate-900 text-white hover:bg-slate-800 disabled:bg-slate-100 disabled:text-slate-400 border border-slate-900 transition shadow-xs cursor-pointer disabled:cursor-not-allowed"
            >
              {isInvestigating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            </button>
          </div>
        </form>
      )}
    </div>
  );
};
