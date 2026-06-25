import { useRef, useState } from "react";

type HistoryTurn = { role: "user" | "assistant"; content: string };

type ContextFilter = {
  history_turns_received?: number;
  history_turns_included?: number;
  history_turns_excluded?: number;
  history_turns_prompted?: number;
  history_turns_omitted_for_prompt_budget?: number;
  assembled_prompt_chars?: number;
  prompt_char_limit?: number;
};

type ApiResponse = {
  trace_id?: string;
  executed?: boolean;
  reason?: string;
  response?: string;
  context_filter?: ContextFilter;
  response_truncated?: boolean;
  response_char_count_returned?: number;
  response_char_limit?: number;
  response_limit_source?: string;
  response_truncated_false_semantics?: string;
  error_type?: string;
};

type ChatEntry =
  | { kind: "user"; content: string }
  | { kind: "assistant"; content: string; meta: ApiResponse }
  | { kind: "blocked"; reason: string; trace_id?: string }
  | { kind: "error"; message: string; trace_id?: string };

function BudgetMeter({ filter }: { filter: ContextFilter }) {
  const { assembled_prompt_chars, prompt_char_limit } = filter;
  const hasPercent =
    typeof assembled_prompt_chars === "number" &&
    typeof prompt_char_limit === "number" &&
    prompt_char_limit > 0;
  const pct = hasPercent
    ? Math.min(100, Math.round((assembled_prompt_chars! / prompt_char_limit!) * 100))
    : null;

  return (
    <div className="budget-meter">
      <div className="budget-meter-label">Last request local prompt budget</div>
      {hasPercent ? (
        <>
          <div className="budget-bar-outer">
            <div
              className="budget-bar-inner"
              style={{ width: `${pct}%` }}
              role="progressbar"
              aria-valuenow={pct ?? 0}
              aria-valuemin={0}
              aria-valuemax={100}
            />
          </div>
          <div className="budget-chars">
            {pct}% · {assembled_prompt_chars!.toLocaleString()} / {prompt_char_limit!.toLocaleString()} chars
          </div>
        </>
      ) : typeof prompt_char_limit === "number" ? (
        <div className="budget-chars">
          Limit: {prompt_char_limit.toLocaleString()} chars (usage not available for this request)
        </div>
      ) : (
        <div className="budget-empty">
          Local prompt budget usage will appear after a successful local-chat response.
        </div>
      )}
      {(filter.history_turns_omitted_for_prompt_budget ?? 0) > 0 && (
        <div className="budget-warn">
          Some clean history turns were omitted to stay within the local prompt budget.
        </div>
      )}
      {(filter.history_turns_excluded ?? 0) > 0 && (
        <div className="budget-warn">
          Some history turns were excluded by deterministic safety filtering.
        </div>
      )}
    </div>
  );
}

function DevLocalChat() {
  const [entries, setEntries] = useState<ChatEntry[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [lastFilter, setLastFilter] = useState<ContextFilter | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  function buildHistory(): HistoryTurn[] {
    const turns: HistoryTurn[] = [];
    for (const e of entries) {
      if (e.kind === "user") turns.push({ role: "user", content: e.content });
      else if (e.kind === "assistant") turns.push({ role: "assistant", content: e.content });
    }
    return turns;
  }

  async function sendMessage() {
    const msg = input.trim();
    if (!msg || loading) return;

    const history = buildHistory();
    setInput("");
    setEntries((prev) => [...prev, { kind: "user", content: msg }]);
    setLoading(true);

    try {
      const res = await fetch("/api/dev/local-chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg, history, run_local_responder: true }),
      });

      let data: ApiResponse = {};
      try {
        data = await res.json();
      } catch {
        data = { reason: "invalid_json_response" };
      }

      if (res.status === 404) {
        setEntries((prev) => [
          ...prev,
          {
            kind: "error",
            message:
              "Dev endpoint not found (404). Check: backend running on 127.0.0.1:8000 and JARVISOS_ENABLE_DEV_MESSAGE_ROUTE_SMOKE=1.",
            trace_id: data.trace_id,
          },
        ]);
      } else if (res.status === 422) {
        setEntries((prev) => [
          ...prev,
          {
            kind: "error",
            message: "Validation error (422). Check request format.",
            trace_id: data.trace_id,
          },
        ]);
      } else if (res.status >= 500) {
        setEntries((prev) => [
          ...prev,
          {
            kind: "error",
            message: `Internal error (${res.status}).${data.error_type ? ` ${data.error_type}` : ""}`,
            trace_id: data.trace_id,
          },
        ]);
      } else if (data.executed === true && typeof data.response === "string") {
        setEntries((prev) => [
          ...prev,
          { kind: "assistant", content: data.response!, meta: data },
        ]);
        if (data.context_filter) setLastFilter(data.context_filter);
      } else {
        setEntries((prev) => [
          ...prev,
          { kind: "blocked", reason: data.reason ?? "unknown", trace_id: data.trace_id },
        ]);
      }
    } catch {
      setEntries((prev) => [
        ...prev,
        {
          kind: "error",
          message: "Network error. Is the backend running and the Vite proxy configured?",
        },
      ]);
    } finally {
      setLoading(false);
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), 50);
    }
  }

  return (
    <div className="dev-local-chat">
      <div className="dev-warning">
        <strong>Dev local chat only.</strong> Not production chat. No persistent memory. No
        retrieval. No external providers. No tools.
        <br />
        Local prompt budget is a char-based adapter budget, not the model context window.
        <br />
        <code>response_truncated=false</code> only means JarvisOS did not slice the returned
        response; it is not a completion guarantee.
      </div>

      <div className="chat-entries">
        {entries.length === 0 && (
          <p className="chat-empty">Send a message to test the local chat backend.</p>
        )}
        {entries.map((e, i) => {
          if (e.kind === "user") {
            return (
              <div key={i} className="chat-turn chat-turn--user">
                <span className="chat-role">You</span>
                <p className="chat-content">{e.content}</p>
              </div>
            );
          }
          if (e.kind === "assistant") {
            const t = e.meta.response_truncated;
            return (
              <div key={i} className="chat-turn chat-turn--assistant">
                <span className="chat-role">Local AI</span>
                <p className="chat-content" style={{ whiteSpace: "pre-wrap" }}>
                  {e.content}
                </p>
                {t === true && (
                  <div className="chat-warn">
                    Response was truncated by the local JarvisOS/Ollama adapter limit.
                  </div>
                )}
                {t === false && (
                  <div className="chat-meta-note">
                    Not sliced by JarvisOS local adapter.
                  </div>
                )}
                {e.meta.trace_id && (
                  <div className="chat-trace">trace: {e.meta.trace_id}</div>
                )}
              </div>
            );
          }
          if (e.kind === "blocked") {
            return (
              <div key={i} className="chat-turn chat-turn--blocked">
                <span className="chat-role">Blocked</span>
                <p className="chat-content">
                  Not executed — reason: <code>{e.reason}</code>
                </p>
                {(e.reason === "dev_message_route_smoke_disabled" ||
                  e.reason === "local_responder_disabled") && (
                  <p className="chat-hint">
                    Backend dev env gates must be enabled:{" "}
                    <code>JARVISOS_ENABLE_DEV_MESSAGE_ROUTE_SMOKE=1</code>,{" "}
                    <code>JARVISOS_DEV_MESSAGE_ROUTE_ALLOW_LOCAL_RESPONDER=1</code>
                  </p>
                )}
                {e.trace_id && <div className="chat-trace">trace: {e.trace_id}</div>}
              </div>
            );
          }
          return (
            <div key={i} className="chat-turn chat-turn--error">
              <span className="chat-role">Error</span>
              <p className="chat-content">{e.message}</p>
              {e.trace_id && <div className="chat-trace">trace: {e.trace_id}</div>}
            </div>
          );
        })}
        {loading && (
          <div className="chat-turn chat-turn--loading">
            <span className="chat-role">Local AI</span>
            <p className="chat-content">…</p>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="chat-input-row">
        <textarea
          className="chat-input"
          rows={3}
          placeholder="Type a message… (Enter to send, Shift+Enter for newline)"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              sendMessage();
            }
          }}
          disabled={loading}
        />
        <button
          className="chat-send"
          type="button"
          onClick={sendMessage}
          disabled={loading || !input.trim()}
        >
          Send
        </button>
      </div>

      {lastFilter !== null ? (
        <BudgetMeter filter={lastFilter} />
      ) : (
        <div className="budget-meter">
          <div className="budget-meter-label">Last request local prompt budget</div>
          <div className="budget-empty">
            Local prompt budget usage will appear after a successful local-chat response.
          </div>
        </div>
      )}
    </div>
  );
}

export default DevLocalChat;
