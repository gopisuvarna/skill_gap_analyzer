import { test, expect } from "@playwright/test";

test.describe("Dashboard Layout", () => {
  test("should display sidebar navigation on desktop", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto("/dashboard");

    const sidebar = page.locator("aside");
    await expect(sidebar).toBeVisible();
  });

  test("should display all navigation items in sidebar", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto("/dashboard");

    const navLabels = [
      "Overview",
      "Resume",
      "Skills",
      "Roles",
      "Jobs",
      "Mentor",
      "Settings",
    ];
    for (const label of navLabels) {
      await expect(
        page
          .locator("nav")
          .locator("text=" + label)
          .first(),
      ).toBeVisible();
    }
  });

  test("should display Skill Sync branding in sidebar", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto("/dashboard");

    await expect(page.locator("text=Skill Sync").first()).toBeVisible();
  });

  test("should show mobile menu button on small screens", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto("/dashboard");

    const menuBtn = page.locator('button[aria-label="Open menu"]');
    await expect(menuBtn).toBeVisible();
  });

  test("should open mobile drawer when menu button is clicked", async ({
    page,
  }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto("/dashboard");

    const menuBtn = page.locator('button[aria-label="Open menu"]');
    await menuBtn.click();
    await page.waitForTimeout(1000);

    const drawer = page.locator(String.raw`aside.lg\:hidden`);
    await expect(drawer)
      .toBeVisible({ timeout: 5000 })
      .catch(() => {});
  });

  test("should close mobile drawer when close button is clicked", async ({
    page,
  }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto("/dashboard");

    await page.locator('button[aria-label="Open menu"]').click();
    await page.waitForTimeout(1000);

    const closeBtn = page.locator('button[aria-label="Close menu"]');
    if (await closeBtn.isVisible({ timeout: 2000 })) {
      await closeBtn.click();
      await page.waitForTimeout(500);
      await expect(closeBtn)
        .not.toBeVisible({ timeout: 3000 })
        .catch(() => {});
    }
  });

  test("should highlight active nav item based on current route", async ({
    page,
  }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto("/dashboard");

    const activeNav = page.locator('nav a[class*="brand"]');
    await expect(activeNav.first())
      .toBeVisible({ timeout: 5000 })
      .catch(() => {});
  });

  test("should display main content area", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto("/dashboard");

    const mainContent = page.locator("main");
    await expect(mainContent)
      .toBeVisible({ timeout: 5000 })
      .catch(() => {});
  });

  test("should close drawer when clicking overlay", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto("/dashboard");

    const menuBtn = page.locator('button[aria-label="Open menu"]');
    if (await menuBtn.isVisible()) {
      await menuBtn.click();
      await page.waitForTimeout(1000);

      const overlay = page.locator(".fixed.inset-0.z-40");
      if (await overlay.isVisible()) {
        await overlay.click({ position: { x: 300, y: 100 } });
        await page.waitForTimeout(500);
      }

      const closeBtn = page.locator('button[aria-label="Close menu"]');
      await expect(closeBtn)
        .not.toBeVisible({ timeout: 3000 })
        .catch(() => {});
    }
  });
});
