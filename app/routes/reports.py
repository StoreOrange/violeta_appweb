from flask import Blueprint, render_template, request, jsonify, send_file
from datetime import date, datetime, timedelta
import unicodedata
import re
from io import BytesIO
from collections import Counter

# CRUD reales (no inventamos funciones)
from app.crud.proyecto_crud import listar_proyectos
from app.crud.tarea_crud import listar_tareas
from app import db
from app.models import Tarea, TareaDependencia, Comentario
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

reports_bp = Blueprint("reports", __name__)

def _to_date(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    return value

def _normalizar_inicio_fin(inicio, fin, duracion):
    if inicio and not fin:
        fin = inicio + timedelta(days=duracion - 1)
    if fin and not inicio:
        inicio = fin - timedelta(days=duracion - 1)
    if inicio and fin and fin < inicio:
        fin = inicio
    return inicio, fin

def _estado_nombre(estado):
    if estado is None:
        return "Sin estado"
    if hasattr(estado, "nombre_estado"):
        return estado.nombre_estado
    return str(estado)

def _estado_clase(nombre):
    if not nombre:
        return "sin-estado"
    normalized = unicodedata.normalize("NFKD", nombre)
    stripped = "".join(c for c in normalized if not unicodedata.combining(c))
    return (
        stripped.lower()
        .replace("/", " ")
        .replace("_", " ")
        .strip()
        .replace(" ", "-")
    )

def _estado_color(estado):
    if estado is None:
        return None
    if hasattr(estado, "color"):
        return estado.color
    return None

def _texto_color(hex_color):
    if not hex_color or not isinstance(hex_color, str):
        return "#111827"
    value = hex_color.lstrip("#")
    if len(value) != 6:
        return "#111827"
    try:
        r = int(value[0:2], 16)
        g = int(value[2:4], 16)
        b = int(value[4:6], 16)
    except ValueError:
        return "#111827"
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#111827" if luminance > 0.6 else "#ffffff"

def _parse_date_param(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None

def _comment_excerpt(text, limit=150):
    if not text:
        return "Sin detalle registrado"
    clean = " ".join(str(text).split())
    if len(clean) <= limit:
        return clean
    return clean[: limit - 3].rstrip() + "..."

def _build_ticket_report_data(proyecto_id, fecha_inicio, fecha_fin):
    proyectos = listar_proyectos()
    comentarios_query = (
        Comentario.query
        .join(Tarea, Comentario.idtarea == Tarea.idtarea)
        .filter(Comentario.fecha.isnot(None))
    )

    if proyecto_id:
        comentarios_query = comentarios_query.filter(Tarea.idproyecto == proyecto_id)
    if fecha_inicio:
        comentarios_query = comentarios_query.filter(Comentario.fecha >= datetime.combine(fecha_inicio, datetime.min.time()))
    if fecha_fin:
        comentarios_query = comentarios_query.filter(Comentario.fecha < datetime.combine(fecha_fin + timedelta(days=1), datetime.min.time()))

    comentarios = (
        comentarios_query
        .order_by(Comentario.fecha.desc(), Comentario.idcomentario.desc())
        .all()
    )

    resumen_por_tarea = {}
    total_adjuntos = 0
    usuarios_activos = set()
    estados_counter = Counter()
    ultimos_movimientos = []

    for comentario in comentarios:
        tarea = comentario.tarea
        if not tarea:
            continue

        resumen = resumen_por_tarea.get(tarea.idtarea)
        if resumen is None:
            resumen = {
                "tarea": tarea,
                "comentarios": [],
                "participantes": {},
                "estado_counter": Counter(),
                "con_adjuntos": 0,
            }
            resumen_por_tarea[tarea.idtarea] = resumen

        resumen["comentarios"].append(comentario)
        if comentario.usuario:
            resumen["participantes"][comentario.usuario.idusuario] = comentario.usuario
            usuarios_activos.add(comentario.usuario.idusuario)
        if comentario.idadjunto:
            resumen["con_adjuntos"] += 1
            total_adjuntos += 1

        estado_nombre = _estado_nombre(comentario.estado)
        resumen["estado_counter"][estado_nombre] += 1
        estados_counter[estado_nombre] += 1

    filas = []
    for resumen in resumen_por_tarea.values():
        comentarios_tarea = sorted(
            resumen["comentarios"],
            key=lambda item: (item.fecha or datetime.min, item.idcomentario or 0)
        )
        primero = comentarios_tarea[0]
        ultimo = comentarios_tarea[-1]
        ultimo_estado_nombre = _estado_nombre(ultimo.estado or resumen["tarea"].estado)
        ultimo_estado_clase = _estado_clase(ultimo_estado_nombre)
        ultimo_estado_color = _estado_color(ultimo.estado or resumen["tarea"].estado)
        ultimo_estado_texto = _texto_color(ultimo_estado_color)
        participantes = list(resumen["participantes"].values())
        estado_detalle = [
            {"nombre": nombre, "total": total}
            for nombre, total in resumen["estado_counter"].most_common()
        ]

        fila = {
            "tarea": resumen["tarea"],
            "total_comentarios": len(comentarios_tarea),
            "total_participantes": len(participantes),
            "participantes": participantes,
            "fecha_primera_respuesta": primero.fecha,
            "fecha_ultima_respuesta": ultimo.fecha,
            "ultimo_usuario": ultimo.usuario,
            "ultimo_estado_nombre": ultimo_estado_nombre,
            "ultimo_estado_clase": ultimo_estado_clase,
            "ultimo_estado_color": ultimo_estado_color,
            "ultimo_estado_texto": ultimo_estado_texto,
            "estado_detalle": estado_detalle,
            "con_adjuntos": resumen["con_adjuntos"],
            "ultimo_comentario": _comment_excerpt(ultimo.comentario),
        }
        filas.append(fila)
        ultimos_movimientos.append(ultimo)

    filas.sort(
        key=lambda item: (
            item["fecha_ultima_respuesta"] or datetime.min,
            item["tarea"].titulo or ""
        ),
        reverse=True
    )

    tareas_cerradas = 0
    for fila in filas:
        normalized = unicodedata.normalize("NFKD", fila["ultimo_estado_nombre"] or "")
        stripped = "".join(c for c in normalized if not unicodedata.combining(c)).lower()
        if any(word in stripped for word in ("cerrad", "terminad", "completad", "finalizad")):
            tareas_cerradas += 1

    resumen_estados = [
        {"nombre": nombre, "total": total, "clase": _estado_clase(nombre)}
        for nombre, total in estados_counter.most_common()
    ]

    resumen_general = {
        "total_tareas": len(filas),
        "total_comentarios": len(comentarios),
        "total_participantes": len(usuarios_activos),
        "total_adjuntos": total_adjuntos,
        "tareas_cerradas": tareas_cerradas,
        "promedio_seguimientos": round((len(comentarios) / len(filas)), 1) if filas else 0,
        "ultimo_movimiento": max(ultimos_movimientos, key=lambda item: item.fecha) if ultimos_movimientos else None,
    }

    return {
        "proyectos": proyectos,
        "filas": filas,
        "resumen_general": resumen_general,
        "resumen_estados": resumen_estados,
        "proyecto_seleccionado": proyecto_id,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
    }

def _parse_predecesores(raw):
    if not raw:
        return [], []
    items = [p.strip() for p in raw.split(",")]
    deps = []
    errors = []
    pattern = re.compile(r"^(\d+)\s*(FS|SS|FF|SF)?\s*([+-]\s*\d+\s*d)?$", re.I)
    for item in items:
        if not item:
            continue
        match = pattern.match(item)
        if not match:
            errors.append(item)
            continue
        pred_id = int(match.group(1))
        tipo = (match.group(2) or "FS").upper()
        lag_raw = match.group(3)
        lag = 0
        if lag_raw:
            lag_clean = lag_raw.replace(" ", "").lower().replace("d", "")
            try:
                lag = int(lag_clean)
            except ValueError:
                errors.append(item)
                continue
        deps.append({"idpredecesor": pred_id, "tipo": tipo, "lag_dias": lag})
    return deps, errors

def _detect_cycle(nodes, edges):
    adj = {n: [] for n in nodes}
    for a, b in edges:
        adj.setdefault(a, []).append(b)

    visiting = set()
    visited = set()

    def dfs(node):
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        for nxt in adj.get(node, []):
            if dfs(nxt):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    for n in nodes:
        if dfs(n):
            return True
    return False

def _auto_schedule(tareas_db, dependencias):
    tareas = {}
    for t in tareas_db:
        inicio = _to_date(t.fecha_creacion)
        fin = _to_date(t.fecha_limite)
        if inicio and fin:
            duracion = (fin - inicio).days + 1
        else:
            duracion = 1
        inicio, fin = _normalizar_inicio_fin(inicio, fin, duracion)
        tareas[t.idtarea] = {
            "inicio": inicio,
            "fin": fin,
            "duracion": duracion
        }

    for _ in range(len(tareas)):
        changed = False
        for dep in dependencias:
            pred = tareas.get(dep.idpredecesor)
            succ = tareas.get(dep.idtarea)
            if not pred or not succ:
                continue
            lag = dep.lag_dias or 0
            if dep.tipo == "FS" and pred["fin"]:
                limite = pred["fin"] + timedelta(days=lag)
                if not succ["inicio"] or succ["inicio"] < limite:
                    succ["inicio"] = limite
                    succ["fin"] = succ["inicio"] + timedelta(days=succ["duracion"] - 1)
                    changed = True
            elif dep.tipo == "SS" and pred["inicio"]:
                limite = pred["inicio"] + timedelta(days=lag)
                if not succ["inicio"] or succ["inicio"] < limite:
                    succ["inicio"] = limite
                    succ["fin"] = succ["inicio"] + timedelta(days=succ["duracion"] - 1)
                    changed = True
            elif dep.tipo == "FF" and pred["fin"]:
                limite = pred["fin"] + timedelta(days=lag)
                if not succ["fin"] or succ["fin"] < limite:
                    succ["fin"] = limite
                    succ["inicio"] = succ["fin"] - timedelta(days=succ["duracion"] - 1)
                    changed = True
            elif dep.tipo == "SF" and pred["inicio"]:
                limite = pred["inicio"] + timedelta(days=lag)
                if not succ["fin"] or succ["fin"] < limite:
                    succ["fin"] = limite
                    succ["inicio"] = succ["fin"] - timedelta(days=succ["duracion"] - 1)
                    changed = True
        if not changed:
            break
    return tareas

def _build_report_data(proyecto_id):
    proyectos = listar_proyectos()
    tareas_db = listar_tareas(proyecto_id)
    if not tareas_db:
        return proyectos, [], [], []

    fechas_inicio = []
    fechas_fin = []
    tareas = []
    tareas_por_id = {}

    for t in tareas_db:
        inicio = _to_date(t.fecha_creacion)
        fin = _to_date(t.fecha_limite) or inicio

        if inicio:
            fechas_inicio.append(inicio)
        if fin:
            fechas_fin.append(fin)

        estado_nombre = _estado_nombre(t.estado)
        estado_clase = _estado_clase(estado_nombre)
        estado_color = _estado_color(t.estado)
        estado_texto = _texto_color(estado_color)

        duracion = (fin - inicio).days + 1 if inicio and fin else 1
        inicio, fin = _normalizar_inicio_fin(inicio, fin, duracion)

        tarea_dict = {
            "id": t.idtarea,
            "titulo": t.titulo,
            "descripcion": t.descripcion,
            "fecha_inicio": inicio,
            "fecha_fin": fin,
            "estado_nombre": estado_nombre,
            "estado_clase": estado_clase,
            "estado_color": estado_color,
            "estado_texto": estado_texto,
            "duracion": (fin - inicio).days + 1 if inicio and fin else duracion
        }
        tareas.append(tarea_dict)
        tareas_por_id[t.idtarea] = tarea_dict

    task_ids = [t.idtarea for t in tareas_db]
    dependencias = []
    if task_ids:
        dependencias = (
            TareaDependencia.query
            .filter(TareaDependencia.idtarea.in_(task_ids))
            .all()
        )

    dependencias_info = []
    dependencias_por_tarea = {}
    for dep in dependencias:
        if dep.idpredecesor not in tareas_por_id:
            continue
        dependencias_por_tarea.setdefault(dep.idtarea, []).append(dep)
        dependencias_info.append({
            "tarea_id": dep.idtarea,
            "predecesor_id": dep.idpredecesor,
            "tipo": dep.tipo,
            "lag_dias": dep.lag_dias
        })

    schedule = _auto_schedule(tareas_db, dependencias)
    for tarea_id, fechas in schedule.items():
        if tarea_id in tareas_por_id:
            tareas_por_id[tarea_id]["fecha_inicio"] = fechas["inicio"]
            tareas_por_id[tarea_id]["fecha_fin"] = fechas["fin"]
            tareas_por_id[tarea_id]["duracion"] = fechas["duracion"]

    for tarea_id, deps in dependencias_por_tarea.items():
        partes = []
        for dep in deps:
            lag = dep.lag_dias or 0
            if lag > 0:
                lag_txt = f"+{lag}d"
            elif lag < 0:
                lag_txt = f"{lag}d"
            else:
                lag_txt = ""
            partes.append(f"{dep.idpredecesor}{dep.tipo}{lag_txt}")
        tareas_por_id[tarea_id]["predecesores"] = ", ".join(partes)

    for tarea in tareas:
        tarea["predecesores"] = tarea.get("predecesores", "")

    fechas_inicio = [t["fecha_inicio"] for t in tareas if t.get("fecha_inicio")]
    fechas_fin = [t["fecha_fin"] for t in tareas if t.get("fecha_fin")]

    calendario = []
    if fechas_inicio and fechas_fin:
        fecha_inicio = min(fechas_inicio)
        fecha_fin = max(fechas_fin)
        fecha_actual = fecha_inicio
        while fecha_actual <= fecha_fin:
            calendario.append(fecha_actual)
            fecha_actual += timedelta(days=1)

    tareas.sort(
        key=lambda x: (
            x["fecha_inicio"] or date.min,
            x["fecha_fin"] or date.min,
            x["titulo"] or ""
        )
    )

    return proyectos, tareas, calendario, dependencias_info


@reports_bp.route("/project-report", methods=["GET"])
def project_report():
    proyecto_id = request.args.get("proyecto_id", type=int)
    print_mode = request.args.get("print", type=int) == 1

    proyectos = listar_proyectos()

    if not proyecto_id:
        return render_template(
            "reports/project_report.html",
            proyectos=proyectos,
            proyecto_seleccionado=None,
            tareas=[],
            calendario=[],
            dependencias=[],
            print_mode=print_mode
        )

    proyectos, tareas, calendario, dependencias_info = _build_report_data(proyecto_id)

    return render_template(
        "reports/project_report.html",
        proyectos=proyectos,
        proyecto_seleccionado=proyecto_id,
        tareas=tareas,
        calendario=calendario,
        dependencias=dependencias_info,
        print_mode=print_mode
    )


@reports_bp.route("/ticket-report", methods=["GET"])
def ticket_report():
    proyecto_id = request.args.get("proyecto_id", type=int)
    fecha_inicio = _parse_date_param(request.args.get("fecha_inicio")) or (date.today() - timedelta(days=29))
    fecha_fin = _parse_date_param(request.args.get("fecha_fin")) or date.today()

    if fecha_fin < fecha_inicio:
        fecha_fin = fecha_inicio

    report = _build_ticket_report_data(proyecto_id, fecha_inicio, fecha_fin)
    return render_template("reports/ticket_report.html", **report)


@reports_bp.route("/project-report/export/excel", methods=["GET"])
def export_excel():
    proyecto_id = request.args.get("proyecto_id", type=int)
    if not proyecto_id:
        return jsonify({"ok": False, "message": "Proyecto requerido."}), 400

    _, tareas, _, _ = _build_report_data(proyecto_id)
    wb = Workbook()
    ws = wb.active
    ws.title = "Reporte"

    headers = [
        "ID",
        "Tarea",
        "Descripcion",
        "Estado",
        "ColorEstado",
        "Predecesor",
        "DuracionDias",
        "Inicio",
        "Fin"
    ]
    ws.append(headers)

    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")

    for t in tareas:
        ws.append([
            t["id"],
            t["titulo"],
            t["descripcion"],
            t["estado_nombre"],
            t.get("estado_color", ""),
            t.get("predecesores", ""),
            t.get("duracion", ""),
            t["fecha_inicio"].strftime("%Y-%m-%d") if t.get("fecha_inicio") else "",
            t["fecha_fin"].strftime("%Y-%m-%d") if t.get("fecha_fin") else "",
        ])

    widths = [8, 40, 60, 18, 16, 24, 12, 14, 14]
    for idx, width in enumerate(widths, start=1):
        ws.column_dimensions[chr(64 + idx)].width = width

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name="project_report.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@reports_bp.route("/project-report/export/pdf", methods=["GET"])
def export_pdf():
    proyecto_id = request.args.get("proyecto_id", type=int)
    if not proyecto_id:
        return jsonify({"ok": False, "message": "Proyecto requerido."}), 400

    _, tareas, _, _ = _build_report_data(proyecto_id)

    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=landscape(letter))
    styles = getSampleStyleSheet()
    elements = [Paragraph("Project Report", styles["Title"]), Spacer(1, 12)]

    data = [["ID", "Tarea", "Estado", "Predecesor", "Duracion", "Inicio", "Fin"]]
    for t in tareas:
        data.append([
            str(t["id"]),
            t["titulo"],
            t["estado_nombre"],
            t.get("predecesores", ""),
            str(t.get("duracion", "")),
            t["fecha_inicio"].strftime("%Y-%m-%d") if t.get("fecha_inicio") else "",
            t["fecha_fin"].strftime("%Y-%m-%d") if t.get("fecha_fin") else "",
        ])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7c3aed")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
    ]))
    elements.append(table)
    doc.build(elements)
    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name="project_report.pdf",
        mimetype="application/pdf"
    )


@reports_bp.route("/project-report/dependencies", methods=["POST"])
def update_dependencies():
    payload = request.get_json(silent=True) or {}
    proyecto_id = payload.get("proyecto_id")
    tarea_id = payload.get("tarea_id")
    predecesores_raw = payload.get("predecesores", "")
    deps_payload = payload.get("deps")

    if not proyecto_id or not tarea_id:
        return jsonify({"ok": False, "message": "Datos incompletos."}), 400

    tareas_db = listar_tareas(proyecto_id)
    task_ids = {t.idtarea for t in tareas_db}
    if tarea_id not in task_ids:
        return jsonify({"ok": False, "message": "Tarea no valida."}), 400

    deps = []
    errors = []
    if isinstance(deps_payload, list):
        for item in deps_payload:
            try:
                pred_id = int(item.get("idpredecesor"))
                tipo = str(item.get("tipo", "FS")).upper()
                lag = int(item.get("lag_dias", 0))
            except (TypeError, ValueError):
                errors.append(item)
                continue
            if tipo not in {"FS", "SS", "FF", "SF"}:
                errors.append(item)
                continue
            deps.append({"idpredecesor": pred_id, "tipo": tipo, "lag_dias": lag})
    else:
        deps, errors = _parse_predecesores(predecesores_raw)
        if errors:
            return jsonify({
                "ok": False,
                "message": "Formato invalido. Usa: 5FS+3d, 8SS-2d"
            }), 400

    deps = [d for d in deps if d["idpredecesor"] in task_ids and d["idpredecesor"] != tarea_id]

    # Build edges for cycle detection
    existing = (
        TareaDependencia.query
        .filter(TareaDependencia.idtarea.in_(task_ids))
        .all()
    )
    edges = []
    for dep in existing:
        if dep.idtarea == tarea_id:
            continue
        edges.append((dep.idpredecesor, dep.idtarea))
    for dep in deps:
        edges.append((dep["idpredecesor"], tarea_id))

    if _detect_cycle(task_ids, edges):
        return jsonify({"ok": False, "message": "Dependencia ciclica detectada."}), 400

    # Replace dependencies for this task
    TareaDependencia.query.filter_by(idtarea=tarea_id).delete()
    for dep in deps:
        db.session.add(TareaDependencia(
            idtarea=tarea_id,
            idpredecesor=dep["idpredecesor"],
            tipo=dep["tipo"],
            lag_dias=dep["lag_dias"]
        ))

    # Persist recalculated dates
    dependencias = (
        TareaDependencia.query
        .filter(TareaDependencia.idtarea.in_(task_ids))
        .all()
    )
    schedule = _auto_schedule(tareas_db, dependencias)
    for t in tareas_db:
        fechas = schedule.get(t.idtarea)
        if not fechas:
            continue
        inicio = fechas["inicio"]
        fin = fechas["fin"]
        if inicio:
            t.fecha_creacion = datetime.combine(inicio, datetime.min.time())
        if fin:
            t.fecha_limite = fin

    db.session.commit()

    return jsonify({"ok": True})
