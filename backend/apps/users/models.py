from django.db import models

class AuditableModel(models.Model):
    """
    Modelo base abstracto que incluye campos de auditoría comunes a casi todas las tablas.
    """
    estado = models.CharField(max_length=1, default='A')
    usuarioCreacion = models.CharField(max_length=50, null=True, blank=True)
    fechaCreacion = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    usuarioModificacion = models.CharField(max_length=50, null=True, blank=True)
    fechaModificacion = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        abstract = True

class Empresa(AuditableModel):
    idEmpresa = models.AutoField(primary_key=True)
    codigoEmpresa = models.CharField(db_column='codigoEmpresa', max_length=50, null=True, blank=True)
    nombreEmpresa = models.CharField(max_length=150, null=True, blank=True)
    direccion = models.CharField(max_length=255, null=True, blank=True)
    ruc = models.CharField(db_column='ruc', max_length=20, null=True, blank=True)

    class Meta:
        db_table = 'empresa'
        managed = False  # Para que se mapee en solo lectura a las tablas SQL manuales


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


class Rol(AuditableModel):
    idRol = models.AutoField(primary_key=True)
    nombreRol = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = 'rol'
        managed = False


class Menuoption(AuditableModel):
    idOption = models.AutoField(primary_key=True)
    nombreOption = models.CharField(db_column='nombreOption', max_length=100, null=True, blank=True)

    class Meta:
        db_table = 'menuOption'
        managed = False


class EmpresaUsuarioRol(AuditableModel):
    idEmpresaUsuarioRol = models.AutoField(primary_key=True)
    idEmpresa = models.ForeignKey(Empresa, models.DO_NOTHING, db_column='idEmpresa', null=True, blank=True)
    idUsuario = models.ForeignKey(Users, models.DO_NOTHING, db_column='idUsuario', null=True, blank=True)
    idRol = models.ForeignKey(Rol, models.DO_NOTHING, db_column='idRol', null=True, blank=True)

    class Meta:
        db_table = 'empresaUsuarioRol'
        managed = False


class RolOption(models.Model):
    idRolOption = models.AutoField(primary_key=True)
    idRol = models.ForeignKey(Rol, models.DO_NOTHING, db_column='idRol', null=True, blank=True)
    idOption = models.ForeignKey(Menuoption, models.DO_NOTHING, db_column='idOption', null=True, blank=True)

    class Meta:
        db_table = 'rolOption'
        managed = False


class ParametrosCabecera(AuditableModel):
    idParametrosCabecera = models.AutoField(primary_key=True)
    idEmpresa = models.ForeignKey(Empresa, models.DO_NOTHING, db_column='idEmpresa', null=True, blank=True)
    nombreParametro = models.CharField(max_length=100, null=True, blank=True)
    codigoParametro = models.CharField(db_column='codigoParametro', max_length=50, unique=True, null=True, blank=True)

    class Meta:
        db_table = 'parametrosCabecera'
        managed = False


class ParametroDetalle(AuditableModel):
    idParametroDetalle = models.AutoField(primary_key=True)
    codigoParametro = models.ForeignKey(ParametrosCabecera, models.DO_NOTHING, db_column='codigoParametro', to_field='codigoParametro', null=True, blank=True)
    nombreDetalle = models.CharField(max_length=100, null=True, blank=True)
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    valor = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'parametroDetalle'
        managed = False
