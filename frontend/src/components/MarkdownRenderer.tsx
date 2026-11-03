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

      return rawHtml;
    } catch {
      return content;
    }
  }, [content]);

  return (
    <div
      className={`markdown-body ${className}`}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
};
