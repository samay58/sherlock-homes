# ---- SvelteKit frontend image ----
FROM node:20 AS frontend

WORKDIR /app

COPY package.json yarn.lock ./
RUN rm -rf node_modules && yarn install --frozen-lockfile && rm -rf node_modules/.vite

COPY . .

EXPOSE 5173
CMD ["yarn", "dev", "--host", "0.0.0.0"] 