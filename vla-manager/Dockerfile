FROM node:23-slim AS build

ENV PNPM_HOME=/pnpm
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable

WORKDIR /app/
COPY . /app

RUN --mount=type=cache,id=pnpm,target=/pnpm/store pnpm install --frozen-lockfile
RUN pnpm run build


FROM nginx:1.27-alpine-slim
COPY --from=build /app/dist /usr/share/nginx/html
COPY --from=build /app/misc/nginx.conf.template /etc/nginx/templates/default.conf.template
EXPOSE 80
HEALTHCHECK --interval=5s --timeout=2s CMD nc -z 127.0.0.1 80
