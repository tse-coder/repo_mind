'use client';

import React, { useState } from 'react';
import { Eye, Code } from 'lucide-react';
import { MarkdownRenderer } from './MarkdownRenderer';

interface ToolOutputViewerProps {
  tool: string;
  summary: string;
}

export const ToolOutputViewer: React.FC<ToolOutputViewerProps> = ({ tool, summary }) => {
  const [mode, setMode] = useState<'preview' | 'raw'>('preview');

  // Strip framing delimiters
  const cleanSummary = summary
    .replace(/<<<UNTRUSTED_REPOSITORY_DATA[^>]*>>>/g, '')
    .replace(/<<<END_UNTRUSTED_REPOSITORY_DATA>>>/g, '')
    .trim();

  // Try parsing structured JSON payload
  let parsedJson: any = null;
  try {
    parsedJson = JSON.parse(cleanSummary);
  } catch {
    // Not valid JSON, keep as raw text
  }

  // Check if there is markdown or structured preview available
  const hasContent = parsedJson && typeof parsedJson.content === 'string';
  const isMarkdown =
    hasContent &&
    ((parsedJson.file_path && parsedJson.file_path.endsWith('.md')) ||
      parsedJson.content.includes('#') ||
      parsedJson.content.includes('**') ||
      parsedJson.content.includes('|'));
  const isSearchMatches = parsedJson && Array.isArray(parsedJson.matches) && parsedJson.matches.length > 0;
  const isTreeEntries = parsedJson && Array.isArray(parsedJson.entries) && parsedJson.entries.length > 0;

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <span className="text-slate-500 font-mono text-[11px] block">
          Output:
        </span>
        <div className="inline-flex border border-slate-300 rounded-none bg-slate-100 p-0.5">
          <button
            type="button"
            onClick={() => setMode('preview')}
            className={`flex items-center gap-1 px-1.5 py-0.5 text-[10px] font-mono transition ${
              mode === 'preview'
                ? 'bg-white text-slate-900 font-semibold shadow-xs'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            <Eye className="w-2.5 h-2.5" />
            <span>Preview</span>
          </button>
          <button
            type="button"
            onClick={() => setMode('raw')}
            className={`flex items-center gap-1 px-1.5 py-0.5 text-[10px] font-mono transition ${
              mode === 'raw'
                ? 'bg-white text-slate-900 font-semibold shadow-xs'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            <Code className="w-2.5 h-2.5" />
            <span>Raw JSON</span>
          </button>
        </div>
      </div>

      {mode === 'preview' ? (
        <div className="p-2.5 bg-slate-50 border border-slate-200 text-xs overflow-x-auto max-h-60 rounded-none">
          {isMarkdown ? (
            <MarkdownRenderer content={parsedJson.content} />
          ) : hasContent ? (
            <pre className="font-mono text-[11px] text-slate-900 whitespace-pre-wrap">
              {parsedJson.content}
            </pre>
          ) : isSearchMatches ? (
            <div className="space-y-1.5">
              <span className="text-[10px] font-mono font-semibold text-slate-600 block">
                Matches ({parsedJson.matches.length}):
              </span>
              <table className="w-full text-left font-mono text-[11px] border border-slate-200">
                <thead>
                  <tr className="bg-slate-100 border-b border-slate-200 text-slate-600">
                    <th className="p-1 px-1.5">File</th>
                    <th className="p-1 px-1.5">Line</th>
                    <th className="p-1 px-1.5">Match</th>
                  </tr>
                </thead>
                <tbody>
                  {parsedJson.matches.map((m: any, idx: number) => (
                    <tr key={idx} className="border-b border-slate-200 hover:bg-white">
                      <td className="p-1 px-1.5 font-semibold text-slate-800 whitespace-nowrap">{m.file_path}</td>
                      <td className="p-1 px-1.5 text-slate-500">{m.line_number}</td>
                      <td className="p-1 px-1.5 text-slate-900 font-sans">{m.line}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : isTreeEntries ? (
            <div className="space-y-1.5">
              <span className="text-[10px] font-mono font-semibold text-slate-600 block">
                Entries ({parsedJson.entries.length}):
              </span>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-1 font-mono text-[11px]">
                {parsedJson.entries.map((e: any, idx: number) => (
                  <div key={idx} className="p-1 px-1.5 bg-white border border-slate-200 truncate" title={e.path}>
                    <span className="text-slate-400 mr-1">{e.type === 'directory' ? '📁' : '📄'}</span>
                    <span className="text-slate-800">{e.path}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <pre className="font-mono text-[11px] text-slate-900 whitespace-pre-wrap">
              {cleanSummary}
            </pre>
          )}
        </div>
      ) : (
        <pre className="p-2.5 rounded-none bg-slate-900 border border-slate-800 text-[11px] font-mono text-slate-100 overflow-x-auto max-h-48 whitespace-pre-wrap">
          {summary}
        </pre>
      )}
    </div>
  );
};
