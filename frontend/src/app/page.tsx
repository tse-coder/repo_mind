'use client';

import React, { useEffect, useRef, useState } from 'react';
import { Header } from '../components/Header';
import { ChatList } from '../components/ChatList';
import { ChatPane } from '../components/ChatPane';
import { DetailsPanel } from '../components/DetailsPanel';
import { ClarificationModal } from '../components/ClarificationModal';
import {
  ChatSession,
  ClarificationPrompt,
  InvestigationState,
  ReflectionItem,
  ToolCallItem,
  createEmptyInvestigation,
} from '../types';
import { List, MessageSquare, PanelRight } from 'lucide-react';

const STORAGE_KEY = 'repomind.chats.v1';

type MobilePane = 'list' | 'chat' | 'details';

function newChatSession(): ChatSession {
  const now = Date.now();
  return {
    id: `chat_${now}_${Math.random().toString(36).slice(2, 8)}`,
    title: 'New investigation',
    createdAt: now,
    updatedAt: now,
    maxSteps: 15,
    messages: [],
    state: createEmptyInvestigation(),
  };
}

function patchChat(
  chats: ChatSession[],
  chatId: string,
  updater: (chat: ChatSession) => ChatSession
): ChatSession[] {
  return chats.map((c) => (c.id === chatId ? updater({ ...c, updatedAt: Date.now() }) : c));
}

export default function Home() {
  const [chats, setChats] = useState<ChatSession[]>([]);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [hydrated, setHydrated] = useState(false);
  const [mobilePane, setMobilePane] = useState<MobilePane>('chat');
  const eventSourceRef = useRef<EventSource | null>(null);
  const chatByInvestigation = useRef<Map<string, string>>(new Map());

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as { chats?: ChatSession[]; activeChatId?: string };
        if (Array.isArray(parsed.chats)) {
          setChats(parsed.chats);
          setActiveChatId(parsed.activeChatId || parsed.chats[0]?.id || null);
        }
      }
    } catch {}
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ chats, activeChatId }));
    } catch {}
  }, [chats, activeChatId, hydrated]);

  const activeChat = chats.find((c) => c.id === activeChatId) || null;
  const displayState: InvestigationState = activeChat?.state || createEmptyInvestigation();
  const isInvestigating =
    displayState.status === 'RUNNING' || displayState.status === 'INITIALIZED';

  const handleNewChat = () => {
    const created = newChatSession();
    setChats((prev) => [created, ...prev]);
    setActiveChatId(created.id);
    setMobilePane('chat');
  };

  const handleDeleteChat = (id: string) => {
    setChats((prev) => prev.filter((c) => c.id !== id));
    setActiveChatId((current) => {
      if (current !== id) return current;
      const remaining = chats.filter((c) => c.id !== id);
      return remaining[0]?.id || null;
    });
  };

  const updateChat = (chatId: string, updater: (chat: ChatSession) => ChatSession) => {
    setChats((prev) => patchChat(prev, chatId, updater));
  };

  const handleStartInvestigation = async (
    repoPath: string,
    query: string,
    maxSteps: number
  ) => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    let chatId = activeChatId;
    if (!chatId) {
      const created = newChatSession();
      chatId = created.id;
      setChats((prev) => [created, ...prev]);
      setActiveChatId(created.id);
    }
    const targetChatId = chatId;

    const userMsg = {
      id: `msg_${Date.now()}_u`,
      role: 'user' as const,
      content: query,
      timestamp: Date.now(),
    };
    const assistantMsg = {
      id: `msg_${Date.now()}_a`,
      role: 'assistant' as const,
      content: '',
      timestamp: Date.now(),
    };

    const existingInvId = activeChat?.state.investigation_id;

    updateChat(targetChatId, (chat) => {
      const isFirstTurn = chat.messages.length === 0;
      return {
        ...chat,
        title: isFirstTurn ? (query.length > 72 ? `${query.slice(0, 72)}…` : query) : chat.title,
        maxSteps,
        messages: [...chat.messages, userMsg, assistantMsg],
        state: isFirstTurn
          ? createEmptyInvestigation({
              status: 'INITIALIZED',
              repo_path: repoPath,
              query,
            })
          : {
              ...chat.state,
              status: 'INITIALIZED',
              query,
              tokens: [],
              final_answer: undefined,
              currentNode: undefined,
              error: undefined,
            },
      };
    });
    setMobilePane('chat');

    try {
      const resp = await fetch('/api/investigate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo_path: repoPath,
          query,
          max_steps: maxSteps,
          session_id: existingInvId || undefined,
        }),
      });

      if (!resp.ok) {
        const errorData = await resp.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to start investigation');
      }

      const data = await resp.json();
      const invId = data.investigation_id as string;
      chatByInvestigation.current.set(invId, targetChatId);

      updateChat(targetChatId, (chat) => ({
        ...chat,
        state: {
          ...chat.state,
          investigation_id: invId,
          status: 'RUNNING',
        },
      }));

      const eventSource = new EventSource(`/api/investigate/stream/${invId}`);
      eventSourceRef.current = eventSource;

      eventSource.addEventListener('node_change', (e: MessageEvent) => {
        try {
          const payload = JSON.parse(e.data);
          updateChat(targetChatId, (chat) => ({
            ...chat,
            state: { ...chat.state, currentNode: payload.node },
          }));
        } catch {}
      });

      eventSource.addEventListener('plan_update', (e: MessageEvent) => {
        try {
          const payload = JSON.parse(e.data);
          updateChat(targetChatId, (chat) => ({
            ...chat,
            state: {
              ...chat.state,
              plan: payload.plan || [],
              plan_version: payload.plan_version || chat.state.plan_version,
            },
          }));
        } catch {}
      });

      eventSource.addEventListener('tool_call', (e: MessageEvent) => {
        try {
          const payload = JSON.parse(e.data);
          const newCall: ToolCallItem = {
            id: `call_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
            tool: payload.tool,
            arguments: payload.arguments || {},
            rationale: payload.rationale || '',
            status: 'PENDING',
            timestamp: Date.now(),
          };
          updateChat(targetChatId, (chat) => ({
            ...chat,
            state: { ...chat.state, toolCalls: [...chat.state.toolCalls, newCall] },
          }));
        } catch {}
      });

      eventSource.addEventListener('tool_result', (e: MessageEvent) => {
        try {
          const payload = JSON.parse(e.data);
          updateChat(targetChatId, (chat) => {
            const updated = [...chat.state.toolCalls];
            if (updated.length > 0) {
              const lastIdx = updated.length - 1;
              updated[lastIdx] = {
                ...updated[lastIdx],
                status: payload.status,
                summary: payload.summary,
              };
            }
            return { ...chat, state: { ...chat.state, toolCalls: updated } };
          });
        } catch {}
      });

      eventSource.addEventListener('reflection', (e: MessageEvent) => {
        try {
          const payload = JSON.parse(e.data);
          const newRef: ReflectionItem = {
            id: `ref_${Date.now()}`,
            trigger: payload.trigger,
            diagnosis: payload.diagnosis,
            next_approach: payload.next_approach,
            timestamp: Date.now(),
          };
          updateChat(targetChatId, (chat) => ({
            ...chat,
            state: { ...chat.state, reflections: [...chat.state.reflections, newRef] },
          }));
        } catch {}
      });

      eventSource.addEventListener('token', (e: MessageEvent) => {
        try {
          const payload = JSON.parse(e.data);
          if (payload.token) {
            updateChat(targetChatId, (chat) => {
              const tokens = [...chat.state.tokens, payload.token];
              const live = tokens.join('');
              const messages = chat.messages.map((m, i, arr) =>
                i === arr.length - 1 && m.role === 'assistant' ? { ...m, content: live } : m
              );
              return { ...chat, messages, state: { ...chat.state, tokens } };
            });
          }
        } catch {}
      });

      eventSource.addEventListener('interrupt', (e: MessageEvent) => {
        try {
          const payload: ClarificationPrompt = JSON.parse(e.data);
          updateChat(targetChatId, (chat) => ({
            ...chat,
            state: { ...chat.state, status: 'PAUSED', clarificationPrompt: payload },
          }));
        } catch {}
      });

      eventSource.addEventListener('done', (e: MessageEvent) => {
        try {
          const payload = JSON.parse(e.data);
          updateChat(targetChatId, (chat) => {
            const answer = payload.final_answer || chat.state.final_answer || chat.state.tokens.join('');
            const messages = chat.messages.map((m, i, arr) =>
              i === arr.length - 1 && m.role === 'assistant' ? { ...m, content: answer } : m
            );
            return {
              ...chat,
              messages,
              state: {
                ...chat.state,
                status: payload.status || 'COMPLETED',
                final_answer: payload.final_answer,
                limitations: payload.limitations || [],
                currentNode: undefined,
              },
            };
          });
          eventSource.close();
        } catch {}
      });

      eventSource.onerror = async () => {
        try {
          const stateRes = await fetch(`/api/investigate/${invId}/state`);
          if (stateRes.ok) {
            const stateData = await stateRes.json();
            updateChat(targetChatId, (chat) => {
              const answer = stateData.final_answer || chat.state.final_answer || chat.state.tokens.join('');
              const messages = chat.messages.map((m, i, arr) =>
                i === arr.length - 1 && m.role === 'assistant' && answer
                  ? { ...m, content: answer }
                  : m
              );
              return {
                ...chat,
                messages,
                state: {
                  ...chat.state,
                  status: stateData.status,
                  final_answer: stateData.final_answer || chat.state.final_answer,
                  plan: stateData.plan || chat.state.plan,
                  evidenceStore: stateData.evidence_store || chat.state.evidenceStore,
                  findings: stateData.findings || chat.state.findings,
                  limitations: stateData.limitations || chat.state.limitations,
                  currentNode: undefined,
                },
              };
            });
          }
        } catch {}
        eventSource.close();
      };
    } catch (err: any) {
      updateChat(targetChatId, (chat) => ({
        ...chat,
        state: { ...chat.state, status: 'FAILED', error: err.message },
      }));
    }
  };

  const handleResume = async (response: string) => {
    if (!displayState.investigation_id) return;
    try {
      const resp = await fetch(`/api/investigate/resume/${displayState.investigation_id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ response }),
      });
      if (!resp.ok) {
        throw new Error('Failed to resume investigation.');
      }
      if (activeChatId) {
        updateChat(activeChatId, (chat) => ({
          ...chat,
          state: { ...chat.state, status: 'RUNNING', clarificationPrompt: null },
        }));
      }
    } catch (err: any) {
      alert(`Error resuming investigation: ${err.message}`);
    }
  };

  return (
    <div className="h-screen flex flex-col bg-slate-50 text-slate-900 font-sans overflow-hidden">
      <Header
        currentNode={displayState.currentNode}
        status={displayState.status}
        commitSha={displayState.commit_sha}
        investigationId={displayState.investigation_id}
      />

      <div className="md:hidden flex border-b border-slate-200 bg-white shrink-0">
        {(
          [
            ['list', List, 'Chats'],
            ['chat', MessageSquare, 'Chat'],
            ['details', PanelRight, 'Tools'],
          ] as const
        ).map(([id, Icon, label]) => (
          <button
            key={id}
            type="button"
            onClick={() => setMobilePane(id)}
            className={`flex-1 flex items-center justify-center gap-1.5 py-2 text-[11px] font-mono uppercase ${
              mobilePane === id ? 'text-slate-900 border-b-2 border-slate-900' : 'text-slate-500'
            }`}
          >
            <Icon className="w-3.5 h-3.5" />
            {label}
          </button>
        ))}
      </div>

      <main className="flex-1 min-h-0 grid grid-cols-1 md:grid-cols-[16rem_minmax(0,1fr)_22rem] lg:grid-cols-[18rem_minmax(0,1fr)_24rem]">
        <section className={`min-h-0 ${mobilePane === 'list' ? 'block' : 'hidden'} md:block`}>
          <ChatList
            chats={chats}
            activeChatId={activeChatId}
            onSelect={(id) => {
              setActiveChatId(id);
              setMobilePane('chat');
            }}
            onNew={handleNewChat}
            onDelete={handleDeleteChat}
          />
        </section>

        <section className={`min-h-0 ${mobilePane === 'chat' ? 'block' : 'hidden'} md:block`}>
          <ChatPane
            chat={activeChat}
            isInvestigating={isInvestigating}
            onStart={handleStartInvestigation}
          />
        </section>

        <section className={`min-h-0 ${mobilePane === 'details' ? 'block' : 'hidden'} md:block`}>
          <DetailsPanel state={displayState} />
        </section>
      </main>

      <ClarificationModal
        prompt={displayState.clarificationPrompt || null}
        investigationId={displayState.investigation_id}
        onResume={handleResume}
      />
    </div>
  );
}
