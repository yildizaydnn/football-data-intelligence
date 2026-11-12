import createClient from "openapi-fetch";

import type { paths } from "./schema";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const api = createClient<paths>({ baseUrl: API_URL });

/** Backend'in standart hata gövdesi: {"error": {"code", "message"}}. */
export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type ApiResult<T> = {
  data?: T;
  error?: unknown;
  response: Response;
};

/** openapi-fetch sonucunu "ya veri ya hata fırlat" biçimine çevirir (TanStack Query bunu bekler). */
export async function unwrap<T>(request: Promise<ApiResult<T>>): Promise<T> {
  let result: ApiResult<T>;
  try {
    result = await request;
  } catch {
    throw new ApiError("Sunucuya ulaşılamıyor", 0, "network_error");
  }
  const { data, error, response } = result;
  if (error !== undefined || data === undefined) {
    const detail = (error as { error?: { code?: string; message?: string } } | undefined)?.error;
    throw new ApiError(
      detail?.message ?? `Beklenmeyen yanıt (HTTP ${response.status})`,
      response.status,
      detail?.code ?? "unknown_error",
    );
  }
  return data;
}
