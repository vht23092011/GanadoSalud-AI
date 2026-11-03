# Manual de despliegue — Docker y nube

**Versión:** 1.0 · **Estado:** estrategia documentada, despliegue público pendiente de ejecutar.

## Requisitos
Docker con Compose v2, Git, cuenta GitHub y cuenta de proveedor de nube. La plataforma debe admitir Docker y una comunicación privada entre frontend y backend o un servicio de proxy equivalente. Los servicios gratuitos y límites cambian; verificar tarifas antes de crear recursos.

## A. Construcción y ejecución local
1. Instalar Docker Desktop y abrirlo.
2. Descomprimir el proyecto y abrirlo en VS Code.
3. Desde la carpeta raíz ejecutar `docker compose build`.
4. Comprobar imágenes con `docker images`.
5. Ejecutar `docker compose up -d`.
6. Verificar `docker compose ps` y `docker compose logs backend`.
7. Abrir `http://localhost:3000` y enviar un formulario.
8. Abrir `http://localhost:8000/docs` y probar `POST /predict`.
9. Detener con `docker compose down`.

## B. Subir a GitHub
Crear un repositorio vacío en github.com (sin README inicial) y ejecutar desde la raíz:
```bash
git init
git add .
git commit -m "DairyHealth AI: API, frontend, Docker y documentación"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/dairyhealth-ai.git
git push -u origin main
```
Nunca subir tokens, contraseñas o `.env` con secretos.

## C. Estrategia de nube: VM Linux con Docker Compose
Es la opción más directa para conservar la arquitectura de dos contenedores; puede generar costos.
1. Crear VM Linux con Docker Engine + plugin Compose, acceso SSH y reglas de firewall.
2. Permitir HTTPS 443 y HTTP 80 al público; limitar SSH a IP autorizada. No exponer el backend 8000 públicamente.
3. Clonar el repositorio en la VM: `git clone URL_DEL_REPOSITORIO`.
4. Configurar un proxy HTTPS externo (por ejemplo, Caddy) con dominio y certificado válido; adaptar el puerto del frontend a un puerto local accesible solo por el proxy.
5. Quitar `ports: 8000:8000` del backend en producción; Nginx continuará accediendo al servicio por red interna.
6. Ejecutar `docker compose up --build -d`.
7. Probar dominio HTTPS, formulario, API a través de `/api/health` y revisar logs.
8. Para actualizar: `git pull && docker compose up --build -d`; verificar salud y disponer de un tag anterior para reversión.

## D. Alternativa PaaS
Para plataformas que despliegan contenedores independientes, publicar las dos imágenes en un registry y desplegar backend y frontend con conectividad privada. **Atención:** `frontend/nginx.conf` supone que el backend se resuelve como `backend` por DNS; en PaaS debe reemplazarse por el nombre DNS interno real del servicio o ajustar el enrutamiento. No asumir que Docker Compose funciona directamente en cualquier PaaS.

## Evidencia que debe capturarse
Terminal de `docker compose build`, `docker images`, `docker compose ps`, `/docs`, formulario con predicción, prueba negativa HTTP 422, `pytest`, repositorio GitHub y URL pública si se realiza despliegue real.
