import { useEffect, useRef, useCallback, useState } from 'react';

export function useWebSocket() {
  const ws = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messageHandlers = useRef<Set<(msg: any) => void>>(new Set());
  const onOpenCallback = useRef<(() => void) | null>(null);
  const pingTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  const connect = useCallback((url: string, onOpen?: () => void) => {
    if (ws.current) {
      ws.current.close(1000);
    }
    onOpenCallback.current = onOpen || null;
    setError(null);

    const socket = new WebSocket(url);
    ws.current = socket;

    socket.onopen = () => {
      setConnected(true);
      setError(null);
      onOpenCallback.current?.();

      // 心跳保活：每30秒发一次ping
      if (pingTimer.current) clearInterval(pingTimer.current);
      pingTimer.current = setInterval(() => {
        if (socket.readyState === WebSocket.OPEN) {
          socket.send(JSON.stringify({ type: 'ping' }));
        }
      }, 30000);
    };

    socket.onclose = () => {
      setConnected(false);
      if (pingTimer.current) {
        clearInterval(pingTimer.current);
        pingTimer.current = null;
      }
    };

    socket.onerror = () => {
      setConnected(false);
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type !== 'pong') {
          messageHandlers.current.forEach((h) => h(data));
        }
      } catch {
        console.error('WebSocket消息解析失败');
      }
    };
  }, []);

  const disconnect = useCallback(() => {
    if (pingTimer.current) {
      clearInterval(pingTimer.current);
      pingTimer.current = null;
    }
    ws.current?.close(1000);
    ws.current = null;
    setConnected(false);
  }, []);

  const send = useCallback((type: string, payload: any) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type, payload }));
    }
  }, []);

  const onMessage = useCallback((handler: (msg: any) => void) => {
    messageHandlers.current.add(handler);
    return () => {
      messageHandlers.current.delete(handler);
    };
  }, []);

  useEffect(() => {
    return () => {
      if (pingTimer.current) clearInterval(pingTimer.current);
      ws.current?.close(1000);
    };
  }, []);

  return { connected, error, connect, disconnect, send, onMessage };
}
