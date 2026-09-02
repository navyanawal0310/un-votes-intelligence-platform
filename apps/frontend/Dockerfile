FROM node:20-alpine AS build

WORKDIR /app

COPY apps/frontend/package*.json ./apps/frontend/
RUN cd /app/apps/frontend && npm ci

COPY apps/frontend ./apps/frontend

ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

RUN cd /app/apps/frontend && npm run build

FROM nginx:1.27-alpine

COPY apps/frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/apps/frontend/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
