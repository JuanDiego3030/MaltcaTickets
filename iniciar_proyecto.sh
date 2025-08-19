#!/bin/bash
# Script para iniciar el proyecto Django y configurar el webhook de Telegram con ngrok

# Variables
PORT=7000
NGROK_AUTH_TOKEN="" # Opcional: tu token de ngrok si lo tienes
TELEGRAM_BOT_TOKEN="8173472907:AAHXGiKOv-FYRhDlnmiXWVo6_JaPQeCqt58"
WEBHOOK_PATH="/bot/"

# 1. Activar entorno virtual si existe
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "Entorno virtual activado."
else
    echo "No se encontró entorno virtual (venv)."
fi

# 2. Iniciar el servidor Django en segundo plano
nohup python manage.py runserver 0.0.0.0:$PORT > django.log 2>&1 &
DJANGO_PID=$!
echo "Servidor Django iniciado en el puerto $PORT (PID $DJANGO_PID)"

# 3. Iniciar ngrok en segundo plano
if [ -n "$NGROK_AUTH_TOKEN" ]; then
    ngrok config add-authtoken $NGROK_AUTH_TOKEN
fi
nohup ngrok http $PORT > ngrok.log 2>&1 &
NGROK_PID=$!
echo "ngrok iniciado (PID $NGROK_PID)"

# 4. Esperar a que ngrok esté listo y obtener la URL pública
sleep 5
NGROK_URL=$(curl --silent http://localhost:4040/api/tunnels | grep -o '"public_url":"https:[^"]*' | sed 's/"public_url":"//;s/"//')

if [ -z "$NGROK_URL" ]; then
    echo "No se pudo obtener la URL pública de ngrok."
    exit 1
fi

WEBHOOK_URL="${NGROK_URL}${WEBHOOK_PATH}"
echo "URL pública de ngrok: $WEBHOOK_URL"

# 5. Configurar el webhook de Telegram
curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" -d "url=${WEBHOOK_URL}"
echo "Webhook configurado en Telegram."

echo "Listo. Puedes ver logs en django.log y ngrok.log."

# pkill -f "manage.py runserver"

# pkill -f "ngrok http"