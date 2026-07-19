"use client";
/**
 * useWebSocket — Custom hook for managing the live WebSocket connection to
 * the FIFA WC Stadium Operations backend.
 *
 * Handles: connection lifecycle, reconnection with exponential back-off,
 * typed message dispatching, and an offline/degraded-mode fallback.
 */
import { useEffect, useRef, useCallback, useState } from "react";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://127.0.0.1:8000/ws/updates";
const MAX_RECONNECT_ATTEMPTS = 5;

/**
 * @typedef {Object} WSMessage
 * @property {"crowd_update"|"transit_update"|"incident_approved"} type
 * @property {any} [zone]
 * @property {any} [route]
 * @property {number} [incident_id]
 */

/**
 * @param {function(WSMessage):void} onMessage   Callback invoked on each typed message
 * @param {boolean}                  offlineMode  Skip connection when offline mode is active
 */
export function useWebSocket(onMessage, offlineMode = false) {
  const wsRef = useRef(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimer = useRef(null);
  const [isConnected, setIsConnected] = useState(false);

  const connect = useCallback(() => {
    if (offlineMode || typeof window === "undefined") return;

    try {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        reconnectAttempts.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data && data.type) {
            onMessage(data);
          }
        } catch {
          // Ignore malformed payloads
        }
      };

      ws.onerror = () => {
        setIsConnected(false);
      };

      ws.onclose = () => {
        setIsConnected(false);
        wsRef.current = null;

        // Exponential back-off reconnection
        if (reconnectAttempts.current < MAX_RECONNECT_ATTEMPTS && !offlineMode) {
          const delay = Math.min(1000 * 2 ** reconnectAttempts.current, 30000);
          reconnectAttempts.current += 1;
          reconnectTimer.current = setTimeout(connect, delay);
        }
      };
    } catch {
      setIsConnected(false);
    }
  }, [onMessage, offlineMode]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { isConnected };
}
