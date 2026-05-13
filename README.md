# Lunch Microcentro

App de gestión completa para emprendimiento de viandas: pedidos, recetario con rendimientos, costos, packaging, gastos, clientes.

## Stack

- **Streamlit** (UI)
- **SQLite** local en dev / **Turso** (SQLite serverless) en producción
- **Pandas** para manejo de datos

## Variables de entorno

Para usar Turso (cloud), definir:

```
TURSO_DATABASE_URL=libsql://...
TURSO_AUTH_TOKEN=...
```

Si no están definidas, usa SQLite local en `data/lunch.db`.

En Streamlit Cloud, estas se configuran en **Settings → Secrets** con formato TOML:

```toml
TURSO_DATABASE_URL = "libsql://..."
TURSO_AUTH_TOKEN = "..."
```

## Desarrollo local

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Deploy en Streamlit Cloud

1. Push del repo a GitHub
2. En streamlit.io: New app → seleccionar repo → main branch → `app.py`
3. Settings → Secrets → pegar credenciales de Turso
4. Deploy
