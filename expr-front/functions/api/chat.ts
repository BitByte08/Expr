import type { PagesFunction } from '@cloudflare/workers-types';

// Proxy SSE to the backend (Express/FastAPI) from Cloudflare Pages Functions.
// Set BACKEND_API_URL in Pages env (e.g., https://your-backend.example.com).
export const onRequest: PagesFunction = async ({ request, env }) => {
  const backendBase = env.BACKEND_API_URL as string | undefined;
  if (!backendBase) {
    return new Response('BACKEND_API_URL is not set', { status: 500 });
  }

  const url = new URL(request.url);
  const prompt = url.searchParams.get('prompt');
  const history = url.searchParams.get('history');

  if (!prompt) {
    return new Response('prompt is required', { status: 400 });
  }

  const target = new URL('/api/chat', backendBase);
  target.searchParams.set('prompt', prompt);
  if (history) target.searchParams.set('history', history);

  const backendResp = await fetch(target.toString(), {
    method: 'GET',
    headers: {
      Accept: 'text/event-stream',
    },
  });

  if (!backendResp.ok || !backendResp.body) {
    return new Response(`Upstream error: ${backendResp.status}`, { status: 502 });
  }

  // Stream passthrough for SSE
  const { readable, writable } = new TransformStream();
  backendResp.body.pipeTo(writable);

  return new Response(readable, {
    status: 200,
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
      'Access-Control-Allow-Origin': '*',
    },
  });
};
