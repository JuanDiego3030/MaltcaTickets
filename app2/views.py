

from django.shortcuts import render, redirect
from django.contrib import messages
from app2.models import TipoSoporte, Usuario, Area
from app1.models import User
from app2.crud import crear_ticket as crear_ticket_crud, obtener_tickets

def crear_ticket(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'Debe iniciar sesión primero')
        return redirect('login')
    try:
        usuario_atiende = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'Usuario no encontrado')
        return redirect('login')

    # Crear usuario atendido
    if request.method == 'POST' and 'crear_usuario' in request.POST:
        nombre = request.POST.get('nuevo_nombre')
        cedula = request.POST.get('nuevo_cedula')
        if nombre:
            Usuario.objects.create(nombre=nombre, cedula=cedula)
            messages.success(request, 'Usuario creado exitosamente')
            return redirect(request.path + '?abrir_modal_ticket=1')
        else:
            messages.error(request, 'El nombre es obligatorio para usuario')

    # Crear área
    if request.method == 'POST' and 'crear_area' in request.POST:
        nombre = request.POST.get('nuevo_area_nombre')
        if nombre:
            Area.objects.create(nombre=nombre)
            messages.success(request, 'Área creada exitosamente')
            return redirect('crear_ticket')
        else:
            messages.error(request, 'El nombre es obligatorio para área')

    # Crear tipo de soporte
    if request.method == 'POST' and 'crear_tipo_soporte' in request.POST:
        nombre = request.POST.get('nuevo_tipo_nombre')
        if nombre:
            TipoSoporte.objects.create(nombre=nombre)
            messages.success(request, 'Tipo de soporte creado exitosamente')
            return redirect('crear_ticket')
        else:
            messages.error(request, 'El nombre es obligatorio para tipo de soporte')

    # Crear ticket
    if request.method == 'POST' and 'crear_ticket' in request.POST:
        tipo_soporte_id = request.POST.get('tipo_soporte')
        comentario = request.POST.get('comentario')
        usuario_id = request.POST.get('usuario')
        area_id = request.POST.get('area')
        atendido_por_id = request.POST.get('atendido_por')
        if tipo_soporte_id and comentario and usuario_id and area_id and atendido_por_id:
            ticket = crear_ticket_crud(
                tipo_soporte_id=tipo_soporte_id,
                comentario=comentario,
                usuario_id=usuario_id,
                area_id=area_id,
                atendido_por_id=atendido_por_id
            )
            messages.success(request, 'Ticket creado exitosamente')
            return redirect('crear_ticket')
        else:
            messages.error(request, 'Todos los campos son obligatorios')

    tipos_soporte = TipoSoporte.objects.all()
    usuarios = Usuario.objects.all()
    areas = Area.objects.all()
    tickets = obtener_tickets()
    from app2.models import Soporte
    soportes = Soporte.objects.all()

    # Filtros por usuario, tipo y fecha
    usuario_filtro = request.GET.get('usuario')
    tipo_filtro = request.GET.get('tipo_soporte')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    if usuario_filtro:
        tickets = tickets.filter(usuario_id=usuario_filtro)
    if tipo_filtro:
        tickets = tickets.filter(tipo_soporte_id=tipo_filtro)
    if fecha_inicio:
        tickets = tickets.filter(fecha_creacion__gte=fecha_inicio)
    if fecha_fin:
        tickets = tickets.filter(fecha_creacion__lte=fecha_fin)

    return render(request, 'Ticket.html', {
        'user': usuario_atiende,
        'tipos_soporte': tipos_soporte,
        'usuarios': usuarios,
        'usuarios_soporte': soportes,
        'areas': areas,
        'tickets': tickets,
    })

