import { useState } from 'react';

interface Props {
  content: string;
  locked?: boolean;
  filePath?: string;
  onLock: () => void;
}

export function SpecDraftCard({ content, locked, filePath, onLock }: Props) {
  const [expanded, setExpanded] = useState(false);
  const [locking, setLocking] = useState(false);

  const handleLock = () => {
    setLocking(true);
    onLock();
  };

  if (locked) {
    return (
      <div className="mb-4 bg-blue-50 border-l-4 border-blue-400 rounded-r-lg p-4">
        <p className="text-sm font-medium text-blue-700 mb-1">Spec已锁定</p>
        {filePath && <p className="text-xs text-gray-600">文件: {filePath}</p>}
      </div>
    );
  }

  return (
    <div className="mb-4 bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
      <div className="px-4 py-2 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
        <span className="text-sm font-medium text-gray-700">Spec草案</span>
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-xs text-blue-600 hover:underline"
        >
          {expanded ? '收起' : '展开'}
        </button>
      </div>

      <div className={`px-4 py-3 ${expanded ? '' : 'max-h-40 overflow-hidden'}`}>
        <pre className="text-xs text-gray-600 whitespace-pre-wrap font-mono leading-relaxed">
          {content}
        </pre>
      </div>

      {!expanded && content.length > 300 && (
        <div className="px-4 pb-2">
          <span className="text-xs text-gray-400">...(内容已折叠)</span>
        </div>
      )}

      <div className="px-4 py-3 bg-gray-50 border-t border-gray-200 flex gap-2 items-center">
        <button
          onClick={handleLock}
          disabled={locking}
          className="px-4 py-1.5 bg-blue-500 text-white text-sm rounded hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-1"
        >
          {locking && (
            <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
          )}
          {locking ? '锁定中...' : '确认锁定'}
        </button>
        <span className="text-xs text-gray-400">
          锁定后开发将严格按照Spec执行
        </span>
      </div>
    </div>
  );
}
