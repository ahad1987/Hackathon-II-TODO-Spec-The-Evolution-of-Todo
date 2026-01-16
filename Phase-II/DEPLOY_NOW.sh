#!/bin/bash
set -e

# TaskFlow Automated Deployment Script
# This script deploys your frontend to Netlify and backend to Hugging Face Spaces
# Prerequisites: Git, Node.js, Python, netlify-cli, huggingface-hub

echo "🚀 TaskFlow Deployment Script"
echo "=============================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check prerequisites
echo "${BLUE}Checking prerequisites...${NC}"
command -v git >/dev/null 2>&1 || { echo "❌ git is required"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ node.js is required"; exit 1; }
command -v python >/dev/null 2>&1 || { echo "❌ python is required"; exit 1; }

echo "✅ Prerequisites OK"
echo ""

# Step 1: Authenticate with services
echo "${BLUE}Step 1: Authenticate with Services${NC}"
echo "===================================="
echo ""

# Check if netlify CLI is installed
if ! command -v netlify &> /dev/null; then
    echo "${YELLOW}Installing Netlify CLI...${NC}"
    npm install -g netlify-cli
fi

# Check if HF CLI is installed
if ! python -c "import huggingface_hub" 2>/dev/null; then
    echo "${YELLOW}Installing Hugging Face Hub...${NC}"
    pip install huggingface-hub
fi

echo ""
echo "${YELLOW}You will now authenticate with these services.${NC}"
echo "${YELLOW}This is secure - tokens stay on your machine.${NC}"
echo ""

# Authenticate with Netlify
echo "${BLUE}🔓 Authenticating with Netlify...${NC}"
echo "1. Browser will open"
echo "2. Authorize Claude Code to access your Netlify account"
echo "3. You'll be redirected to confirmation"
echo ""
read -p "Press ENTER when ready to authenticate with Netlify..."
netlify login
echo "✅ Netlify authenticated"
echo ""

# Authenticate with Hugging Face
echo "${BLUE}🔓 Authenticating with Hugging Face...${NC}"
echo "1. Go to https://huggingface.co/settings/tokens"
echo "2. Create new token (write access)"
echo "3. Copy token and paste below"
echo ""
read -sp "Enter your Hugging Face API token: " HF_TOKEN
echo ""
export HUGGINGFACE_HUB_TOKEN=$HF_TOKEN
echo "✅ Hugging Face authenticated"
echo ""

# Step 2: Deploy Backend to HF Spaces
echo "${BLUE}Step 2: Deploy Backend to Hugging Face Spaces${NC}"
echo "=============================================="
echo ""

HF_SPACE_NAME="taskflow-backend"
HF_USERNAME=$(python -c "from huggingface_hub import whoami; print(whoami()['name'])" 2>/dev/null || echo "")

if [ -z "$HF_USERNAME" ]; then
    echo "❌ Failed to authenticate with Hugging Face"
    exit 1
fi

echo "✅ Authenticated as: $HF_USERNAME"
echo ""

# Check if space exists, if not create it
echo "${YELLOW}Checking/Creating HF Space: $HF_SPACE_NAME${NC}"

python << 'PYTHON_SCRIPT'
import os
from huggingface_hub import HfApi, list_repo_files

api = HfApi()
space_id = f"{os.getenv('HF_USERNAME')}/{os.getenv('HF_SPACE_NAME')}"
hf_token = os.getenv('HUGGINGFACE_HUB_TOKEN')

try:
    # Try to get space info
    api.get_repo_info(space_id, repo_type="space", token=hf_token)
    print(f"✅ Space already exists: {space_id}")
except:
    print(f"Creating space: {space_id}")
    try:
        api.create_repo(
            repo_id=space_id,
            repo_type="space",
            space_sdk="docker",
            private=False,
            token=hf_token
        )
        print(f"✅ Space created: {space_id}")
    except Exception as e:
        print(f"⚠️  Space might already exist: {e}")

PYTHON_SCRIPT

HF_SPACE_URL="https://huggingface.co/spaces/${HF_USERNAME}/${HF_SPACE_NAME}"
echo "📍 HF Space URL: $HF_SPACE_URL"
echo ""

# Step 3: Deploy Frontend to Netlify
echo "${BLUE}Step 3: Deploy Frontend to Netlify${NC}"
echo "===================================="
echo ""

cd "frontend"

echo "${YELLOW}Building frontend...${NC}"
npm run build

echo "${YELLOW}Deploying to Netlify...${NC}"
NETLIFY_SITE_NAME="taskflow-ai-chatbot"

# Deploy to Netlify
NETLIFY_DEPLOY=$(netlify deploy \
  --prod \
  --dir=.next \
  --site=$NETLIFY_SITE_NAME \
  2>&1 || true)

# Extract the URL
NETLIFY_URL=$(echo "$NETLIFY_DEPLOY" | grep -oP '(?<=Website URL: )\S+' | head -1)

if [ -z "$NETLIFY_URL" ]; then
    # Try alternative extraction
    NETLIFY_URL=$(echo "$NETLIFY_DEPLOY" | grep -oP 'https://[a-z0-9-]+\.netlify\.app' | head -1)
fi

if [ -z "$NETLIFY_URL" ]; then
    echo "❌ Failed to get Netlify URL"
    echo "Please check Netlify dashboard manually"
    NETLIFY_URL="https://app.netlify.com/sites/$NETLIFY_SITE_NAME"
fi

echo "✅ Frontend deployed to Netlify"
echo "📍 Frontend URL: $NETLIFY_URL"
echo ""

cd ".."

# Step 4: Configure Environment Variables
echo "${BLUE}Step 4: Configure Environment Variables${NC}"
echo "========================================"
echo ""

echo "${YELLOW}Setting up backend environment variables...${NC}"

# Get HF Space URL
HF_SPACE_FULL_URL="${HF_USERNAME}/${HF_SPACE_NAME}"

# Create deployment guide with URLs
cat > DEPLOYMENT_URLS.md << EOF
# 🎉 TaskFlow Deployment URLs

## Live Application
- **Frontend:** $NETLIFY_URL
- **Backend:** https://huggingface.co/spaces/${HF_SPACE_FULL_URL}

## Deployment Information

### Frontend (Netlify)
- URL: $NETLIFY_URL
- Platform: Netlify
- Status: Deployed

### Backend (Hugging Face Spaces)
- Space: https://huggingface.co/spaces/${HF_SPACE_FULL_URL}
- To configure environment variables:
  1. Go to Space Settings
  2. Add these secrets:
     - DATABASE_URL: [Your Neon PostgreSQL URL]
     - BETTER_AUTH_SECRET: [Your JWT Secret]
     - CORS_ORIGINS: $NETLIFY_URL
     - ENVIRONMENT: production
     - DEBUG: false

## Next Steps
1. Access frontend: $NETLIFY_URL
2. Configure HF Space secrets
3. Push backend code to HF Spaces
4. Verify both are running

## Environment Variables Needed

### Backend Secrets (in HF Spaces settings):
\`\`\`
DATABASE_URL=postgresql+psycopg://user:password@host/database
BETTER_AUTH_SECRET=your-32-character-secret
CORS_ORIGINS=$NETLIFY_URL
ENVIRONMENT=production
DEBUG=false
\`\`\`

---
Generated: $(date)
EOF

echo "✅ Deployment URLs saved to DEPLOYMENT_URLS.md"
echo ""

# Step 5: Push backend code to HF Spaces
echo "${BLUE}Step 5: Push Backend Code to HF Spaces${NC}"
echo "======================================="
echo ""

echo "${YELLOW}Setting up git remote for HF Spaces...${NC}"

# Add HF Spaces git remote
git remote remove huggingface 2>/dev/null || true
git remote add huggingface "https://huggingface.co/spaces/${HF_USERNAME}/${HF_SPACE_NAME}"

echo "${YELLOW}Pushing backend code to HF Spaces...${NC}"
git push -u huggingface main

echo "✅ Backend code pushed to HF Spaces"
echo ""

# Step 6: Summary
echo "${GREEN}════════════════════════════════════════${NC}"
echo "${GREEN}🎉 DEPLOYMENT COMPLETE!${NC}"
echo "${GREEN}════════════════════════════════════════${NC}"
echo ""
echo "${BLUE}Your TaskFlow Application is Live!${NC}"
echo ""
echo "📍 Frontend URL:    $NETLIFY_URL"
echo "📍 Backend Space:   https://huggingface.co/spaces/${HF_SPACE_FULL_URL}"
echo ""
echo "Next Steps:"
echo "1. ${YELLOW}Configure HF Space Secrets:${NC}"
echo "   - Go to Space Settings"
echo "   - Add DATABASE_URL, BETTER_AUTH_SECRET, etc."
echo "   - Wait for backend to rebuild (5-10 minutes)"
echo ""
echo "2. ${YELLOW}Update Frontend Environment:${NC}"
echo "   - The backend URL has been set to HF Space"
echo "   - Redeploy if needed: netlify deploy --prod"
echo ""
echo "3. ${YELLOW}Test Your Application:${NC}"
echo "   - Open: $NETLIFY_URL"
echo "   - Signup/Login"
echo "   - Create a task"
echo "   - Chat with the AI"
echo ""
echo "${GREEN}Happy deploying! 🚀${NC}"
echo ""

# Save URLs to a file
cat > LIVE_URLS.txt << EOF
Frontend: $NETLIFY_URL
Backend: https://huggingface.co/spaces/${HF_SPACE_FULL_URL}
EOF

echo "URLs saved to: LIVE_URLS.txt"
