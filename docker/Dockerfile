# Imagem base oficial do Evolution API
FROM atendai/evolution-api:latest

# Define a porta
ENV SERVER_PORT=8080

# Desativa o uso de banco e migrações
ENV DATABASE_ENABLED=false
ENV PRISMA_ENABLED=false
ENV DISABLE_PRISMA_MIGRATE=true
ENV DATABASE_PROVIDER=postgresql
ENV DATABASE_URL=postgresql://user:password@localhost:5432/fake
ENV CACHE_LOCAL_ENABLED=true
ENV CACHE_REDIS_ENABLED=false
ENV S3_ENABLED=false
ENV LANGUAGE=pt
ENV LOG_LEVEL=INFO

# Copia o .env para o container
COPY .env .env

# Comando de inicialização: pula o prisma e roda direto o servidor
CMD ["sh", "-c", "echo '🚀 Iniciando Evolution API (modo sem banco)...' && node dist/main.js"]
