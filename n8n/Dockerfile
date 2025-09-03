# --- n8n-only/Dockerfile ---
FROM docker.n8n.io/n8nio/n8n:latest
 
# Optional defaults (override at runtime)
ENV GENERIC_TIMEZONE=Asia/Kolkata \
    N8N_PORT=5678
 
# Persist n8n credentials/workflows
VOLUME ["/home/node/.n8n"]
 
EXPOSE 5678
 
# # Healthcheck using built-in Node (no curl/nc needed)
# HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=5 \
#   CMD node -e "const http=require('http');const p=process.env.N8N_PORT||5678;const r=http.request({host:'127.0.0.1',port:p,path:'/'},()=>process.exit(0));r.on('error',()=>process.exit(1));r.end();"
 
# Start n8n (the base image would do this anyway—explicit for clarity)
CMD ["n8n"]