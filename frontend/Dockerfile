# Dev image
FROM node:20-alpine

WORKDIR /app

# Speed up installs and keep cache
ENV CI=true

# Install deps first (better layer caching)
COPY package.json package-lock.json* ./
RUN npm ci || npm install

RUN npm install \
    react-markdown remark-gfm rehype-raw rehype-sanitize react-syntax-highlighter \
    remark-math rehype-katex katex

# Bring in the rest
COPY . .

# Expose Vite dev server
EXPOSE 5173

CMD ["npm","run","dev","--","--host","0.0.0.0"]
