import express, { Request, Response } from 'express';
import cors from 'cors';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js'; // SSE 대신 이거 사용
import Groq from 'groq-sdk';
import dotenv from 'dotenv';

// EventSource 관련 코드(폴리필, global 설정)는 모두 제거했습니다.

dotenv.config();

const app = express();
const PORT = 8080;
const MCP_SERVER_URL = 'http://localhost:8000/mcp'; // 만약 404가 뜨면 /mcp/messages 인지 확인 필요
const GROQ_API_KEY = process.env.GROQ_API_KEY || '';
const GROQ_MODEL = process.env.GROQ_MODEL || 'openai/gpt-oss-120b';
const MAX_CONTEXT_MESSAGES = 12; // rate-limit 대응을 위해 맥락을 제한

app.use(cors());

// ------------------------------------------------------------------
// 1. MCP 클라이언트 생성 (HTTP 방식)
// ------------------------------------------------------------------
async function createMcpClient() {
  console.log(`Attempting HTTP connection to ${MCP_SERVER_URL}...`);
  
  // SSEClientTransport 대신 StreamableHTTPClientTransport 사용
  const transport = new StreamableHTTPClientTransport(new URL(MCP_SERVER_URL));
  
  const client = new Client(
    { name: "express-groq-client", version: "1.0.0" },
    { capabilities: {} }
  );

  client.onerror = (err) => console.error("[MCP Client Error]", err);

  await client.connect(transport);
  return client;
}

// ------------------------------------------------------------------
// 2. 도구 변환 유틸리티 (MCP -> OpenAI tools)
// ------------------------------------------------------------------
function mapMcpToolsToOpenAI(mcpTools: any[]) {
  return mcpTools.map((tool) => ({
    type: 'function',
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
  // Vue 쪽과는 여전히 SSE로 통신해야 실시간 출력이 됩니다.
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');

  const prompt = req.query.prompt as string;
  const historyJson = req.query.history as string;
  
  if (!prompt) {
    res.write(`event: error\ndata: ${JSON.stringify({ error: "Prompt is required" })}\n\n`);
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
    const trimmedHistory = chatHistory.slice(-MAX_CONTEXT_MESSAGES);
    const contextMessages = trimmedHistory.map((msg: any) => ({
      role: msg.sender === 'user' ? 'user' : 'assistant',
      content: msg.text,
    }));
    const allMessages = [...contextMessages, { role: 'user', content: prompt }];
    
    await runChat(allMessages);
    res.write(`event: status\ndata: ${JSON.stringify({ status: 'STREAMING_END' })}\n\n`);

  } catch (error) {
    console.error("[Fatal Error]", error);
    const msg = error instanceof Error ? error.message : String(error);
    res.write(`event: chunk\ndata: ${JSON.stringify({ text: `\n⚠️ 오류 발생: ${msg}` })}\n\n`);
    res.write(`event: status\ndata: ${JSON.stringify({ status: 'STREAMING_END' })}\n\n`);
  } finally {
    res.end();
    if (mcpClient) {
        // HTTP Transport는 명시적 close가 덜 중요하지만 해제해주는 것이 좋음
        await mcpClient.close(); 
    }
  }
});

app.listen(PORT, () => {
  console.log(`Express server running on http://localhost:${PORT}`);
});