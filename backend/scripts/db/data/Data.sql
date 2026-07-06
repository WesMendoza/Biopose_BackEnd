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

-- 3. Data para Tabla `menuOption` (Opciones de Menú Base)
    IF NOT EXISTS (SELECT 1 FROM "Dev"."menuOption") THEN
        INSERT INTO "Dev"."menuOption" 
        ("nombreOption", "ruta", "estado", "usuarioCreacion") 
        VALUES
        ('Dashboard', '/app/dashboard', 'A', 'Sistema'),
        ('Gestión de Usuarios', '/app/users', 'A', 'Sistema'),
        ('Gestión de Empresas', '/app/gestion-empresas', 'A', 'Sistema'),
        ('Gestión de Roles', '/app/gestion-roles', 'A', 'Sistema'),
        ('Configuración de rutas', '/app/pose/routes', 'A', 'Sistema'),
        ('Detección en imagen', '/app/pose/image', 'A', 'Sistema'),
        ('Detección en video', '/app/pose/video', 'A', 'Sistema'),
        ('Verifica tus imágenes', '/app/pose/verify', 'A', 'Sistema'),
        ('Video (Individual)', '/app/events/individual/video', 'A', 'Sistema'),
        ('En vivo (Individual)', '/app/events/individual/live', 'A', 'Sistema'),
        ('Video (Multipersona)', '/app/events/multi/video', 'A', 'Sistema'),
        ('En vivo (Multipersona)', '/app/events/multi/live', 'A', 'Sistema');
        RAISE NOTICE 'Opciones de menú base insertadas correctamente.';
    END IF;
END $$;