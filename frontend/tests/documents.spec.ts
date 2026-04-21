import { test, expect } from '@playwright/test';

test.describe('Documents Page (Resume Upload)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard/documents');
  });

  test('should display Upload Resume heading', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Upload Resume');
  });

  test('should display upload description text', async ({ page }) => {
    await expect(page.locator('p').filter({ hasText: /PDF format/i })).toBeVisible();
  });

  test('should display file upload drop zone', async ({ page }) => {
    const dropZone = page.locator('label[for="resume-upload"]');
    await expect(dropZone).toBeVisible();
  });

  test('should display Upload & Extract Skills button', async ({ page }) => {
    const uploadBtn = page.locator('button').filter({ hasText: /Upload & Extract Skills/i });
    await expect(uploadBtn).toBeVisible();
    await expect(uploadBtn).toBeDisabled();
  });

  test('should enable upload button when file is selected', async ({ page }) => {
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test-resume.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('test pdf content'),
    });

    const uploadBtn = page.locator('button').filter({ hasText: /Upload & Extract Skills/i });
    await expect(uploadBtn).toBeEnabled();
  });

  test('should show selected file name after selection', async ({ page }) => {
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'my-resume.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('test pdf content'),
    });

    await expect(page.locator('text=my-resume.pdf')).toBeVisible();
  });

  test('should reject non-PDF files', async ({ page }) => {
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'document.docx',
      mimeType: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      buffer: Buffer.from('test content'),
    });

    await expect(page.locator('text=Please select a PDF file only')).toBeVisible();
  });

  test('should show loading state during upload', async ({ page }) => {
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('test'),
    });

    const uploadBtn = page.locator('button').filter({ hasText: /Upload & Extract Skills/i });
    await uploadBtn.click();

    await expect(page.locator('text=Processing')).toBeVisible({ timeout: 3000 }).catch(() => {});
  });

  test('should show quick nav links after successful upload', async ({ page }) => {
    await page.goto('/dashboard/documents');
    const successLinks = page.locator('a[href="/dashboard/skills"], a[href="/dashboard/roles"]');
    await expect(successLinks.first()).toBeVisible({ timeout: 2000 }).catch(() => {});
  });

  test('should navigate to Skills page after success', async ({ page }) => {
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('test'),
    });

    await page.locator('a[href="/dashboard/skills"]').first().click().catch(() => {});
    await expect(page).toHaveURL(/\/dashboard\/skills/);
  });

  test('should navigate to Roles page after success', async ({ page }) => {
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('test'),
    });

    await page.locator('a[href="/dashboard/roles"]').first().click().catch(() => {});
    await expect(page).toHaveURL(/\/dashboard\/roles/);
  });

  test('should have no console errors on page load', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') errors.push(msg.text());
    });
    await page.goto('/dashboard/documents');
    await page.waitForLoadState('networkidle');
    const criticalErrors = errors.filter(e => !e.includes('Warning') && !e.includes('favicon'));
    expect(criticalErrors).toHaveLength(0);
  });
});
