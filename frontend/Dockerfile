FROM node:24-alpine

WORKDIR /app

COPY package.json pnpm-lock.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile

COPY tsconfig.json next.config.ts postcss.config.mjs tailwind.config.ts ./
COPY src/ ./src/

EXPOSE 3000
CMD ["pnpm", "dev"]
