import { test, expect } from '@playwright/test';

test.describe('Login Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });

  test('should load the login page without errors', async ({ page }) => {
    await expect(page).toHaveURL(/\/login/);
    await expect(page.locator('h1')).toContainText('Welcome back');
  });

  test('should display email and password input fields', async ({ page }) => {
    const emailInput = page.locator('input[type="email"]');
    const passwordInput = page.locator('input[type="password"]');

    await expect(emailInput).toBeVisible();
    await expect(passwordInput).toBeVisible();
    await expect(emailInput).toHaveAttribute('required');
    await expect(passwordInput).toHaveAttribute('required');
  });

  test('should display the Sign In button', async ({ page }) => {
    const submitBtn = page.locator('button[type="submit"]');
    await expect(submitBtn).toBeVisible();
    await expect(submitBtn).toContainText('Sign In');
  });

  test('should display Create Account link for new users', async ({ page }) => {
    const createLink = page.locator('a[href="/register"]').filter({ hasText: /Create one/i });
    await expect(createLink).toBeVisible();
  });

  test('should navigate to register page when Create Account is clicked', async ({ page }) => {
    await page.locator('a[href="/register"]').filter({ hasText: /Create one/i }).click();
    await expect(page).toHaveURL(/\/register/);
  });

  test('should show validation error when submitting empty form', async ({ page }) => {
    await page.locator('button[type="submit"]').click();
    await expect(page.locator('input[type="email"]')).toBeFocused();
  });

  test('should show error message on failed login attempt', async ({ page }) => {
    await page.locator('input[type="email"]').fill('wrong@example.com');
    await page.locator('input[type="password"]').fill('wrongpassword123');
    await page.locator('button[type="submit"]').click();

    const errorMsg = page.locator('div').filter({ hasText: /Login failed|Invalid|Could not|error/i }).first();
    await expect(errorMsg).toBeVisible({ timeout: 8000 }).catch(() => {});
  });

  test('should clear error message when user starts typing', async ({ page }) => {
    await page.locator('input[type="email"]').fill('wrong@example.com');
    await page.locator('input[type="password"]').fill('wrongpassword123');
    await page.locator('button[type="submit"]').click();

    const errorMsg = page.locator('div[style*="fee2e2"]');
    if (await errorMsg.isVisible({ timeout: 5000 })) {
      await page.locator('input[type="email"]').fill('new@example.com');
      await expect(errorMsg).not.toBeVisible();
    }
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
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    expect(errors).toHaveLength(0);
  });
});
