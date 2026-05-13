"""Carga datos iniciales (insumos, platos, recetas, packaging, gastos)
desde el Excel/conocimiento previo. Idempotente."""
from db import init_db, get_conn, set_cfg


INSUMOS = [
    # (nombre, categoría, unidad, precio_unitario, rendimiento_default, notas)
    # Proteínas
    ("Pechuga de pollo", "Proteína", "gr", 10.43, 0.75, "Suprema $73000/7kg = $10,43/gr · rinde 75% al cocinar"),
    ("Carne / pollo (mixto burrito)", "Proteína", "gr", 13.33, 0.75, "Estimado pollo+carne mezcla"),
    ("Huevos", "Proteína", "unidad", 167.0, 0.90, "Maple 30 ≈ $5.000"),
    # Lácteos
    ("Queso parmesano", "Lácteos", "gr", 30.0, 1.0, ""),
    ("Queso (sandwich/burrito)", "Lácteos", "gr", 17.5, 1.0, "Saint Paulin $9062/2,43kg"),
    ("Crema", "Lácteos", "ml", 12.93, 1.0, "Ilolay 350ml $4526"),
    ("Manteca", "Lácteos", "gr", 13.52, 1.0, "200gr $2703"),
    ("Muzzarella", "Lácteos", "gr", 11.55, 1.0, "Barraza 1.075kg $12426"),
    ("Leche", "Lácteos", "ml", 2.40, 1.0, "3 Niñas 1L $2400"),
    # Secos / almacén
    ("Lechuga romana", "Verdura", "gr", 4.7, 0.80, "Verdulería · pierde 20% por descarte"),
    ("Crutones", "Almacén", "gr", 10.0, 1.0, ""),
    ("Salsa César", "Almacén", "ml", 10.0, 1.0, "Casera o envasada"),
    ("Aderezo limón/aceite", "Almacén", "porción", 400.0, 1.0, ""),
    ("Papa", "Verdura", "gr", 2.67, 0.82, "Pierde ~18% al asar"),
    ("Batata", "Verdura", "gr", 3.33, 0.80, ""),
    ("Condimentos", "Almacén", "porción", 300.0, 1.0, ""),
    ("Aceite girasol", "Almacén", "ml", 3.11, 1.0, "$2799/900cc"),
    ("Aceite oliva", "Almacén", "ml", 21.77, 1.0, "$43532/2L"),
    ("Aceite de sésamo", "Almacén", "ml", 40.0, 1.0, ""),
    ("Masa de tarta", "Almacén", "unidad", 1200.0, 1.0, ""),
    ("Relleno verdura/queso", "Almacén", "gr", 9.0, 1.0, ""),
    ("Ensalada mixta", "Verdura", "porción", 700.0, 0.85, ""),
    ("Arroz", "Almacén", "gr", 1.75, 2.50, "$8743/5kg · gana peso x2,5 al cocinar"),
    ("Salsa teriyaki", "Almacén", "ml", 16.0, 1.0, ""),
    ("Sésamo / cebolla verde", "Almacén", "gr", 30.0, 1.0, ""),
    ("Pan de campo", "Panadería", "unidad", 600.0, 1.0, ""),
    ("Proteína sandwich", "Proteína", "gr", 15.0, 0.85, ""),
    ("Vegetales frescos", "Verdura", "gr", 7.5, 0.85, ""),
    ("Aderezo sandwich", "Almacén", "ml", 10.0, 1.0, ""),
    ("Tortilla grande", "Panadería", "unidad", 400.0, 1.0, ""),
    ("Frijoles", "Almacén", "gr", 6.25, 1.0, ""),
    ("Salsa / guacamole", "Almacén", "ml", 15.0, 1.0, ""),
    ("Lechuga / tomate", "Verdura", "gr", 5.0, 0.85, ""),
    ("Pan rallado Morixe", "Almacén", "gr", 15.97, 1.0, "$7983,97/500gr"),
    ("Pimentón", "Almacén", "gr", 19.08, 1.0, "$19080/1kg estimado"),
]


PLATOS = [
    # (nombre, dia, precio_venta)
    ("Ensalada César",          "LUN", 11000),
    ("Pollo con Papa y Batata", "MAR", 11000),
    ("Tarta con Ensalada",      "MIE", 11000),
    ("Arroz con Pollo Teriyaki","JUE", 11000),
    ("Sandwich",                "VIE", 10000),
    ("Burrito",                 "VIE", 13000),
]


# (plato, insumo, cantidad_servida, rendimiento_override (None = usar default))
RECETAS = [
    ("Ensalada César",          "Lechuga romana",        170, None),
    ("Ensalada César",          "Crutones",              50,  None),
    ("Ensalada César",          "Pechuga de pollo",      150, None),
    ("Ensalada César",          "Queso parmesano",       30,  None),
    ("Ensalada César",          "Salsa César",           60,  None),
    ("Ensalada César",          "Aderezo limón/aceite",  1,   None),

    ("Pollo con Papa y Batata", "Pechuga de pollo",      200, None),
    ("Pollo con Papa y Batata", "Papa",                  150, None),
    ("Pollo con Papa y Batata", "Batata",                150, None),
    ("Pollo con Papa y Batata", "Condimentos",           1,   None),
    ("Pollo con Papa y Batata", "Aceite girasol",        20,  None),

    ("Tarta con Ensalada",      "Masa de tarta",         1,   None),
    ("Tarta con Ensalada",      "Relleno verdura/queso", 200, None),
    ("Tarta con Ensalada",      "Huevos",                3,   None),
    ("Tarta con Ensalada",      "Ensalada mixta",        1,   None),

    ("Arroz con Pollo Teriyaki","Arroz",                 220, None),
    ("Arroz con Pollo Teriyaki","Pechuga de pollo",      180, None),
    ("Arroz con Pollo Teriyaki","Salsa teriyaki",        50,  None),
    ("Arroz con Pollo Teriyaki","Sésamo / cebolla verde",10,  None),
    ("Arroz con Pollo Teriyaki","Aceite de sésamo",      10,  None),

    ("Sandwich",                "Pan de campo",          1,   None),
    ("Sandwich",                "Proteína sandwich",     120, None),
    ("Sandwich",                "Vegetales frescos",     80,  None),
    ("Sandwich",                "Queso (sandwich/burrito)",40,None),
    ("Sandwich",                "Aderezo sandwich",      30,  None),

    ("Burrito",                 "Tortilla grande",       2,   None),
    ("Burrito",                 "Carne / pollo (mixto burrito)", 180, None),
    ("Burrito",                 "Arroz",                 100, None),
    ("Burrito",                 "Frijoles",              80,  None),
    ("Burrito",                 "Queso (sandwich/burrito)",50, None),
    ("Burrito",                 "Salsa / guacamole",     60,  None),
    ("Burrito",                 "Lechuga / tomate",      60,  None),
]


PACKAGING = [
    ("Bandeja principal",  200, 116900, "Plato principal caliente"),
    ("Bandeja F275",       100, 32900,  "Plato chico / sandwich / tarta"),
    ("Bandeja frío",       100, 16049,  "Ensaladas frías"),
    ("Pote 80cc",          100, 16917,  "Salsa/aderezo · 1 por vianda"),
    ("Vaso americano",     50,  4600,   "Bebida (opcional)"),
    ("Papel film Bonux",   150, 11946,  "1 rollo rinde ~150 viandas"),
    ("Rollo de cocina",    80,  8336.98,"1 rollo rinde ~80 usos"),
]


# (plato, packaging, cantidad)
PLATO_PACK = [
    ("Ensalada César",          "Bandeja frío",       1),
    ("Ensalada César",          "Pote 80cc",          1),
    ("Ensalada César",          "Papel film Bonux",   1),
    ("Ensalada César",          "Rollo de cocina",    1),

    ("Pollo con Papa y Batata", "Bandeja principal",  1),
    ("Pollo con Papa y Batata", "Pote 80cc",          1),
    ("Pollo con Papa y Batata", "Papel film Bonux",   1),
    ("Pollo con Papa y Batata", "Rollo de cocina",    1),

    ("Tarta con Ensalada",      "Bandeja F275",       1),
    ("Tarta con Ensalada",      "Pote 80cc",          1),
    ("Tarta con Ensalada",      "Papel film Bonux",   1),
    ("Tarta con Ensalada",      "Rollo de cocina",    1),

    ("Arroz con Pollo Teriyaki","Bandeja principal",  1),
    ("Arroz con Pollo Teriyaki","Pote 80cc",          1),
    ("Arroz con Pollo Teriyaki","Papel film Bonux",   1),
    ("Arroz con Pollo Teriyaki","Rollo de cocina",    1),

    ("Sandwich",                "Bandeja F275",       1),
    ("Sandwich",                "Pote 80cc",          1),
    ("Sandwich",                "Papel film Bonux",   1),
    ("Sandwich",                "Rollo de cocina",    1),

    ("Burrito",                 "Bandeja principal",  1),
    ("Burrito",                 "Pote 80cc",          1),
    ("Burrito",                 "Papel film Bonux",   1),
    ("Burrito",                 "Rollo de cocina",    1),
]


GASTOS = [
    # (fecha, categoría, producto, cantidad, unidad, precio_u, total, lugar)
    ("2026-05-08", "COMIDA - LÁCTEOS",  "Crema Ilolay",            3, "350ml",   4526,    13578,    "Vital"),
    ("2026-05-08", "COMIDA - LÁCTEOS",  "Manteca",                 3, "200gr",   2703,    8108.98,  "Vital"),
    ("2026-05-08", "COMIDA - LÁCTEOS",  "Muzzarella Barraza",      1, "1.075kg", 12426,   13357.95, "Vital"),
    ("2026-05-08", "COMIDA - LÁCTEOS",  "Saint Paulin La Paulina", 1, "2.430kg", 9062,    22020.67, "Vital"),
    ("2026-05-08", "COMIDA - SECOS",    "Harina 0000",             10,"1kg",     925,     9249.96,  "Vital"),
    ("2026-05-08", "COMIDA - SECOS",    "Pulpa tomate Salsatti",   12,"520gr",   1028,    12336.05, "Vital"),
    ("2026-05-08", "COMIDA - SECOS",    "Sal",                     12,"500gr",   1028,    12336.05, "Vital"),
    ("2026-05-08", "COMIDA - SECOS",    "Aceite girasol",          4, "900cc",   2799,    11195.98, "Vital"),
    ("2026-05-08", "COMIDA - SECOS",    "Aceite oliva SyP",        1, "2L",      43532,   43532,    "Vital"),
    ("2026-05-08", "COMIDA - SECOS",    "Maizena",                 3, "500gr",   2778,    8336.98,  "Vital"),
    ("2026-05-08", "COMIDA - SECOS",    "Arroz",                   1, "5kg",     8743,    8743,     "Vital"),
    ("2026-05-08", "COMIDA - SECOS",    "Caldo verdura",           3, "",        1543,    4629,     "Vital"),
    ("2026-05-08", "COMIDA - SECOS",    "Mostachol Matarazzo",     6, "500gr",   1098.99, 6593.97,  "Vital"),
    ("2026-05-08", "COMIDA - SECOS",    "Tirabuzón Terrabusi",     6, "500gr",   707,     4242.02,  "Vital"),
    ("2026-05-08", "LIMPIEZA",          "Detergente Ala",          3, "750ml",   2192,    6576,     "Vital"),
    ("2026-05-08", "COMIDA - LÁCTEOS",  "Leche 3 Niñas",           4, "1L",      2400.21, 9600.82,  "Vital"),
    ("2026-05-13", "COMIDA - SECOS",    "Pan rallado Morixe",      1, "500gr",   7983.97, 7983.97,  ""),
    ("2026-05-13", "PACKAGING",         "Papel film Bonux",        1, "rollo",   11946,   11946,    ""),
    ("2026-05-13", "COMIDA - SECOS",    "Pimentón Darama",         1, "",        19080,   19080,    ""),
    ("2026-05-13", "LIMPIEZA",          "Rollo de cocina",         1, "",        8336.98, 8336.98,  ""),
    ("2026-05-13", "PACKAGING",         "Vaso americano",          1, "paq.",    4600,    4600,     ""),
    ("2026-05-13", "COMIDA - PROTEÍNA", "Suprema de pollo",        1, "7kg",     73000,   73000,    ""),
    ("2026-05-13", "PACKAGING",         "Bandejas principales",    200,"u",      584.5,   116900,   ""),
    ("2026-05-13", "PACKAGING",         "Bandejas F275",           100,"u",      329,     32900,    ""),
    ("2026-05-13", "PACKAGING",         "Potes 80cc",              100,"u",      169.17,  16917,    ""),
    ("2026-05-13", "PACKAGING",         "Bandejas frío",           100,"u",      160.49,  16049,    ""),
]


CONFIG = [
    ("nombre_negocio", "Lunch Microcentro", "Nombre"),
    ("responsable", "Fernando", "Encargado"),
    ("zona", "CABA - Centro", "Zona delivery"),
    ("hora_corte", "11:00 hs", "Corte pedidos"),
    ("margen_objetivo", "0.65", "Margen objetivo"),
    ("margen_minimo", "0.45", "Margen mínimo"),
    ("whatsapp", "1140756197", "WhatsApp pedidos"),
]


def run():
    init_db()
    with get_conn() as c:
        # Config
        for clave, valor, desc in CONFIG:
            set_cfg(c, clave, valor, desc)

        # Insumos
        for nom, cat, unidad, precio, rend, notas in INSUMOS:
            c.execute(
                """INSERT INTO insumos(nombre,categoria,unidad,precio_unitario,rendimiento_default,notas)
                   VALUES(?,?,?,?,?,?)
                   ON CONFLICT(nombre) DO UPDATE SET
                     categoria=excluded.categoria,
                     unidad=excluded.unidad,
                     precio_unitario=excluded.precio_unitario,
                     rendimiento_default=excluded.rendimiento_default,
                     notas=excluded.notas""",
                (nom, cat, unidad, precio, rend, notas),
            )

        # Platos
        for nom, dia, pv in PLATOS:
            c.execute(
                """INSERT INTO platos(nombre,dia,precio_venta) VALUES(?,?,?)
                   ON CONFLICT(nombre) DO UPDATE SET dia=excluded.dia, precio_venta=excluded.precio_venta""",
                (nom, dia, pv),
            )

        # Recetas - reset y carga
        c.execute("DELETE FROM receta")
        for plato, insumo, cant, rend in RECETAS:
            plato_id = c.execute("SELECT id FROM platos WHERE nombre=?", (plato,)).fetchone()["id"]
            row = c.execute("SELECT id, rendimiento_default FROM insumos WHERE nombre=?", (insumo,)).fetchone()
            if not row:
                print(f"AVISO: insumo no encontrado: {insumo}")
                continue
            r = rend if rend is not None else row["rendimiento_default"]
            c.execute(
                "INSERT INTO receta(plato_id,insumo_id,cantidad_servida,rendimiento) VALUES(?,?,?,?)",
                (plato_id, row["id"], cant, r),
            )

        # Packaging
        for nom, u_pack, precio, notas in PACKAGING:
            c.execute(
                """INSERT INTO packaging(nombre,unidades_por_pack,precio_pack,notas) VALUES(?,?,?,?)
                   ON CONFLICT(nombre) DO UPDATE SET
                     unidades_por_pack=excluded.unidades_por_pack,
                     precio_pack=excluded.precio_pack,
                     notas=excluded.notas""",
                (nom, u_pack, precio, notas),
            )

        # Plato-packaging
        c.execute("DELETE FROM plato_packaging")
        for plato, pack, cant in PLATO_PACK:
            plato_id = c.execute("SELECT id FROM platos WHERE nombre=?", (plato,)).fetchone()["id"]
            pack_id = c.execute("SELECT id FROM packaging WHERE nombre=?", (pack,)).fetchone()["id"]
            c.execute(
                "INSERT INTO plato_packaging(plato_id,packaging_id,cantidad) VALUES(?,?,?)",
                (plato_id, pack_id, cant),
            )

        # Gastos (solo si la tabla está vacía, idempotente)
        cnt = c.execute("SELECT COUNT(*) as n FROM gastos").fetchone()["n"]
        if cnt == 0:
            for g in GASTOS:
                c.execute(
                    """INSERT INTO gastos(fecha,categoria,producto,cantidad,unidad_medida,precio_unitario,total,lugar)
                       VALUES(?,?,?,?,?,?,?,?)""",
                    g,
                )

    print("Seed completado:", DB_PATH := "data/lunch.db")


if __name__ == "__main__":
    run()
