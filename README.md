# Private Project Finder

Programa local en Python para detectar señales diarias de proyectos físicos privados donde podrían aparecer necesidades futuras de integración tecnológica en espacios.

El programa consulta RSS, aplica una puntuación configurable, guarda histórico en CSV y genera un informe HTML diario.

Para auditar en qué se basa el agente, revisa:

```text
docs/criterios_de_busqueda_y_clasificacion.md
```

## Requisitos

- Windows 10 u 11.
- Python 3.10 o superior.
- Conexión a internet para consultar fuentes RSS.

## Instalar Python en Windows

1. Entra en la página oficial de Python: https://www.python.org/downloads/windows/
2. Descarga la versión estable más reciente para Windows.
3. Durante la instalación, marca la opción `Add python.exe to PATH`.
4. Comprueba la instalación en PowerShell:

```powershell
python --version
```

## Crear entorno virtual

Desde la carpeta del proyecto:

```powershell
cd private_project_finder
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la activación del entorno, ejecuta:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Después vuelve a activar el entorno virtual.

## Instalar dependencias

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Ejecutar

```powershell
python main.py
```

El programa generará o actualizará:

- `data/opportunities.csv`
- `data/sources_catalog.xlsx`
- `reports/daily_report_YYYY-MM-DD.html`

Al terminar, la consola muestra el número de noticias encontradas, oportunidades por prioridad y la ruta del informe HTML generado.

## Catálogo de fuentes

El agente mantiene un Excel acumulado con las fuentes de información detectadas:

```text
data/sources_catalog.xlsx
```

Este archivo tiene una fila por web principal, no una fila por noticia.

Columnas:

- `Fuente`: dominio principal de la fuente.
- `numero de apariciones`: cuántas veces ha aparecido esa fuente.
- `sectores`: sectores en los que ha aparecido, acumulados sin repetir.
- `ultima aparicion`: última fecha en la que apareció.
- `prioridad maxima encontrada`: prioridad más alta que generó esa fuente.

Ejemplo de comportamiento:

Si una fuente aparece por primera vez, se añade una fila nueva. Si vuelve a aparecer, no se crea otra fila: se actualizan apariciones, sectores, última aparición y prioridad máxima.

En GitHub Actions, este Excel también se guarda como artefacto descargable de cada ejecución.

## Fuentes directas RSS

Además de Google News RSS, el agente puede consultar fuentes concretas directamente si tienen RSS.

Están configuradas en:

```text
config/sources.yaml
```

Sección:

```yaml
additional_rss:
  - name: EjePrime
    enabled: true
    sector: Inmobiliario
    url: https://www.ejeprime.com/rss.xml

  - name: Modaes
    enabled: true
    sector: Retail
    url: https://www.modaes.com/rss.xml
```

Estas fuentes se consultan en cada ejecución, independientemente de que Google News las muestre o no en una búsqueda concreta.

## Envío por email

El proyecto puede enviar el informe HTML como adjunto al terminar la ejecución.

La configuración está en:

```text
config/email.yaml
```

Configuración actual:

```yaml
email:
  enabled: true
  provider: gmail
  smtp_host: smtp.gmail.com
  smtp_port: 587
  from_address: buscadoragente@gmail.com
  to:
    - javicsilva@gmail.com
  attach_html: true
  summary_level: basico
```

La contraseña no se guarda en el proyecto. Para Gmail necesitas crear una contraseña de aplicación en la cuenta remitente y definir estas variables de entorno en Windows:

```powershell
setx SMTP_USER "buscadoragente@gmail.com"
setx SMTP_PASSWORD "contraseña_de_aplicacion"
```

Cierra y vuelve a abrir PowerShell después de usar `setx`.

Para probar en la sesión actual sin reiniciar PowerShell:

```powershell
$env:SMTP_USER="buscadoragente@gmail.com"
$env:SMTP_PASSWORD="contraseña_de_aplicacion"
python main.py
```

Si faltan esas variables, el programa genera el informe igualmente y muestra un aviso indicando que el email no se ha enviado.

## Filtro temporal

El funcionamiento diario normal es estricto: el programa pide y analiza noticias publicadas en las últimas 48 horas.

La configuración está en:

```text
config/sources.yaml
```

Valores principales:

```yaml
max_news_age_hours: 48
initial_backfill_enabled: false
initial_backfill_days: 7
```

Cuando se usan búsquedas de Google News RSS, el programa añade automáticamente un filtro temporal a cada búsqueda:

- `when:2d` si `max_news_age_hours` es 48 o menos.
- `when:3d` si `max_news_age_hours` es 72.
- `when:7d` si se activa la carga inicial con `initial_backfill_enabled: true` y `initial_backfill_days: 7`.

Con `initial_backfill_enabled: false`, se usa siempre `max_news_age_hours`. Si quieres una primera carga más amplia, cambia temporalmente:

```yaml
initial_backfill_enabled: true
```

En ese caso se usará `initial_backfill_days`. Después de la primera carga, conviene volver a dejarlo en `false` para mantener el informe diario limitado a las últimas 48 horas.

Reglas aplicadas:

- Una noticia anterior al rango activo se marca como `Descartada` por `noticia antigua`.
- Una noticia con fecha futura absurda o mal interpretada se marca como `Descartada`.
- Una noticia sin fecha clara se penaliza y no puede ser prioridad `Alta`.
- El CSV histórico no se borra.
- El informe HTML diario muestra solo noticias recientes de la ejecución actual.
- Las noticias antiguas se cuentan en el resumen, pero no se listan una por una en el HTML.
- Si no hay oportunidades recientes, el informe muestra un aviso claro en el resumen ejecutivo.

## Editar búsquedas

Las búsquedas están en:

```text
config/sources.yaml
```

Cada bloque tiene un `sector` y una lista `terms`. Puedes añadir, cambiar o quitar búsquedas sin tocar el código.

También puedes añadir fuentes RSS concretas en `additional_rss`:

```yaml
additional_rss:
  - name: Fuente sectorial
    enabled: true
    sector: Hoteles
    url: https://example.com/feed.xml
```

## Editar palabras clave

Las palabras clave están en:

```text
config/keywords.yaml
```

Ahí puedes ajustar:

- Señales positivas.
- Señales negativas.
- Sectores prioritarios.
- Tipos de proyecto.
- Ciudades o zonas.
- Necesidades tecnológicas probables por sector.

## Editar puntuación

Las reglas de puntuación están en:

```text
config/scoring.yaml
```

La clasificación se interpreta así:

- `Alta`: 75 a 100 puntos.
- `Media`: 50 a 74 puntos.
- `Baja`: 25 a 49 puntos.
- `Descartada`: 0 a 24 puntos.

Los duplicados se detectan por URL y por similitud de título. El umbral se puede cambiar en `deduplication.title_similarity_threshold`.

## Prioridad por fase del proyecto

El programa prioriza oportunidades futuras, no proyectos que ya parecen ejecutados.

Se consideran señales positivas las noticias que indiquen planificación, obra, reforma, inversión o próxima apertura. Por ejemplo:

- `abrirá`
- `prevé abrir`
- `prepara apertura`
- `iniciará obras`
- `en construcción`
- `en desarrollo`
- `reformará`
- `ampliará`
- `plan de expansión`
- `aperturas previstas`

Se penalizan con fuerza las noticias que indiquen que el espacio ya está inaugurado o ya ha abierto. Por ejemplo:

- `inaugura`
- `ha inaugurado`
- `inauguró`
- `ya ha abierto`
- `abrió`
- `ha abierto sus puertas`
- `estrena sede`
- `acaba de inaugurar`

Si una noticia está ya inaugurada y no incluye una fase futura adicional clara, no puede ser prioridad `Alta` ni `Media`; como máximo será `Baja`.

Excepción: si la misma noticia habla de algo ya inaugurado pero además anuncia una fase futura clara, se mantiene la penalización, pero puede subir si las señales futuras son suficientemente fuertes.

El informe muestra:

- `fase_detectada`: `futuro`, `en planificación`, `en obra/reforma`, `próxima apertura`, `ya inaugurado` o `desconocida`.
- `timing_reason`: explicación de la fase detectada.

## Interpretar el informe

El informe HTML incluye:

- Resumen ejecutivo.
- Noticias encontradas.
- Noticias dentro del rango temporal.
- Oportunidades Alta.
- Oportunidades Media.
- Oportunidades Baja.
- Descartadas recientes por otros motivos en sección separada.
- Descartadas por antigüedad solo como contador.
- Penalizadas por estar ya inauguradas como contador.
- Fase detectada y motivo temporal.
- Enlaces clicables.
- Motivo de clasificación.
- Acción sugerida.

Una oportunidad `Alta` no significa venta inmediata. Significa que la noticia contiene señales de proyecto físico privado, ubicación, operador, apertura, reforma u otros indicadores que merecen revisión manual.

## Configurar el Programador de tareas de Windows

1. Abre `Programador de tareas`.
2. Crea una tarea básica.
3. Elige frecuencia diaria y hora `10:00`.
4. En acción, selecciona `Iniciar un programa`.
5. En `Programa o script`, usa la ruta del Python del entorno virtual:

```text
C:\ruta\al\proyecto\private_project_finder\.venv\Scripts\python.exe
```

6. En `Agregar argumentos`, escribe:

```text
main.py
```

7. En `Iniciar en`, escribe la carpeta del proyecto:

```text
C:\ruta\al\proyecto\private_project_finder
```

8. Guarda la tarea y ejecuta una prueba manual.

## Automatizar en la nube con GitHub Actions

Si quieres que el informe se envíe aunque el portátil esté apagado, usa GitHub Actions.

Pasos:

1. Sube este proyecto a un repositorio privado de GitHub.
2. En GitHub, entra en `Settings > Secrets and variables > Actions`.
3. Crea estos secretos:

```text
SMTP_USER=buscadoragente@gmail.com
SMTP_PASSWORD=contraseña_de_aplicacion
```

4. El workflow está en:

```text
.github/workflows/daily_report.yml
```

5. Se ejecuta automáticamente a las `10:00` hora España.
6. También puedes lanzarlo manualmente desde `Actions > Daily opportunity report > Run workflow`.

GitHub programa los cron en UTC. Para evitar problemas con el cambio de horario, el workflow se despierta a las 08:00 y 09:00 UTC, comprueba la hora real en `Europe/Madrid` y solo ejecuta el informe cuando allí son las 10:00.

El informe HTML se envía por email y además queda como artefacto descargable en la ejecución de GitHub Actions.

## Notas

- El envío de email usa SMTP y solo funciona si las variables de entorno están configuradas.
- Esta versión no usa base de datos.
- Esta versión no hace scraping agresivo: consulta RSS y aplica pausas entre búsquedas.
- Los resultados deben revisarse manualmente antes de tomar decisiones.
