'use client';

import React, { useMemo } from 'react';
import dynamic from 'next/dynamic';
import { marked } from 'marked';

const MermaidBlock = dynamic(
  () => import('./MermaidBlock').then((mod) => mod.MermaidBlock),
  { ssr: false }
);

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

interface ContentPart {
  type: 'markdown' | 'mermaid';
  content: string;
  key: string;
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content, className = '' }) => {
  const parts = useMemo<ContentPart[]>(() => {
    if (!content) return [];

    const mermaidRegex = /```mermaid\s*([\s\S]*?)```/g;
    const result: ContentPart[] = [];
    let lastIndex = 0;
    let match: RegExpExecArray | null;
    let idx = 0;

    while ((match = mermaidRegex.exec(content)) !== null) {
      if (match.index > lastIndex) {
        result.push({
          type: 'markdown',
          content: content.substring(lastIndex, match.index),
          key: `md_${idx++}`,
        });
      }
      result.push({
        type: 'mermaid',
        content: match[1],
        key: `mm_${idx++}`,
      });
      lastIndex = match.index + match[0].length;
    }

    if (lastIndex < content.length) {
      result.push({
        type: 'markdown',
        content: content.substring(lastIndex),
        key: `md_${idx++}`,
      });
    }

    return result;
  }, [content]);

  // Configure marked for github-flavored markdown
  marked.setOptions({
    gfm: true,
    breaks: true,
  });

  const renderMarkdownPart = (markdownText: string) => {
    try {
      let rawHtml = marked.parse(markdownText) as string;

      // Enhance citations: [file:line] -> stylized badge
      rawHtml = rawHtml.replace(
        /\[([a-zA-Z0-9_\-\./\\]+\.[a-zA-Z0-9]+:\d+(?:-\d+)?)\]/g,
        '<span class="font-mono text-[10px] bg-slate-100 text-slate-800 border border-slate-300 px-1 py-0.5 font-semibold inline-block my-0.5">[$1]</span>'
      );

      // Enhance evidence IDs: [ev_12345678] -> stylized badge
      rawHtml = rawHtml.replace(
        /\[(ev_[a-zA-Z0-9]+)\]/g,
        '<span class="font-mono text-[10px] bg-emerald-50 text-emerald-800 border border-emerald-300 px-1 py-0.5 font-semibold inline-block my-0.5">[$1]</span>'
      );

      return (
        <div
          className={`markdown-body ${className}`}
          dangerouslySetInnerHTML={{ __html: rawHtml }}
        />
      );
    } catch {
      return (
        <div className={`markdown-body ${className}`}>
          {markdownText}
        </div>
      );
    }
  };

  if (parts.length === 0) return null;

  return (
    <div className="space-y-2">
      {parts.map((p) => {
        if (p.type === 'mermaid') {
          return <MermaidBlock key={p.key} code={p.content} />;
        }
        return <React.Fragment key={p.key}>{renderMarkdownPart(p.content)}</React.Fragment>;
      })}
    </div>
  );
};
