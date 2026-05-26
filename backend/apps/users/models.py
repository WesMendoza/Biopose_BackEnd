from django.db import models

class AuditableModel(models.Model):
    """
    Modelo base abstracto que incluye campos de auditoría comunes a casi todas las tablas.
    """
    estado = models.CharField(max_length=1, default='A')
    usuarioCreacion = models.CharField(db_column='usuarioCreacion', max_length=50, null=True, blank=True)
    fechaCreacion = models.DateTimeField(db_column='fechaCreacion', auto_now_add=True, null=True, blank=True)
    usuarioModificacion = models.CharField(db_column='usuarioModificacion', max_length=50, null=True, blank=True)
    fechaModificacion = models.DateTimeField(db_column='fechaModificacion', auto_now=True, null=True, blank=True)

    class Meta:
        abstract = True

class Users(AuditableModel):
    idUsuario = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, null=True, blank=True)
    apellido = models.CharField(max_length=100, null=True, blank=True)
    cedula = models.CharField(max_length=20, null=True, blank=True)
    correo = models.CharField(max_length=150, unique=True, null=True, blank=True)
    password = models.CharField(max_length=255, null=True, blank=True)
    ultimoIngreso = models.DateTimeField(null=True, blank=True)

    @property
    def is_authenticated(self):
        return True

    class Meta:
        db_table = 'users'
        managed = False

