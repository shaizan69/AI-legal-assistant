# PowerShell script to restart Ollama with GPU
Write-Host "🔄 RESTARTING OLLAMA WITH GPU FORCE" -ForegroundColor Green
Write-Host "=" * 50

# Stop Ollama
Write-Host "Stopping Ollama..." -ForegroundColor Yellow
Get-Process -Name "ollama" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 3

# Set environment variables
Write-Host "Setting GPU environment variables..." -ForegroundColor Yellow
$env:CUDA_VISIBLE_DEVICES = "0"
$env:OLLAMA_GPU_LAYERS = "-1"
$env:OLLAMA_NUM_GPU = "1"
$env:OLLAMA_MODELS = "D:\Ollama"

Write-Host "CUDA_VISIBLE_DEVICES = $env:CUDA_VISIBLE_DEVICES"
Write-Host "OLLAMA_GPU_LAYERS = $env:OLLAMA_GPU_LAYERS"
Write-Host "OLLAMA_NUM_GPU = $env:OLLAMA_NUM_GPU"
Write-Host "OLLAMA_MODELS = $env:OLLAMA_MODELS"

# Start Ollama
Write-Host "Starting Ollama with GPU settings..." -ForegroundColor Yellow
Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden

# Wait for Ollama to start
Write-Host "Waiting for Ollama to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Test GPU usage
Write-Host "Testing GPU usage..." -ForegroundColor Yellow
try {
    $payload = @{
        model = "mistral-legal-q4:latest"
        prompt = "What is a contract? Answer briefly."
        stream = $false
        options = @{
            num_gpu = 1
            gpu_layers = -1
            low_vram = $false
            num_ctx = 1024
            num_thread = 4
            num_batch = 4
        }
    } | ConvertTo-Json -Depth 3

    $response = Invoke-RestMethod -Uri "http://localhost:11434/api/generate" -Method Post -Body $payload -ContentType "application/json" -TimeoutSec 30
    
    Write-Host "✅ GPU test successful!" -ForegroundColor Green
    Write-Host "Response: $($response.response.Substring(0, [Math]::Min(100, $response.response.Length)))..."
    
} catch {
    Write-Host "❌ GPU test failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n📊 CHECK TASK MANAGER GPU USAGE NOW!" -ForegroundColor Cyan
Write-Host "Look for GPU memory usage in Task Manager > Performance > GPU" -ForegroundColor Cyan
Write-Host "=" * 50
