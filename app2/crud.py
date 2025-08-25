# CRUD para Usuario
def obtener_usuarios():
    return Usuario.objects.all()

def obtener_usuario(usuario_id):
    return Usuario.objects.get(id=usuario_id)

def actualizar_usuario(usuario_id, **kwargs):
    Usuario.objects.filter(id=usuario_id).update(**kwargs)
    return Usuario.objects.get(id=usuario_id)

def eliminar_usuario(usuario_id):
    Usuario.objects.filter(id=usuario_id).delete()
from .models import Ticket, TipoSoporte, Usuario, Area
from django.db import transaction

# CRUD para Ticket
def crear_ticket(tipo_soporte_id, comentario, usuario_id, area_id, atendido_por_id, solucion=None, tipo_problema=None):
    with transaction.atomic():
        ticket = Ticket.objects.create(
            tipo_soporte_id=tipo_soporte_id,
            comentario=comentario,
            usuario_id=usuario_id,
            area_id=area_id,
            atendido_por_id=atendido_por_id,
            solucion=solucion,
            tipo_problema=tipo_problema
        )
    return ticket

def obtener_tickets():
    return Ticket.objects.select_related('tipo_soporte', 'usuario', 'area', 'atendido_por').all()

def obtener_ticket(ticket_id):
    return Ticket.objects.select_related('tipo_soporte', 'usuario', 'area', 'atendido_por').get(id=ticket_id)

def actualizar_ticket(ticket_id, tipo_soporte_id=None, comentario=None, usuario_id=None, area_id=None, atendido_por_id=None, solucion=None, tipo_problema=None):
    update_fields = {}
    if tipo_soporte_id is not None:
        update_fields['tipo_soporte_id'] = tipo_soporte_id
    if comentario is not None:
        update_fields['comentario'] = comentario
    if usuario_id is not None:
        update_fields['usuario_id'] = usuario_id
    if area_id is not None:
        update_fields['area_id'] = area_id
    if atendido_por_id is not None:
        update_fields['atendido_por_id'] = atendido_por_id
    if solucion is not None:
        update_fields['solucion'] = solucion
    if tipo_problema is not None:
        update_fields['tipo_problema'] = tipo_problema
    Ticket.objects.filter(id=ticket_id).update(**update_fields)
    return Ticket.objects.get(id=ticket_id)

def eliminar_ticket(ticket_id):
    Ticket.objects.filter(id=ticket_id).delete()
