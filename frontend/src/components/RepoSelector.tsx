'use client';

import React, { useState } from 'react';
import { Folder, Search, Sparkles, Sliders, Play, Loader2 } from 'lucide-react';

interface RepoSelectorProps {
  onStart: (repoPath: string, query: string, maxSteps: number) => void;
  isLoading: boolean;
}

const QUICK_PATHS = [
  { label: 'Sample Auth Repo', path: 'tests/fixtures/sample_repo' },
  { label: 'RepoMind Engine', path: '.' },
];

const EXAMPLE_QUERIES = [
  'Where is the login handler and authentication logic defined?',
  'Trace how requests flow from auth router to user model.',
  'What security policies and sandbox protections are enforced?',
  'Where are secrets redacted before entering LLM context?',
];

export const RepoSelector: React.FC<RepoSelectorProps> = ({ onStart, isLoading }) => {
  const [repoPath, setRepoPath] = useState('tests/fixtures/sample_repo');
  const [query, setQuery] = useState('Where is the login handler and authentication logic defined?');
  const [maxSteps, setMaxSteps] = useState(5);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoPath.trim() || !query.trim() || isLoading) return;
    onStart(repoPath.trim(), query.trim(), maxSteps);
  };

  return (
    <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-5 shadow-lg">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Repo Path Input */}
        <div>
          <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
            <Folder className="w-3.5 h-3.5 text-blue-400" />
            Target Repository Directory
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              value={repoPath}
              onChange={(e) => setRepoPath(e.target.value)}
              placeholder="/absolute/path/to/local/project or relative path"
              className="flex-1 bg-[#090d16] border border-gray-800 rounded-lg px-3.5 py-2 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 font-mono"
              disabled={isLoading}
              required
            />
          </div>
          {/* Quick path chips */}
          <div className="flex items-center gap-2 mt-2">
            <span className="text-[11px] text-gray-500">Quick select:</span>
            {QUICK_PATHS.map((item) => (
              <button
                key={item.path}
                type="button"
                onClick={() => setRepoPath(item.path)}
                className="text-[11px] px-2 py-0.5 rounded bg-gray-800/80 hover:bg-gray-700 text-gray-300 border border-gray-700/60 transition"
                disabled={isLoading}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>

        {/* Query Input */}
        <div>
          <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
            <Search className="w-3.5 h-3.5 text-blue-400" />
            Investigation Query
          </label>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask an architectural, flow-tracing, error-origin, or symbol question..."
            rows={2}
            className="w-full bg-[#090d16] border border-gray-800 rounded-lg px-3.5 py-2 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 resize-none"
            disabled={isLoading}
            required
          />
          {/* Example query chips */}
          <div className="flex flex-wrap items-center gap-1.5 mt-2">
            <span className="text-[11px] text-gray-500 flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-amber-400" /> Examples:
            </span>
            {EXAMPLE_QUERIES.map((q, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setQuery(q)}
                className="text-[11px] px-2 py-0.5 rounded bg-blue-950/40 hover:bg-blue-900/50 text-blue-300 border border-blue-800/40 transition truncate max-w-[280px]"
                disabled={isLoading}
                title={q}
              >
                {q}
              </button>
            ))}
          </div>
        </div>

        {/* Controls Row */}
        <div className="pt-2 border-t border-gray-800/80 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-400 flex items-center gap-1.5">
              <Sliders className="w-3.5 h-3.5 text-gray-400" /> Max Tool Steps:
            </span>
            <input
              type="range"
              min="1"
              max="20"
              value={maxSteps}
              onChange={(e) => setMaxSteps(parseInt(e.target.value, 10))}
              className="w-28 accent-blue-500 cursor-pointer"
              disabled={isLoading}
            />
            <span className="text-xs font-mono font-bold text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">
              {maxSteps}
            </span>
          </div>

          <button
            type="submit"
            disabled={isLoading || !repoPath.trim() || !query.trim()}
            className="flex items-center gap-2 px-5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:bg-gray-800 disabled:text-gray-500 text-white text-sm font-semibold shadow-lg shadow-blue-600/20 transition cursor-pointer disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Investigating...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-white" />
                <span>Run Investigation</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

