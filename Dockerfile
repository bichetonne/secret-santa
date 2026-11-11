FROM oven/bun:1
COPY . .
EXPOSE 3000
CMD ["bun", "run", "index.html"]