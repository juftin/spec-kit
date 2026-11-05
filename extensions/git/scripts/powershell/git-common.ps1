#!/usr/bin/env pwsh
# Git-specific common functions for the git extension.
# Extracted from scripts/powershell/common.ps1 -- contains only git-specific
# branch validation and detection logic.

function Test-HasGit {
    param([string]$RepoRoot = (Get-Location))
    try {
        if (-not (Test-Path (Join-Path $RepoRoot '.git'))) { return $false }
        if (-not (Get-Command git -ErrorAction SilentlyContinue)) { return $false }
        git -C $RepoRoot rev-parse --is-inside-work-tree 2>$null | Out-Null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

function Get-SpecKitEffectiveBranchName {
    param([string]$Branch)
    if ($Branch -match '^([^/]+)/([^/]+)$') {
        return $Matches[2]
    }
    return $Branch
}

function Test-FeatureBranch {
    param(
        [string]$Branch,
        [bool]$HasGit = $true
    )

    # For non-git repos, we can't enforce branch naming but still provide output
    if (-not $HasGit) {
        Write-Warning "[specify] Warning: Git repository not detected; skipped branch validation"
        return $true
    }

    $raw = $Branch
    $Branch = Get-SpecKitEffectiveBranchName $raw
    $featureSegment = ($Branch -split '/')[-1]

    # Accept sequential prefix (3+ digits), at the start or after namespace
    # segments, but exclude malformed timestamps.
    $hasMalformedTimestamp = ($featureSegment -match '^[0-9]{7}-[0-9]{6}-') -or ($featureSegment -match '^(?:\d{7}|\d{8})-\d{6}$')
    $isSequential = ($featureSegment -match '^[0-9]{3,}-') -and (-not $hasMalformedTimestamp)
    if (-not $isSequential -and $featureSegment -notmatch '^\d{8}-\d{6}-') {
        [Console]::Error.WriteLine("ERROR: Not on a feature branch. Current branch: $raw")
        [Console]::Error.WriteLine("Feature branches should be named like: 001-feature-name, 1234-feature-name, 20260319-143022-feature-name, or <prefix>/001-feature-name")
        return $false
    }
    return $true
}


function Resolve-SpecifyInitDir {
    param([switch]$ReturnNullOnError)

    $initDir = $env:SPECIFY_INIT_DIR
    # Normalize: relative paths resolve against the current directory.
    if (-not [System.IO.Path]::IsPathRooted($initDir)) {
        $initDir = Join-Path (Get-Location).Path $initDir
    }
    $resolved = Resolve-Path -LiteralPath $initDir -ErrorAction SilentlyContinue
    # Resolve-Path also succeeds for files, so check the resolved path is a
    # directory; otherwise a file value would slip through to the less accurate
    # "not a Spec Kit project" error below.
    if (-not $resolved -or -not (Test-Path -LiteralPath $resolved.Path -PathType Container)) {
        [Console]::Error.WriteLine("ERROR: SPECIFY_INIT_DIR does not point to an existing directory: $($env:SPECIFY_INIT_DIR)")
        if ($ReturnNullOnError) { return $null }
        exit 1
    }
    # Resolve-Path echoes back any trailing separator from the input; trim it so
    # the returned root matches the bash resolver, whose `cd && pwd` never yields
    # one. TrimEnd (not [Path]::TrimEndingDirectorySeparator, which is .NET Core
    # only) keeps this working on Windows PowerShell 5.1 / .NET Framework, as
    # Get-FeaturePathsEnv already does below. Unlike a bare TrimEnd, the
    # GetPathRoot check preserves a path that *is* its own root ('C:\' must not
    # become 'C:', which every later API re-resolves against the current
    # directory instead of the drive root). No-op on a path with no trailing
    # separator.
    $initRoot = $resolved.Path.TrimEnd('/', '\')
    if ($initRoot.Length -lt [System.IO.Path]::GetPathRoot($resolved.Path).Length) {
        $initRoot = $resolved.Path
    }
    if (-not (Test-Path -LiteralPath (Join-Path $initRoot '.specify') -PathType Container)) {
        [Console]::Error.WriteLine("ERROR: SPECIFY_INIT_DIR is not a Spec Kit project (no .specify/ directory): $initRoot")
        if ($ReturnNullOnError) { return $null }
        exit 1
    }
    return $initRoot
}

function Get-RepoRoot {
    if ($env:SPECIFY_INIT_DIR) { return Resolve-SpecifyInitDir }
    $current = (Get-Location).Path
    while ($current) {
        if (Test-Path -LiteralPath (Join-Path $current '.specify') -PathType Container) {
            return $current
        }
        $parent = Split-Path -Parent $current
        if ($parent -eq $current) { break }
        $current = $parent
    }
    return git rev-parse --show-toplevel
}
