'use client';

import React, { useEffect, useState } from 'react';
import { Cpu, GitBranch, Activity, ShieldCheck, AlertCircle } from 'lucide-react';

interface HeaderProps {
  currentNode?: string;
  status: string;
  commitSha?: string;
  investigationId?: string;
}

export const Header: React.FC<HeaderProps> = ({
  currentNode,
  status,
  commitSha,
  investigationId,
}) => {
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch('/api/health');
        if (res.ok) {
          setBackendOnline(true);
        } else {
          setBackendOnline(false);
        }
      } catch {
        setBackendOnline(false);
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (s: string) => {
    switch (s) {
      case 'RUNNING':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/30';
      case 'PAUSED':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      case 'COMPLETED':
      case 'SUFFICIENT':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'PARTIAL':
        return 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30';
      case 'FAILED':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
      default:
        return 'bg-gray-800 text-gray-400 border-gray-700';
    }
  };

  return (
    <header className="border-b border-[#1f2937] bg-[#0c1220]/90 backdrop-blur sticky top-0 z-40 px-6 py-3.5 flex items-center justify-between">
      {/* Brand */}
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
          <Cpu className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-base font-bold tracking-tight text-white">RepoMind</h1>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-300 font-semibold border border-blue-500/30">
              v1.0 (LangGraph)
            </span>
          </div>
          <p className="text-xs text-gray-400">Autonomous Read-Only Repository Investigation Agent</p>
        </div>
      </div>

      {/* Middle Status Indicators */}
      <div className="flex items-center gap-3">
        {commitSha && (
          <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-gray-900 border border-gray-800 text-xs font-mono text-gray-300">
            <GitBranch className="w-3.5 h-3.5 text-blue-400" />
            <span className="text-gray-400">Snapshot:</span>
            <span className="font-semibold text-gray-200">{commitSha}</span>
          </div>
        )}

        {investigationId && (
          <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-gray-900 border border-gray-800 text-xs font-mono text-gray-300">
            <span className="text-gray-500">ID:</span>
            <span className="text-gray-300">{investigationId}</span>
          </div>
        )}

        {currentNode && (
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/30 text-xs font-mono text-blue-300 animate-pulse-subtle">
            <Activity className="w-3.5 h-3.5 text-blue-400 animate-spin" />
            <span>Node: <strong className="text-white">{currentNode}</strong></span>
          </div>
        )}

        <div className={`px-2.5 py-1 rounded-full text-xs font-semibold border uppercase tracking-wider ${getStatusColor(status)}`}>
          {status}
        </div>
      </div>

      {/* Backend API Health Status */}
      <div className="flex items-center gap-2">
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-gray-900/80 border border-gray-800 text-xs">
          {backendOnline === true && (
            <>
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-gray-300 font-medium">API Connected</span>
            </>
          )}
          {backendOnline === false && (
            <>
              <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
              <span className="text-rose-400 font-medium">Backend Offline</span>
            </>
          )}
          {backendOnline === null && (
            <>
              <span className="w-2 h-2 rounded-full bg-gray-500" />
              <span className="text-gray-400">Connecting...</span>
            </>
          )}
        </div>
      </div>
    </header>
  );
};

