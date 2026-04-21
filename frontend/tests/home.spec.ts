import { test, expect } from '@playwright/test';

test.describe('Home Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should load the home page without errors', async ({ page }) => {
    await expect(page).toHaveTitle(/AI Skill Sync/);
    await expect(page.locator('body')).toBeVisible();
  });

  test('should display the main heading with AI Skill Sync branding', async ({ page }) => {
    const heading = page.locator('h1');
    await expect(heading).toBeVisible();
    await expect(heading).toContainText('AI');
    await expect(heading).toContainText('Skill Sync');
  });

  test('should display hero description text', async ({ page }) => {
    const description = page.locator('p').filter({ hasText: /skill gap|Identify skill gaps/ }).first();
    await expect(description).toBeVisible();
    await expect(description).toContainText(/Identify skill gaps|Explore career paths/);
  });

  test('should display Sign In and Create Account buttons', async ({ page }) => {
    const signInBtn = page.locator('a[href="/login"]').filter({ hasText: /Sign In/i });
    const createBtn = page.locator('a[href="/register"]').filter({ hasText: /Create Account/i });

    await expect(signInBtn).toBeVisible();
    await expect(createBtn).toBeVisible();
  });

  test('should navigate to login page when Sign In is clicked', async ({ page }) => {
    await page.locator('a[href="/login"]').filter({ hasText: /Sign In/i }).click();
    await expect(page).toHaveURL(/\/login/);
  });

  test('should navigate to register page when Create Account is clicked', async ({ page }) => {
    await page.locator('a[href="/register"]').filter({ hasText: /Create Account/i }).click();
    await expect(page).toHaveURL(/\/register/);
  });

  test('should display three feature cards', async ({ page }) => {
    const cards = page.locator('div.card');
    await expect(cards).toHaveCount(3);
  });

  test('should have no console errors on page load', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') errors.push(msg.text());
    });
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    expect(errors).toHaveLength(0);
  });

  test('should have proper meta description', async ({ page }) => {
    const metaDesc = page.locator('meta[name="description"]');
    await expect(metaDesc).toHaveAttribute('content', /skill gap|career|job readiness/i);
  });
});
