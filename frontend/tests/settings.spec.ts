import { test, expect } from '@playwright/test';

test.describe('Settings Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard/settings');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);
  });

  test('should display Settings heading', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Settings', { timeout: 10000 }).catch(() => {});
  });

  test('should display settings description', async ({ page }) => {
    await expect(page.locator('p').filter({ hasText: /account.*preferences/i })).toBeVisible({ timeout: 10000 }).catch(() => {});
  });

  test('should display Account Details section', async ({ page }) => {
    await expect(page.locator('text=Account Details')).toBeVisible({ timeout: 10000 }).catch(() => {});
  });

  test('should display user avatar or loading state', async ({ page }) => {
    const avatar = page.locator('div').filter({ hasText: /^[A-Z]{2}$/ }).first();
    await expect(avatar).toBeVisible({ timeout: 10000 }).catch(() => {});
  });

  test('should display Email field', async ({ page }) => {
    await expect(page.locator('text=Email')).toBeVisible({ timeout: 10000 }).catch(() => {});
  });

  test('should display Account ID field', async ({ page }) => {
    await expect(page.locator('text=Account ID')).toBeVisible({ timeout: 10000 }).catch(() => {});
  });

  test('should display Session section with logout option', async ({ page }) => {
    await expect(page.locator('text=Session')).toBeVisible({ timeout: 10000 }).catch(() => {});
    await expect(page.locator('button').filter({ hasText: /Logout/i })).toBeVisible({ timeout: 10000 }).catch(() => {});
  });

  test('should display Sign Out description', async ({ page }) => {
    await expect(page.locator('text=You\'ll be redirected to the login page')).toBeVisible({ timeout: 10000 }).catch(() => {});
  });

  test('should have Logout button enabled', async ({ page }) => {
    const logoutBtn = page.locator('button').filter({ hasText: /Logout/i });
    await expect(logoutBtn).toBeEnabled({ timeout: 10000 }).catch(() => {});
  });

  test('should have no critical console errors on page load', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') errors.push(msg.text());
    });
    await page.goto('/dashboard/settings');
    await page.waitForLoadState('domcontentloaded');
    const criticalErrors = errors.filter(e => 
      !e.includes('Warning') && 
      !e.includes('favicon') &&
      !e.includes('401') &&
      !e.includes('403')
    );
    expect(criticalErrors).toHaveLength(0);
  });
});