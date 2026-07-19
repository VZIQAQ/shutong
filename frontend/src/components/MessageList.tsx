import { useRef, useEffect } from 'react';
import type { Message } from '../types';
import { MessageBubble } from './MessageBubble';
import { FileDraftCard } from './FileDraftCard';
import { SpecDraftCard } from './SpecDraftCard';
import { SpecLockedCard } from './SpecLockedCard';

interface Props {
  messages: Message[];
  confirmedFiles: Set<string>;
  onLock: () => void;
  onConfirmFile: (path: string) => void;
  onReviseFile: (path: string, feedback: string) => void;
}

export function MessageList({ messages, confirmedFiles, onLock, onConfirmFile, onReviseFile }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto px-4 py-4 space-y-1">
      {messages.map((msg) => {
        if (msg.type === 'file_draft') {
          return (
            <FileDraftCard
              key={msg.id}
              path={msg.payload.path}
              content={msg.payload.content}
              confirmed={confirmedFiles.has(msg.payload.path)}
              onConfirm={onConfirmFile}
              onRevise={onReviseFile}
            />
          );
        }
        if (msg.type === 'file_confirmed') {
          return (
            <div key={msg.id} className="flex justify-center my-2">
              <span className="text-xs text-green-600 bg-green-50 px-3 py-1 rounded-full">
                {msg.payload.path} 已确认写入
              </span>
            </div>
          );
        }
        if (msg.type === 'spec_draft') {
          return (
            <SpecDraftCard
              key={msg.id}
              content={msg.payload.content}
              onLock={onLock}
            />
          );
        }
        if (msg.type === 'spec_locked') {
          return <SpecLockedCard key={msg.id} filePath={msg.payload.filePath} />;
        }
        return <MessageBubble key={msg.id} msg={msg} />;
      })}
      <div ref={bottomRef} />
    </div>
  );
}
