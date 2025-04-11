# Azure Function para ETL de Datos Estructurados

## Descripción

Esta Azure Function implementa un proceso de ETL (Extracción, Transformación y Carga) automatizado que opera como puente entre Azure Blob Storage y Cosmos DB, específicamente diseñado para normalizar y persistir datos estructurados de publicaciones sociales. La solución emplea un enfoque serverless que se ejecuta periódicamente para procesar lotes de documentos JSON, extraer atributos relevantes según un esquema predefinido, y almacenarlos en una base de datos documental optimizada para consultas.

## Arquitectura del Sistema

```
┌────────────────┐     ┌─────────────────┐     ┌────────────────┐
│  Azure Blob    │     │ Azure Function  │     │   Cosmos DB    │
│   Storage      │────▶│  (Procesador)   │────▶│  (Destino)     │
│ (posts/*.json) │     │ Timer-Triggered │     │ (database/     │
└────────────────┘     └─────────────────┘     │    posts)      │
         │                                      └────────────────┘
         │
         ▼
┌────────────────┐
│  Azure Blob    │
│   Storage      │
│(synced/*.json) │
└────────────────┘
```

## Componentes Principales

### Disparador (Trigger)

- **Tipo**: Timer Trigger
- **Programación**: Cada minuto (`0 */1 * * * *`)
- **Comportamiento**: Ejecuta el procesamiento al iniciar y según la programación definida

### Procesamiento de Datos

1. **Extracción**: Lectura de documentos JSON desde el contenedor de origen en Blob Storage
2. **Transformación**: Normalización de la estructura mediante la función `extract_data`
3. **Carga**: Persistencia de datos transformados en Cosmos DB
4. **Archivado**: Traslado de blobs procesados a un contenedor de respaldo

### Modelo de Datos Procesado

Se extrae un subconjunto optimizado de los datos originales, enfocándose en:

- Metadatos de propietario (username, verificación, privacidad)
- Información geográfica
- Identificadores únicos
- Atributos de publicación (timestamp, estado de comentarios)
- Contenido textual (descripción)
- Información de engagement (comentarios, previsualizaciones)

## Configuración

### Variables de Entorno

| Variable                  | Descripción                                 | Valor Predeterminado |
| ------------------------- | ------------------------------------------- | -------------------- |
| `AzureWebJobsStorage`     | Cadena de conexión a Azure Storage          | _Requerido_          |
| `SOURCE_CONTAINER`        | Contenedor de origen                        | `posts`              |
| `TARGET_CONTAINER`        | Contenedor de destino para blobs procesados | `synced`             |
| `COSMOS_ENDPOINT`         | Punto de conexión de Cosmos DB              | _Requerido_          |
| `COSMOS_KEY`              | Clave de acceso a Cosmos DB                 | _Requerido_          |
| `COSMOS_DB_NAME`          | Nombre de la base de datos                  | `database`           |
| `COSMOS_CONTAINER_NAME`   | Nombre del contenedor en Cosmos DB          | `posts`              |
| `MAX_BLOBS_PER_EXECUTION` | Límite de blobs a procesar por ejecución    | `100`                |

## Implementación

### Requisitos Previos

- Python 3.12+
- Azure Functions Core Tools
- Suscripción de Azure con permisos para:
  - Azure Functions
  - Azure Storage Account
  - Azure Cosmos DB

## Aspectos Técnicos

### Estrategia

La arquitectura de la función implementa un modelo de resiliencia distribuida con prácticas de sistemas data-intensive:

1. **Aislamiento de Errores**: El procesamiento de cada blob se encapsula en un contexto de excepción independiente, creando fronteras de fallo bien definidas que evitan la propagación de errores entre documentos. Esta aproximación de compartimentación permite que un documento malformado no comprometa el procesamiento del conjunto completo.

2. **Transaccionalidad Secuencial**: La función orquesta una secuencia de operaciones (persistencia en Cosmos DB, replicación al contenedor de respaldo, eliminación del origen) que implementa un patrón transaccional distribuido.

3. **Control Adaptativo de Carga**: La parametrización del tamaño de lote (`MAX_BLOBS_PER_EXECUTION`) establece un mecanismo de control de presión que optimiza el equilibrio entre latencia de procesamiento y utilización de recursos, mitigando efectivamente el riesgo de timeouts en entornos serverless con limitaciones temporales predefinidas.
