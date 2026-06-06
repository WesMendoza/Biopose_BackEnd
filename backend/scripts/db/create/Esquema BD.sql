TABLE empresa {
  idEmpresa int [primary key]
  CodigoEmpresa varchar
  nombreEmpresa varchar
  direccion varchar
  Ruc varchar
  estado char
  usuarioCreacion varchar
  fechaCreacion datetime
  usuarioModificacion varchar
  fechaModificacion datetime
}

TABLE empresaUsuarioRol {
  idEmpresaUsuarioRol int [primary key]
  idEmpresa int [ref: > empresa.idEmpresa]
  idUsuario int [ref: > users.idUsuario]
  idRol int [ref: > rol.idRol]
  estado char
  usuarioCreacion varchar
  fechaCreacion datetime
  usuarioModificacion varchar
  fechaModificacion datetime
}

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
  idEmpresa int [ref: > empresa.idEmpresa]
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

TABLE analysis_videoupload {
  idVideoUpload int [primary key]
  idUsuario int [ref: > users.idUsuario]
  nombreOriginal varchar
  rutaArchivo varchar
  tamanioBytes bigint
  duracionSegundos float
  fps float
  estado varchar
  celeryTaskId varchar
  fechaCarga datetime
  fechaProcesamiento datetime
}

TABLE analysis_detectionevent {
  idDetectionEvent int [primary key]
  idVideoUpload int [ref: > analysis_videoupload.idVideoUpload]
  tipoEvento varchar
  confianza float
  frameInicio int
  frameFin int
  tiempoInicio float
  tiempoFin float
  personasInvolucradas int
  detalles json
  fechaCreacion datetime
}

TABLE analysis_personkeypoints {
  idPersonKeypoints int [primary key]
  idDetectionEvent int [ref: > analysis_detectionevent.idDetectionEvent]
  personId int
  frameNumber int
  keypointsJson json
  fechaCreacion datetime
}

TABLE analysis_report {
  idAnalysisReport int [primary key]
  idVideoUpload int [unique, ref: > analysis_videoupload.idVideoUpload]
  totalFrames int
  totalDuracionSegundos float
  totalEventos int
  totalPeleas int
  totalDisturbios int
  confianzaPromedio float
  confianzaMaxima float
  tiempoProcesamientoSegundos float
  estadisticas json
  resumenJson json
  rutaJsonKeypoints varchar
  generadoEn datetime
  actualizadoEn datetime
}

TABLE systemParameter {
  idParameter int [primary key]
  codigo varchar [unique]
  valor varchar
  descripcion varchar
  tipo varchar
}
