-- Script para modificar la tabla menuOption añadiendo idEmpresa y ruta
-- Fase: Implementación de Opciones de Menú por Empresa

SET search_path TO "Dev";

ALTER TABLE "menuOption" 
ADD COLUMN IF NOT EXISTS ruta VARCHAR(255);

ALTER TABLE "rolOption" 
ADD COLUMN IF NOT EXISTS "idEmpresa" INT REFERENCES empresa("idEmpresa") ON DELETE CASCADE,
ADD COLUMN IF NOT EXISTS "estado" CHAR(1),
ADD COLUMN IF NOT EXISTS "usuarioCreacion" VARCHAR(50),
ADD COLUMN IF NOT EXISTS "fechaCreacion" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS "usuarioModificacion" VARCHAR(50),
ADD COLUMN IF NOT EXISTS "fechaModificacion" TIMESTAMP;
ADD COLUMN IF NOT EXISTS "descripcion" VARCHAR(255);

-- Insertamos todas las pantallas de tu sistema
INSERT INTO "menuOption" ("nombreOption", "ruta", "estado", "usuarioCreacion") 
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