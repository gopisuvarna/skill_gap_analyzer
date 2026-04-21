export interface User {
  id: string;
  email: string;
  is_active: boolean;
  created_at: string;
}

export async function getCsrfToken(): Promise<string> {
  await fetch(
    `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/auth/me/`,
    {
      credentials: "include",
    },
  );
  const tokenMatch = /csrftoken=([^;]+)/.exec(document.cookie);
  return tokenMatch?.[1] ?? "";
}
