-- 1. Data para Tabla `Empresa` (Empresa Base)
DO $$ 
DECLARE
    v_id_empresa INT;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM "Dev".empresa WHERE "nombreEmpresa" = 'BIOPOSE') THEN
        INSERT INTO "Dev".empresa
        ("nombreEmpresa", "estado", "usuarioCreacion", "fechaCreacion", "usuarioModificacion", "fechaModificacion")
        VALUES('BIOPOSE', 'A', 'Script', now(), 'admin', now()) RETURNING "idEmpresa" INTO v_id_empresa;
        RAISE NOTICE 'Empresa BIOPOSE insertada correctamente con ID %.', v_id_empresa;
    ELSE 
        SELECT "idEmpresa" INTO v_id_empresa FROM "Dev".empresa WHERE "nombreEmpresa" = 'BIOPOSE';
        RAISE NOTICE 'La empresa BIOPOSE ya existe (ID %).', v_id_empresa;
    END IF;

-- 2. Data for Table `Roles` asociados a la Empresa Base
    IF NOT EXISTS (SELECT 1 FROM "Dev".rol WHERE "nombreRol" = 'Administrador' AND "idEmpresa" = v_id_empresa) THEN
        INSERT INTO "Dev".rol
        ("nombreRol", "estado", "usuarioCreacion", "fechaCreacion", "usuarioModificacion", "fechaModificacion", "idEmpresa")
        VALUES('Administrador', 'A', 'Script', now(), 'admin', now(), v_id_empresa);
        RAISE NOTICE 'Rol Administrador para BIOPOSE insertado correctamente.';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM "Dev".rol WHERE "nombreRol" = 'Invitado' AND "idEmpresa" = v_id_empresa) THEN
        INSERT INTO "Dev".rol
        ("nombreRol", "estado", "usuarioCreacion", "fechaCreacion", "usuarioModificacion", "fechaModificacion", "idEmpresa")
        VALUES('Invitado', 'A', 'Script', now(), 'admin', now(), v_id_empresa);
        RAISE NOTICE 'Rol Invitado para BIOPOSE insertado correctamente.';
    END IF;
END $$;