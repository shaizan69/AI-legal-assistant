param(
    [string]$DestinationRoot = 'D:\Hugging Face',
    [switch]$IncludePipCache,
    [switch]$IncludeCondaPkgs,
    [switch]$IncludeTorchCaches,
    [switch]$DryRun,
    [switch]$VerboseLog
)

# Guard: Windows PowerShell 5.1+
if ($PSVersionTable.PSVersion.Major -lt 5) {
    Write-Error 'This script requires PowerShell 5.1 or later.'
    exit 1
}

function Write-Info([string]$msg) {
    if ($VerboseLog) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
}

function Write-Step([string]$msg) {
    Write-Host "[+] $msg" -ForegroundColor Green
}

function Write-Warn([string]$msg) {
    Write-Host "[WARN] $msg" -ForegroundColor Yellow
}

function Write-Err([string]$msg) {
    Write-Host "[ERR]  $msg" -ForegroundColor Red
}

function Get-SizeGB([string]$path) {
    try {
        if (-not (Test-Path -LiteralPath $path)) { return 0 }
        $sum = (Get-ChildItem -LiteralPath $path -Recurse -Force -ErrorAction SilentlyContinue |
            Where-Object { -not $_.PSIsContainer } | Measure-Object -Property Length -Sum).Sum
        if (-not $sum) { return 0 }
        return [math]::Round($sum / 1GB, 2)
    } catch { return 0 }
}

function Ensure-Directory([string]$path) {
    if (-not (Test-Path -LiteralPath $path)) {
        if ($DryRun) { Write-Info "Would create directory: $path" }
        else { New-Item -ItemType Directory -Path $path -Force | Out-Null }
    }
}

function Make-UniqueDestination([string]$root, [string]$leaf) {
    $candidate = Join-Path $root $leaf
    $i = 1
    while (Test-Path -LiteralPath $candidate) {
        $candidate = Join-Path $root ("{0}_{1}" -f $leaf, $i)
        $i++
    }
    return $candidate
}

function Create-JunctionSafe([string]$linkPath, [string]$targetPath) {
    try {
        if ($DryRun) {
            Write-Info "Would create junction: '$linkPath' -> '$targetPath'"
            return $true
        }
        # Prefer native PowerShell junction creation when available
        try {
            New-Item -ItemType Junction -Path $linkPath -Target $targetPath -ErrorAction Stop | Out-Null
            return $true
        } catch {
            # Fallback to mklink
            $lp = '"' + $linkPath + '"'
            $tp = '"' + $targetPath + '"'
            $out = cmd /c ("mklink /J " + $lp + " " + $tp) 2>&1
            if ($LASTEXITCODE -eq 0) { return $true }
            Write-Err "mklink failed: $out"
            return $false
        }
    } catch {
        Write-Err "Failed to create junction: $linkPath -> $targetPath. $_"
        return $false
    }
}

function Is-Junction([string]$path) {
    try {
        $item = Get-Item -LiteralPath $path -ErrorAction Stop
        return ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0
    } catch { return $false }
}

function Move-And-Link([string]$sourcePath, [string]$destRoot, [ref]$movedList) {
    if (-not (Test-Path -LiteralPath $sourcePath)) {
        Write-Info "Missing: $sourcePath"
        return
    }

    if (Is-Junction $sourcePath) {
        Write-Info "Already a junction (skip): $sourcePath"
        return
    }

    # Only move if on C: drive
    if (-not ($sourcePath -like 'C:*')) {
        Write-Info "Not on C: (skip): $sourcePath"
        return
    }

    $leaf = Split-Path -Path $sourcePath -Leaf
    if (-not $leaf) { $leaf = (Split-Path -Path $sourcePath -Parent | Split-Path -Leaf) }
    $destPath = Make-UniqueDestination -root $destRoot -leaf $leaf

    Write-Step "Relocating '$sourcePath' -> '$destPath'"

    if (-not $DryRun) {
        try {
            Ensure-Directory (Split-Path -Path $destPath -Parent)
            Move-Item -LiteralPath $sourcePath -Destination $destPath -Force -ErrorAction Stop
        } catch {
            Write-Err "Move failed: $sourcePath -> $destPath. $_"
            return
        }
    } else {
        Write-Info "Would move: $sourcePath -> $destPath"
    }

    # Recreate parent for junction
    $parent = Split-Path -Path $sourcePath -Parent
    Ensure-Directory $parent

    # Create junction
    if (Create-JunctionSafe -linkPath $sourcePath -targetPath $destPath) {
        $null = $movedList.Value.Add([pscustomobject]@{ Source = $sourcePath; Target = $destPath })
        Write-Info "Linked: $sourcePath -> $destPath"
    } else {
        Write-Err "Could not create junction for: $sourcePath"
    }
}

# Record free space before
$driveCBefore = (Get-PSDrive -Name C).Free
$freeGBBefore = [math]::Round($driveCBefore / 1GB, 2)

Write-Host "\n=== Free Hugging Face Space (C: -> $DestinationRoot) ===" -ForegroundColor Magenta

# Prepare destination
Ensure-Directory $DestinationRoot

$home  = $env:USERPROFILE
$local = $env:LOCALAPPDATA

# Canonical Hugging Face and related cache locations
$candidates = New-Object System.Collections.Generic.List[string]
$candidates.Add( (Join-Path $home '.cache\huggingface') )
$candidates.Add( (Join-Path $home 'AppData\Local\huggingface') )
$candidates.Add( (Join-Path $home 'AppData\Roaming\huggingface') )
$candidates.Add( 'C:\ProgramData\huggingface' )
$candidates.Add( 'C:\huggingface' )

if ($IncludeTorchCaches) {
    $candidates.Add( (Join-Path $home '.cache\torch\hub\checkpoints') )
    $candidates.Add( (Join-Path $home '.cache\torch\transformers') )
}

if ($IncludePipCache) {
    if ($local) { $candidates.Add( (Join-Path $local 'pip\Cache') ) }
}

if ($IncludeCondaPkgs) {
    $candidates.Add( (Join-Path $home '.conda\pkgs') )
    $candidates.Add( 'C:\ProgramData\conda\pkgs' )
}

# Collect found paths and sizes
Write-Step 'Scanning candidate directories...'
$found = New-Object System.Collections.Generic.List[pscustomobject]
foreach ($p in $candidates) {
    if (Test-Path -LiteralPath $p) {
        $sizeGB = Get-SizeGB -path $p
        $found.Add([pscustomobject]@{ Path = $p; SizeGB = $sizeGB })
    }
}

if ($found.Count -eq 0) {
    Write-Warn 'No candidate directories found to relocate. Try enabling switches like -IncludeTorchCaches, -IncludePipCache, -IncludeCondaPkgs.'
}

if ($found.Count -gt 0) {
    Write-Host "Found on C::" -ForegroundColor Gray
    $found | Sort-Object -Property SizeGB -Descending | ForEach-Object { "  {0}  |  {1} GB" -f $_.Path, $_.SizeGB }
}

# Move and link
$moved = New-Object System.Collections.Generic.List[pscustomobject]
foreach ($entry in $found | Sort-Object -Property SizeGB -Descending) {
    Move-And-Link -sourcePath $entry.Path -destRoot $DestinationRoot -movedList ([ref]$moved)
}

# Environment variables for future downloads
Write-Step 'Configuring environment variables (User scope)'
$envMap = @{
    'HF_HOME'            = $DestinationRoot
    'TRANSFORMERS_CACHE' = (Join-Path $DestinationRoot 'huggingface')
    'HF_HUB_CACHE'       = (Join-Path $DestinationRoot 'huggingface')
    'HF_DATASETS_CACHE'  = (Join-Path $DestinationRoot 'datasets')
}

foreach ($kv in $envMap.GetEnumerator()) {
    if ($DryRun) { Write-Info "Would set $($kv.Key) = $($kv.Value)" }
    else { [Environment]::SetEnvironmentVariable($kv.Key, $kv.Value, 'User') }
}

# Summary and freed space
Start-Sleep -Milliseconds 200
$driveCAfter = (Get-PSDrive -Name C).Free
$freeGBAfter = [math]::Round($driveCAfter / 1GB, 2)
$freedGB = [math]::Round(($driveCAfter - $driveCBefore) / 1GB, 2)

Write-Host "\n=== Summary ===" -ForegroundColor Magenta
if ($moved.Count -gt 0) {
    Write-Host 'Relocated and linked:' -ForegroundColor Gray
    $moved | ForEach-Object { "  {0} -> {1}" -f $_.Source, $_.Target }
} else {
    Write-Warn 'No directories were moved.'
}
Write-Host ("Free space on C:  before: {0} GB" -f $freeGBBefore)
Write-Host ("Free space on C:   after: {0} GB" -f $freeGBAfter)
Write-Host ("Space freed on C:: {0} GB" -f $freedGB) -ForegroundColor Green

Write-Host "\nNote: If any apps are running, restart them (or reboot) to ensure they pick up the new environment variables. If junction creation failed due to permissions, run this script in an elevated PowerShell." -ForegroundColor Yellow
