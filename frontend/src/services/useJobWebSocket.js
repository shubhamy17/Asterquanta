import { useEffect, useRef, useCallback, useState } from "react";

/**
 * WebSocket hook for real-time job progress updates.
 *
 * Usage:
 *   const { isConnected, lastMessage } = useJobWebSocket(userId, (data) => {
 *     // Handle progress update
 *     console.log(data.job_id, data.progress_percent);
 *   });
 *
 * Message format received:
 *   {
 *     type: "job_progress",
 *     job_id: 123,
 *     status: "RUNNING" | "COMPLETED",
 *     progress_percent: 45,
 *     processed_records: 450,
 *     total_records: 1000,
 *     valid_records: 440,
 *     invalid_records: 10,
 *     suspicious_records: 5,
 *     batch_completed: 5,
 *     total_batches: 10
 *   }
 */
export const useJobWebSocket = (userId, onProgress) => {
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const connectRef = useRef(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);

  // Get WebSocket URL from environment or default
  const getWsUrl = useCallback(() => {
    const apiBaseUrl =
      import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
    // Convert http(s) to ws(s)
    const wsUrl = apiBaseUrl.replace(/^http/, "ws");
    return `${wsUrl}/ws/${userId}`;
  }, [userId]);

  // Stable reference for onProgress callback
  const onProgressRef = useRef(onProgress);

  // Update refs in useEffect to avoid render-time ref access
  useEffect(() => {
    onProgressRef.current = onProgress;
  }, [onProgress]);

  // Store connect function in ref for recursive calls
  useEffect(() => {
    connectRef.current = () => {
      if (!userId) return;

      // Clean up existing connection
      if (wsRef.current) {
        wsRef.current.close();
      }

      const wsUrl = getWsUrl();
      console.log(`[WebSocket] Connecting to ${wsUrl}`);

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log("[WebSocket] Connected");
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        const data = event.data;

        // Handle ping/pong
        if (data === "ping") {
          ws.send("pong");
          return;
        }
        if (data === "pong") {
          return;
        }

        // Parse JSON message
        try {
          const message = JSON.parse(data);
          console.log("[WebSocket] Message received:", message);
          setLastMessage(message);

          // Call progress callback if provided
          if (message.type === "job_progress" && onProgressRef.current) {
            onProgressRef.current(message);
          }
        } catch {
          console.warn("[WebSocket] Failed to parse message:", data);
        }
      };

      ws.onerror = (error) => {
        console.error("[WebSocket] Error:", error);
      };

      ws.onclose = (event) => {
        console.log("[WebSocket] Disconnected:", event.code, event.reason);
        setIsConnected(false);
        wsRef.current = null;

        // Reconnect after 3 seconds (unless intentionally closed)
        if (event.code !== 1000) {
          console.log("[WebSocket] Reconnecting in 3 seconds...");
          reconnectTimeoutRef.current = setTimeout(() => {
            if (connectRef.current) {
              connectRef.current();
            }
          }, 3000);
        }
      };
    };
  }, [userId, getWsUrl]);

  const connect = useCallback(() => {
    if (connectRef.current) {
      connectRef.current();
    }
  }, []);

  // Send a message through the WebSocket
  const sendMessage = useCallback((message) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        typeof message === "string" ? message : JSON.stringify(message),
      );
    }
  }, []);

  // Disconnect WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close(1000, "User disconnected");
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close(1000, "Component unmounted");
      }
    };
  }, [connect]);

  return {
    isConnected,
    lastMessage,
    sendMessage,
    disconnect,
    reconnect: connect,
  };
};

export default useJobWebSocket;
