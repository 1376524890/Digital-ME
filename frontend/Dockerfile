FROM node:24-alpine

WORKDIR /app

# Clear proxy
ENV HTTP_PROXY=""
ENV HTTPS_PROXY=""
ENV http_proxy=""
ENV https_proxy=""

COPY package.json ./
RUN corepack enable && pnpm install --no-frozen-lockfile

COPY tsconfig.json next.config.ts postcss.config.mjs tailwind.config.ts ./
COPY src/ ./src/

EXPOSE 3000
CMD ["pnpm", "dev"]
