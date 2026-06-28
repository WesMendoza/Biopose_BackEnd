from django.db import models
from apps.users.models import AuditableModel
from apps.gestionEmpresas.models import Empresa, Rol

class MenuOpcion(AuditableModel):
    idOption = models.AutoField(primary_key=True)
    nombreOption = models.CharField(db_column='nombreOption', max_length=100, null=True, blank=True)
    ruta = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'menuOption'
        managed = False


class RolOption(AuditableModel):
    idRolOption = models.AutoField(primary_key=True)
    idRol = models.ForeignKey(Rol, models.DO_NOTHING, db_column='idRol', null=True, blank=True)
    idOption = models.ForeignKey(MenuOpcion, models.DO_NOTHING, db_column='idOption', null=True, blank=True)
    idEmpresa = models.ForeignKey(Empresa, models.DO_NOTHING, db_column='idEmpresa', null=True, blank=True)

    class Meta:
        db_table = 'rolOption'
        managed = False

class ParametroCabecera(models.Model):
    idParametrosCabecera = models.AutoField(primary_key=True, db_column='idParametrosCabecera')
    idEmpresa = models.IntegerField(null=True, blank=True, db_column='idEmpresa') 
    nombreParametro = models.CharField(max_length=150, db_column='nombreParametro')
    codigoParametro = models.CharField(max_length=50, unique=True, db_column='codigoParametro')
    estado = models.CharField(max_length=1, default='A')
    
    usuarioCreacion = models.CharField(max_length=50, default='Sistema', db_column='usuarioCreacion')
    fechaCreacion = models.DateTimeField(auto_now_add=True, db_column='fechaCreacion')
    usuarioModificacion = models.CharField(max_length=50, null=True, blank=True, db_column='usuarioModificacion')
    fechaModificacion = models.DateTimeField(auto_now=True, null=True, blank=True, db_column='fechaModificacion')

    class Meta:
        # AQUI ESTA LA CORRECCION CLAVE (con "s")
        db_table = 'parametrosCabecera' 
        managed = False

class ParametroDetalle(models.Model):
    idParametroDetalle = models.AutoField(primary_key=True, db_column='idParametroDetalle')
    # Y aquí nos aseguramos que el ForeignKey use la columna correcta de la BD
    codigoParametro = models.ForeignKey(ParametroCabecera, to_field='codigoParametro', on_delete=models.CASCADE, db_column='codigoParametro')
    nombreDetalle = models.CharField(max_length=100, db_column='nombreDetalle')
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    valor = models.CharField(max_length=500)
    estado = models.CharField(max_length=1, default='A')
    
    usuarioCreacion = models.CharField(max_length=50, default='Sistema', db_column='usuarioCreacion')
    fechaCreacion = models.DateTimeField(auto_now_add=True, db_column='fechaCreacion')
    usuarioModificacion = models.CharField(max_length=50, null=True, blank=True, db_column='usuarioModificacion')
    fechaModificacion = models.DateTimeField(auto_now=True, null=True, blank=True, db_column='fechaModificacion')

    class Meta:
        # AQUI ESTA LA OTRA CORRECCION (asegúrate de que coincida con tu BD, si es singular o plural)
        db_table = 'parametroDetalle' 
        managed = False