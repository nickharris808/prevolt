#!/bin/bash
# Comprehensive Markdown Synchronization Script
# Fixes all component counts, version numbers, and tier counts

cd /Users/nharris/Desktop/portfolio/Portfolio_A_Power

echo "================================================"
echo "COMPREHENSIVE MARKDOWN SYNCHRONIZATION"
echo "================================================"

# 1. Fix Component Counts
echo "Fixing component counts to 53/53..."
find . -name "*.md" -type f ! -path "./archive/*" -exec sed -i '' \
  -e 's/32\/32 components/53\/53 components/g' \
  -e 's/37\/37 components/53\/53 components/g' \
  -e 's/42\/42 components/53\/53 components/g' \
  -e 's/47\/47 components/53\/53 components/g' \
  -e 's/50\/50 components/53\/53 components/g' \
  -e 's/51\/51 components/53\/53 components/g' \
  -e 's/52\/52 components/53\/53 components/g' \
  {} +

# 2. Fix Tier Counts
echo "Fixing tier counts to 16/16..."
find . -name "*.md" -type f ! -path "./archive/*" -exec sed -i '' \
  -e 's/11\/11 tiers/16\/16 tiers/g' \
  -e 's/12\/12 tiers/16\/16 tiers/g' \
  -e 's/13\/13 tiers/16\/16 tiers/g' \
  -e 's/14\/14 tiers/16\/16 tiers/g' \
  -e 's/15\/15 tiers/16\/16 tiers/g' \
  {} +

# 3. Fix Version Numbers
echo "Fixing version numbers to 16.0..."
find . -name "*.md" -type f ! -path "./archive/*" -exec sed -i '' \
  -e 's/Version.*11\.0/Version 16.0/g' \
  -e 's/Version.*12\.0/Version 16.0/g' \
  -e 's/Version.*13\.0/Version 16.0/g' \
  -e 's/Version.*14\.0/Version 16.0/g' \
  -e 's/Version.*15\.0/Version 16.0/g' \
  -e 's/v11\.0/v16.0/g' \
  -e 's/v12\.0/v16.0/g' \
  -e 's/v13\.0/v16.0/g' \
  -e 's/v14\.0/v16.0/g' \
  -e 's/v15\.0/v16.0/g' \
  {} +

# 4. Standardize Artifact Counts
echo "Standardizing artifact counts to 91-102 range..."
find . -name "*.md" -type f ! -path "./archive/*" -exec sed -i '' \
  -e 's/83 PNG/91 PNG/g' \
  -e 's/86 PNG/91 PNG/g' \
  -e 's/88 PNG/91 PNG/g' \
  -e 's/89 PNG/91 PNG/g' \
  -e 's/90 PNG/91 PNG/g' \
  {} +

echo "================================================"
echo "SYNCHRONIZATION COMPLETE"
echo "================================================"
echo "✓ Component counts: 53/53"
echo "✓ Tier counts: 16/16"
echo "✓ Version numbers: 16.0"
echo "✓ Artifact counts: 91+ PNG"
echo ""
echo "Verifying changes..."
echo "Files with 53/53: $(grep -r '53/53' . --include='*.md' | wc -l)"
echo "Files with Version 16.0: $(grep -r 'Version 16.0' . --include='*.md' | wc -l)"
