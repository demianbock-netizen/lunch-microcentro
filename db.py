"""Capa de base de datos. Soporta SQLite local (dev) y Turso (cloud).

Si las variables TURSO_DATABASE_URL y TURSO_AUTH_TOKEN están presentes,
usa la API HTTP de Turso (sin libs nativas). Si no, usa SQLite local.
"""
import os
import sqlite3
from pathlib import Path
from contextlib import contextmanager

import requests

DB_PATH = Path(__file__).parent / "data" / "lunch.db"

# Detectar entorno
TURSO_URL = os.getenv("TURSO_DATABASE_URL", "").strip()
TURSO_TOKEN = os.getenv("TURSO_AUTH_TOKEN", "").strip()

# Permitir cargar desde Streamlit secrets
try:
    import streamlit as st  # type: ignore
    if hasattr(st, "secrets"):
        try:
            TURSO_URL = (st.secrets.get("TURSO_DATABASE_URL", "") or TURSO_URL).strip()
            TURSO_TOKEN = (st.secrets.get("TURSO_AUTH_TOKEN", "") or TURSO_TOKEN).strip()
        except Exception:
            pass
except ImportError:
    pass

USE_TURSO = bool(TURSO_URL and TURSO_TOKEN)


def _turso_http_url(url: str) -> str:
    """Convierte libsql://host a https://host/v2/pipeline."""
    if url.startswith("libsql://"):
        url = "https://" + url[len("libsql://"):]
    return url.rstrip("/") + "/v2/pipeline"


def _to_arg(v):
    """Convierte un valor Python al formato de arg HTTP de Turso."""
    if v is None:
        return {"type": "null", "value": None}
    if isinstance(v, bool):
        return {"type": "integer", "value": "1" if v else "0"}
    if isinstance(v, int):
        return {"type": "integer", "value": str(v)}
    if isinstance(v, float):
        return {"type": "float", "value": v}
    if isinstance(v, (bytes, bytearray)):
        import base64
        return {"type": "blob", "base64": base64.b64encode(v).decode()}
    return {"type": "text", "value": str(v)}


def _from_cell(cell):
    """Convierte una celda de respuesta Turso a Python."""
    if cell is None:
        return None
    t = cell.get("type")
    v = cell.get("value")
    if t == "null":
        return None
    if t == "integer":
        try:
            return int(v)
        except (TypeError, ValueError):
            return v
    if t == "float":
        try:
            return float(v)
        except (TypeError, ValueError):
            return v
    return v


class _TursoCursor:
    def __init__(self, cols, rows):
        self._cols = cols
        self._rows = rows
        self._idx = 0

    @property
    def description(self):
        return [(c, None, None, None, None, None, None) for c in self._cols]

    def _wrap(self, row):
        if row is None:
            return None
        return dict(zip(self._cols, row))

    def fetchone(self):
        if self._idx >= len(self._rows):
            return None
        row = self._rows[self._idx]
        self._idx += 1
        return self._wrap(row)

    def fetchall(self):
        out = [self._wrap(r) for r in self._rows[self._idx:]]
        self._idx = len(self._rows)
        return out

    def __iter__(self):
        while self._idx < len(self._rows):
            yield self._wrap(self._rows[self._idx])
            self._idx += 1


class _TursoConn:
    """Cliente HTTP minimalista compatible con la API sqlite3 que usa la app."""

    def __init__(self, url: str, token: str):
        self._url = _turso_http_url(url)
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def _pipeline(self, statements):
        """statements: lista de (sql, params)"""
        body = {
            "requests": [
                {"type": "execute", "stmt": {"sql": sql, "args": [_to_arg(p) for p in params]}}
                for sql, params in statements
            ] + [{"type": "close"}]
        }
        resp = requests.post(self._url, json=body, headers=self._headers, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"Turso HTTP {resp.status_code}: {resp.text}")
        data = resp.json()
        results = []
        for r in data.get("results", []):
            if r.get("type") == "error":
                err = r.get("error", {})
                raise RuntimeError(f"Turso error: {err.get('message', err)}")
            if r.get("type") == "ok":
                resp_data = r.get("response", {}).get("result")
                if resp_data:
                    cols = [c.get("name") for c in resp_data.get("cols", [])]
                    rows = [[_from_cell(cell) for cell in row] for row in resp_data.get("rows", [])]
                    results.append((cols, rows))
                else:
                    results.append((None, None))
        return results

    def execute(self, sql, params=()):
        if isinstance(params, dict):
            raise NotImplementedError("Named params no soportados todavía.")
        results = self._pipeline([(sql, tuple(params))])
        cols, rows = results[0]
        return _TursoCursor(cols or [], rows or [])

    def executescript(self, sql):
        stmts = [(s.strip(), ()) for s in sql.split(";") if s.strip()]
        if stmts:
            self._pipeline(stmts)

    def commit(self):
        pass  # cada request es auto-commit en HTTP API

    def close(self):
        pass


@contextmanager
def get_conn():
    if USE_TURSO:
        conn = _TursoConn(TURSO_URL, TURSO_TOKEN)
        try:
            yield conn
        finally:
            conn.close()
    else:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS config (
    clave TEXT PRIMARY KEY,
    valor TEXT NOT NULL,
    descripcion TEXT
);

CREATE TABLE IF NOT EXISTS insumos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE NOT NULL,
    categoria TEXT,
    unidad TEXT NOT NULL,
    precio_unitario REAL NOT NULL,
    rendimiento_default REAL DEFAULT 1.0,
    notas TEXT
);

CREATE TABLE IF NOT EXISTS platos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE NOT NULL,
    dia TEXT,
    precio_venta REAL NOT NULL,
    activo INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS receta (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plato_id INTEGER NOT NULL,
    insumo_id INTEGER NOT NULL,
    cantidad_servida REAL NOT NULL,
    rendimiento REAL NOT NULL DEFAULT 1.0
);

CREATE TABLE IF NOT EXISTS packaging (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE NOT NULL,
    unidades_por_pack INTEGER NOT NULL,
    precio_pack REAL NOT NULL,
    notas TEXT
);

CREATE TABLE IF NOT EXISTS plato_packaging (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plato_id INTEGER NOT NULL,
    packaging_id INTEGER NOT NULL,
    cantidad REAL NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    empresa TEXT,
    direccion TEXT,
    telefono TEXT,
    restricciones TEXT,
    forma_pago TEXT,
    cliente_desde DATE DEFAULT CURRENT_DATE
);

CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL,
    fecha DATE NOT NULL,
    lunes TEXT,
    martes TEXT,
    miercoles TEXT,
    jueves TEXT,
    viernes TEXT,
    observaciones TEXT,
    estado_pago TEXT DEFAULT 'Pendiente'
);

CREATE TABLE IF NOT EXISTS gastos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha DATE NOT NULL,
    categoria TEXT NOT NULL,
    producto TEXT NOT NULL,
    cantidad REAL,
    unidad_medida TEXT,
    precio_unitario REAL,
    total REAL NOT NULL,
    lugar TEXT
);
"""


def init_db():
    with get_conn() as c:
        c.executescript(SCHEMA)


def costo_plato(conn, plato_id):
    cur = conn.execute(
        """SELECT r.cantidad_servida, r.rendimiento, i.precio_unitario
           FROM receta r JOIN insumos i ON i.id = r.insumo_id
           WHERE r.plato_id = ?""",
        (plato_id,),
    )
    comida = 0.0
    for row in cur:
        cant_cruda = row["cantidad_servida"] / max(row["rendimiento"], 0.001)
        comida += cant_cruda * row["precio_unitario"]

    cur = conn.execute(
        """SELECT pp.cantidad, p.unidades_por_pack, p.precio_pack
           FROM plato_packaging pp JOIN packaging p ON p.id = pp.packaging_id
           WHERE pp.plato_id = ?""",
        (plato_id,),
    )
    pack = 0.0
    for row in cur:
        unit_cost = row["precio_pack"] / max(row["unidades_por_pack"], 1)
        pack += row["cantidad"] * unit_cost
    return comida, pack, comida + pack


def get_cfg(conn, clave, default=None):
    row = conn.execute("SELECT valor FROM config WHERE clave=?", (clave,)).fetchone()
    return row["valor"] if row else default


def set_cfg(conn, clave, valor, descripcion=None):
    existing = conn.execute("SELECT 1 FROM config WHERE clave=?", (clave,)).fetchone()
    if existing:
        conn.execute("UPDATE config SET valor=?, descripcion=? WHERE clave=?", (str(valor), descripcion, clave))
    else:
        conn.execute(
            "INSERT INTO config(clave, valor, descripcion) VALUES(?,?,?)",
            (clave, str(valor), descripcion),
        )


def is_seeded(conn) -> bool:
    try:
        row = conn.execute("SELECT COUNT(*) as n FROM platos").fetchone()
        return row["n"] > 0
    except Exception:
        return False
