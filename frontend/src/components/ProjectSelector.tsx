import { useState, useEffect, useRef } from 'react';

interface Props {
  onConfirm: (path: string) => void;
}

const STORAGE_KEY = 'shutong_recent_projects';
const MAX_RECENT = 5;

function getRecentProjects(): string[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveRecentProject(path: string) {
  const recent = getRecentProjects().filter((p) => p !== path);
  recent.unshift(path);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(recent.slice(0, MAX_RECENT)));
}

export function ProjectSelector({ onConfirm }: Props) {
  const [path, setPath] = useState('');
  const [recent, setRecent] = useState<string[]>([]);
  const [showRecent, setShowRecent] = useState(false);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const r = getRecentProjects();
    setRecent(r);
    if (r.length > 0) setPath(r[0]);
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowRecent(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const handleConfirm = () => {
    const p = path.trim();
    if (!p) return;
    setLoading(true);
    saveRecentProject(p);
    onConfirm(p);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleConfirm();
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
      <div className="bg-white rounded-lg shadow-xl p-6 w-[480px]">
        <h1 className="text-xl font-bold text-gray-800 mb-2">欢迎使用书童V1</h1>
        <p className="text-sm text-gray-500 mb-6">
          请输入项目文件夹路径，书童将自动创建规范文件
        </p>

        <div className="relative mb-4" ref={dropdownRef}>
          <div className="flex items-center border border-gray-300 rounded-lg focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-blue-500">
            <span className="pl-3 text-gray-400 text-sm">📁</span>
            <input
              ref={inputRef}
              type="text"
              value={path}
              onChange={(e) => setPath(e.target.value)}
              onKeyDown={handleKeyDown}
              onFocus={() => recent.length > 0 && setShowRecent(true)}
              placeholder="D:\Projects\my-app"
              className="flex-1 px-2 py-2.5 text-sm outline-none rounded-r-lg"
            />
          </div>

          {showRecent && recent.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-10">
              {recent.map((p) => (
                <div
                  key={p}
                  onClick={() => {
                    setPath(p);
                    setShowRecent(false);
                  }}
                  className="px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 cursor-pointer truncate"
                >
                  {p}
                </div>
              ))}
            </div>
          )}
        </div>

        <button
          onClick={handleConfirm}
          disabled={!path.trim() || loading}
          className="w-full py-2.5 bg-blue-500 text-white text-sm font-medium rounded-lg hover:bg-blue-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              正在连接...
            </>
          ) : (
            '进入书童'
          )}
        </button>
      </div>
    </div>
  );
}
