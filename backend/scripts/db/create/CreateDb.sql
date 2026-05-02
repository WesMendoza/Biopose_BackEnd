-- ==========================================
-- PARÁMETRO DE ENTORNO (Esquema)
-- ==========================================
CREATE SCHEMA IF NOT EXISTS "Dev";
SET search_path TO "Dev";

-- ==========================================
-- CREACIÓN DE TABLAS MAESTRAS
-- ==========================================
CREATE TABLE empresa (
  idEmpresa SERIAL PRIMARY KEY,
  CodigoEmpresa VARCHAR(50),
  nombreEmpresa VARCHAR(150),
  direccion VARCHAR(255),
  Ruc VARCHAR(20),
  estado CHAR(1),
  usuarioCreacion VARCHAR(50),
  fechaCreacion TIMESTAMP,
  usuarioModificacion VARCHAR(50),
  fechaModificacion TIMESTAMP
);

CREATE TABLE users (
  idUsuario SERIAL PRIMARY KEY,
  nombre VARCHAR(100),
  apellido VARCHAR(100),
  cedula VARCHAR(20),
  correo VARCHAR(150) UNIQUE,
  password VARCHAR(255),
  estado CHAR(1),
  usuarioCreacion VARCHAR(50),
  fechaCreacion TIMESTAMP,
  usuarioModificacion VARCHAR(50),
  fechaModificacion TIMESTAMP,
  ultimoIngreso TIMESTAMP
);

CREATE TABLE rol (
  idRol SERIAL PRIMARY KEY,
  nombreRol VARCHAR(100),
  estado CHAR(1),
  usuarioCreacion VARCHAR(50),
  fechaCreacion TIMESTAMP,
  usuarioModificacion VARCHAR(50),
  fechaModificacion TIMESTAMP
);

CREATE TABLE menuoption (
  idOption SERIAL PRIMARY KEY,
  nombreoption VARCHAR(100),
  estado CHAR(1),
  usuarioCreacion VARCHAR(50),
  fechaCreacion TIMESTAMP,
  usuarioModificacion VARCHAR(50),
  fechaModificacion TIMESTAMP
);

-- ==========================================
-- TABLAS TRANSACCIONALES / PIVOTES
-- ==========================================
CREATE TABLE empresaUsuarioRol (
  idEmpresaUsuarioRol SERIAL PRIMARY KEY,
  idEmpresa INT REFERENCES empresa(idEmpresa) ON DELETE CASCADE,
  idUsuario INT REFERENCES users(idUsuario) ON DELETE CASCADE,
  idRol INT REFERENCES rol(idRol) ON DELETE CASCADE,
  estado CHAR(1),
  usuarioCreacion VARCHAR(50),
  fechaCreacion TIMESTAMP,
  usuarioModificacion VARCHAR(50),
  fechaModificacion TIMESTAMP
);

CREATE TABLE rolOption (
  idRolOption SERIAL PRIMARY KEY,
  idRol INT REFERENCES rol(idRol) ON DELETE CASCADE,
  idOption INT REFERENCES menuoption(idOption) ON DELETE CASCADE
);

CREATE TABLE parametrosCabecera (
  idParametrosCabecera SERIAL PRIMARY KEY,
  idEmpresa INT REFERENCES empresa(idEmpresa) ON DELETE CASCADE,
  nombreParametro VARCHAR(100),
  codigoParmetro VARCHAR(50) UNIQUE, -- Necesario UNIQUE para la FK del detalle
  estado CHAR(1),
  usuarioCreacion VARCHAR(50),
  fechaCreacion TIMESTAMP,
  usuarioModificacion VARCHAR(50),
  fechaModificacion TIMESTAMP
);

CREATE TABLE parametroDetalle (
  idParametroDetalle SERIAL PRIMARY KEY,
  codigoParametro VARCHAR(50) REFERENCES parametrosCabecera(codigoParmetro) ON DELETE CASCADE,
  nombreDetalle VARCHAR(100),
  descripcion VARCHAR(255),
  valor VARCHAR(255),
  estado CHAR(1),
  usuarioCreacion VARCHAR(50),
  fechaCreacion TIMESTAMP,
  usuarioModificacion VARCHAR(50),
  fechaModificacion TIMESTAMP
);