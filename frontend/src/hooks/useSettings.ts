import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { User } from "@/lib/auth";

export function useSettings() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [logoutLoading, setLogoutLoading] = useState<boolean>(false);

  useEffect(() => {
    api
      .get<User>("/auth/me/")
      .then((r) => setUser(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  async function handleLogout() {
    setLogoutLoading(true);
    try {
      await api.post("/auth/logout/");
    } catch {
    } finally {
      router.push("/login");
    }
  }

  return { user, loading, logoutLoading, handleLogout };
}
