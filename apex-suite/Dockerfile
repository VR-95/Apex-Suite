# ─────────────────────────────────────────────────────────────────────────────
#  APEX SUITE  ·  Docker build for Render
#  Stage 1: build the React frontend (Node) — stage 2 never needs Node at all,
#  it just copies in the already-built dist/ folder. Keeps the final image
#  small and avoids any ambiguity about whether Render's runtime has Node.
# ─────────────────────────────────────────────────────────────────────────────

FROM node:20-slim AS frontend-build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY index.html vite.config.js ./
COPY src ./src
RUN npm run build

FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend ./backend
COPY --from=frontend-build /app/dist ./dist

EXPOSE 8000
CMD ["python", "backend/main.py"]
