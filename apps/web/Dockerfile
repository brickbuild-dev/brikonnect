FROM node:22-alpine

WORKDIR /repo

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web/package.json apps/web/package.json

RUN corepack enable && pnpm install --frozen-lockfile --filter web...

COPY apps/web apps/web

WORKDIR /repo/apps/web
RUN pnpm build

EXPOSE 3000
CMD ["pnpm", "preview", "--host", "0.0.0.0", "--port", "3000"]
