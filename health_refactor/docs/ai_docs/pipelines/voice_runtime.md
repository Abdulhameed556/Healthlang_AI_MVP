# Voice Runtime Pipeline

Endpoint: `WS /api/v1/voice/stream`

Twilio sends a Media Stream WebSocket. The AI service bridges it to
the LLM's realtime audio API (e.g. OpenAI Realtime).

## Steps
1. **authenticate_session** — verify JWT from handshake headers
2. **load_agent_config** — fetch voice agent config from backend
3. **open_llm_audio_stream** — connect to realtime audio API
4. **bridge_audio** — bidirectional audio forwarding loop
5. **handle_tool_calls** — intercept function call events, execute tools
6. **on_stream_end** — persist CONVERSATION_LOG, trigger summarisation job
