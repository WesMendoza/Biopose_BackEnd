-- Script de actualizacion: 002_image_upload.sql
-- Fase 3: Agrega tabla para llevar el registro de las imagenes subidas y procesadas

SET search_path TO "Dev";

CREATE TABLE IF NOT EXISTS "analysisImageUpload" (
  "idImageUpload" SERIAL PRIMARY KEY,
  "idUsuario" INT NULL REFERENCES users("idUsuario") ON DELETE SET NULL,
  "idEmpresa" INT NULL REFERENCES empresa("idEmpresa") ON DELETE SET NULL,
  "nombreOriginal" VARCHAR(255) NOT NULL,
  "rutaArchivoOriginal" VARCHAR(500) NOT NULL,
  "rutaArchivoProcesado" VARCHAR(500) NULL,
  "tamanioBytes" BIGINT NOT NULL CHECK ("tamanioBytes" >= 0),
  estado VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (estado IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')),
  "fechaCarga" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "fechaProcesamiento" TIMESTAMP NULL
);

CREATE INDEX IF NOT EXISTS ix_image_estado ON "analysisImageUpload" (estado);
CREATE INDEX IF NOT EXISTS ix_image_fechacarga ON "analysisImageUpload" ("fechaCarga");
