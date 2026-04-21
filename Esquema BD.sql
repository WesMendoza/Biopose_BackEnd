TABLE users {
  idUsuario int [primary key]
  nombre varchar
  apellido varchar
  cedula varchar
  correo varchar
  password varchar
  estado char
  usuarioCreacion varchar
  fechaCreacion datetime
  usuarioModificacion varchar
  fechaModificacion varchar
  ultimoIngreso datetime
}

TABLE rol {
  idRol int [primary key]
  nombreRol varchar
  estado char
  usuarioCreacion varchar
  fechaCreacion datetime
  usuarioModificacion varchar
  fechaModificacion varchar
}

TABLE usersRol {
  idUsersRol int [primary key]
  idUsuario int [ref: >users.idUsuario]
  idRol int [ref: > rol.idRol]
  estado char
  usuarioCreacion varchar
  fechaCreacion datetime
  usuarioModificacion varchar
  fechaModificacion varchar
}

TABLE menuoption {
  idOption int [primary key]
  nombreoption varchar
  estado char
  usuarioCreacion varchar
  fechaCreacion datetime
  usuarioModificacion varchar
  fechaModificacion varchar
}

TABLE rolOption {
  idRolOption int [primary key]
  idRol int [ref: > rol.idRol]
  idOption int [ref: > menuoption.idOption]
}

TABLE  parametrosCabecera {
  idParametrosCabecera int [primary key]
  nombreParametro varchar
  codigoParmetro varchar
  estado char
  usuarioCreacion varchar
  fechaCreacion datetime
  usuarioModificacion varchar
  fechaModificacion varchar
}


TABLE parametroDetalle {
  idParametroDetalle int [primary key]
  codigoParametro varchar [ref: > parametrosCabecera.codigoParmetro]
  nombreDetalle varchar
  descripcion varchar
  valor varchar
  estado char
  usuarioCreacion varchar
  fechaCreacion datetime
  usuarioModificacion varchar
  fechaModificacion varchar
}
