# AutoPublisher

Herramienta de gestión personal de publicaciones para comunidades de Telegram
a las que el usuario ya pertenece. Publicación **siempre manual, comunidad por
comunidad** — no incluye ni incluirá un disparador de envío masivo automático.

## Requisitos previos

1. **Bot de Telegram**: crear con [@BotFather](https://t.me/BotFather) → `/newbot`, guardar el `BOT_TOKEN`.
2. **API de Telegram (para leer comunidades del usuario)**: registrar app en https://my.telegram.org → obtener `TELEGRAM_API_ID` y `TELEGRAM_API_HASH`.
3. **Base de datos**: crear proyecto gratis en https://neon.tech, copiar el connection string y cambiar `postgresql://` por `postgresql+asyncpg://`.
4. **Mini App**: en BotFather, `/newapp`, vincular la URL del frontend desplegado.

## Desarrollo local

Backend:
```bash
cd autopublisher
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # completar valores reales
uvicorn app.main:app --reload
```

Frontend:
```bash
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env
npm run dev
```

## Despliegue en Render

1. Push del repo a GitHub.
2. En Render, "New" → "Blueprint" → seleccionar el repo (usa `render.yaml`).
3. Completar las variables marcadas `sync: false` en el dashboard de Render:
   `DATABASE_URL`, `BOT_TOKEN`, `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`.
4. En el servicio `autopublisher-miniapp`, agregar `VITE_API_URL` apuntando
   a la URL pública del servicio `autopublisher-api`.
5. En BotFather, vincular `/newapp` con la URL del servicio `autopublisher-miniapp`.

## Límites de diseño (intencionales)

- No hay envío masivo automático ni scheduler que publique sin intervención.
- Cada publicación en una comunidad requiere un click explícito del usuario
  (`POST /campaigns/{id}/execute-one`), con rate limit anti-abuso
  (`MAX_POSTS_PER_HOUR`, default 20/hora).
- Solo se gestionan comunidades a las que el usuario ya pertenece (se leen
  vía su propia sesión de Telegram, nunca se buscan comunidades externas).
"# autopublisher" 
