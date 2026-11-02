'use client';

import React, { useState, useRef } from 'react';
import { Header } from '../components/Header';
import { RepoSelector } from '../components/RepoSelector';
import { PlanChecklist } from '../components/PlanChecklist';
import { ToolActivityFeed } from '../components/ToolActivityFeed';
import { EvidencePanel } from '../components/EvidencePanel';
import { AnswerView } from '../components/AnswerView';
import { ClarificationModal } from '../components/ClarificationModal';
import {
  InvestigationState,
  ToolCallItem,
  ReflectionItem,
  EvidenceItem,
  FindingItem,
  PlanGoal,
  ClarificationPrompt,
} from '../types';

export default function Home() {
  const [state, setState] = useState<InvestigationState>({
    investigation_id: '',
    status: 'IDLE',
    repo_path: '',
    query: '',
    plan: [],
    plan_version: 1,
    toolCalls: [],
    reflections: [],
    evidenceStore: [],
    findings: [],
    tokens: [],
    limitations: [],
    clarificationPrompt: null,
  });

  const eventSourceRef = useRef<EventSource | null>(null);

  const handleStartInvestigation = async (
    repoPath: string,
    query: string,
    maxSteps: number
  ) => {
    // Close any previous event source
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    // Reset state for new investigation
    setState({
      investigation_id: '',
      status: 'INITIALIZED',
      repo_path: repoPath,
      query: query,
      plan: [],
      plan_version: 1,
      toolCalls: [],
      reflections: [],
      evidenceStore: [],
      findings: [],
      tokens: [],
      limitations: [],
      clarificationPrompt: null,
    });

    try {
      const resp = await fetch('/api/investigate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo_path: repoPath,
          query: query,
          max_steps: maxSteps,
        }),
      });

      if (!resp.ok) {
        const errorData = await resp.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to start investigation');
      }

      const data = await resp.json();
      const invId = data.investigation_id;

      setState((prev) => ({
        ...prev,
        investigation_id: invId,
        status: 'RUNNING',
      }));

      // Connect to Server-Sent Events stream
      const eventSource = new EventSource(`/api/investigate/stream/${invId}`);
      eventSourceRef.current = eventSource;

      // 1. node_change
      eventSource.addEventListener('node_change', (e: MessageEvent) => {
        try {
          const payload = JSON.parse(e.data);
          setState((prev) => ({
            ...prev,
            currentNode: payload.node,
          }));
        } catch {}
      });

      // 2. plan_update
      eventSource.addEventListener('plan_update', (e: MessageEvent) => {
        try {
          const payload = JSON.parse(e.data);
          setState((prev) => ({
            ...prev,
            plan: payload.plan || [],
            plan_version: payload.plan_version || prev.plan_version,
          }));
        } catch {}
      });

      // 3. tool_call
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
          setState((prev) => ({
            ...prev,
            toolCalls: [...prev.toolCalls, newCall],
          }));
        } catch {}
      });

      // 4. tool_result
      eventSource.addEventListener('tool_result', (e: MessageEvent) => {
        try {
          const payload = JSON.parse(e.data);
          setState((prev) => {
            const updated = [...prev.toolCalls];
            if (updated.length > 0) {
              const lastIdx = updated.length - 1;
              updated[lastIdx] = {
                ...updated[lastIdx],
                status: payload.status,
                summary: payload.summary,
              };
            }
            return {
              ...prev,
              toolCalls: updated,
            };
          });
        } catch {}
      });

      // 5. reflection
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
          setState((prev) => ({
            ...prev,
            reflections: [...prev.reflections, newRef],
          }));
        } catch {}
      });

      // 6. token
      eventSource.addEventListener('token', (e: MessageEvent) => {
        try {
          const payload = JSON.parse(e.data);
          if (payload.token) {
            setState((prev) => ({
              ...prev,
              tokens: [...prev.tokens, payload.token],
            }));
          }
        } catch {}
      });

      // 7. interrupt (clarification required)
      eventSource.addEventListener('interrupt', (e: MessageEvent) => {
        try {
          const payload: ClarificationPrompt = JSON.parse(e.data);
          setState((prev) => ({
            ...prev,
            status: 'PAUSED',
            clarificationPrompt: payload,
          }));
        } catch {}
      });

      // 8. done
      eventSource.addEventListener('done', (e: MessageEvent) => {
        try {
          const payload = JSON.parse(e.data);
          setState((prev) => ({
            ...prev,
            status: payload.status || 'COMPLETED',
            final_answer: payload.final_answer,
            limitations: payload.limitations || [],
            currentNode: undefined,
          }));
          eventSource.close();
        } catch {}
      });

      // Error handler
      eventSource.onerror = async () => {
        // Fetch state to see if it finished or paused
        try {
          const stateRes = await fetch(`/api/investigate/${invId}/state`);
          if (stateRes.ok) {
            const stateData = await stateRes.json();
            setState((prev) => ({
              ...prev,
              status: stateData.status,
              final_answer: stateData.final_answer || prev.final_answer,
              plan: stateData.plan || prev.plan,
              evidenceStore: stateData.evidence_store || prev.evidenceStore,
              findings: stateData.findings || prev.findings,
              limitations: stateData.limitations || prev.limitations,
              currentNode: undefined,
            }));
          }
        } catch {}
        eventSource.close();
      };
    } catch (err: any) {
      setState((prev) => ({
        ...prev,
        status: 'FAILED',
        error: err.message,
      }));
    }
  };

  const handleResume = async (response: string) => {
    if (!state.investigation_id) return;
    try {
      const resp = await fetch(`/api/investigate/resume/${state.investigation_id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ response }),
      });
      if (!resp.ok) {
        throw new Error('Failed to resume investigation.');
      }
      setState((prev) => ({
        ...prev,
        status: 'RUNNING',
        clarificationPrompt: null,
      }));
    } catch (err: any) {
      alert(`Error resuming investigation: ${err.message}`);
    }
  };

  const isInvestigating = state.status === 'RUNNING' || state.status === 'INITIALIZED';

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 font-sans">
      {/* Top Header */}
      <Header
        currentNode={state.currentNode}
        status={state.status}
        commitSha={state.commit_sha}
        investigationId={state.investigation_id}
      />

      {/* Main Grid Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 md:p-6 space-y-5">
        {state.error && (
          <div className="p-3.5 rounded-none bg-red-50 border border-red-200 text-red-800 text-xs font-mono">
            <strong>ERROR:</strong> {state.error}
          </div>
        )}

        {/* Upper Row: Repo Selector (left) & Plan Checklist (right) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          <div className="lg:col-span-7">
            <RepoSelector onStart={handleStartInvestigation} isLoading={isInvestigating} />
          </div>
          <div className="lg:col-span-5">
            <PlanChecklist plan={state.plan} planVersion={state.plan_version} />
          </div>
        </div>

        {/* Middle Row: Tool Activity Feed (left) & Evidence Panel (right) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          <div className="lg:col-span-7">
            <ToolActivityFeed
              toolCalls={state.toolCalls}
              reflections={state.reflections}
            />
          </div>
          <div className="lg:col-span-5">
            <EvidencePanel
              evidenceStore={state.evidenceStore}
              findings={state.findings}
            />
          </div>
        </div>

        {/* Lower Row: Synthesized Final Answer with Line Citations */}
        <AnswerView
          answer={state.final_answer}
          streamingTokens={state.tokens}
          findings={state.findings}
          limitations={state.limitations}
          status={state.status}
        />
      </main>

      {/* Clarification Modal Dialog */}
      <ClarificationModal
        prompt={state.clarificationPrompt || null}
        investigationId={state.investigation_id}
        onResume={handleResume}
      />
    </div>
  );
}

