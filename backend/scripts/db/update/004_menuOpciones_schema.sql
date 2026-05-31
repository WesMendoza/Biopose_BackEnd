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