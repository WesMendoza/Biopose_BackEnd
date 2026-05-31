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
