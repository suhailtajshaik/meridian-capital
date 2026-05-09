import { useState, useRef, useCallback, useEffect } from 'react';
import { streamChat } from '../lib/api.js';
import { getSessionId } from '../lib/session.js';

/**
 * useAgentStream — manages real-time chat state against the SSE backend.
 *
 * Returns:
 *   messages       — array of chat message objects (role, content, agent?, trace?)
 *   sendMessage    — (text: string) => void
 *   isStreaming    — boolean
 *   activeAgent    — string|null  (most recent agent_start payload)
 *   currentTrace   — TraceEvent[] in-flight for the assistant reply being built
 *   error          — Error|null
 *   clear          — () => void  resets the thread
 */
export function useAgentStream() {
  const [messages, setMessages] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [activeAgent, setActiveAgent] = useState(null);
  const [currentTrace, setCurrentTrace] = useState([]);
  const [error, setError] = useState(null);

  // Track the AbortController for the in-flight request so we can cancel
  const abortRef = useRef(null);
  // Keep a ref to the latest messages array so sendMessage closure can read it
  const messagesRef = useRef(messages);
  useEffect(() => { messagesRef.current = messages; }, [messages]);

  const clear = useCallback(() => {
    abortRef.current?.abort();
    setMessages([]);
    setIsStreaming(false);
    setActiveAgent(null);
    setCurrentTrace([]);
    setError(null);
  }, []);

  const sendMessage = useCallback(async (text) => {
    if (!text.trim()) return;

    // Cancel any existing stream
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setError(null);
    setCurrentTrace([]);
    setActiveAgent(null);
    setIsStreaming(true);

    const userMessage = { role: 'user', content: text };

    // Append user message and a placeholder for the assistant response
    const PLACEHOLDER_ID = '__streaming__';
    setMessages((prev) => [
      ...prev,
      userMessage,
      { role: 'assistant', content: '', _id: PLACEHOLDER_ID, _streaming: true, trace: [] },
    ]);

    // Build the messages array the backend expects (omit internal fields)
    // We read from a snapshot of the pre-append state via a closure trick —
    // use a ref to get the latest messages without a stale closure.
    const sessionId = getSessionId();

    // Accumulator for trace events and streamed content in this request
    let traceEvents = [];
    let assistantContent = '';
    let assistantAgent = null;

    // Build the ChatMessage[] history from the current thread (before the new user msg was appended).
    // We include only role/content/agent — stripping internal fields like _id, _streaming, trace.
    const historyBeforeThis = messagesRef.current
      .filter((m) => !m._streaming)  // exclude any in-flight placeholder
      .map(({ role, content, agent }) => ({
        role: role === 'agent' ? 'assistant' : role,
        content: content ?? '',
        ...(agent ? { agent } : {}),
      }));

    // Append the user message we just sent
    const outboundMessages = [...historyBeforeThis, { role: 'user', content: text }];

    try {
      await streamChat({
        messages: outboundMessages,
        sessionId,
        onEvent: (event) => {
          if (controller.signal.aborted) return;

          if (event.type === 'trace') {
            const traceEvent = event.event;
            traceEvents = [...traceEvents, traceEvent];
            // Update active agent label from agent_start events
            if (traceEvent.type === 'agent_start') {
              setActiveAgent(traceEvent.agent ?? null);
            }
            setCurrentTrace(traceEvents);
            // Attach the growing trace to the placeholder
            setMessages((prev) =>
              prev.map((m) =>
                m._id === PLACEHOLDER_ID ? { ...m, trace: traceEvents } : m
              )
            );
          } else if (event.type === 'message') {
            const msg = event.message;
            if (msg.role === 'assistant' || msg.role === 'agent' || msg.role === 'supervisor') {
              assistantContent += msg.content ?? '';
              assistantAgent = msg.agent ?? assistantAgent;
              setMessages((prev) =>
                prev.map((m) =>
                  m._id === PLACEHOLDER_ID
                    ? { ...m, content: assistantContent, agent: assistantAgent }
                    : m
                )
              );
            }
          } else if (event.type === 'done') {
            // Finalize the placeholder — strip internal fields, lock trace
            setMessages((prev) =>
              prev.map((m) => {
                if (m._id !== PLACEHOLDER_ID) return m;
                const { _id, _streaming, ...rest } = m;
                return {
                  ...rest,
                  content: assistantContent || rest.content,
                  agent: assistantAgent ?? rest.agent,
                  trace: traceEvents,
                };
              })
            );
            setIsStreaming(false);
            setActiveAgent(null);
            setCurrentTrace([]);
          }
        },
        signal: controller.signal,
      });
    } catch (err) {
      if (err.name === 'AbortError') {
        // User cancelled or new message sent — clean up placeholder
        setMessages((prev) => prev.filter((m) => m._id !== PLACEHOLDER_ID));
      } else {
        setError(err);
        // Remove the empty placeholder, keep user message
        setMessages((prev) => prev.filter((m) => m._id !== PLACEHOLDER_ID));
      }
    } finally {
      if (!controller.signal.aborted) {
        setIsStreaming(false);
        setActiveAgent(null);
        setCurrentTrace([]);
      }
    }
  }, []);

  return { messages, sendMessage, isStreaming, activeAgent, currentTrace, error, clear };
}
