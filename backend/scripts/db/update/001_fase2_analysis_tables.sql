-- ==========================================
-- FASE 2: TABLAS DE ANALISIS (MIGRACION MANUAL)
-- Archivo: scripts/db/update/001_fase2_analysis_tables.sql
-- Entorno objetivo: Esquema Dev
-- ==========================================

SET search_path TO "Dev";

-- ==========================================
-- 1) VIDEO UPLOAD
-- ==========================================
CREATE TABLE IF NOT EXISTS analysis_videoupload (
  idVideoUpload SERIAL PRIMARY KEY,
  idUsuario INT NULL REFERENCES users(idUsuario) ON DELETE SET NULL,
  idEmpresa INT NULL REFERENCES empresa(idEmpresa) ON DELETE SET NULL,
  nombreOriginal VARCHAR(255) NOT NULL,
  rutaArchivo VARCHAR(500) NOT NULL,
  tamanioBytes BIGINT NOT NULL CHECK (tamanioBytes >= 0),
  duracionSegundos DOUBLE PRECISION NULL CHECK (duracionSegundos IS NULL OR duracionSegundos >= 0),
  fps DOUBLE PRECISION NULL CHECK (fps IS NULL OR fps >= 0),
  estado VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (estado IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')),
  celeryTaskId VARCHAR(255) NULL,
  fechaCarga TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  fechaProcesamiento TIMESTAMP NULL
);

CREATE INDEX IF NOT EXISTS ix_video_estado ON analysis_videoupload (estado);
CREATE INDEX IF NOT EXISTS ix_video_fechacarga ON analysis_videoupload (fechaCarga);

-- ==========================================
-- 2) DETECTION EVENT
-- ==========================================
CREATE TABLE IF NOT EXISTS analysis_detectionevent (
  idDetectionEvent SERIAL PRIMARY KEY,
  idVideoUpload INT NOT NULL REFERENCES analysis_videoupload(idVideoUpload) ON DELETE CASCADE,
  tipoEvento VARCHAR(20) NOT NULL CHECK (tipoEvento IN ('PELEA', 'DISTURBIO', 'NORMAL')),
  confianza DOUBLE PRECISION NOT NULL CHECK (confianza >= 0 AND confianza <= 1),
  frameInicio INT NOT NULL CHECK (frameInicio >= 0),
  frameFin INT NOT NULL CHECK (frameFin >= frameInicio),
  tiempoInicio DOUBLE PRECISION NOT NULL CHECK (tiempoInicio >= 0),
  tiempoFin DOUBLE PRECISION NOT NULL CHECK (tiempoFin >= tiempoInicio),
  personasInvolucradas INT NOT NULL DEFAULT 1 CHECK (personasInvolucradas >= 1),
  detalles JSONB NULL,
  fechaCreacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  usuarioCreacion VARCHAR(100) NULL,
  usuarioModificacion VARCHAR(100) NULL,
  fechaModificacion TIMESTAMP NULL
);

CREATE INDEX IF NOT EXISTS ix_event_video_fecha ON analysis_detectionevent (idVideoUpload, fechaCreacion);
CREATE INDEX IF NOT EXISTS ix_event_tipo ON analysis_detectionevent (tipoEvento);

-- ==========================================
-- 3) PERSON KEYPOINTS
-- ==========================================
CREATE TABLE IF NOT EXISTS analysis_personkeypoints (
  idPersonKeypoints SERIAL PRIMARY KEY,
  idDetectionEvent INT NOT NULL REFERENCES analysis_detectionevent(idDetectionEvent) ON DELETE CASCADE,
  personId INT NOT NULL CHECK (personId >= 0),
  frameNumber INT NOT NULL CHECK (frameNumber >= 0),
  keypointsJson JSONB NOT NULL DEFAULT '{}'::jsonb,
  fechaCreacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  usuarioCreacion VARCHAR(100) NULL,
  usuarioModificacion VARCHAR(100) NULL,
  fechaModificacion TIMESTAMP NULL
);

CREATE INDEX IF NOT EXISTS ix_kp_event_person ON analysis_personkeypoints (idDetectionEvent, personId);
CREATE INDEX IF NOT EXISTS ix_kp_frame ON analysis_personkeypoints (frameNumber);

-- ==========================================
-- 4) ANALYSIS REPORT
-- ==========================================
CREATE TABLE IF NOT EXISTS analysis_report (
  idAnalysisReport SERIAL PRIMARY KEY,
  idVideoUpload INT NOT NULL UNIQUE REFERENCES analysis_videoupload(idVideoUpload) ON DELETE CASCADE,
  idEmpresa INT NULL REFERENCES empresa(idEmpresa) ON DELETE SET NULL,
  totalFrames INT NOT NULL DEFAULT 0 CHECK (totalFrames >= 0),
  totalDuracionSegundos DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (totalDuracionSegundos >= 0),
  totalEventos INT NOT NULL DEFAULT 0 CHECK (totalEventos >= 0),
  totalPeleas INT NOT NULL DEFAULT 0 CHECK (totalPeleas >= 0),
  totalDisturbios INT NOT NULL DEFAULT 0 CHECK (totalDisturbios >= 0),
  confianzaPromedio DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (confianzaPromedio >= 0 AND confianzaPromedio <= 1),
  confianzaMaxima DOUBLE PRECISION NOT NULL DEFAULT 0 CHECK (confianzaMaxima >= 0 AND confianzaMaxima <= 1),
  tiempoProcesamientoSegundos DOUBLE PRECISION NULL CHECK (tiempoProcesamientoSegundos IS NULL OR tiempoProcesamientoSegundos >= 0),
  estadisticas JSONB NULL,
  resumenJson JSONB NULL,
  generadoEn TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizadoEn TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  usuarioCreacion VARCHAR(100) NULL,
  usuarioModificacion VARCHAR(100) NULL,
  fechaCreacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  fechaModificacion TIMESTAMP NULL
);

-- Trigger para mantener actualizadoEn automáticamente
CREATE OR REPLACE FUNCTION fn_set_actualizadoen_analysis_report()
RETURNS TRIGGER AS $$
BEGIN
  NEW.actualizadoEn = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_set_actualizadoen_analysis_report ON analysis_report;
CREATE TRIGGER trg_set_actualizadoen_analysis_report
BEFORE UPDATE ON analysis_report
FOR EACH ROW
EXECUTE FUNCTION fn_set_actualizadoen_analysis_report();

-- ==========================================
-- 5) SYSTEM PARAMETER
-- ==========================================
CREATE TABLE IF NOT EXISTS systemParameter (
  idParameter SERIAL PRIMARY KEY,
  codigo VARCHAR(100) NOT NULL UNIQUE,
  valor VARCHAR(500) NOT NULL,
  descripcion VARCHAR(255) NULL,
  tipo VARCHAR(20) NOT NULL DEFAULT 'STRING' CHECK (tipo IN ('INT', 'FLOAT', 'STRING', 'BOOL'))
);

-- ==========================================
-- VALIDACION RAPIDA (opcional)
-- ==========================================
-- SELECT table_name
-- FROM information_schema.tables
-- WHERE table_schema = 'Dev'
--   AND table_name IN (
--     'analysis_videoupload',
--     'analysis_detectionevent',
--     'analysis_personkeypoints',
--     'analysis_report',
--     'systemparameter'
--   )
-- ORDER BY table_name;
