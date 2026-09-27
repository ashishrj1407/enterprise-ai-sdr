import { NextResponse } from "next/server";

const BACKEND =
  process.env.BACKEND_ORIGIN || process.env.LOCAL_BACKEND_ORIGIN || "http://backend:8000";

async function proxy(request, context) {
  const params = await context.params;
  const pathParts = params.path || [];
  const targetPath = Array.isArray(pathParts) ? pathParts.join("/") : String(pathParts);
  const url = new URL(request.url);
  const target = `${BACKEND}/api/${targetPath}${url.search}`;

  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  const customerId = request.headers.get("x-customer-id");
  if (contentType) headers.set("content-type", contentType);
  if (customerId) headers.set("X-Customer-Id", customerId);

  const init = {
    method: request.method,
    headers,
    cache: "no-store",
  };

  if (request.method !== "GET" && request.method !== "HEAD") {
    init.body = await request.text();
  }

  const upstream = await fetch(target, init);
  const body = await upstream.text();
  return new NextResponse(body, {
    status: upstream.status,
    headers: {
      "content-type": upstream.headers.get("content-type") || "application/json",
    },
  });
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
