# Arquitectura de Procesamiento de Datos e Análisis de Publicaciones Sociales usando Azure

## Autores

- Pedro Orlando Acosta Pereira
- Francisco José Salas Gómez

## Visión Arquitectónica

Esta plataforma implementa una arquitectura de procesamiento de datos distribuida y escalable que integra múltiples componentes para gestionar el ciclo de vida completo de los datos de publicaciones sociales: desde la extracción y transformación inicial hasta su análisis mediante herramientas de inteligencia empresarial.

La solución adopta un enfoque modular con componentes desacoplados que operan como etapas independientes en un pipeline coordinado, maximizando la escalabilidad, resiliencia y mantenibilidad del sistema.

## Diagrama de Arquitectura

```
┌───────────────┐        ┌───────────────┐        ┌───────────────┐        ┌───────────────┐        ┌───────────────┐
│  Origen de    │        │ Extracción y  │        │  Azure Blob   │        │ Procesamiento │        │  Cosmos DB    │
│  Archivos     │───────▶│ Transformación│───────▶│   Storage     │───────▶│ Serverless    │───────▶│  (Almacén     │
│  (.info)      │        │ Inicial       │        │ (posts/*.json)│        │ (Azure Func.) │        │  Analítico)   │
└───────────────┘        └───────────────┘        └───────────────┘        └───────────────┘        └───────────────┘
                                                          │                        │                        │
                                                          │                        │                        │
                                                          ▼                        ▼                        ▼
                                                  ┌───────────────┐        ┌───────────────┐        ┌───────────────┐
                                                  │ Almacenamiento│        │ Monitorización│        │  PowerBI      │
                                                  │ de Respaldo   │        │ y Logging     │        │  Consumo      │
                                                  │(synced/*.json)│        │               │        │  Analítico    │
                                                  └───────────────┘        └───────────────┘        └───────────────┘
```

## Componentes Principales

El sistema está compuesto por módulos especializados, cada uno documentado exhaustivamente en su correspondiente README:

### 1. Carga de Datos a Blob Storage (`[./esesa-instagram-posts-to-blob-storage/README.md]`)

Este componente gestiona la extracción y carga inicial de datos desde archivos locales hacia Azure Blob Storage, implementando:

- Procesamiento multithreaded para optimización de rendimiento
- Estrategias robustas de gestión de errores y reintentos
- Monitorización detallada del proceso de carga
- Control granular de parámetros de ejecución

[Ver documentación detallada →](./esesa-instagram-posts-to-blob-storage/README.md)

### 2. Procesamiento Serverless (`[./instagram-posts-from-blob-to-cosmos/README.md]`)

Esta Azure Function implementa un proceso de ETL optimizado que transforma los datos almacenados en Blob Storage y los persiste en Cosmos DB, proporcionando:

- Transformación estructural para optimización de consultas analíticas
- Procesamiento por lotes con barreras de error aisladas
- Control adaptativo de carga y elasticidad computacional

[Ver documentación detallada →](./instagram-posts-from-blob-to-cosmos/README.md)

### 3. Análisis con PowerBI (En desarrollo)

Este componente proporciona capacidades avanzadas de visualización y análisis sobre los datos procesados en Cosmos DB:

- Dashboards interactivos para análisis multidimensional
- Métricas de engagement y análisis contextual
- Segmentación dinámica y clasificación automatizada

## Fundamentos Tecnológicos

La arquitectura se sustenta sobre un stack tecnológico moderno y cloud-native:

### Computación

- **Azure Functions**: Procesamiento serverless event-driven
- **Python**: Lenguaje core para implementación de componentes

### Almacenamiento

- **Azure Blob Storage**: Persistencia de datos no estructurados a escala
- **Azure Cosmos DB**: Base de datos documental geo-distribuida

### Analítica

- **Power BI**: Plataforma de visualización e inteligencia empresarial

## Guía de Inicio Rápido

### Requisitos Previos

- Suscripción de Azure con servicios compatibles habilitados
- Python 3.10+ para componentes de procesamiento
- Acceso administrativo a PowerBI para visualizaciones

### Configuración del Entorno

1. **Aprovisionamiento de Servicios Azure**:

   - Cuenta de Storage con contenedores apropiados
   - Azure Function con plan de consumo
   - Instancia de Cosmos DB con contenedor configurado

2. **Configuración de Variables de Entorno**:

   - Credenciales de conexión para servicios Azure
   - Parámetros operativos para componentes de procesamiento

3. **Despliegue de Componentes**:
   - Implementación de scripts de carga y procesamiento
   - Configuración de funciones serverless
   - Integración con PowerBI
