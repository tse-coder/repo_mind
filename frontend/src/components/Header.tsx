'use client';

import React, { useEffect, useState } from 'react';
import { Terminal, GitBranch, Activity, AlertCircle, CheckCircle2 } from 'lucide-react';

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

  const getStatusBadge = (s: string) => {
    switch (s) {
      case 'RUNNING':
        return 'bg-blue-50 text-blue-700 border-blue-300';
      case 'PAUSED':
        return 'bg-amber-50 text-amber-700 border-amber-300';
      case 'COMPLETED':
      case 'SUFFICIENT':
        return 'bg-emerald-50 text-emerald-700 border-emerald-300';
      case 'PARTIAL':
        return 'bg-yellow-50 text-yellow-800 border-yellow-300';
      case 'FAILED':
        return 'bg-red-50 text-red-700 border-red-300';
      default:
        return 'bg-slate-100 text-slate-600 border-slate-300';
    }
  };

  return (
    <header className="border-b border-slate-200 bg-white sticky top-0 z-40 px-6 py-3 flex items-center justify-between">
      {/* Brand */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 bg-slate-900 text-white rounded-none flex items-center justify-center font-mono font-bold text-xs tracking-wider">
          RM
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-sm font-semibold tracking-tight text-slate-900">RepoMind</h1>
            <span className="text-[10px] font-mono px-1.5 py-0.2 rounded-none bg-slate-100 text-slate-600 border border-slate-200 font-medium">
              read-only engine
            </span>
          </div>
          <p className="text-xs text-slate-500">Local Repository Investigation Agent</p>
        </div>
      </div>

      {/* Middle Status Indicators */}
      <div className="flex items-center gap-2.5">
        {commitSha && (
          <div className="hidden sm:flex items-center gap-1.5 px-2 py-0.5 rounded-none bg-slate-100 border border-slate-200 text-xs font-mono text-slate-700">
            <GitBranch className="w-3.5 h-3.5 text-slate-500" />
            <span className="text-slate-400">commit:</span>
            <span className="font-semibold text-slate-800">{commitSha}</span>
          </div>
        )}

        {investigationId && (
          <div className="hidden md:flex items-center gap-1.5 px-2 py-0.5 rounded-none bg-slate-100 border border-slate-200 text-xs font-mono text-slate-700">
            <span className="text-slate-400">id:</span>
            <span>{investigationId}</span>
          </div>
        )}

        {currentNode && (
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-none bg-blue-50 border border-blue-200 text-xs font-mono text-blue-700">
            <Activity className="w-3.5 h-3.5 text-blue-600 animate-spin" />
            <span>node: <strong>{currentNode}</strong></span>
          </div>
        )}

        <div className={`px-2 py-0.5 rounded-none text-xs font-mono font-medium border uppercase tracking-wider ${getStatusBadge(status)}`}>
          {status}
        </div>
      </div>

      {/* Backend API Health Status */}
      <div className="flex items-center gap-2">
        <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-none bg-slate-100 border border-slate-200 text-xs">
          {backendOnline === true && (
            <>
              <span className="w-2 h-2 rounded-none bg-emerald-600" />
              <span className="text-slate-700 font-medium text-[11px]">API Online</span>
            </>
          )}
          {backendOnline === false && (
            <>
              <AlertCircle className="w-3 h-3 text-red-600" />
              <span className="text-red-600 font-medium text-[11px]">API Offline</span>
            </>
          )}
          {backendOnline === null && (
            <>
              <span className="w-2 h-2 rounded-none bg-slate-400" />
              <span className="text-slate-500 text-[11px]">Connecting...</span>
            </>
          )}
        </div>
      </div>
    </header>
  );
};
