# Plan de Migracion de Arquitectura

## Objetivo

Migrar la aplicacion actual, hoy implementada como un monolito en Flask, hacia una arquitectura distribuida con un backend central en Django que maneje solo la logica de negocio, autenticacion, permisos y exposicion de servicios.

El objetivo es separar responsabilidades, facilitar el mantenimiento, mejorar la escalabilidad y permitir que los procesos de deteccion y analisis puedan ejecutarse de forma desacoplada.

## Enfoque de trabajo

La migracion no debe entenderse como una reescritura total inmediata, sino como una secuencia de actividades tecnicas ordenadas.

El punto de partida debe ser la preparacion del ambiente del backend, la estructura base del proyecto Django y la definicion de contratos entre componentes.

La interfaz grafica del frontend no sera mantenida como componente central del sistema. En esta etapa, el frontend solo quedara como consumidor de servicios API y WebSocket, o se reemplazara por completo segun la estrategia final.

## Plan de actividades

### Actividades iniciales

- Definir el alcance tecnico de la migracion.
- Confirmar que el backend sera el unico componente activo de negocio.
- Identificar que partes del frontend actual se descontinuaran.
- Revisar la base de datos actual y las tablas que deben preservarse.

### Actividades de preparacion del backend

- Crear el entorno virtual de Python.
- Instalar Django y dependencias base.
- Crear el proyecto Django inicial.
- Configurar PostgreSQL como base principal.
- Preparar variables de entorno y archivo de configuracion.
- Organizar la estructura de apps internas por dominio funcional.
- Definir la configuracion inicial de autenticacion y permisos.

### Actividades de integracion base

- Integrar Django REST Framework para exponer servicios.
- Integrar Django Channels para tiempo real.
- Integrar Celery y Redis para tareas distribuidas.
- Definir la integracion con el modulo o servicio de IA.
- Establecer formato de respuestas, errores y trazabilidad.

### Actividades de control y validacion

- Validar conexion a base de datos.
- Validar creacion de usuarios y autenticacion.
- Validar un endpoint simple de prueba.
- Validar un canal WebSocket de prueba.
- Validar ejecucion de una tarea asíncrona de ejemplo.

## Alcance

Este plan cubre la migracion de la capa backend actual hacia una nueva solucion basada en Python y Django.

Queda dentro del alcance:

- Autenticacion y gestion de usuarios.
- Permisos, menus y configuracion general.
- CRUD de entidades de negocio.
- Exposicion de endpoints para frontend y servicios externos.
- Comunicacion en tiempo real con WebSocket.
- Tareas asíncronas y distribuidas para procesos pesados.
- Separacion del servicio de inferencia IA como modulo o microservicio aparte.
- Backend como centro unico de logica de negocio.

Queda fuera del alcance inicial:

- Mantenimiento de la interfaz grafica del frontend como parte principal del sistema.
- Cambio inmediato de toda la logica IA.
- Migracion completa de una sola vez.

## Arquitectura objetivo

La arquitectura recomendada para la nueva etapa es la siguiente:

- Django: autenticacion, permisos, menus, configuracion, CRUD y panel administrativo.
- Django REST Framework: endpoints para frontend y servicios externos.
- Django Channels: WebSocket para progreso, alertas y resultados en tiempo real.
- Celery + Redis: tareas distribuidas de deteccion y procesamiento pesado.
- PostgreSQL: base de datos principal.
- Servicio IA separado: inferencia de pose y comportamiento, idealmente como modulo o microservicio aparte.
- Frontend actual: puede seguir como cliente web consumiendo API y WebSocket.

## Estado actual

La aplicacion actual funciona como un monolito donde una sola base concentra:

- Interfaz web.
- Autenticacion.
- Acceso a base de datos.
- Procesamiento de imagen y video.
- Inferencia de modelos.
- Generacion de eventos y reportes.

Este enfoque funciona como base funcional, pero limita la escalabilidad, el aislamiento de errores y la evolucion modular del sistema.

## Estrategia de migracion

La migracion se realizara de forma incremental para reducir riesgo.

### Fase 1. Analisis y definicion

- Identificar modulos actuales reutilizables.
- Definir entidades de negocio definitivas.
- Revisar estructura actual de base de datos.
- Establecer contratos de entrada y salida entre backend, IA y frontend.
- Definir que funcionalidades permanecen en el monolito durante la transicion.

### Fase 2. Creacion del backend Django

- Crear el proyecto base en Django.
- Configurar entorno, settings, logging y variables de entorno.
- Preparar PostgreSQL como base principal.
- Estructurar apps por dominio funcional.
- Definir la capa de autenticacion y permisos.

### Fase 3. Exposicion de API

- Implementar Django REST Framework.
- Publicar endpoints para usuarios, roles, parametros y menus.
- Crear endpoints de consulta y registro para los flujos principales.
- Estandarizar respuestas y manejo de errores.

### Fase 4. Tiempo real

- Configurar Django Channels.
- Crear canal WebSocket para notificaciones de estado.
- Emitir avances de procesamiento, alertas y resultados.
- Integrar el frontend como consumidor del socket.

### Fase 5. Tareas distribuidas

- Integrar Celery con Redis.
- Mover procesamiento pesado a workers asíncronos.
- Separar analisis de video, analisis de imagen y eventos intensivos.
- Publicar el estado de cada tarea para seguimiento en tiempo real.

### Fase 6. Separacion del servicio IA

- Extraer la inferencia de pose y comportamiento del backend principal.
- Definir si quedara como modulo interno o servicio independiente.
- Establecer un contrato claro de peticiones y respuestas.
- Evitar que el backend web dependa del ciclo pesado de procesamiento.

### Fase 7. Transicion del frontend

- Mantener el frontend actual como cliente mientras dure la migracion.
- Cambiar gradualmente llamadas directas por consumo de API.
- Reemplazar los puntos que dependan de Flask por endpoints Django.
- Validar compatibilidad con WebSocket para estados en vivo.

## Entregables por etapa

- Documento de arquitectura objetivo.
- Proyecto Django inicial con configuracion base.
- API funcional para autenticacion y datos principales.
- WebSocket operativo para notificaciones.
- Procesamiento asíncrono con Celery.
- Separacion del componente de IA.
- Plan de corte definitivo del monolito.

## Criterios de exito

La migracion se considerara exitosa cuando:

- El backend Django administre la logica de negocio central.
- El frontend consuma API en lugar de depender del monolito.
- Las tareas pesadas no bloqueen el servidor principal.
- Los eventos se transmitan en tiempo real por WebSocket.
- La capa IA quede aislada o encapsulada de forma controlada.
- La base de datos principal opere sobre PostgreSQL con trazabilidad clara.

## Riesgos y consideraciones

- Migrar todo de una vez aumenta el riesgo de regresiones.
- El procesamiento de video e inferencia puede requerir optimizacion adicional.
- WebSocket y tareas distribuidas requieren disciplina en configuracion y monitoreo.
- La separacion entre backend y servicio IA debe definir formatos estables de comunicacion.

## Orden sugerido de trabajo

1. Preparar el entorno de desarrollo del backend.
2. Crear el proyecto Django base.
3. Configurar PostgreSQL, variables de entorno y settings.
4. Migrar autenticacion, roles y configuracion.
5. Exponer los primeros endpoints con DRF.
6. Habilitar Channels para eventos en tiempo real.
7. Integrar Celery y Redis para tareas pesadas.
8. Separar la logica IA.
9. Descontinuar o minimizar el frontend grafico segun la decision final.

## Nota operativa

Este documento debe usarse como referencia viva durante la migracion. Si cambian el alcance, la arquitectura o el orden de ejecucion, esta guia debe actualizarse antes de continuar con el siguiente paso tecnico.

*Nota de Actualización (Fase 4): Se implementó el rastreo y evaluación multi-persona utilizando ByteTrack, permitiendo la evaluación aislada de múltiples sujetos por el modelo LSTM asíncrono.*