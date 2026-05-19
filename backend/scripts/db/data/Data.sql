-- Data for Table `Roles`
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM "Dev".rol WHERE "nombreRol" = 'Administrador') THEN
        INSERT INTO "Dev".rol
        ("nombreRol", "estado", "usuarioCreacion", "fechaCreacion", "usuarioModificacion", "fechaModificacion")
        VALUES('Administrador', 'A', 'Script', now(), 'admin', now());
        
        RAISE NOTICE 'Rol Administrador insertado correctamente.';
    ELSE 
        RAISE NOTICE 'El rol Administrador ya existe, no se insertará.';
    END IF;
END $$;

-- Data para Tabla `Empresa`
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM "Dev".empresa WHERE "nombreEmpresa" = 'BIOPOSE') THEN
        INSERT INTO "Dev".empresa
        ("nombreEmpresa", "estado", "usuarioCreacion", "fechaCreacion", "usuarioModificacion", "fechaModificacion")
        VALUES('BIOPOSE', 'A', 'Script', now(), 'admin', now());
        
        RAISE NOTICE 'Empresa BIOPOSE insertada correctamente.';
    ELSE 
        RAISE NOTICE 'La empresa BIOPOSE ya existe, no se insertará.';
    END IF;
END $$;