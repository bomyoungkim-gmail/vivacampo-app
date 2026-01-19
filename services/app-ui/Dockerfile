FROM node:20-alpine AS base

# Install dependencies only when needed
FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN rm -f package-lock.json
RUN npm install --legacy-peer-deps

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app

# Accept build-time arguments for Next.js public variables
ARG NEXT_PUBLIC_API_BASE
ARG NEXT_PUBLIC_BASE_PATH
ARG NEXT_PUBLIC_ENABLE_MOCK_AUTH

# Set environment variables for build
ENV NEXT_PUBLIC_API_BASE=$NEXT_PUBLIC_API_BASE
ENV NEXT_PUBLIC_BASE_PATH=$NEXT_PUBLIC_BASE_PATH
ENV NEXT_PUBLIC_ENABLE_MOCK_AUTH=$NEXT_PUBLIC_ENABLE_MOCK_AUTH
ENV NEXT_TELEMETRY_DISABLED=1

COPY --from=deps /app/node_modules ./node_modules
COPY . .

RUN npm run build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000

CMD ["node", "server.js"]
