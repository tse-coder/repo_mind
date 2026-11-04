'use client';

import React from 'react';
import { Plus, Trash2, Folder } from 'lucide-react';
import { ChatSession } from '../types';

interface ChatListProps {
  chats: ChatSession[];
  activeChatId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
}

function statusDot(status: string) {
  switch (status) {
    case 'RUNNING':
    case 'INITIALIZED':
      return 'bg-blue-500';
    case 'PAUSED':
      return 'bg-amber-500';
    case 'COMPLETED':
    case 'SUFFICIENT':
      return 'bg-emerald-500';
    case 'PARTIAL':
      return 'bg-yellow-500';
    case 'FAILED':
      return 'bg-red-500';
    default:
      return 'bg-slate-300';
  }
}

function formatTime(ts: number) {
  const d = new Date(ts);
  return d.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export const ChatList: React.FC<ChatListProps> = ({
  chats,
  activeChatId,
  onSelect,
  onNew,
  onDelete,
}) => {
  const ordered = [...chats].sort((a, b) => b.updatedAt - a.updatedAt);

  return (
    <div className="h-full flex flex-col bg-white border-r border-slate-200 min-h-0">
      <div className="p-3 border-b border-slate-200 flex items-center justify-between gap-2">
        <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-800">
          Investigations
        </h2>
        <button
          type="button"
          onClick={onNew}
          title="New investigation"
          aria-label="New investigation"
          className="flex items-center justify-center p-1.5 bg-slate-900 text-white hover:bg-slate-800 border border-slate-900 rounded-lg transition shadow-xs cursor-pointer"
        >
          <Plus className="w-3.5 h-3.5" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto min-h-0 p-2">
        {ordered.length === 0 ? (
          <div className="p-6 text-center text-xs font-mono text-slate-400">
            No investigations yet. Start a query in the center pane.
          </div>
        ) : (
          <ul className="space-y-1">
            {ordered.map((chat) => {
              const active = chat.id === activeChatId;
              return (
                <li key={chat.id}>
                  <div
                    className={`group flex items-start gap-2.5 px-3 py-2 rounded-lg cursor-pointer transition ${
                      active ? 'bg-slate-100 text-slate-900 shadow-xs' : 'hover:bg-slate-50 text-slate-600'
                    }`}
                    onClick={() => onSelect(chat.id)}
                  >
                    <span className={`mt-1.5 w-2 h-2 rounded-full shrink-0 ${statusDot(chat.state.status)}`} />
                    <div className="min-w-0 flex-1">
                      <div className="text-xs font-medium text-slate-900 truncate">
                        {chat.title || 'New investigation'}
                      </div>
                      {chat.state.repo_path && (
                        <div className="flex items-center gap-1 mt-0.5 text-[10px] font-mono text-slate-500 truncate">
                          <Folder className="w-3 h-3 shrink-0" />
                          <span className="truncate">{chat.state.repo_path.split('/').slice(-2).join('/')}</span>
                        </div>
                      )}
                      <div className="text-[10px] font-mono text-slate-400 mt-0.5">
                        {formatTime(chat.updatedAt)}
                      </div>
                    </div>
                    <button
                      type="button"
                      title="Delete investigation"
                      onClick={(e) => {
                        e.stopPropagation();
                        onDelete(chat.id);
                      }}
                      className="opacity-0 group-hover:opacity-100 p-1 rounded-md text-slate-400 hover:text-red-600 transition"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
};
