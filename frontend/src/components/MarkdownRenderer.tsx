'use client';

import React, { useMemo } from 'react';
import { marked } from 'marked';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content, className = '' }) => {
  const html = useMemo(() => {
    if (!content) return '';

    // Configure marked for github-flavored markdown
    marked.setOptions({
      gfm: true,
      breaks: true,
    });

    try {
      let rawHtml = marked.parse(content) as string;

      // Enhance tables: wrap in a rounded scrollable wrapper
      rawHtml = rawHtml
        .replace(/<table(\s*>|\s+[^>]*>)/g, '<div class="overflow-x-auto my-3 rounded-xl border border-slate-200/90 shadow-2xs max-w-full"><table$1')
        .replace(/<\/table>/g, '</table></div>');

      // Enhance citations: [file:line] -> stylized rounded badge
      rawHtml = rawHtml.replace(
        /\[([a-zA-Z0-9_\-\./\\]+\.[a-zA-Z0-9]+:\d+(?:-\d+)?)\]/g,
        '<span class="font-mono text-[10px] bg-slate-100 text-slate-800 border border-slate-300 px-1.5 py-0.5 rounded-md font-semibold inline-block my-0.5 shadow-2xs">[$1]</span>'
      );

      // Enhance evidence IDs: [ev_12345678] -> stylized rounded badge
      rawHtml = rawHtml.replace(
        /\[(ev_[a-zA-Z0-9]+)\]/g,
        '<span class="font-mono text-[10px] bg-emerald-50 text-emerald-800 border border-emerald-300 px-1.5 py-0.5 rounded-md font-semibold inline-block my-0.5 shadow-2xs">[$1]</span>'
      );

      return rawHtml;
    } catch {
      return content;
    }
  }, [content]);

  return (
    <div
      className={`markdown-body min-w-0 max-w-full overflow-hidden ${className}`}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
};
