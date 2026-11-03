'use client';

import React, { useEffect, useRef, useState } from 'react';
import { Copy, Check, Download, AlertCircle } from 'lucide-react';

interface MermaidBlockProps {
  code: string;
}

export const MermaidBlock: React.FC<MermaidBlockProps> = ({ code }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [svgHtml, setSvgHtml] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let isMounted = true;

    // Load mermaid dynamically in browser only
    import('mermaid')
      .then((m) => {
        const mermaid = m.default;
        mermaid.initialize({
          startOnLoad: false,
          theme: 'neutral',
          themeVariables: {
            fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
            fontSize: '12px',
            primaryColor: '#f8fafc',
            primaryBorderColor: '#64748b',
            primaryTextColor: '#0f172a',
            lineColor: '#475569',
            secondaryColor: '#f1f5f9',
            tertiaryColor: '#ffffff',
          },
          securityLevel: 'loose',
        });

        const id = `mermaid_${Math.random().toString(36).substring(2, 9)}`;
        const cleanCode = code.trim();

        return mermaid.render(id, cleanCode);
      })
      .then(({ svg }) => {
        if (isMounted) {
          setSvgHtml(svg);
          setError(null);
        }
      })
      .catch((err) => {
        if (isMounted) {
          console.error('Mermaid render error:', err);
          setError(err?.message || 'Failed to render diagram syntax.');
        }
      });

    return () => {
      isMounted = false;
    };
  }, [code]);

  const copyCode = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadSvg = () => {
    if (!svgHtml) return;
    const blob = new Blob([svgHtml], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `repomind_diagram_${Date.now()}.svg`;
    link.click();
    URL.revokeObjectURL(url);
  };

  if (error) {
    return (
      <div className="my-3 border border-amber-300 bg-amber-50 rounded-none p-3 text-xs space-y-2">
        <div className="flex items-center justify-between text-amber-800 font-mono font-semibold">
          <span className="flex items-center gap-1.5">
            <AlertCircle className="w-3.5 h-3.5" />
            Diagram Syntax Note:
          </span>
          <button
            type="button"
            onClick={copyCode}
            className="flex items-center gap-1 text-[11px] text-amber-900 hover:text-black font-mono underline"
          >
            {copied ? 'Copied Source' : 'Copy Mermaid Source'}
          </button>
        </div>
        <p className="text-slate-700 text-xs">{error}</p>
        <pre className="p-2 bg-slate-900 text-slate-100 font-mono text-[11px] overflow-x-auto whitespace-pre-wrap">
          {code}
        </pre>
      </div>
    );
  }

  return (
    <div className="my-3 border border-slate-300 bg-white rounded-none shadow-xs overflow-hidden">
      {/* Control bar */}
      <div className="flex items-center justify-between px-3 py-1.5 bg-slate-100 border-b border-slate-200 text-xs font-mono">
        <span className="text-slate-600 font-semibold text-[11px] uppercase tracking-wider">
          Architecture / Flow Diagram
        </span>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={copyCode}
            className="flex items-center gap-1 text-[11px] text-slate-700 hover:text-slate-900 bg-white border border-slate-300 px-2 py-0.5 rounded-none transition"
            title="Copy Mermaid Code"
          >
            {copied ? (
              <>
                <Check className="w-3 h-3 text-emerald-600" />
                <span>Copied</span>
              </>
            ) : (
              <>
                <Copy className="w-3 h-3" />
                <span>Copy Code</span>
              </>
            )}
          </button>
          {svgHtml && (
            <button
              type="button"
              onClick={downloadSvg}
              className="flex items-center gap-1 text-[11px] text-slate-700 hover:text-slate-900 bg-white border border-slate-300 px-2 py-0.5 rounded-none transition"
              title="Download as SVG image"
            >
              <Download className="w-3 h-3" />
              <span>Export SVG</span>
            </button>
          )}
        </div>
      </div>

      {/* Rendered SVG */}
      <div
        ref={containerRef}
        className="p-4 overflow-x-auto flex justify-center bg-white min-h-[140px]"
        dangerouslySetInnerHTML={{ __html: svgHtml }}
      />
    </div>
  );
};
