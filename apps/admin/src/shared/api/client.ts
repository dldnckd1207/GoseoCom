export const BASE_URL =
  import.meta.env.VITE_PUBLIC_API_URL ??
  import.meta.env.VITE_API_BASE_URL ??
  "";

export interface ApiWrappedResponse<T> {
  header: { success: boolean; code: string; message: string };
  body: { data: T | null };
}

export class ApiError extends Error {
  constructor(
    public code: string,
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function extractData<T>(json: ApiWrappedResponse<T>, status: number): T {
  if (!json.header.success) {
    throw new ApiError(json.header.code, json.header.message, status);
  }

  return json.body.data as T;
}

// double-submit CSRF: non-httpOnly csrf_token 쿠키를 읽어 X-CSRF-Token 헤더로 재전송 (보안 #7)
function getCsrfToken(): string | undefined {
  if (typeof document === "undefined") return undefined;
  const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : undefined;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string> | undefined),
  };
  const csrf = getCsrfToken();
  if (csrf) headers["X-CSRF-Token"] = csrf;

  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    credentials: "include",
    headers,
  });

  if (res.status === 401) {
    throw new ApiError("UNAUTHORIZED", "관리자 로그인이 필요합니다.", res.status);
  }

  if (res.status === 0 || res.status >= 502) {
    throw new ApiError("NETWORK_ERROR", "서버에 연결할 수 없습니다.", res.status);
  }

  const json = (await res.json()) as ApiWrappedResponse<T>;
  return extractData(json, res.status);
}

export const apiClient = {
  get: <T>(path: string) => request<T>(path, { method: "GET" }),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body ?? {}) }),
  put: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PUT", body: JSON.stringify(body) }),
  delete: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "DELETE", body: JSON.stringify(body ?? {}) }),
};
