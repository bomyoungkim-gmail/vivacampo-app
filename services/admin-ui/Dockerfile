FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN rm -f package-lock.json
RUN npm install

FROM deps AS builder
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV production

COPY --from=builder /app/next.config.js ./
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3001
ENV PORT 3001
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]
