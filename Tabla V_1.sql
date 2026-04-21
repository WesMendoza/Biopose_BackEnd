CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100),
    apellido VARCHAR(100),
    cedula VARCHAR(20) UNIQUE,
    pass VARCHAR(255),
    mail VARCHAR(100) UNIQUE,
    stateuser INTEGER,
    idrol INTEGER,
    first_tutorial INTEGER,
    lastentry TIMESTAMP
);
CREATE TABLE rol (
    id_rol SERIAL PRIMARY KEY,
    nombrerol VARCHAR(50)
);
CREATE TABLE parametrizador_fps (
    id SERIAL PRIMARY KEY,
    valor_fps INTEGER,
    id_user INTEGER REFERENCES users(id)
);
CREATE TABLE menuoption (
    id SERIAL PRIMARY KEY,
    nombreoption VARCHAR(100),
    rol_id INTEGER REFERENCES rol(id_rol)
);
CREATE TABLE parametrizador_rutas (
    id SERIAL PRIMARY KEY,
    ruta TEXT,
    user_id INTEGER REFERENCES users(id)
);
CREATE TABLE parametrizador_ruta_imagen (
    id_ruta_imagen SERIAL PRIMARY KEY,
    ruta_imagen TEXT,
    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    id_ruta_principal INTEGER REFERENCES parametrizador_rutas(id)
);