-- ==========================================
-- SCRIPT: BIOPOSE DB 
-- ==========================================

-- 1. CREACIÓN DE ESQUEMA
CREATE SCHEMA IF NOT EXISTS "Dev";
SET search_path TO "Dev";

-- ==========================================
-- 2. CREACIÓN DE TABLAS MAESTRAS (Sin dependencias)
-- ==========================================
CREATE TABLE empresa (
  "idEmpresa" SERIAL PRIMARY KEY,
  "codigoEmpresa" VARCHAR(50),
  "nombreEmpresa" VARCHAR(150),
  direccion VARCHAR(255),
  ruc VARCHAR(20),
  estado CHAR(1),
  "usuarioCreacion" VARCHAR(50),
  "fechaCreacion" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  "usuarioModificacion" VARCHAR(50),
  "fechaModificacion" TIMESTAMP
);

CREATE TABLE users (
  "idUsuario" SERIAL PRIMARY KEY,
  nombre VARCHAR(100),
  apellido VARCHAR(100),
  cedula VARCHAR(20),
  correo VARCHAR(150) UNIQUE,
  password VARCHAR(255),
  estado CHAR(1),
  "usuarioCreacion" VARCHAR(50),
  "fechaCreacion" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  "usuarioModificacion" VARCHAR(50),
  "fechaModificacion" TIMESTAMP,
  "ultimoIngreso" TIMESTAMP
);

CREATE TABLE rol (
  "idRol" SERIAL PRIMARY KEY,
  "idEmpresa" INT REFERENCES empresa("idEmpresa") ON DELETE CASCADE,
  "nombreRol" VARCHAR(100),
  estado CHAR(1),
  "usuarioCreacion" VARCHAR(50),
  "fechaCreacion" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  "usuarioModificacion" VARCHAR(50),
  "fechaModificacion" TIMESTAMP
);

CREATE TABLE "menuOption" (
  "idOption" SERIAL PRIMARY KEY,
  "nombreOption" VARCHAR(100),
  ruta VARCHAR(255),
  estado CHAR(1),
  "usuarioCreacion" VARCHAR(50),
  "fechaCreacion" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  "usuarioModificacion" VARCHAR(50),
  "fechaModificacion" TIMESTAMP
);

CREATE TABLE "systemParameter" (
  "idParameter" SERIAL PRIMARY KEY,
  codigo VARCHAR(100) NOT NULL UNIQUE,
  valor VARCHAR(500) NOT NULL,
  descripcion VARCHAR(255) NULL,
  tipo VARCHAR(20) NOT NULL DEFAULT 'STRING' CHECK (tipo IN ('INT', 'FLOAT', 'STRING', 'BOOL'))
);

-- ==========================================
-- 3. TABLAS TRANSACCIONALES
-- ==========================================
CREATE TABLE "empresaUsuarioRol" (
  "idEmpresaUsuarioRol" SERIAL PRIMARY KEY,
  "idEmpresa" INT REFERENCES empresa("idEmpresa") ON DELETE CASCADE,
  "idUsuario" INT REFERENCES users("idUsuario") ON DELETE CASCADE,
  "idRol" INT REFERENCES rol("idRol") ON DELETE CASCADE,
  estado CHAR(1),
  "usuarioCreacion" VARCHAR(50),
  "fechaCreacion" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  "usuarioModificacion" VARCHAR(50),
  "fechaModificacion" TIMESTAMP
);

CREATE TABLE "rolOption" (
  "idRolOption" SERIAL PRIMARY KEY,
  "idEmpresa" INT REFERENCES empresa("idEmpresa") ON DELETE CASCADE,
  "idRol" INT REFERENCES rol("idRol") ON DELETE CASCADE,
  "idOption" INT REFERENCES "menuOption"("idOption") ON DELETE CASCADE,
  estado CHAR(1),
  "usuarioCreacion" VARCHAR(50),
  "fechaCreacion" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  "usuarioModificacion" VARCHAR(50),
  "fechaModificacion" TIMESTAMP
);

CREATE TABLE "parametrosCabecera" (
  "idParametrosCabecera" SERIAL PRIMARY KEY,
  "idEmpresa" INT REFERENCES empresa("idEmpresa") ON DELETE CASCADE,
  "nombreParametro" VARCHAR(100),
  "codigoParametro" VARCHAR(50) UNIQUE,
  estado CHAR(1),
  "usuarioCreacion" VARCHAR(50),
  "fechaCreacion" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  "usuarioModificacion" VARCHAR(50),
  "fechaModificacion" TIMESTAMP
);

CREATE TABLE "parametroDetalle" (
  "idParametroDetalle" SERIAL PRIMARY KEY,
  "codigoParametro" VARCHAR(50) REFERENCES "parametrosCabecera"("codigoParametro") ON DELETE CASCADE, -- ¡CORREGIDO!
  "nombreDetalle" VARCHAR(100),
  descripcion VARCHAR(255),
  valor VARCHAR(255),
  estado CHAR(1),
  "usuarioCreacion" VARCHAR(50),
  "fechaCreacion" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  "usuarioModificacion" VARCHAR(50),
  "fechaModificacion" TIMESTAMP
);

-- ==========================================
-- 4. TABLAS DE ANÁLISIS
-- ==========================================
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

CREATE TABLE IF NOT EXISTS "analysisVideoUpload" (
  "idVideoUpload" SERIAL PRIMARY KEY,
  "idUsuario" INT NULL REFERENCES users("idUsuario") ON DELETE SET NULL,
  "idEmpresa" INT NULL REFERENCES empresa("idEmpresa") ON DELETE SET NULL,
  "nombreOriginal" VARCHAR(255) NOT NULL,
  "rutaArchivo" VARCHAR(500) NOT NULL,
  "tamanioBytes" BIGINT NOT NULL CHECK ("tamanioBytes" >= 0),
  "duracionSegundos" DOUBLE PRECISION NULL CHECK ("duracionSegundos" IS NULL OR "duracionSegundos" >= 0),
  fps DOUBLE PRECISION NULL CHECK (fps IS NULL OR fps >= 0),
  estado VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (estado IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')),
  "celeryTaskId" VARCHAR(255) NULL,
  "fechaCarga" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "fechaProcesamiento" TIMESTAMP NULL
);

CREATE INDEX IF NOT EXISTS ix_video_estado ON "analysisVideoUpload" (estado);
CREATE INDEX IF NOT EXISTS ix_video_fechacarga ON "analysisVideoUpload" ("fechaCarga");

CREATE TABLE IF NOT EXISTS "analysisDetectionEvent" (
  "idDetectionEvent" SERIAL PRIMARY KEY,
  "idVideoUpload" INT NOT NULL REFERENCES "analysisVideoUpload"("idVideoUpload") ON DELETE CASCADE,
  "tipoEvento" VARCHAR(20) NOT NULL CHECK ("tipoEvento" IN ('PELEA', 'DISTURBIO', 'NORMAL')),
  confianza DOUBLE PRECISION NOT NULL CHECK (confianza >= 0 AND confianza <= 1),
  "frameInicio" INT NOT NULL CHECK ("frameInicio" >= 0),
  "frameFin" INT NOT NULL CHECK ("frameFin" >= "frameInicio"),
  "tiempoInicio" DOUBLE PRECISION NOT NULL CHECK ("tiempoInicio" >= 0),
  "tiempoFin" DOUBLE PRECISION NOT NULL CHECK ("tiempoFin" >= "tiempoInicio"),
  "personasInvolucradas" INT NOT NULL DEFAULT 1 CHECK ("personasInvolucradas" >= 1),
  detalles JSONB NULL,
  "fechaCreacion" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "usuarioCreacion" VARCHAR(100) NULL,
  "usuarioModificacion" VARCHAR(100) NULL,
  "fechaModificacion" TIMESTAMP NULL
);

CREATE INDEX IF NOT EXISTS ix_event_video_fecha ON "analysisDetectionEvent" ("idVideoUpload", "fechaCreacion");
CREATE INDEX IF NOT EXISTS ix_event_tipo ON "analysisDetectionEvent" ("tipoEvento");

CREATE TABLE IF NOT EXISTS "analysisPersonKeypoints" (
  "idPersonKeypoints" SERIAL PRIMARY KEY,
  "idDetectionEvent" INT NOT NULL REFERENCES "analysisDetectionEvent"("idDetectionEvent") ON DELETE CASCADE,
  "personId" INT NOT NULL CHECK ("personId" >= 0),
  "frameNumber" INT NOT NULL CHECK ("frameNumber" >= 0),
  "keypointsJson" JSONB NOT NULL DEFAULT '{}'::jsonb,
  "fechaCreacion" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "usuarioCreacion" VARCHAR(100) NULL,
  "usuarioModificacion" VARCHAR(100) NULL,
  "fechaModificacion" TIMESTAMP NULL
);

CREATE INDEX IF NOT EXISTS ix_kp_event_person ON "analysisPersonKeypoints" ("idDetectionEvent", "personId");
CREATE INDEX IF NOT EXISTS ix_kp_frame ON "analysisPersonKeypoints" ("frameNumber");

CREATE TABLE IF NOT EXISTS "analysisReport" (
  "idAnalysisReport" SERIAL PRIMARY KEY,
  "idVideoUpload" INT NOT NULL UNIQUE REFERENCES "analysisVideoUpload"("idVideoUpload") ON DELETE CASCADE,
  "idEmpresa" INT NULL REFERENCES empresa("idEmpresa") ON DELETE SET NULL,
  "totalFrames" INT NOT NULL DEFAULT 0 CHECK ("totalFrames" >= 0),
  "totalDuracionSegundos" DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK ("totalDuracionSegundos" >= 0),
  "totalEventos" INT NOT NULL DEFAULT 0 CHECK ("totalEventos" >= 0),
  "totalPeleas" INT NOT NULL DEFAULT 0 CHECK ("totalPeleas" >= 0),
  "totalDisturbios" INT NOT NULL DEFAULT 0 CHECK ("totalDisturbios" >= 0),
  "confianzaPromedio" DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK ("confianzaPromedio" >= 0 AND "confianzaPromedio" <= 1),
  "confianzaMaxima" DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK ("confianzaMaxima" >= 0 AND "confianzaMaxima" <= 1),
  "tiempoProcesamientoSegundos" DOUBLE PRECISION NULL CHECK ("tiempoProcesamientoSegundos" IS NULL OR "tiempoProcesamientoSegundos" >= 0),
  estadisticas JSONB NULL,
  "resumenJson" JSONB NULL,
  "rutaJsonKeypoints" VARCHAR(500) NULL,
  "generadoEn" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "actualizadoEn" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "usuarioCreacion" VARCHAR(100) NULL,
  "usuarioModificacion" VARCHAR(100) NULL,
  "fechaCreacion" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "fechaModificacion" TIMESTAMP NULL
);

-- ==========================================
-- 5. FUNCIONES Y TRIGGERS
-- ==========================================
CREATE OR REPLACE FUNCTION fn_set_actualizadoen_analysisReport()
RETURNS TRIGGER AS $$
BEGIN
  NEW."actualizadoEn" = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_set_actualizadoen_analysisReport ON "analysisReport";
CREATE TRIGGER trg_set_actualizadoen_analysisReport
BEFORE UPDATE ON "analysisReport"
FOR EACH ROW
EXECUTE FUNCTION fn_set_actualizadoen_analysisReport();