import { useState, useEffect } from "react";
import { usePathname } from "next/navigation";

export function useMobileNav() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState<boolean>(false);

  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  useEffect(() => {
    document.body.style.overflow = mobileOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileOpen]);

  return {
    mobileOpen,
    openMenu: () => setMobileOpen(true),
    closeMenu: () => setMobileOpen(false),
  };
}
