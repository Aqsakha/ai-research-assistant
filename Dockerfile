# Use Node.js base image for frontend build
FROM node:18-alpine AS frontend-build
WORKDIR /app/frontend

# Install dependencies
COPY frontend/package*.json ./
RUN npm install

# Copy frontend source and build
COPY frontend/ .
RUN npm run build

# Use Python base image for runtime
FROM python:3.11-slim
WORKDIR /app

# Install nginx and curl for debugging
RUN apt-get update && apt-get install -y nginx curl && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./backend/

# Copy built frontend to nginx directory
COPY --from=frontend-build /app/frontend/dist/ai-research-assistant-frontend /usr/share/nginx/html

# Remove default nginx configuration and copy our custom config
RUN rm -f /etc/nginx/sites-enabled/default /etc/nginx/conf.d/default.conf
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Create startup script with comprehensive debugging
RUN echo '#!/bin/bash\n\
set -e\n\
echo "=== Starting CerebroGPT Services ==="\n\
export LISTEN_PORT=${PORT:-10000}\n\
echo "Render PORT is: $PORT"\n\
echo "Nginx will listen on: $LISTEN_PORT"\n\
echo "Flask will run on: 5000"\n\
echo "Current directory: $(pwd)"\n\
echo "Contents of /usr/share/nginx/html:"\n\
ls -la /usr/share/nginx/html\n\
echo "Checking if index.html exists:"\n\
if [ -f /usr/share/nginx/html/index.html ]; then\n\
    echo "✅ index.html found:"\n\
    ls -la /usr/share/nginx/html/index.html\n\
    echo "First 5 lines of index.html:"\n\
    head -5 /usr/share/nginx/html/index.html\n\
else\n\
    echo "❌ index.html NOT FOUND in /usr/share/nginx/html"\n\
fi\n\
echo "Templating nginx listen port..."\n\
sed -i "s/LISTEN_PORT/$LISTEN_PORT/g" /etc/nginx/conf.d/default.conf\n\
echo "Nginx configuration:"\n\
cat /etc/nginx/conf.d/default.conf\n\
echo "Testing nginx configuration..."\n\
nginx -t && echo "Nginx config is valid"\n\
echo "Starting nginx..."\n\
nginx -g "daemon off;" &\n\
NGINX_PID=$!\n\
echo "Nginx started with PID: $NGINX_PID"\n\
sleep 2\n\
echo "Testing nginx is responding on $LISTEN_PORT:"\n\
curl -I http://localhost:$LISTEN_PORT/ || echo "Nginx not responding on port $LISTEN_PORT"\n\
echo "Starting Flask backend on port 5000..."\n\
cd /app/backend\n\
PORT=5000 python app.py &\n\
FLASK_PID=$!\n\
echo "Flask started with PID: $FLASK_PID"\n\
echo "=== All services started ==="\n\
wait' > /start.sh && chmod +x /start.sh

EXPOSE 10000
CMD ["/start.sh"]
