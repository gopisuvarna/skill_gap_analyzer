$ErrorActionPreference = "Continue"
$devServer = Start-Process -FilePath "npm" -ArgumentList "run", "dev" -WorkingDirectory "C:\Users\Suvarna\OneDrive\Desktop\venkata-sai-gopi-suvarna-bailapudi\frontend" -PassThru -WindowStyle Hidden
Write-Host "Dev server started with PID: $($devServer.Id)"
Start-Sleep -Seconds 15
Write-Host "Waiting for server to be ready..."
$maxAttempts = 30
$attempt = 0
while ($attempt -lt $maxAttempts) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "Server is ready!"
            break
        }
    } catch {
        $attempt++
        Write-Host "Attempt $attempt of $maxAttempts - server not ready yet..."
        Start-Sleep -Seconds 2
    }
}
Write-Host "Running Playwright tests..."
node node_modules/@playwright/test/cli.js test --reporter=list
$exitCode = $LASTEXITCODE
Write-Host "Tests completed with exit code: $exitCode"
Write-Host "Stopping dev server..."
Stop-Process -Id $devServer.Id -Force -ErrorAction SilentlyContinue
exit $exitCode
