import { NextRequest } from "next/server";
export const runtime = "nodejs";
export const dynamic = "force-dynamic";
const maxBytes = 1_048_576;
async function forward(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  if (!["v1", "health", "docs", "openapi.json"].includes(path[0]))
    return new Response(null, { status: 404 });
  const headers = new Headers();
  for (const name of [
    "content-type",
    "cookie",
    "origin",
    "x-csrf-protection",
  ]) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }
  let body: Uint8Array | undefined;
  if (!["GET", "HEAD"].includes(request.method)) {
    const chunks: Uint8Array[] = [];
    let size = 0;
    const reader = request.body?.getReader();
    if (reader) {
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        size += value.length;
        if (size > maxBytes) {
          await reader.cancel();
          return Response.json(
            { error: { message: "File troppo grande: massimo 1 MB" } },
            { status: 413 },
          );
        }
        chunks.push(value);
      }
    }
    body = new Uint8Array(size);
    let position = 0;
    for (const chunk of chunks) {
      body.set(chunk, position);
      position += chunk.length;
    }
    headers.set("content-length", String(size));
  }
  try {
    const base = process.env.API_INTERNAL_URL || "http://127.0.0.1:8000";
    const url = new URL(
      `/api/${path.map(encodeURIComponent).join("/")}${request.nextUrl.search}`,
      base,
    );
    const response = await fetch(url, {
      method: request.method,
      headers,
      body: body as BodyInit | undefined,
      cache: "no-store",
      redirect: "manual",
      signal: AbortSignal.timeout(20_000),
    });
    const outgoing = new Headers({ "Cache-Control": "no-store" });
    for (const name of [
      "content-type",
      "content-disposition",
      "retry-after",
      "x-request-id",
    ]) {
      const value = response.headers.get(name);
      if (value) outgoing.set(name, value);
    }
    for (const cookie of response.headers.getSetCookie())
      outgoing.append("set-cookie", cookie);
    return new Response(response.body, {
      status: response.status,
      headers: outgoing,
    });
  } catch {
    return Response.json(
      {
        error: {
          message:
            "Servizio temporaneamente non disponibile. Riprova tra poco.",
        },
      },
      { status: 502 },
    );
  }
}
export { forward as GET, forward as POST, forward as PUT, forward as PATCH };
