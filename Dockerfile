# ---- build stage: JS deps + headless chrome ---------------------------------
FROM node:20-bookworm-slim AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci --no-audit --no-fund
# Download Remotion's headless Chrome shell during build (image layer cache)
RUN npx remotion browser ensure || true

# ---- runtime stage ---------------------------------------------------------
FROM node:20-bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    ffmpeg \
    ca-certificates \
    curl \
    git \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Node deps (copied from build stage)
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /root/.cache/remotion /root/.cache/remotion
ENV PATH="/app/node_modules/.bin:${PATH}"

# Project
COPY package*.json ./
COPY remotion.config.ts ./
COPY tsconfig.json ./
COPY app.json ./
COPY src ./src
COPY public ./public
COPY server ./server
COPY scripts ./scripts
COPY requirements.txt ./

# Python deps
RUN python3 -m pip install --no-cache-dir --upgrade pip && \
    python3 -m pip install --no-cache-dir -r requirements.txt

RUN mkdir -p out .work public/scenes public/audio
ENV PORT=8080
EXPOSE 8080

# Cloud Run default; worker timeout near the 60 min platform cap
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-b", ":8080", \
     "-w", "1", "-t", "3540", "--graceful-timeout", "300", "server.main:app"]