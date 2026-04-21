import { test, expect } from '@playwright/test';

test.describe('Accessibility Tests', () => {
  const pages = [
    { name: 'Home', path: '/' },
    { name: 'Login', path: '/login' },
    { name: 'Register', path: '/register' },
    { name: 'Dashboard', path: '/dashboard' },
    { name: 'Documents', path: '/dashboard/documents' },
    { name: 'Skills', path: '/dashboard/skills' },
    { name: 'Jobs', path: '/dashboard/jobs' },
    { name: 'Roles', path: '/dashboard/roles' },
    { name: 'Chat', path: '/dashboard/chat' },
    { name: 'Settings', path: '/dashboard/settings' },
  ];

  for (const pageInfo of pages) {
    test(`${pageInfo.name} page should load without errors`, async ({ page }) => {
      await page.goto(pageInfo.path);
      await page.waitForLoadState('domcontentloaded');
      await expect(page).toHaveTitle(/.+/);
    });
  }

  test('Login page should have proper form labels', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('domcontentloaded');
    await expect(page.locator('label').filter({ hasText: /email/i })).toBeVisible();
    await expect(page.locator('label').filter({ hasText: /password/i })).toBeVisible();
  });

  test('Register page should have proper form labels', async ({ page }) => {
    await page.goto('/register');
    await page.waitForLoadState('domcontentloaded');
    await expect(page.locator('label').filter({ hasText: /email/i })).toBeVisible();
    await expect(page.locator('label').filter({ hasText: /password/i })).toBeVisible();
  });

  test('All pages should have proper page titles', async ({ page }) => {
    for (const pageInfo of pages) {
      await page.goto(pageInfo.path, { timeout: 15000 });
      await page.waitForLoadState('domcontentloaded');
      const title = await page.title();
      expect(title.length).toBeGreaterThan(0);
    }
  });

  test('Login form inputs should have proper types', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('domcontentloaded');
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
  });

  test('Register form inputs should have proper types', async ({ page }) => {
    await page.goto('/register');
    await page.waitForLoadState('domcontentloaded');
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
  });
});
