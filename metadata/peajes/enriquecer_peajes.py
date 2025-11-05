#!/usr/bin/env python3
"""
enriquecer_peajes.py

Objetivo:
  - Tomar un archivo de georreferencias (peajes_mop.json) y un archivo de tarifas (precios.json)
  - Para cada peaje georreferenciado, intentar asignarle las tarifas correspondientes desde precios.json
  - Guardar peajes_enriquecidos.json con las tarifas asignadas y generar métricas de cobertura

Cómo usar:
  1) Coloca este script en la misma carpeta que peajes_mop.json y precios.json
  2) Ejecuta: python enriquecer_peajes.py
  3) Salidas:
     - peajes_enriquecidos.json
     - peajes_enriquecidos_report.txt (resumen con métricas y peajes sin match)
"""
import json
import os
import re
from collections import defaultdict
from unidecode import unidecode

# ---------- Configuración ----------
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
GEO_FILE = os.path.join(SCRIPT_DIR, "peajes_mop.json")
PRECIOS_FILE = os.path.join(SCRIPT_DIR, "precios.json")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "peajes_enriquecidos.json")
REPORT_FILE = os.path.join(SCRIPT_DIR, "peajes_enriquecidos_report.txt")

# Palabras vacías útiles para normalizar
STOP_WORDS = {
    "de", "la", "el", "los", "las", "y", "en", "con", "a", "del", "tramo",
    "ruta", "autopista", "peaje", "peajes", "plaza", "plazas", "paso", "ap",
    "km", "k", "s", "n", "e", "o"
}

# ---------- Utilidades ----------
def normalizar(texto):
    """Normaliza un texto: quita tildes, pone minúsculas, elimina no alfanuméricos,
    y saca stop words. Devuelve string y set de tokens."""
    if texto is None:
        return "", set()
    s = unidecode(str(texto)).lower()
    s = re.sub(r'[^a-z0-9\s]', ' ', s)
    tokens = [t.strip() for t in s.split() if t.strip() and t.strip() not in STOP_WORDS]
    return " ".join(tokens), set(tokens)

def cargar_json_ruta(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def extraer_precios_lista(precios_raw):
    """Normaliza la estructura de precios a una lista de autopistas.
    Soporta formato {'autopistas': [...]} o lista directa [...]."""
    if isinstance(precios_raw, dict) and "autopistas" in precios_raw:
        return precios_raw["autopistas"]
    if isinstance(precios_raw, list):
        return precios_raw
    # caso inesperado: envolver en lista si es un solo objeto
    return [precios_raw]

# ---------- Lógica de matching ----------
def indexar_precios(precios_list):
    """
    Crea índices simples para acelerar búsquedas:
      - index_by_autopista: nombre_autopista_norm -> list(autopista_obj)
      - index_by_tramo: tramo_norm -> list(autopista_obj)
    """
    index_by_autopista = defaultdict(list)
    index_by_tramo = defaultdict(list)
    for ap in precios_list:
        nombre_ap = ap.get("nombre_autopista") or ap.get("autopista") or ""
        tramo_desc = ap.get("tramo_descripcion") or ap.get("tramo") or ""
        nombre_norm, nombre_tokens = normalizar(nombre_ap)
        tramo_norm, tramo_tokens = normalizar(tramo_desc)
        ap["_nombre_norm"] = nombre_norm
        ap["_nombre_tokens"] = nombre_tokens
        ap["_tramo_norm"] = tramo_norm
        ap["_tramo_tokens"] = tramo_tokens
        index_by_autopista[nombre_norm].append(ap)
        index_by_tramo[tramo_norm].append(ap)
    return index_by_autopista, index_by_tramo

def buscar_matches_para_peaje(peaje, precios_list, idx_autopista, idx_tramo):
    """
    Devuelve lista de tarifas encontradas (puede ser vacía).
    Estrategia (jerárquica y tolerante):
      1) Coincidencia estricta por contrato/autopista o tramo (nombre exacto normalizado)
      2) Coincidencia por tokens entre nombre del peaje y portico.nombre o tipo
      3) Coincidencia por tipo (troncal/lateral)
      4) Fallback: buscar en todos los porticos por tokens (más costoso)
    """
    resultados = []

    nombre_geo_raw = peaje.get("Nombre") or peaje.get("nombre") or ""
    tipo_geo_raw = peaje.get("Posicion") or peaje.get("tipo") or ""
    contrato_geo_raw = peaje.get("Contrato") or peaje.get("concesionaria") or ""
    tramo_geo_raw = peaje.get("Tramo") or ""

    nombre_geo_norm, nombre_geo_tokens = normalizar(nombre_geo_raw)
    tipo_geo_norm, tipo_geo_tokens = normalizar(tipo_geo_raw)
    contrato_geo_norm, contrato_geo_tokens = normalizar(contrato_geo_raw)
    tramo_geo_norm, tramo_geo_tokens = normalizar(tramo_geo_raw)

    # 1) Buscar por nombre_autopista / contrato exacto
    cand_aps = []
    if contrato_geo_norm:
        cand_aps.extend(idx_autopista.get(contrato_geo_norm, []))
    if tramo_geo_norm:
        cand_aps.extend(idx_tramo.get(tramo_geo_norm, []))

    # Remove duplicates
    cand_aps = list({id(a): a for a in cand_aps}.values())

    # 2) Dentro de candidatos, buscar porticos por coincidencia de nombre o tipo
    def extraer_tarifas_desde_autopista(ap):
        tarifas_encontradas = []
        # Normalizar la estructura de ejes
        for eje in ap.get("ejes", []) or []:
            # porticos o porticos dentro de "direcciones"
            # casos: eje["direcciones"] -> each direction has "porticos"
            if "direcciones" in eje and isinstance(eje["direcciones"], list):
                directions = eje["direcciones"]
                for d in directions:
                    for portico in d.get("porticos", []) or []:
                        tarifas_encontradas.extend(extraer_tarifas_de_portico(portico))
            # caso: eje tiene "porticos"
            for portico in eje.get("porticos", []) or []:
                tarifas_encontradas.extend(extraer_tarifas_de_portico(portico))
            # caso: eje tiene "tarifas" con estructura alternativa
            for tarifa_block in eje.get("tarifas", []) or []:
                # "tarifas" puede contener bloques con "peajes" o "porticos"
                if "peajes" in tarifa_block and isinstance(tarifa_block["peajes"], dict):
                    # tarifas por tipo dentro de este bloque
                    # e.g. tarifa_block might be {"tipo": "NORMAL", "peajes": {...}}
                    tipo = tarifa_block.get("tipo") or tarifa_block.get("nombre") or "NORMAL"
                    peajes_obj = tarifa_block.get("peajes", {})
                    # here peajes_obj might be dict of categories -> prices
                    if all(isinstance(v, (int, float)) or v is None for v in peajes_obj.values()):
                        for cat, val in peajes_obj.items():
                            tarifas_encontradas.append({
                                "categoria_vehiculo": cat,
                                "tipo_tarifa": tipo.upper(),
                                "precio": val
                            })
                    else:
                        # nested structure (ej: {"normal": {...}, "punta": {...}})
                        for tipo_tar, precios_map in peajes_obj.items():
                            for cat, val in precios_map.items():
                                tarifas_encontradas.append({
                                    "categoria_vehiculo": cat,
                                    "tipo_tarifa": tipo_tar.upper(),
                                    "precio": val
                                })
        return tarifas_encontradas

    def extraer_tarifas_de_portico(portico):
        tarifas = []
        # Portico puede tener "peajes" o "tarifas"
        # Normalizar nombre y tipo
        p_nombre = portico.get("nombre") or portico.get("nombre_portico") or ""
        p_tipo = portico.get("tipo") or ""
        p_nombre_norm, p_nombre_tokens = normalizar(p_nombre)
        p_tipo_norm, p_tipo_tokens = normalizar(p_tipo)

        match_by_name = False
        match_by_type = False

        # si tokens comparten intersección significativa -> match
        if nombre_geo_tokens and p_nombre_tokens:
            inter = nombre_geo_tokens.intersection(p_nombre_tokens)
            if len(inter) >= 1:
                match_by_name = True

        # match por igualdad de nombres normalizados (incluye "Lateral"/"Troncal")
        if p_nombre_norm and (p_nombre_norm in nombre_geo_norm or nombre_geo_norm in p_nombre_norm):
            match_by_name = True
        if p_tipo_norm and p_tipo_norm == tipo_geo_norm and tipo_geo_norm:
            match_by_type = True

        # Si hay match por name o type, extraer sus peajes
        if match_by_name or match_by_type:
            # Estructura 1: portico.get("peajes") -> dict categories -> value or dict of types
            if "peajes" in portico and isinstance(portico["peajes"], dict):
                for cat_key, precios in portico["peajes"].items():
                    if isinstance(precios, dict):
                        # ejemplos: {"TBFP": 839.5, "TBP": null}
                        for tipo_tarifa, precio_val in precios.items():
                            tarifas.append({
                                "categoria_vehiculo": cat_key,
                                "tipo_tarifa": tipo_tarifa,
                                "precio": precio_val
                            })
                    else:
                        tarifas.append({
                            "categoria_vehiculo": cat_key,
                            "tipo_tarifa": "NORMAL",
                            "precio": precios
                        })
            # Estructura 2: portico tiene "tarifas" o "tarifas" está en bloque de eje
            if "tarifas" in portico and isinstance(portico["tarifas"], dict):
                # {"normal": {...}, "punta": {...}}
                for tipo_tarifa, precios_map in portico["tarifas"].items():
                    for cat_key, precio_val in precios_map.items():
                        tarifas.append({
                            "categoria_vehiculo": cat_key,
                            "tipo_tarifa": tipo_tarifa.upper(),
                            "precio": precio_val
                        })
            # Estructura 3: portico directamente anidado (ej. en algunos JSON)
            # (si no hay peajes explícitos, no agregamos nada)
        return tarifas

    # Primero, extraer de candidatos por contrato/tramo
    for ap in cand_aps:
        tarifas = extraer_tarifas_desde_autopista(ap)
        resultados.extend(tarifas)

    # Si no se encontró nada aún, intentar búsqueda amplia por tokens entre nombre_geo y todo precios_list
    if not resultados:
        for ap in precios_list:
            # sólo explorar si hay alguna intersección de tokens entre autopista/tramo y contrato/nombre del peaje
            # chequeo rápido: si tokens intersectan (contrato-autopista)
            if contrato_geo_tokens and ap.get("_nombre_tokens") and contrato_geo_tokens.intersection(ap.get("_nombre_tokens")):
                resultados.extend(extraer_tarifas_desde_autopista(ap))
                continue
            # búsqueda por portico names/tokens
            for eje in ap.get("ejes", []) or []:
                # check porticos in directions
                if "direcciones" in eje and isinstance(eje["direcciones"], list):
                    for d in eje["direcciones"]:
                        for portico in d.get("porticos", []) or []:
                            p_nombre = portico.get("nombre") or ""
                            _, p_tokens = normalizar(p_nombre)
                            if nombre_geo_tokens and p_tokens and nombre_geo_tokens.intersection(p_tokens):
                                resultados.extend(extraer_tarifas_de_portico(portico))
                # porticos directos
                for portico in eje.get("porticos", []) or []:
                    p_nombre = portico.get("nombre") or ""
                    _, p_tokens = normalizar(p_nombre)
                    if nombre_geo_tokens and p_tokens and nombre_geo_tokens.intersection(p_tokens):
                        resultados.extend(extraer_tarifas_de_portico(portico))
                # tarifas bloque
                for tarifa_block in eje.get("tarifas", []) or []:
                    # si el bloque tiene "peajes" y el nombre del bloque coincide con tramo/nombre_geo, extraer
                    block_name = tarifa_block.get("nombre") or tarifa_block.get("tipo") or ""
                    block_norm, block_tokens = normalizar(block_name)
                    if block_tokens and nombre_geo_tokens and block_tokens.intersection(nombre_geo_tokens):
                        # extraer precios del bloque
                        if "peajes" in tarifa_block:
                            # estructura similar a antes
                            peajes_obj = tarifa_block["peajes"]
                            if isinstance(peajes_obj, dict):
                                # puede ser nested
                                if all(isinstance(v, (int, float)) or v is None for v in peajes_obj.values()):
                                    for cat, val in peajes_obj.items():
                                        resultados.append({
                                            "categoria_vehiculo": cat,
                                            "tipo_tarifa": "NORMAL",
                                            "precio": val
                                        })
                                else:
                                    for tipo_tar, precios_map in peajes_obj.items():
                                        for cat, val in precios_map.items():
                                            resultados.append({
                                                "categoria_vehiculo": cat,
                                                "tipo_tarifa": tipo_tar.upper(),
                                                "precio": val
                                            })
    # Deduplicate resultados por (categoria, tipo_tarifa, precio)
    seen = set()
    deduped = []
    for t in resultados:
        key = (t.get("categoria_vehiculo"), t.get("tipo_tarifa"), t.get("precio"))
        if key not in seen:
            seen.add(key)
            deduped.append(t)
    return deduped

# ---------- Proceso principal ----------
def main():
    print("--- Iniciando enriquecimiento de peajes ---")

    if not os.path.exists(GEO_FILE):
        print(f"Error: no se encuentra {GEO_FILE}")
        return
    if not os.path.exists(PRECIOS_FILE):
        print(f"Error: no se encuentra {PRECIOS_FILE}")
        return

    peajes_geo = cargar_json_ruta(GEO_FILE)
    precios_raw = cargar_json_ruta(PRECIOS_FILE)
    precios_list = extraer_precios_lista(precios_raw)

    # Indexar precios para búsquedas rápidas
    idx_autopista, idx_tramo = indexar_precios(precios_list)

    peajes_enriquecidos = []
    sin_match = []
    usado_georef_ids = set()

    for peaje in peajes_geo:
        tarifas = buscar_matches_para_peaje(peaje, precios_list, idx_autopista, idx_tramo)
        if tarifas:
            peaje_out = {
                "OBJECTID": peaje.get("OBJECTID"),
                "globalid": peaje.get("GlobalID"),
                "nombre": peaje.get("Nombre"),
                "tipo": peaje.get("Posicion"),
                "concesionaria": peaje.get("Contrato"),
                "tramo": peaje.get("Tramo"),
                "latitud": peaje.get("latitude"),
                "longitud": peaje.get("longitude"),
                "tarifas": tarifas
            }
            peajes_enriquecidos.append(peaje_out)
            usado_georef_ids.add(peaje.get("OBJECTID"))
        else:
            sin_match.append({
                "OBJECTID": peaje.get("OBJECTID"),
                "nombre": peaje.get("Nombre"),
                "tipo": peaje.get("Posicion"),
                "concesionaria": peaje.get("Contrato"),
                "tramo": peaje.get("Tramo"),
                "latitud": peaje.get("latitude"),
                "longitud": peaje.get("longitude")
            })

    # Guardar resultado
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(peajes_enriquecidos, f, indent=2, ensure_ascii=False)

    # Reporte
    total_geo = len(peajes_geo) if isinstance(peajes_geo, list) else 0
    total_enriq = len(peajes_enriquecidos)
    total_sin = len(sin_match)
    coverage = (total_enriq / total_geo * 100) if total_geo else 0.0

    with open(REPORT_FILE, "w", encoding="utf-8") as rf:
        rf.write("Reporte de Enriquecimiento de Peajes\n")
        rf.write("===================================\n")
        rf.write(f"Total peajes georreferenciados: {total_geo}\n")
        rf.write(f"Peajes con tarifas asignadas: {total_enriq}\n")
        rf.write(f"Peajes sin match: {total_sin}\n")
        rf.write(f"Cobertura (geo -> precios): {coverage:.2f}%\n\n")
        rf.write("Listado de peajes sin match (OBJECTID, nombre, tipo, concesionaria, tramo):\n")
        for p in sin_match:
            rf.write(f"- {p.get('OBJECTID')} | {p.get('nombre')} | {p.get('tipo')} | {p.get('concesionaria')} | {p.get('tramo')}\n")

    # Mensajes finales
    print(f"✅ Guardado: {OUTPUT_FILE} ({total_enriq} peajes enriquecidos)")
    print(f"✅ Reporte: {REPORT_FILE} (total georef: {total_geo}, cobertura: {coverage:.2f}%)")
    if total_sin:
        print(f"⚠️ Peajes sin match: {total_sin} — revisa {REPORT_FILE} para detalles")

if __name__ == "__main__":
    main()