# Criterios de búsqueda y clasificación

Este documento explica en qué se basa el agente para localizar, puntuar y resumir oportunidades privadas relacionadas con proyectos físicos donde podrían aparecer necesidades futuras de tecnología para espacios.

Sirve como documento de revisión: aquí puedes detectar qué búsquedas faltan, qué palabras sobran, qué sectores conviene reforzar y qué reglas pueden estar generando ruido.

## 1. Objetivo del agente

El agente no busca directamente proyectos audiovisuales ni integradores. Busca señales tempranas de proyectos físicos privados:

- nuevas sedes
- oficinas
- tiendas
- hoteles
- campus
- clínicas
- hospitales privados
- gimnasios
- estadios
- museos
- espacios inmersivos
- coworking
- coliving
- centros culturales o de ocio privados

La hipótesis es que esos proyectos pueden necesitar más adelante pantallas, cartelería digital, audio, LED, videoconferencia, salas de reunión, tecnología interactiva o sistemas para espacios.

## 2. Fuentes de información actuales

Archivo editable:

```text
config/sources.yaml
```

Fuente activa:

```text
Google News RSS
```

Configuración actual:

```yaml
google_news:
  enabled: true
  language: es
  country: ES
  max_results_per_query: 10
  timeout_seconds: 15
  pause_seconds: 1
```

También existe una sección para añadir RSS adicionales:

```yaml
additional_rss: []
```

Ahora mismo no hay fuentes RSS sectoriales adicionales configuradas.

## 3. Filtro temporal

El modo diario normal analiza noticias publicadas en las últimas 48 horas.

Configuración:

```yaml
max_news_age_hours: 48
initial_backfill_enabled: false
initial_backfill_days: 7
future_tolerance_hours: 6
```

Cuando usa Google News RSS, el agente añade automáticamente un filtro temporal:

- `when:2d` si el rango es 48 horas o menos.
- `when:3d` si el rango es 72 horas.
- `when:7d` si se activa la carga inicial de 7 días.

Las noticias antiguas se cuentan, pero no se listan una por una en el HTML.

## 4. Búsquedas activas por sector

### Oficinas

- `"nueva sede" empresa España`
- `"nuevas oficinas" empresa España`
- `"abre oficinas" empresa España`
- `"traslada sus oficinas" España`
- `"alquila edificio" oficinas España`
- `"nuevo hub" empresa España`
- `"centro de innovación" empresa España`
- `"campus corporativo" empresa España`

### Retail

- `"nueva tienda" España`
- `"abrirá tienda" España`
- `"apertura tienda" España`
- `"flagship" Madrid`
- `"flagship" Barcelona`
- `"concept store" España`
- `"plan de expansión" tiendas España`
- `"aperturas previstas" tiendas España`
- `"nuevo formato de tienda" España`
- `"retail park" apertura España`

### Hoteles

- `"nuevo hotel" España`
- `"apertura hotel" España`
- `"apertura hotelera" España`
- `"reforma hotel" España`
- `"reapertura hotel" España`
- `"hotel cinco estrellas" apertura España`
- `"cadena hotelera" expansión España`
- `"nuevo resort" España`
- `"hotel boutique" apertura España`

### Educación privada

- `"nuevo campus" universidad privada España`
- `"nuevo edificio" universidad privada España`
- `"universidad privada" "nuevo campus"`
- `"business school" nueva sede España`
- `"colegio privado" nuevo campus España`
- `"colegio internacional" apertura España`
- `"residencia de estudiantes" apertura España`
- `"student housing" España apertura`

### Sanidad privada

- `"nuevo hospital privado" España`
- `"nueva clínica" España`
- `"centro médico privado" apertura España`
- `"hospital privado" ampliación España`
- `"grupo sanitario" nueva clínica España`
- `"clínica dental" expansión España`
- `"clínica estética" apertura España`
- `"centro de diagnóstico" apertura España`

### Deporte

- `"nuevo estadio" España`
- `"remodelación estadio" España`
- `"nuevo centro deportivo" España`
- `"centro deportivo privado" apertura España`
- `"cadena de gimnasios" expansión España`
- `"gimnasio" nuevas aperturas España`
- `"ciudad deportiva" proyecto España`
- `"arena multiusos" España`

### Cultura y ocio

- `"nuevo museo" España`
- `"museo privado" apertura España`
- `"centro cultural" apertura España`
- `"espacio inmersivo" apertura España`
- `"experiencia inmersiva" España`
- `"nuevo espacio expositivo" España`
- `"centro de interpretación" apertura España`
- `"espacio de ocio" apertura España`

### Coworking y coliving

- `"nuevo coworking" España`
- `"coworking" apertura Madrid`
- `"coworking" apertura Barcelona`
- `"oficinas flexibles" nueva sede España`
- `"coliving" apertura España`
- `"flex office" apertura España`

## 5. Palabras y señales que suman puntos

Archivo editable:

```text
config/keywords.yaml
```

Reglas de puntuación:

```text
config/scoring.yaml
```

### Señales temporales futuras

Estas señales indican que el proyecto probablemente aún no está terminado:

- abrirá
- prevé abrir
- prepara apertura
- abrirá sus puertas
- próxima apertura
- proyecta
- planea
- construirá
- desarrollará
- iniciará obras
- invertirá
- reformará
- ampliará
- nuevo proyecto
- en construcción
- en desarrollo
- previsto para
- estará operativo en
- ultima la apertura
- alquila edificio para
- compra edificio para
- busca ubicación
- busca local
- plan de expansión
- aperturas previstas

Puntuación:

- señal futura clara: `+25`
- en obra o reforma: `+20`
- próxima apertura futura: `+20`
- plan de expansión con futuras ubicaciones: `+15`

### Señales de oportunidad física

Estas señales apuntan a un espacio físico:

- nueva sede: `+25`
- nuevas oficinas: `+25`
- apertura confirmada: `+25`
- reforma integral: `+20`
- reapertura: `+20`
- ubicación concreta: `+15`
- fecha prevista: `+10`
- inversión económica: `+15`
- superficie en m2: `+10`
- empresa privada identificada: `+15`
- sector prioritario: `+10`
- flagship: `+15`
- campus: `+15`
- hub: `+15`
- hotel: `+15`
- estadio: `+15`
- museo: `+15`
- espacio inmersivo: `+15`

## 6. Palabras y señales que restan puntos

### Proyecto ya inaugurado o abierto

Estas señales indican que el proyecto puede estar ya ejecutado y equipado:

- inaugura
- ha inaugurado
- inauguró
- ya ha abierto
- abrió
- abre hoy
- abre sus puertas
- ha abierto sus puertas
- estrena sede
- estrena tienda
- celebró la apertura
- acaba de inaugurar
- nueva sede inaugurada
- tienda inaugurada
- hotel inaugurado
- reapertura celebrada

Penalización:

- ya inaugurado / ya abierto: `-60`

Regla adicional:

Si una noticia está ya inaugurada y no incluye una fase futura adicional clara, no puede ser `Alta` ni `Media`; como máximo será `Baja`.

Excepción:

Si la noticia habla de algo ya inaugurado pero también anuncia una fase futura clara, se mantiene la penalización, pero puede subir si las señales futuras son fuertes.

### Sector público, política o bajo valor comercial

Penalizaciones:

- licitación pública: `-50`
- contratación pública: `-50`
- administración pública como protagonista: `-30`
- noticia política: `-40`
- solo resultados financieros: `-25`
- nombramiento sin proyecto físico: `-25`
- fecha de publicación no clara: `-15`
- sin espacio físico asociado: `-30`
- duplicado: `-100`

Palabras de descarte o penalización incluyen:

- licitación
- contratación pública
- concurso público
- adjudicación pública
- BOE
- BOP
- ayuntamiento
- diputación
- ministerio
- consejería
- subvención
- elecciones
- partido político
- resultados financieros
- dividendos
- cotización bursátil
- nombramientos

Nota importante:

No se descarta automáticamente una noticia solo por mencionar una administración. Se penaliza cuando la administración parece protagonista o cuando la noticia apunta a contratación pública.

## 7. Fase detectada

El informe incluye:

```text
fase_detectada
timing_reason
```

Valores posibles de `fase_detectada`:

- `futuro`
- `en planificación`
- `en obra/reforma`
- `próxima apertura`
- `ya inaugurado`
- `desconocida`

`timing_reason` explica qué palabra o señal llevó a esa clasificación.

Ejemplos genéricos:

- Si aparece `abrirá`, puede clasificar como `próxima apertura`.
- Si aparece `iniciará obras`, puede clasificar como `en obra/reforma`.
- Si aparece `busca local`, puede clasificar como `en planificación`.
- Si aparece `ha inaugurado`, puede clasificar como `ya inaugurado`.

## 8. Clasificación final

La puntuación se limita entre 0 y 100.

Clasificación:

- `Alta`: 75 a 100
- `Media`: 50 a 74
- `Baja`: 25 a 49
- `Descartada`: 0 a 24

## 9. Campos del informe

Cada oportunidad incluye:

- `detected_date`
- `published_date`
- `sector`
- `source`
- `title`
- `url`
- `detected_company_or_operator`
- `city_or_area`
- `project_type`
- `detected_signal`
- `fase_detectada`
- `timing_reason`
- `summary`
- `probable_technology_needs`
- `score`
- `priority`
- `priority_reason`
- `suggested_action`
- `status`
- `notes`

## 10. Necesidades tecnológicas probables

El agente no sabe si el proyecto necesita tecnología. Lo infiere por sector.

Ejemplos:

- Oficinas: salas de reunión, videoconferencia, pantallas colaborativas, reserva de salas, señalización digital.
- Retail: cartelería digital, pantallas de escaparate, LED, audio ambiental.
- Hoteles: señalización digital, audio, pantallas para salas, videoconferencia, tecnología para eventos.
- Educación privada: pantallas interactivas, aulas híbridas, audio de aula, videoconferencia.
- Sanidad privada: turnos, cartelería digital, pantallas informativas, salas de formación.
- Deporte: LED, marcadores, audio distribuido, pantallas informativas.
- Cultura y ocio: proyección, audio inmersivo, LED, señalización digital.
- Coworking y coliving: salas de reunión, videoconferencia, señalización digital.

## 11. Posibles mejoras a revisar

### Fuentes

Actualmente depende mucho de Google News RSS. Conviene valorar añadir RSS sectoriales de:

- inmobiliario corporativo
- retail
- hotelería
- educación
- sanidad privada
- arquitectura y construcción
- ocio y cultura
- deporte e instalaciones

### Búsquedas

Puede faltar vocabulario como:

- `licencia de obras`
- `proyecto de reforma`
- `permisos para`
- `adquiere inmueble`
- `compra local`
- `implantación`
- `expansión nacional`
- `nuevas instalaciones`
- `centro logístico`
- `showroom`
- `sala inmersiva`

### Penalizaciones

Puede sobrar o ser demasiado duro:

- penalizar `ayuntamiento` si solo aparece como ubicación o trámite.
- penalizar `inaugura` cuando la noticia también anuncia una expansión futura.
- penalizar demasiado noticias de reapertura si la reapertura aún es futura.

### Sectores

Se podría separar mejor:

- hoteles urbanos
- resorts
- educación universitaria
- colegios internacionales
- clínicas dentales
- diagnóstico médico
- gimnasios boutique
- ocio familiar
- espacios inmersivos

## 12. Archivos que debes revisar para afinar el agente

Fuentes y búsquedas:

```text
config/sources.yaml
```

Palabras clave, señales temporales y necesidades probables:

```text
config/keywords.yaml
```

Puntuaciones:

```text
config/scoring.yaml
```

Email:

```text
config/email.yaml
```

Workflow del agente en GitHub:

```text
.github/workflows/daily_report.yml
```
