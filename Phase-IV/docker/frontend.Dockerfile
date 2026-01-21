# Frontend Dockerfile for TaskFlow AI Chatbot
# Base Image: node:18-alpine (lightweight for Next.js)
# Build Strategy: Multi-stage (dependencies → builder → runner)
# Constitutional Compliance: NO application code modifications

# Stage 1: Dependencies
# Install all dependencies (production + development)
FROM node:18-alpine AS deps

WORKDIR /app

# Copy package files for dependency installation
COPY package.json package-lock.json* ./

# Install dependencies with clean install for reproducibility
RUN npm install

# Stage 2: Builder
# Build the Next.js application
FROM node:18-alpine AS builder

WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy application code AS-IS (IMMUTABLE per Constitution)
COPY . .

# Build Next.js application
# Standalone mode is already enabled in next.config.js (output: 'standalone')
# This creates an optimized production build
RUN npm run build

# Stage 3: Runner
# Production runtime with minimal footprint
FROM node:18-alpine AS runner

WORKDIR /app

# Set production environment
ENV NODE_ENV=production

# Create non-root user for security
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy standalone output from builder
# Next.js standalone mode creates self-contained server
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
#COPY --from=builder /app/public ./public

# Change ownership to non-root user
RUN chown -R nextjs:nodejs /app

# Switch to non-root user
USER nextjs

# Expose port 3000 (IMMUTABLE per api-contracts.md)
EXPOSE 3000

# Health check (optional but recommended)
# Checks root endpoint every 30s
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

# Run Next.js standalone server
# The standalone build includes a minimal server.js
CMD ["node", "server.js"]
