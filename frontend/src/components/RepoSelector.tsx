'use client';

import React, { useEffect, useState } from 'react';
import {
  Folder,
  Search,
  Sliders,
  Play,
  Loader2,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';

interface RepoSelectorProps {
  onStart: (repoPath: string, query: string, maxSteps: number) => void;
  isLoading: boolean;
}

const QUICK_PATHS = [
  { label: 'Sample Auth Repo', path: 'tests/fixtures/sample_repo' },
  { label: 'RepoMind Engine', path: '.' },
];

const ARTIFACT_TEMPLATES = [
  { label: '🏗️ Architecture Map', query: 'Map the high-level system architecture, layers, and module dependencies into a diagram.' },
  { label: '🔄 Request Flow', query: 'Trace the end-to-end request lifecycle and data flow from route handler to database into a sequence diagram.' },
  { label: '🗄️ Database ERD', query: 'Extract the data models and database schemas into an entity-relationship ERD diagram.' },
  { label: '🔌 API Contracts', query: 'Extract and list all API endpoints, HTTP routes, methods, and schemas in an API contract table.' },
];

const EXAMPLE_QUERIES = [
  'Where is the login handler and authentication logic defined?',
  'What security policies and sandbox protections are enforced?',
];

export const RepoSelector: React.FC<RepoSelectorProps> = ({ onStart, isLoading }) => {
  const [repoPath, setRepoPath] = useState('tests/fixtures/sample_repo');
  const [query, setQuery] = useState('Where is the login handler and authentication logic defined?');
  const [maxSteps, setMaxSteps] = useState(15);
  const [resolvedInfo, setResolvedInfo] = useState<{
    exists: boolean;
    resolved_path?: string;
  } | null>(null);

  // Debounced auto-resolution check against backend
  useEffect(() => {
    if (!repoPath.trim()) {
      setResolvedInfo(null);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const res = await fetch(`/api/resolve-path?path=${encodeURIComponent(repoPath.trim())}`);
        if (res.ok) {
          const data = await res.json();
          setResolvedInfo({
            exists: data.exists,
            resolved_path: data.resolved_path,
          });
        }
      } catch {
        setResolvedInfo(null);
      }
    }, 200);

    return () => clearTimeout(timer);
  }, [repoPath]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const targetPath = resolvedInfo?.resolved_path || repoPath.trim();
    if (!targetPath || !query.trim() || isLoading) return;
    onStart(targetPath, query.trim(), maxSteps);
  };

  const handleFolderSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const firstFile = files[0] as any;
    let candidate = '';
    if (firstFile.path) {
      const fullPath = firstFile.path;
      candidate = fullPath.substring(0, fullPath.lastIndexOf('/')) || fullPath;
    } else if (firstFile.webkitRelativePath) {
      candidate = firstFile.webkitRelativePath.split('/')[0];
    }

    if (!candidate) return;

    try {
      const res = await fetch(`/api/resolve-path?path=${encodeURIComponent(candidate)}`);
      if (res.ok) {
        const data = await res.json();
        if (data.exists && data.resolved_path) {
          setRepoPath(data.resolved_path);
          setResolvedInfo({ exists: true, resolved_path: data.resolved_path });
          return;
        }
      }
    } catch {}

    setRepoPath(candidate);
  };

  return (
    <div className="bg-white border border-slate-200 rounded-none p-5 shadow-sm">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Builtin Folder Selector Input */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center gap-1.5 font-mono">
            <Folder className="w-3.5 h-3.5 text-slate-600" />
            Target Repository Directory
          </label>

          <div className="space-y-2">
            {/* Native browser directory selector input */}
            <input
              type="file"
              // @ts-ignore
              webkitdirectory=""
              directory=""
              onChange={handleFolderSelect}
              disabled={isLoading}
              className="w-full text-xs text-slate-600 file:mr-3 file:py-1.5 file:px-3 file:rounded-none file:border-0 file:text-xs file:font-mono file:font-semibold file:bg-slate-900 file:text-white hover:file:bg-slate-800 file:cursor-pointer cursor-pointer bg-slate-50 border border-slate-300 rounded-none p-1.5 focus:outline-none focus:border-slate-800"
            />

            {/* Editable path input showing current or selected path */}
            <div className="flex items-center gap-2">
              <span className="text-[11px] text-slate-500 font-mono shrink-0">Path:</span>
              <input
                type="text"
                value={repoPath}
                onChange={(e) => setRepoPath(e.target.value)}
                placeholder="/absolute/path/to/repository or relative path"
                className="flex-1 bg-white border border-slate-300 rounded-none px-3 py-1.5 text-xs text-slate-900 font-mono focus:outline-none focus:border-slate-800"
                disabled={isLoading}
                required
              />
            </div>

            {/* Live Path Resolution Feedback */}
            {resolvedInfo && (
              <div className="text-[11px] font-mono px-2 py-1 bg-slate-50 border border-slate-200 rounded-none">
                {resolvedInfo.exists ? (
                  <div className="flex items-center justify-between text-emerald-700">
                    <span className="flex items-center gap-1.5 truncate">
                      <CheckCircle2 className="w-3.5 h-3.5 shrink-0 text-emerald-600" />
                      <span className="text-slate-500">Verified:</span> {resolvedInfo.resolved_path}
                    </span>
                    {resolvedInfo.resolved_path !== repoPath && (
                      <button
                        type="button"
                        onClick={() => setRepoPath(resolvedInfo.resolved_path || repoPath)}
                        className="text-[10px] text-blue-600 underline ml-2 shrink-0 hover:text-blue-800"
                      >
                        Use Absolute
                      </button>
                    )}
                  </div>
                ) : (
                  <div className="flex items-center gap-1.5 text-amber-700">
                    <AlertCircle className="w-3.5 h-3.5 shrink-0 text-amber-600" />
                    <span>Path not found. Verify directory exists.</span>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Quick path chips */}
          <div className="flex items-center gap-1.5 mt-2">
            <span className="text-[11px] text-slate-400 font-mono">Quick:</span>
            {QUICK_PATHS.map((item) => (
              <button
                key={item.path}
                type="button"
                onClick={() => setRepoPath(item.path)}
                className="text-[11px] font-mono px-2 py-0.5 rounded-none bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-300 transition"
                disabled={isLoading}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>

        {/* Query Input */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center gap-1.5 font-mono">
            <Search className="w-3.5 h-3.5 text-slate-600" />
            Investigation Query
          </label>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter question about repository structure, flows, or symbols..."
            rows={2}
            className="w-full bg-white border border-slate-300 rounded-none px-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-slate-800 resize-none font-sans"
            disabled={isLoading}
            required
          />
          {/* Defined Artifact Action Chips */}
          <div className="flex flex-wrap items-center gap-1.5 mt-2">
            <span className="text-[11px] text-slate-500 font-mono font-semibold">
              Artifacts:
            </span>
            {ARTIFACT_TEMPLATES.map((tmpl, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setQuery(tmpl.query)}
                className="text-[11px] px-2 py-0.5 rounded-none bg-slate-900 hover:bg-slate-800 text-white font-mono font-medium border border-slate-900 transition flex items-center gap-1"
                disabled={isLoading}
                title={tmpl.query}
              >
                {tmpl.label}
              </button>
            ))}
          </div>

          {/* Example query chips */}
          <div className="flex flex-wrap items-center gap-1.5 mt-1.5">
            <span className="text-[11px] text-slate-400 font-mono">
              Questions:
            </span>
            {EXAMPLE_QUERIES.map((q, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setQuery(q)}
                className="text-[11px] px-2 py-0.5 rounded-none bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 transition truncate max-w-[280px]"
                disabled={isLoading}
                title={q}
              >
                {q}
              </button>
            ))}
          </div>
        </div>

        {/* Controls Row */}
        <div className="pt-2 border-t border-slate-200 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-600 flex items-center gap-1.5 font-mono">
              <Sliders className="w-3.5 h-3.5 text-slate-500" /> Max Steps:
            </span>
            <input
              type="range"
              min="5"
              max="40"
              step="5"
              value={maxSteps}
              onChange={(e) => setMaxSteps(parseInt(e.target.value, 10))}
              className="w-28 accent-slate-900 cursor-pointer"
              disabled={isLoading}
            />
            <span className="text-xs font-mono font-bold text-slate-900 bg-slate-100 px-2 py-0.5 rounded-none border border-slate-300">
              {maxSteps}
            </span>
          </div>

          <button
            type="submit"
            disabled={isLoading || !repoPath.trim() || !query.trim() || (resolvedInfo !== null && !resolvedInfo.exists)}
            className="flex items-center gap-2 px-5 py-2 rounded-none bg-slate-900 hover:bg-slate-800 disabled:bg-slate-200 disabled:text-slate-400 text-white text-xs font-mono font-medium transition cursor-pointer disabled:cursor-not-allowed border border-slate-900"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>INVESTIGATING...</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-white" />
                <span>EXECUTE INVESTIGATION</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
