import { test, expect } from '@playwright/test';

test.describe('Register Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/register');
  });

  test('should load the register page without errors', async ({ page }) => {
    await expect(page).toHaveURL(/\/register/);
    await expect(page.locator('h1')).toContainText('Create account');
  });

  test('should display email and password input fields', async ({ page }) => {
    const emailInput = page.locator('input[type="email"]');
    const passwordInput = page.locator('input[type="password"]');

    await expect(emailInput).toBeVisible();
    await expect(passwordInput).toBeVisible();
  });

  test('should display Create Account button', async ({ page }) => {
    const submitBtn = page.locator('button[type="submit"]');
    await expect(submitBtn).toBeVisible();
    await expect(submitBtn).toContainText('Create Account');
  });

  test('should navigate to login page when Sign in link is clicked', async ({ page }) => {
    await page.locator('a[href="/login"]').filter({ hasText: /Sign in/i }).click();
    await expect(page).toHaveURL(/\/login/);
  });

  test('should show validation error when submitting empty form', async ({ page }) => {
    await page.locator('button[type="submit"]').click();
    await expect(page.locator('input[type="email"]')).toBeFocused();
  });

  test('should show password min length hint', async ({ page }) => {
    const hint = page.locator('span').filter({ hasText: /min 8 characters/i });
    await expect(hint).toBeVisible();
  });

  test('should show loading state while submitting', async ({ page }) => {
    await page.locator('input[type="email"]').fill('test@example.com');
    await page.locator('input[type="password"]').fill('password123');
    
    await page.locator('button[type="submit"]').click();
    
    const loadingBtn = page.locator('button[type="submit"]');
    await expect(loadingBtn).toBeDisabled();
  });

  test('should have logo mark visible', async ({ page }) => {
    const logoMark = page.locator('div').filter({ hasText: /^S$/ }).first();
    await expect(logoMark).toBeVisible();
  });

  test('should have no console errors on page load', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') errors.push(msg.text());
    });
    await page.goto('/register');
    await page.waitForLoadState('networkidle');
    expect(errors).toHaveLength(0);
  });
});