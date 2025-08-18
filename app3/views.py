
import requests
import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .crud import crear_ticket, obtener_tipos_soporte, obtener_areas, obtener_usuarios
from app2.models import Soporte
from telegram import ReplyKeyboardMarkup, KeyboardButton

TELEGRAM_BOT_TOKEN = "8173472907:AAHXGiKOv-FYRhDlnmiXWVo6_JaPQeCqt58"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

# Estado en memoria por chat_id
user_states = {}

# Helper para enviar mensajes a Telegram usando requests
def send_telegram_message(chat_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        requests.post(TELEGRAM_API_URL, data=payload)
    except Exception as e:
        print(f"[BOT] Error enviando mensaje: {e}")


@csrf_exempt
def bot(request):
    if request.method == "GET":
        ayuda = (
            "Bot activo.\n"
            "Comandos disponibles:\n"
            "/crearticket <tipo_soporte_id> <comentario> <usuario_id> <area_id> [atendido_por_id]\n"
            "/reporte para ver los tickets existentes"
        )
        return HttpResponse(ayuda)


    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
        except Exception as e:
            return JsonResponse({"ok": False, "error": f"JSON inválido: {str(e)}"}, status=400)

        message = data.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")
        response_text = None

        # Inicializar estado si no existe
        if chat_id not in user_states:
            user_states[chat_id] = {"step": None, "data": {}}
        state = user_states[chat_id]

        # Comando /start: mostrar lista de comandos disponibles
        if isinstance(text, str) and text.strip().lower() == "/start":
            ayuda = (
                "Bienvenido al bot de tickets.\n\n"
                "Comandos disponibles:\n"
                "/crearticket - Iniciar la creación de un ticket\n"
                "/reporte - Ver y filtrar tickets existentes\n"
                "/crear nuevo usuario - Registrar un nuevo usuario\n"
                "\nPuedes usar los comandos en cualquier momento."
            )
            send_telegram_message(chat_id, ayuda)
            return JsonResponse({"ok": True})

        # Comando /reporte: mostrar lista de tickets con filtros
        if isinstance(text, str) and text.strip().startswith("/reporte"):
            # Flujo interactivo para filtros de reporte
            state["step"] = "reporte_menu"
            send_telegram_message(chat_id,
                "¿Qué reporte deseas ver?\n"
                "1️⃣ Todos los tickets\n"
                "2️⃣ Últimos N tickets\n"
                "3️⃣ Filtrar por usuario\n"
                "4️⃣ Filtrar por tipo de soporte\n"
                "5️⃣ Filtrar por Área\n"
                "Responde con el número de opción.")
            return JsonResponse({"ok": True})

        # Flujo interactivo: respuesta del menú de reporte
        if state.get("step") == "reporte_menu":
            from app2.models import Ticket
            opcion = text.strip()
            if opcion == "1":
                tickets = Ticket.objects.all().order_by('-fecha_creacion')
                reporte = f"Total de tickets: {tickets.count()}\n\n"
                for t in tickets:
                    reporte += f"ID: {t.pk}\nTipo: {getattr(t.tipo_soporte, 'nombre', '-')}, Usuario: {getattr(t.usuario, 'nombre', '-')}, Área: {getattr(t.area, 'nombre', '-')}, Fecha: {t.fecha_creacion.strftime('%d/%m/%Y %H:%M')}\nComentario: {t.comentario}\n---\n"
                send_telegram_message(chat_id, reporte if reporte else "No hay tickets registrados.")
                state["step"] = None
                return JsonResponse({"ok": True})
            elif opcion == "2":
                state["step"] = "reporte_ultimos"
                send_telegram_message(chat_id, "¿Cuántos tickets recientes deseas ver? (Escribe el número)")
                return JsonResponse({"ok": True})
            elif opcion == "3":
                state["step"] = "reporte_usuario"
                send_telegram_message(chat_id, "Escribe el nombre (o parte) del usuario para filtrar:")
                return JsonResponse({"ok": True})
            elif opcion == "4":
                state["step"] = "reporte_tipo"
                send_telegram_message(chat_id, "Escribe el nombre (o parte) del tipo de soporte para filtrar:")
                return JsonResponse({"ok": True})
            elif opcion == "5":
                state["step"] = "reporte_area"
                send_telegram_message(chat_id, "Escribe el nombre (o parte) del Área para filtrar:")
                return JsonResponse({"ok": True})
            else:
                send_telegram_message(chat_id, "Opción inválida. Responde con un número del 1 al 5.")
                return JsonResponse({"ok": True})

        # Últimos N tickets
        if state.get("step") == "reporte_ultimos":
            from app2.models import Ticket
            try:
                n = int(text.strip())
            except Exception:
                send_telegram_message(chat_id, "Por favor escribe un número válido.")
                return JsonResponse({"ok": True})
            tickets = Ticket.objects.all().order_by('-fecha_creacion')[:n]
            if tickets:
                reporte = f"Últimos {n} tickets:\n\n"
                for t in tickets:
                    reporte += f"ID: {t.pk}\nTipo: {getattr(t.tipo_soporte, 'nombre', '-')}, Usuario: {getattr(t.usuario, 'nombre', '-')}, Área: {getattr(t.area, 'nombre', '-')}, Fecha: {t.fecha_creacion.strftime('%d/%m/%Y %H:%M')}\nComentario: {t.comentario}\n---\n"
                send_telegram_message(chat_id, reporte)
            else:
                send_telegram_message(chat_id, "No hay tickets registrados.")
            state["step"] = None
            return JsonResponse({"ok": True})

        # Filtrar por usuario
        if state.get("step") == "reporte_usuario":
            from app2.models import Ticket
            nombre = text.strip()
            tickets = Ticket.objects.filter(usuario__nombre__icontains=nombre).order_by('-fecha_creacion')
            if tickets:
                reporte = f"Tickets para usuario '{nombre}': {tickets.count()}\n\n"
                for t in tickets:
                    reporte += f"ID: {t.pk}\nTipo: {getattr(t.tipo_soporte, 'nombre', '-')}, Usuario: {getattr(t.usuario, 'nombre', '-')}, Área: {getattr(t.area, 'nombre', '-')}, Fecha: {t.fecha_creacion.strftime('%d/%m/%Y %H:%M')}\nComentario: {t.comentario}\n---\n"
                send_telegram_message(chat_id, reporte)
            else:
                send_telegram_message(chat_id, f"No hay tickets para usuario '{nombre}'.")
            state["step"] = None
            return JsonResponse({"ok": True})

        # Filtrar por tipo de soporte
        if state.get("step") == "reporte_tipo":
            from app2.models import Ticket
            nombre = text.strip()
            tickets = Ticket.objects.filter(tipo_soporte__nombre__icontains=nombre).order_by('-fecha_creacion')
            if tickets:
                reporte = f"Tickets para tipo de soporte '{nombre}': {tickets.count()}\n\n"
                for t in tickets:
                    reporte += f"ID: {t.pk}\nTipo: {getattr(t.tipo_soporte, 'nombre', '-')}, Usuario: {getattr(t.usuario, 'nombre', '-')}, Área: {getattr(t.area, 'nombre', '-')}, Fecha: {t.fecha_creacion.strftime('%d/%m/%Y %H:%M')}\nComentario: {t.comentario}\n---\n"
                send_telegram_message(chat_id, reporte)
            else:
                send_telegram_message(chat_id, f"No hay tickets para tipo de soporte '{nombre}'.")
            state["step"] = None
            return JsonResponse({"ok": True})

        # Filtrar por Área
        if state.get("step") == "reporte_area":
            from app2.models import Ticket
            nombre = text.strip()
            tickets = Ticket.objects.filter(area__nombre__icontains=nombre).order_by('-fecha_creacion')
            if tickets:
                reporte = f"Tickets para Área '{nombre}': {tickets.count()}\n\n"
                for t in tickets:
                    reporte += f"ID: {t.pk}\nTipo: {getattr(t.tipo_soporte, 'nombre', '-')}, Usuario: {getattr(t.usuario, 'nombre', '-')}, Área: {getattr(t.area, 'nombre', '-')}, Fecha: {t.fecha_creacion.strftime('%d/%m/%Y %H:%M')}\nComentario: {t.comentario}\n---\n"
                send_telegram_message(chat_id, reporte)
            else:
                send_telegram_message(chat_id, f"No hay tickets para Área '{nombre}'.")
            state["step"] = None
            return JsonResponse({"ok": True})
        try:
            data = json.loads(request.body.decode("utf-8"))
        except Exception as e:
            return JsonResponse({"ok": False, "error": f"JSON inválido: {str(e)}"}, status=400)

        message = data.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")
        response_text = None

        # Inicializar estado si no existe
        if chat_id not in user_states:
            user_states[chat_id] = {"step": None, "data": {}}

        state = user_states[chat_id]

        # INICIO DEL FLUJO INTERACTIVO
        if text.startswith("/crearticket") or (state["step"] is None and text == "/crearticket"):
            tipos = obtener_tipos_soporte()
            print(f"[DEBUG] Tipos de soporte: {tipos}")
            keyboard = [[KeyboardButton(str(t.nombre))] for t in tipos]
            markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
            state["step"] = "tipo_soporte"
            state["data"] = {}
            reply_markup_dict = markup.to_dict() if markup else None
            send_telegram_message(chat_id, "Selecciona el tipo de soporte:", reply_markup=reply_markup_dict)
            return JsonResponse({"ok": True})

        # Selección de tipo de soporte
        if state["step"] == "tipo_soporte":
            tipos = obtener_tipos_soporte()
            # Comparación insensible a mayúsculas y espacios
            tipo = next((t for t in tipos if t.nombre.strip().lower() == text.strip().lower()), None)
            tipo_id = getattr(tipo, 'id', None)
            if tipo and tipo_id:
                state["data"]["tipo_soporte_id"] = tipo_id
                areas = obtener_areas()
                keyboard = [[KeyboardButton(str(a.nombre))] for a in areas]
                markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
                state["step"] = "area"
                reply_markup_dict = markup.to_dict() if markup else None
                send_telegram_message(chat_id, "Selecciona el Área:", reply_markup=reply_markup_dict)
            else:
                send_telegram_message(chat_id, "Por favor selecciona un tipo de soporte válido.")
            return JsonResponse({"ok": True})

        # Selección de CECO
        if state["step"] == "area":
            areas = obtener_areas()
            area = next((a for a in areas if a.nombre == text), None)
            print(f"[DEBUG] Seleccionado area: {area} (text={text})")
            area_id = getattr(area, 'id', None)
            if area and area_id:
                state["data"]["area_id"] = area_id
                state["step"] = "usuario"
                send_telegram_message(chat_id, "Escribe parte del nombre del usuario que será atendido:")
            else:
                send_telegram_message(chat_id, "Por favor selecciona un Área válida.")
            return JsonResponse({"ok": True})

        # Permitir crear usuario desde cualquier parte con /crear nuevo usuario
        if text.strip().lower().startswith("/crear nuevo usuario"):
            state["step"] = "nuevo_usuario_nombre"
            send_telegram_message(chat_id, "Vas a crear un nuevo usuario. Escribe el nombre completo:")
            return JsonResponse({"ok": True})

        # Selección de usuario o crear nuevo (búsqueda directa por nombre)
        if state["step"] == "usuario":
            usuarios = obtener_usuarios()
            coincidencias = [u for u in usuarios if text.lower() in u.nombre.lower()]
            if len(coincidencias) == 0:
                send_telegram_message(chat_id, "No se encontraron usuarios con ese nombre. Intenta de nuevo o escribe '/crear nuevo usuario' para registrar uno nuevo:")
                return JsonResponse({"ok": True})
            elif len(coincidencias) == 1:
                usuario = coincidencias[0]
                usuario_id = getattr(usuario, 'id', None)
                state["data"]["usuario_id"] = usuario_id
                # Paso siguiente: seleccionar soporte
                soportes = list(Soporte.objects.all())
                keyboard = [[KeyboardButton(str(s.nombre))] for s in soportes]
                markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
                state["step"] = "soporte"
                reply_markup_dict = markup.to_dict() if markup else None
                send_telegram_message(chat_id, f"Seleccionado: {usuario.nombre}\nSelecciona el usuario que atiende el ticket:", reply_markup=reply_markup_dict)
                return JsonResponse({"ok": True})
            elif len(coincidencias) <= 5:
                keyboard = [[KeyboardButton(str(u.nombre))] for u in coincidencias]
                keyboard.append([KeyboardButton("/crear nuevo usuario")])
                markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
                reply_markup_dict = markup.to_dict() if markup else None
                send_telegram_message(chat_id, "Selecciona el usuario que será atendido, escribe más letras para filtrar, o pulsa '/crear nuevo usuario' para registrar uno nuevo:", reply_markup=reply_markup_dict)
                return JsonResponse({"ok": True})
            else:
                send_telegram_message(chat_id, f"Demasiados resultados ({len(coincidencias)}). Escribe más letras del nombre para filtrar:")
                return JsonResponse({"ok": True})

        # Selección de soporte (usuario que atiende) simple
        if state["step"] == "soporte":
            soportes = list(Soporte.objects.all())
            soporte = next((s for s in soportes if s.nombre == text), None)
            soporte_id = getattr(soporte, 'id', None)
            if soporte and soporte_id:
                state["data"]["soporte_id"] = soporte_id
                state["step"] = "comentario"
                send_telegram_message(chat_id, "Escribe el comentario del ticket:")
            else:
                send_telegram_message(chat_id, "Por favor selecciona un usuario de soporte válido.")
            return JsonResponse({"ok": True})

        # Crear nuevo usuario (solo nombre)
        if state["step"] == "nuevo_usuario_nombre":
            nombre = text.strip()
            from app2.models import Usuario
            nuevo_usuario = Usuario(nombre=nombre)
            nuevo_usuario.save()
            usuario_id = getattr(nuevo_usuario, 'id', None)
            if usuario_id:
                state["data"]["usuario_id"] = usuario_id
                soportes = list(Soporte.objects.all())
                keyboard = [[KeyboardButton(str(s.nombre))] for s in soportes]
                markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
                state["step"] = "soporte"
                reply_markup_dict = markup.to_dict() if markup else None
                send_telegram_message(chat_id, f"Usuario '{nombre}' creado exitosamente. Selecciona el usuario que atiende el ticket:", reply_markup=reply_markup_dict)
            else:
                send_telegram_message(chat_id, "Error creando usuario. Intenta de nuevo.")
            return JsonResponse({"ok": True})

        # Comentario
        if state["step"] == "comentario":
            state["data"]["comentario"] = text
            # Crear ticket
            tipo_soporte_id = state["data"].get("tipo_soporte_id")
            comentario = state["data"].get("comentario")
            usuario_id = state["data"].get("usuario_id")
            area_id = state["data"].get("area_id")
            soporte_id = state["data"].get("soporte_id")
            ticket = crear_ticket(tipo_soporte_id, comentario, usuario_id, area_id, soporte_id)
            ticket_id = getattr(ticket, "id", None) or getattr(ticket, "pk", None)
            send_telegram_message(chat_id, f"Ticket creado con ID: {ticket_id}")
            # Limpiar estado
            user_states[chat_id] = {"step": None, "data": {}}
            return JsonResponse({"ok": True})

        # Si no se reconoce el comando o paso
        ayuda = (
            "Comando no reconocido.\n"
            "Usa: /crearticket para iniciar el flujo interactivo."
        )
    send_telegram_message(chat_id, ayuda)
    return JsonResponse({"ok": True})
