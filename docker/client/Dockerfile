FROM node:20-alpine AS builder

ARG VITE_API_BASE_URL=http://server:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

ARG VITE_PUBLIC_API_URL=http://localhost:8000
ENV VITE_PUBLIC_API_URL=$VITE_PUBLIC_API_URL

WORKDIR /app
COPY apps/client/package*.json ./
RUN npm ci
COPY apps/client/ .
RUN npm run build

# ---

FROM node:20-alpine

WORKDIR /app
COPY --from=builder /app/package*.json ./
RUN npm ci --omit=dev
COPY --from=builder /app/build ./build

EXPOSE 3000
CMD ["npm", "start"]
