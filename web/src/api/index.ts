export async function http<T = unknown>(
  url: string,
  init: RequestInit = {},
): Promise<T> {
  const response = await fetch(url, init);

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const contentType = response.headers.get("content-type") ?? "";

  if (contentType.includes("application/json")) {
    return (await response.json()) as T;
  }

  return (await response.text()) as T;
}


export async function post<T = unknown>(url: string, init: RequestInit = {}): Promise<T> {
  return http<T>(url, { ...init, method: "POST" });
}

export async function get<T = unknown>(url: string, init: RequestInit = {}): Promise<T> {
  return http<T>(url, { ...init, method: "GET" });
}

export async function put<T = unknown>(url: string, init: RequestInit = {}): Promise<T> {
  return http<T>(url, { ...init, method: "PUT" });
}

export async function del<T = unknown>(url: string, init: RequestInit = {}): Promise<T> {
  return http<T>(url, { ...init, method: "DELETE" });
} 

