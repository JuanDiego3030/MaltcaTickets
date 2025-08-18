from app2.models import Ticket, TipoSoporte, Usuario, Area, Soporte
from django.db import transaction

def crear_ticket(tipo_soporte_id, comentario, usuario_id, area_id, atendido_por_id=None):
    with transaction.atomic():
        ticket = Ticket.objects.create(
            tipo_soporte_id=tipo_soporte_id,
            comentario=comentario,
            usuario_id=usuario_id,
            area_id=area_id,
            atendido_por_id=atendido_por_id
        )
    return ticket

def obtener_tipos_soporte():
    from app2.models import TipoSoporte
    return list(TipoSoporte.objects.all())

def obtener_areas():
    from app2.models import Area
    return list(Area.objects.all())

def obtener_usuarios():
    from app2.models import Usuario
    return list(Usuario.objects.all())
