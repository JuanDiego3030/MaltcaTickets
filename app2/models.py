from django.db import models


class TipoSoporte(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre



class Usuario(models.Model):
    nombre = models.CharField(max_length=100)
    cedula = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.nombre

# Nuevo modelo para usuarios de soporte
class Soporte(models.Model):
    nombre = models.CharField(max_length=100, default='Soporte')

    def __str__(self):
        return self.nombre


class Area(models.Model):
    nombre = models.CharField(max_length=100, default='')

    def __str__(self):
        return self.nombre

class Ticket(models.Model):
    tipo_soporte = models.ForeignKey(TipoSoporte, on_delete=models.CASCADE)
    comentario = models.TextField()
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='tickets_recibidos')
    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    atendido_por = models.ForeignKey(Soporte, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets_atendidos')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    solucion = models.TextField(blank=True, null=True)
    TIPO_PROBLEMA_CHOICES = [
        ('usuario', 'Usuario'),
        ('sistema', 'Sistema'),
        ('hardware', 'Hardware'),
    ]
    tipo_problema = models.CharField(max_length=20, choices=TIPO_PROBLEMA_CHOICES, default='usuario')

    def __str__(self):
        return f"Ticket #{self.id} - {self.tipo_soporte.nombre}" # pyright: ignore[reportAttributeAccessIssue]
