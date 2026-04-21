"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { UploadResultProvider } from "./upload-result-context";
import { useMobileNav } from "@/hooks/useMobileNav";
import "@/styles/components.css";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Overview", icon: "◈" },
  { href: "/dashboard/documents", label: "Resume", icon: "📄" },
  { href: "/dashboard/skills", label: "Skills", icon: "🛠" },
  { href: "/dashboard/roles", label: "Roles", icon: "🗺" },
  { href: "/dashboard/jobs", label: "Jobs", icon: "💼" },
  { href: "/dashboard/chat", label: "Mentor", icon: "✦" },
  { href: "/dashboard/settings", label: "Settings", icon: "⚙" },
];

function LogoMark() {
  return (
    <Link href="/dashboard" className="flex items-center gap-2.5 no-underline">
      <div className="sidebar-logo-mark">S</div>
      <span className="sidebar-brand-name">Skill Sync</span>
    </Link>
  );
}

type NavLinksProps = Readonly<{ mobile?: boolean }>;

function NavLinks({ mobile = false }: NavLinksProps) {
  const pathname = usePathname();
  return (
    <>
      {NAV_ITEMS.map((item) => {
        const active = pathname === item.href;
        return (
          <Link
            key={item.href}
            href={item.href}
            className={`nav-link ${mobile ? "mobile-nav-link" : ""} ${active ? "nav-link-active" : ""}`}
          >
            <span className={mobile ? "mobile-nav-icon" : "nav-link-icon"}>
              {item.icon}
            </span>
            {item.label}
          </Link>
        );
      })}
    </>
  );
}

type DashboardLayoutProps = Readonly<{ children: React.ReactNode }>;

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const pathname = usePathname();
  const { mobileOpen, openMenu, closeMenu } = useMobileNav();
  const activeLabel =
    NAV_ITEMS.find((n) => n.href === pathname)?.label ?? "Dashboard";

  return (
    <UploadResultProvider>
      <div className="flex min-h-screen">
        
        <aside className="sidebar hidden lg:flex">
          <div className="sidebar-logo-area">
            <LogoMark />
          </div>
          <nav className="sidebar-nav">
            <NavLinks />
          </nav>
        </aside>

        
        {mobileOpen && (
          <button
            type="button"
            aria-label="Close menu overlay"
            className="mobile-overlay lg:hidden fixed inset-0 z-40"
            onClick={closeMenu}
          />
        )}

        
        <div
          className={`mobile-drawer lg:hidden fixed inset-y-0 left-0 z-50 transition-transform duration-300 ${
            mobileOpen ? "mobile-drawer-open" : "mobile-drawer-closed"
          }`}
        >
          <div className="mobile-drawer-header">
            <LogoMark />
            <button
              className="mobile-close-btn"
              onClick={closeMenu}
              aria-label="Close menu"
            >
              ×
            </button>
          </div>
          <nav className="mobile-drawer-nav">
            <NavLinks mobile />
          </nav>
        </div>

        
        <div className="flex flex-col flex-1 min-w-0">
          
          <header className="mobile-topbar lg:hidden sticky top-0 z-30 flex items-center gap-3 px-4 py-3">
            <button
              className="hamburger-btn"
              onClick={openMenu}
              aria-label="Open menu"
            >
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              >
                <line x1="3" y1="6" x2="21" y2="6" />
                <line x1="3" y1="12" x2="21" y2="12" />
                <line x1="3" y1="18" x2="21" y2="18" />
              </svg>
            </button>
            <span className="mobile-topbar-title">{activeLabel}</span>
            <div className="mobile-topbar-logo ml-auto">S</div>
          </header>

          
          <main className="flex-1 p-4 sm:p-8">
            <div className="max-w-[1100px] mx-auto">{children}</div>
          </main>
        </div>
      </div>
    </UploadResultProvider>
  );
}
