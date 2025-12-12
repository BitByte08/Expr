import { httpServerHandler } from 'cloudflare:node';
import {env} from 'cloudflare:workers';
import express, { Request, Response } from 'express';
import cors from 'cors';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';
import Groq from 'groq-sdk';

const app = express();
const PORT = 3000;
const MCP_SERVER_URL = 'https://port-0-expr-mj2a706qacdc1bb8.sel3.cloudtype.app/mcp';
const GROQ_API_KEY = env.GROQ_API_KEY || process.env.GROQ_API_KEY || '';
const GROQ_MODEL = env.GROQ_MODEL || process.env.GROQ_MODEL || 'openai/gpt-oss-120b';
const MAX_CONTEXT_MESSAGES = 12;
// Simple in-memory session memory (non-durable)
const sessionMemory = new Map<string, { summary: string }>();

// KV/D1 bindings (provided by wrangler.jsonc)
declare const MEMORY_KV: KVNamespace;
declare const CHAT_DB: D1Database;

app.use(cors({ origin: 'https://expr.bitworkspace.kr' }));

// ------------------------------------------------------------------
// 1. MCP 클라이언트 생성 (HTTP 방식)
// ------------------------------------------------------------------
async function createMcpClient() {
  console.log(`Attempting HTTP connection to ${MCP_SERVER_URL}...`);

  const transport = new StreamableHTTPClientTransport(new URL(MCP_SERVER_URL));

  const client = new Client(
    { name: 'express-groq-client', version: '1.0.0' },
    { capabilities: {} }
  );

  client.onerror = (err: any) => console.error('[MCP Client Error]', err);

  await client.connect(transport);
  return client;
}

// ------------------------------------------------------------------
// 2. 도구 변환 유틸리티 (MCP -> OpenAI tools)
// ------------------------------------------------------------------
function mapMcpToolsToOpenAI(mcpTools: any[]) {
  return mcpTools.map((tool) => ({
    type: 'function' as const,
    function: {
      name: tool.name,
      description: tool.description,
      parameters: tool.inputSchema,
    },
  }));
}

// ------------------------------------------------------------------
// 3. 채팅 API (OpenAI 스트리밍 -> Vue SSE 응답)
// ------------------------------------------------------------------
app.get('/api/chat', async (req: Request, res: Response) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');

  const prompt = req.query.prompt as string;
  const historyJson = req.query.history as string;
  const sessionId = (req.query.sid as string) || 'default';

  if (!prompt) {
    res.write(`event: error\ndata: ${JSON.stringify({ error: 'Prompt is required' })}\n\n`);
    res.end();
    return;
  }

  // 이전 대화 히스토리 파싱
  let chatHistory: any[] = [];
  if (historyJson) {
    try {
      const parsed = JSON.parse(decodeURIComponent(historyJson));
      chatHistory = Array.isArray(parsed) ? parsed : [];
    } catch (e) {
      console.warn('history parse error:', e);
    }
  }

  let mcpClient: Client | null = null;
  const groq = new Groq({ apiKey: GROQ_API_KEY });

  try {
    // 1. MCP 서버 연결 (HTTP)
    mcpClient = await createMcpClient();

    // 2. 도구 목록 로드
    const toolsResult = await mcpClient.listTools();
    const openaiTools = mapMcpToolsToOpenAI(toolsResult.tools);
    console.log(`[Tools Loaded] Count: ${openaiTools.length}`);

    const isRateLimitError = (err: any) => {
      const code = err?.error?.error?.code || err?.code;
      return code === 'rate_limit_exceeded';
    };

    const sendRateLimitNotice = (err: any) => {
      const msg = err?.error?.error?.message || 'Rate limit reached. Please retry shortly.';
      res.write(`event: chunk\ndata: ${JSON.stringify({ text: `\n⚠️ ${msg}` })}\n\n`);
      res.write(`event: status\ndata: ${JSON.stringify({ status: 'STREAMING_END' })}\n\n`);
    };

    // 3. Groq 스트리밍 + 함수 호출 처리
    const runChat = async (messages: any[]) => {
      let stream;
      try {
        stream = await groq.chat.completions.create({
          model: GROQ_MODEL,
          stream: true,
          messages,
          tools: openaiTools,
        });
      } catch (err) {
        if (isRateLimitError(err)) {
          sendRateLimitNotice(err);
          return;
        }
        throw err;
      }

      const toolCalls: { id?: string; name?: string; arguments: string; index: number }[] = [];

      for await (const chunk of stream) {
        const delta = chunk.choices?.[0]?.delta;
        if (!delta) continue;

        // 텍스트 스트림 전송 (delta.content가 배열/문자열 모두 대응)
        const textPieces = Array.isArray(delta.content)
          ? delta.content
              .map((part: any) => (typeof part === 'string' ? part : part?.text))
              .filter(Boolean)
              .join('')
          : typeof delta.content === 'string'
            ? delta.content
            : '';

        if (textPieces) {
          res.write(`event: chunk\ndata: ${JSON.stringify({ text: textPieces })}\n\n`);
        }

        // 함수 호출 스트림 누적
        if (delta.tool_calls && delta.tool_calls.length > 0) {
          delta.tool_calls.forEach((callDelta: any) => {
            const idx = callDelta.index ?? 0;
            if (!toolCalls[idx]) {
              toolCalls[idx] = { arguments: '', index: idx };
            }

            const target = toolCalls[idx];
            if (callDelta.id) target.id = callDelta.id;
            if (callDelta.function?.name) target.name = callDelta.function.name;
            if (callDelta.function?.arguments) {
              target.arguments += callDelta.function.arguments;
            }
          });
        }
      }

      // 함수 호출이 감지된 경우
      if (toolCalls.length > 0) {
        const call = toolCalls[0];
        if (!call.name) {
          throw new Error('수신한 툴 호출에 name이 없습니다.');
        }
        const parsedArgs = call.arguments ? JSON.parse(call.arguments) : {};
        console.log(`[Tool Execute] ${call.name}`);

        try {
          const toolResult = await mcpClient!.callTool({
            name: call.name,
            arguments: parsedArgs,
          });

          const toolContent = (toolResult as any).content
            .map((c: any) => (c.type === 'text' ? c.text : ''))
            .join('\n');
          console.log(`[Tool Result] Length: ${toolContent.length}`);

          const nextMessages = [
            ...messages,
            {
              role: 'assistant',
              tool_calls: [
                {
                  id: call.id,
                  type: 'function',
                  function: { name: call.name, arguments: call.arguments },
                },
              ],
            },
            {
              role: 'tool',
              tool_call_id: call.id,
              content: toolContent,
            },
          ];

          await runChat(nextMessages);
        } catch (toolError) {
          console.error('[Tool Error]', toolError);
          const errorMsg = `Tool failed: ${toolError instanceof Error ? toolError.message : String(toolError)}`;

          const nextMessages = [
            ...messages,
            {
              role: 'assistant',
              tool_calls: [
                {
                  id: call.id,
                  type: 'function',
                  function: { name: call.name, arguments: call.arguments },
                },
              ],
            },
            {
              role: 'tool',
              tool_call_id: call.id,
              content: errorMsg,
            },
          ];

          await runChat(nextMessages);
        }
      }
    };

    // 이전 메시지를 system 역할로 변환하여 컨텍스트 유지 (최근 N개만 사용)
    const prior = sessionMemory.get(sessionId)?.summary || '';
    const systemPrompt = {
      role: 'system',
      content:
        'You are a Riot/League of Legends assistant. Only answer questions about Riot games, League of Legends data, matches, champions, runes, items, and related esports. If the user asks anything unrelated, politely refuse and ask them to stay on Riot topics. Keep answers concise.\n\nSession Summary: ' + prior,
    };

    const trimmedHistory = chatHistory.slice(-MAX_CONTEXT_MESSAGES);
    const contextMessages = trimmedHistory.map((msg: any) => ({
      role: msg.sender === 'user' ? 'user' : 'assistant',
      content: msg.text,
    }));
    const allMessages = [systemPrompt, ...contextMessages, { role: 'user', content: prompt }];

    await runChat(allMessages);
    res.write(`event: status\ndata: ${JSON.stringify({ status: 'STREAMING_END' })}\n\n`);

    // Update session summary (non-streaming)
    try {
      const summaryPrompt = [
        { role: 'system', content: 'Summarize the conversation so far into 4-6 concise bullet points focusing on user intent, preferences, named entities (player, champion), and any constraints. Keep under 600 characters. Output plain text bullets only.' },
        ...contextMessages,
        { role: 'user', content: prompt },
      ];
      const comp: any = await groq.chat.completions.create({
        model: GROQ_MODEL,
        stream: false,
        messages: summaryPrompt,
      } as any);
      const text = comp.choices?.[0]?.message?.content || '';
      const clipped = (Array.isArray(text) ? text.map((t: any) => (typeof t === 'string' ? t : t?.text)).join('') : (text as string)).slice(0, 800);
      sessionMemory.set(sessionId, { summary: clipped });
      // Persist summary to KV for durability
      await MEMORY_KV.put(`session:${sessionId}:summary`, JSON.stringify({ summary: clipped, updatedAt: Date.now() }));
      // Ensure table exists and log to D1
      await CHAT_DB.exec(`
        CREATE TABLE IF NOT EXISTS messages (
          id TEXT PRIMARY KEY,
          session_id TEXT,
          role TEXT,
          content TEXT,
          created_at INTEGER
        );
      `);
      const now = Date.now();
      // Store last user message and assistant summary for audit
      await CHAT_DB.prepare('INSERT INTO messages (id, session_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)')
        .bind(`u-${sessionId}-${now}`, sessionId, 'user', prompt, now).run();
      await CHAT_DB.prepare('INSERT INTO messages (id, session_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)')
        .bind(`s-${sessionId}-${now}`, sessionId, 'assistant_summary', clipped, now).run();
    } catch (e) {
      // ignore
    }
  } catch (error) {
    console.error('[Fatal Error]', error);
    const msg = error instanceof Error ? error.message : String(error);
    res.write(`event: chunk\ndata: ${JSON.stringify({ text: `\n⚠️ 오류 발생: ${msg}` })}\n\n`);
    res.write(`event: status\ndata: ${JSON.stringify({ status: 'STREAMING_END' })}\n\n`);
  } finally {
    res.end();
    if (mcpClient) {
      await mcpClient.close();
    }
  }
});

// Health check endpoint
app.get('/', (req: Request, res: Response) => {
  res.json({ status: 'ok', service: 'expr-worker' });
});

app.listen(PORT);
export default httpServerHandler({ port: PORT });
