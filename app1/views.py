from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from datetime import datetime
import matplotlib.pyplot as plt
import io, base64
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from .models import User
from app2.models import Ticket, Usuario, Area, TipoSoporte, Soporte


def exportar_reporte_pdf(request):


    def pie_chart(labels, sizes, colors=None, empty=False):
        fig, ax = plt.subplots(figsize=(2.2,2.2))  # Más pequeño y cuadrado
        if empty or sum(sizes) == 0:
            # Gráfico vacío: todo rojo, leyenda 'Sin tickets este mes'
            ax.pie([1], labels=['Sin tickets este mes'], colors=['#dc3545'], startangle=90, textprops={'color':'#dc3545','fontsize':12})
        else:
            ax.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90, textprops={'fontsize':10})
        ax.axis('equal')
        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png', bbox_inches='tight', transparent=True)
        plt.close(fig)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        return f'data:image/png;base64,{img_base64}'

    # Colores para los gráficos
    palette = ['#0d6efd', '#198754', '#ffc107', '#fd7e14', '#6f42c1', '#dc3545', '#0dcaf0']

    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    try:
        fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d') if fecha_inicio else None
        fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d') if fecha_fin else None
    except Exception:
        fecha_inicio_dt = fecha_fin_dt = None



    tickets = Ticket.objects.all()
    if fecha_inicio_dt:
        tickets = tickets.filter(fecha_creacion__gte=fecha_inicio_dt)
    if fecha_fin_dt:
        tickets = tickets.filter(fecha_creacion__lte=fecha_fin_dt)

    tickets_reporte = tickets.order_by('-fecha_creacion')
    # Calcular estadísticas de tipo de problema (falla)
    TIPO_PROBLEMA_CHOICES = dict(Ticket.TIPO_PROBLEMA_CHOICES)
    causas = list(TIPO_PROBLEMA_CHOICES.values())
    causas_falla_stats = []
    total_tickets_causa = tickets.count()
    from collections import Counter, defaultdict
    causas_counter = Counter()
    for t in tickets:
        causa = TIPO_PROBLEMA_CHOICES.get(t.tipo_problema, 'Sin especificar')
        causas_counter[causa] += 1
    for causa in causas:
        cantidad = causas_counter.get(causa, 0)
        porcentaje = (cantidad/total_tickets_causa*100) if total_tickets_causa else 0
        causas_falla_stats.append((causa, cantidad, porcentaje))
    causas_falla_stats.sort(key=lambda x: x[2], reverse=True)

    areas = Area.objects.all()
    # Porcentaje de tipo de falla por área
    area_fallas = []
    for a in areas:
        area_tickets = tickets.filter(area=a)
        total_area = area_tickets.count()
        fallas_area = []
        for key, label in TIPO_PROBLEMA_CHOICES.items():
            cantidad = area_tickets.filter(tipo_problema=key).count()
            porcentaje = (cantidad/total_area*100) if total_area else 0
            fallas_area.append({'tipo': label, 'cantidad': cantidad, 'porcentaje': porcentaje})
        fallas_area.sort(key=lambda x: x['porcentaje'], reverse=True)
        area_fallas.append({'area': a.nombre, 'fallas': fallas_area, 'total': total_area})
    total_tickets = tickets.count()

    soportes = Soporte.objects.all()
    soportes_stats = []
    total_tickets_atendidos = tickets.exclude(atendido_por=None).count()
    for s in soportes:
        cantidad = tickets.filter(atendido_por=s).count()
        porcentaje = (cantidad/total_tickets_atendidos*100) if total_tickets_atendidos else 0
        soportes_stats.append((s.nombre, cantidad, porcentaje))
    soportes_stats.sort(key=lambda x: x[2], reverse=True)

    usuarios = Usuario.objects.all()
    areas = Area.objects.all()
    tipos_soporte = TipoSoporte.objects.all()

    usuarios_stats = []
    for u in usuarios:
        cantidad = tickets.filter(usuario=u).count()
        porcentaje = (cantidad/total_tickets*100) if total_tickets else 0
        usuarios_stats.append((u.nombre, cantidad, porcentaje))
    usuarios_stats.sort(key=lambda x: x[2], reverse=True)

    areas_stats = []
    for a in areas:
        cantidad = tickets.filter(area=a).count()
        porcentaje = (cantidad/total_tickets*100) if total_tickets else 0
        areas_stats.append((a.nombre, cantidad, porcentaje))
    areas_stats.sort(key=lambda x: x[2], reverse=True)

    tipos_stats = []
    for t in tipos_soporte:
        cantidad = tickets.filter(tipo_soporte=t).count()
        porcentaje = (cantidad/total_tickets*100) if total_tickets else 0
        tipos_stats.append((t.nombre, cantidad, porcentaje))
    tipos_stats.sort(key=lambda x: x[2], reverse=True)

    resumen_areas = []
    for a in areas:
        cantidad = tickets.filter(area=a).count()
        porcentaje = (cantidad/total_tickets*100) if total_tickets else 0
        tipos_area = []
        for t in tipos_soporte:
            cantidad_tipo = tickets.filter(area=a, tipo_soporte=t).count()
            porcentaje_tipo = (cantidad_tipo/cantidad*100) if cantidad else 0
            tipos_area.append({
                'nombre': t.nombre,
                'cantidad': cantidad_tipo,
                'porcentaje': porcentaje_tipo
            })
        tipos_area.sort(key=lambda x: x['porcentaje'], reverse=True)
        # Fallas por área
        area_tickets = tickets.filter(area=a)
        total_area = area_tickets.count()
        fallas_area = []
        for key, label in TIPO_PROBLEMA_CHOICES.items():
            cantidad_falla = area_tickets.filter(tipo_problema=key).count()
            porcentaje_falla = (cantidad_falla/total_area*100) if total_area else 0
            fallas_area.append({'tipo': label, 'cantidad': cantidad_falla, 'porcentaje': porcentaje_falla})
        fallas_area.sort(key=lambda x: x['porcentaje'], reverse=True)
        resumen_areas.append({
            'nombre': a.nombre,
            'cantidad': cantidad,
            'porcentaje': porcentaje,
            'tipos': tipos_area,
            'sin_tickets': cantidad == 0,
            'fallas': fallas_area
        })

    html_string = render_to_string('reporte_pdf.html', {
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'total_tickets': total_tickets,
        'usuarios_stats': usuarios_stats,
        'areas_stats': areas_stats,
        'tipos_stats': tipos_stats,
        'resumen_areas': resumen_areas,
        'soportes_stats': soportes_stats,
        'tickets_reporte': tickets_reporte,
        'causas_falla_stats': causas_falla_stats,
        'TIPO_PROBLEMA_CHOICES': TIPO_PROBLEMA_CHOICES,
    })
    html = HTML(string=html_string)
    pdf = html.write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_tickets.pdf"'
    return response



def login(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        password = request.POST.get('password', '')

        try:
            user = User.objects.get(nombre=nombre)
            if user.bloqueado:
                messages.error(request, 'Usuario bloqueado')
            elif user.password == password or check_password(password, user.password):
                request.session['user_id'] = user.id # type: ignore
                return redirect('panel_control')
            else:
                messages.error(request, 'Contraseña incorrecta')
            return render(request, 'login.html')
        except User.DoesNotExist:
            messages.error(request, 'Usuario no encontrado')
            return render(request, 'login.html')

    return render(request, 'login.html')

def panel_control(request):
    from app2.models import Soporte

    # Estadísticas por soporte (tickets atendidos por cada quien)
    soportes = Soporte.objects.all()
    soportes_stats = []
    total_tickets_atendidos = Ticket.objects.exclude(atendido_por=None).count()
    for s in soportes:
        cantidad = Ticket.objects.filter(atendido_por=s).count()
        porcentaje = (cantidad/total_tickets_atendidos*100) if total_tickets_atendidos else 0
        soportes_stats.append((s.nombre, cantidad, porcentaje))
    import json

    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, 'Debe iniciar sesión primero')
        return redirect('login')
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'Usuario no encontrado')
        return redirect('login')
    
    total_tickets = Ticket.objects.count()

    # Estadísticas por usuario atendido
    usuarios = Usuario.objects.all()
    usuarios_stats = []
    for u in usuarios:
        cantidad = Ticket.objects.filter(usuario=u).count()
        porcentaje = (cantidad/total_tickets*100) if total_tickets else 0
        usuarios_stats.append((u.nombre, cantidad, porcentaje))

    areas = Area.objects.all()
    areas_stats = []
    for a in areas:
        cantidad = Ticket.objects.filter(area=a).count()
        porcentaje = (cantidad/total_tickets*100) if total_tickets else 0
        areas_stats.append((a.nombre, cantidad, porcentaje))

    tipos_soporte = TipoSoporte.objects.all()
    tipos_stats = []
    for t in tipos_soporte:
        cantidad = Ticket.objects.filter(tipo_soporte=t).count()
        porcentaje = (cantidad/total_tickets*100) if total_tickets else 0
        tipos_stats.append((t.nombre, cantidad, porcentaje))

    # Nueva estructura: tickets por usuario y tipo
    tickets_por_usuario_tipo = {}
    for u in usuarios:
        tickets_por_usuario_tipo[u.nombre] = {}
        for t in tipos_soporte:
            count = Ticket.objects.filter(usuario=u, tipo_soporte=t).count()
            tickets_por_usuario_tipo[u.nombre][t.nombre] = count

    usuarios_labels = [u[0] for u in usuarios_stats]
    usuarios_porcentajes = [round(u[2], 2) for u in usuarios_stats]
    areas_labels = [a[0] for a in areas_stats]
    areas_porcentajes = [round(a[2], 2) for a in areas_stats]
    tipos_labels = [t[0] for t in tipos_stats]
    tipos_porcentajes = [round(t[2], 2) for t in tipos_stats]

    context = {
        'user': user,
        'total_tickets': total_tickets,
        'usuarios_stats': usuarios_stats,
        'areas_stats': areas_stats,
        'tipos_stats': tipos_stats,
        'soportes_stats': soportes_stats,
        'tickets_por_usuario_tipo': tickets_por_usuario_tipo,
        'usuarios_labels_json': json.dumps(usuarios_labels),
        'usuarios_porcentajes_json': json.dumps(usuarios_porcentajes),
        'areas_labels_json': json.dumps(areas_labels),
        'areas_porcentajes_json': json.dumps(areas_porcentajes),
        'tipos_labels_json': json.dumps(tipos_labels),
        'tipos_porcentajes_json': json.dumps(tipos_porcentajes),
    }
    return render(request, 'control.html', context)

def logout(request):
    request.session.flush()
    return redirect('login')