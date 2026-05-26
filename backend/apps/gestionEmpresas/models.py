from django.db import models
from apps.users.models import Users, AuditableModel

class Empresa(AuditableModel):
    idEmpresa = models.AutoField(primary_key=True, db_column='idEmpresa')
    codigoEmpresa = models.CharField(db_column='codigoEmpresa', max_length=50, null=True, blank=True)
    nombreEmpresa = models.CharField(db_column='nombreEmpresa', max_length=150, null=True, blank=True)
    direccion = models.CharField(max_length=255, null=True, blank=True)
    ruc = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        db_table = 'empresa'
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
