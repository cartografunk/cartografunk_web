param(
  [string]$SourceBranch = "main",
  [string]$ProductionBranch = "production"
)

$ErrorActionPreference = "Stop"

$status = git status --porcelain
if ($status) {
  Write-Error "Working tree is not clean. Commit or stash changes before promoting to production."
}

$currentBranch = git branch --show-current

git fetch origin
git checkout $SourceBranch
git pull --ff-only origin $SourceBranch
git checkout $ProductionBranch
git pull --ff-only origin $ProductionBranch
git merge --ff-only $SourceBranch
git push origin $ProductionBranch
git checkout $currentBranch

Write-Host "Promoted $SourceBranch to $ProductionBranch. Cloudflare Pages should deploy production from $ProductionBranch."
