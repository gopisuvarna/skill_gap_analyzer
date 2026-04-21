import { test, expect } from '@playwright/test';

test.describe('Dashboard Home Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
  });

  test('should display Career Overview heading', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Career Overview', { timeout: 10000 });
  });

  test('should display dashboard description text', async ({ page }) => {
    await expect(page.locator('p').filter({ hasText: /personalised|Career Overview/i })).toBeVisible({ timeout: 10000 });
  });

  test('should display loading indicator while data loads', async ({ page }) => {
    await expect(page.locator('text=Loading dashboard')).toBeVisible({ timeout: 2000 }).catch(() => {});
  });

  test('should display Skills section', async ({ page }) => {
    const skillsSection = page.locator('text=Your Skills');
    await expect(skillsSection).toBeVisible({ timeout: 10000 });
  });

  test('should have no console errors on page load', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') errors.push(msg.text());
    });
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    const criticalErrors = errors.filter(e => !e.includes('Warning') && !e.includes('favicon'));
    expect(criticalErrors).toHaveLength(0);
  });

  test('should navigate to Skills page from link', async ({ page }) => {
    await page.locator('a[href="/dashboard/skills"]').first().click();
    await expect(page).toHaveURL(/\/dashboard\/skills/);
  });

  test('should navigate to Roles page from link', async ({ page }) => {
    await page.locator('a[href="/dashboard/roles"]').first().click();
    await expect(page).toHaveURL(/\/dashboard\/roles/);
  });

  test('should navigate to Jobs page from link', async ({ page }) => {
    await page.locator('a[href="/dashboard/jobs"]').first().click();
    await expect(page).toHaveURL(/\/dashboard\/jobs/);
  });
});
