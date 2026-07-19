import type { Message } from '../types';

export function MessageBubble({ msg }: { msg: Message }) {
  switch (msg.type) {
    case 'user':
      return (
        <div className="flex justify-end mb-4">
          <div className="bg-white border border-gray-200 rounded-lg px-4 py-2 max-w-[80%]">
            <p className="text-sm text-gray-800">{msg.payload}</p>
          </div>
        </div>
      );

    case 'understanding':
      return (
        <div className="flex justify-start mb-4">
          <div className="bg-green-50 border-l-4 border-green-400 rounded-r-lg px-4 py-3 max-w-[85%]">
            <p className="text-xs text-green-700 font-medium mb-1">已理解</p>
            <p className="text-sm text-gray-700 whitespace-pre-line">{msg.payload.content}</p>
          </div>
        </div>
      );

    case 'question':
      return (
        <div className="flex justify-start mb-4">
          <div className="bg-yellow-50 border-l-4 border-yellow-400 rounded-r-lg px-4 py-3 max-w-[85%]">
            <p className="text-xs text-yellow-700 font-medium mb-1">🤔 需要确认</p>
            <p className="text-sm text-gray-700 whitespace-pre-line">
              {msg.payload.content || msg.payload}
            </p>
          </div>
        </div>
      );

    case 'ai':
      return (
        <div className="flex justify-start mb-4">
          <div className="bg-white border border-gray-200 rounded-lg px-4 py-2 max-w-[85%]">
            <p className="text-sm text-gray-700 whitespace-pre-line">{msg.payload.content}</p>
          </div>
        </div>
      );

    case 'system':
      return (
        <div className="flex justify-center my-2">
          <span className="text-xs text-gray-400 italic">
            {msg.payload.content}
          </span>
        </div>
      );

    case 'error':
      return (
        <div className="flex justify-center mb-4">
          <span className="text-xs text-red-500 bg-red-50 px-3 py-1 rounded-full">
            {msg.payload.content}
          </span>
        </div>
      );

    default:
      return null;
  }
}
