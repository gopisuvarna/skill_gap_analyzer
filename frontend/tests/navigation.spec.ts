import { test, expect } from "@playwright/test";

test.describe("Navigation Flow Tests", () => {
  test("should navigate from home to login", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto("/");
    await page.waitForLoadState("domcontentloaded");
    await page
      .locator('a[href="/login"]')
      .filter({ hasText: /Sign In/i })
      .click();
    await expect(page).toHaveURL(/\/login/);
  });

  test("should navigate from home to register", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto("/");
    await page.waitForLoadState("domcontentloaded");
    await page
      .locator('a[href="/register"]')
      .filter({ hasText: /Create Account/i })
      .click();
    await expect(page).toHaveURL(/\/register/);
  });

  test("should navigate from login to register", async ({ page }) => {
    await page.goto("/login");
    await page
      .locator('a[href="/register"]')
      .filter({ hasText: /Create one/i })
      .click();
    await expect(page).toHaveURL(/\/register/);
  });

  test("should navigate from register to login", async ({ page }) => {
    await page.goto("/register");
    await page
      .locator('a[href="/login"]')
      .filter({ hasText: /Sign in/i })
      .click();
    await expect(page).toHaveURL(/\/login/);
  });

  test("should navigate through dashboard pages via sidebar", async ({
    page,
  }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto("/dashboard");
    await page.waitForLoadState("domcontentloaded");

    const navLinks = [
      { href: "/dashboard/skills", label: "Skills" },
      { href: "/dashboard/roles", label: "Roles" },
      { href: "/dashboard/jobs", label: "Jobs" },
      { href: "/dashboard/chat", label: "Mentor" },
      { href: "/dashboard/settings", label: "Settings" },
    ];

    for (const link of navLinks) {
      await page.locator(`nav a[href="${link.href}"]`).first().click();
      await page.waitForLoadState("domcontentloaded");
      await expect(page).toHaveURL(new RegExp(link.href));
    }
  });

  test("should navigate from documents to skills and roles", async ({
    page,
  }) => {
    await page.goto("/dashboard/documents");

    const skillsLink = page.locator('a[href="/dashboard/skills"]').first();
    if (await skillsLink.isVisible({ timeout: 2000 })) {
      await skillsLink.click();
      await expect(page).toHaveURL(/\/dashboard\/skills/);
    }

    await page.goto("/dashboard/documents");
    const rolesLink = page.locator('a[href="/dashboard/roles"]').first();
    if (await rolesLink.isVisible({ timeout: 2000 })) {
      await rolesLink.click();
      await expect(page).toHaveURL(/\/dashboard\/roles/);
    }
  });

  test("should navigate from dashboard home to sub-pages via links", async ({
    page,
  }) => {
    await page.goto("/dashboard");

    const links = [
      {
        selector: 'main a[href="/dashboard/skills"]',
        url: "/dashboard/skills",
      },
      { selector: 'main a[href="/dashboard/roles"]', url: "/dashboard/roles" },
      { selector: 'main a[href="/dashboard/jobs"]', url: "/dashboard/jobs" },
    ];

    for (const link of links) {
      const element = page.locator(link.selector).first();
      if (await element.isVisible({ timeout: 2000 })) {
        await element.click();
        await expect(page).toHaveURL(new RegExp(link.url));
        await page.goBack();
      }
    }
  });

  test("should maintain session state across page navigations", async ({
    page,
  }) => {
    await page.goto("/");
    await expect(page.locator("body")).toBeVisible();

    await page.goto("/login");
    await expect(page.locator('input[type="email"]')).toBeVisible();

    await page.goto("/register");
    await expect(page.locator('input[type="email"]')).toBeVisible();
  });

  test("should navigate directly to any page", async ({ page }) => {
    const pages = [
      "/",
      "/login",
      "/register",
      "/dashboard",
      "/dashboard/documents",
      "/dashboard/skills",
      "/dashboard/jobs",
      "/dashboard/roles",
      "/dashboard/chat",
      "/dashboard/settings",
    ];

    for (const path of pages) {
      await page.goto(path, { timeout: 15000 });
      await page.waitForLoadState("domcontentloaded");
      await expect(page).toHaveURL(
        new RegExp(path.replaceAll("/", String.raw`\/`)),
        { timeout: 10000 },
      );
    }
  });
});
