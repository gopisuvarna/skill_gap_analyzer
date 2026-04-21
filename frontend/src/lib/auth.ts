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
  const pairs = document.cookie.split(";");
  for (const pair of pairs) {
    const [rawKey, ...rawValueParts] = pair.trim().split("=");
    if (rawKey === "csrftoken") {
      return decodeURIComponent(rawValueParts.join("="));
    }
  }
  return "";
}
