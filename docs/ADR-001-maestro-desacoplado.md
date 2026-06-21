# ADR-001: Desacoplamiento del Maestro de Figuritas de la Entidad de Usuario

---

## Contexto

El sistema maneja dos tipos de datos relacionados con figuritas:

1. **Datos de referencia** (catálogo): información oficial de cada figurita del Mundial 2026 — número secuencial, jugador, equipo, posición, número de camiseta. Esta información proviene de un scraping de Wikipedia y es igual para todos los usuarios.

2. **Datos de usuario**: qué figuritas tiene cada usuario en su álbum, cuáles le faltan, cuáles publicó para intercambio.

La pregunta de diseño es: ¿los datos del catálogo deben vivir *dentro* de cada entidad de usuario (embebidos) o en una colección separada (referenciados)?

---

## Decisión

Se mantienen **desacoplados** en dos colecciones independientes:

- `maestro_figuritas`: catálogo global de referencia, generado por el scraper. Contiene `numero`, `equipo`, `jugador`, `posicion`, `numero_camiseta`.
- `album`, `publicaciones`, `intercambios`, etc.: solo almacenan el `numero` de figurita como clave foránea lógica. Los datos del jugador se obtienen consultando el maestro cuando se necesitan.

---

## Alternativas consideradas

### Alternativa A — Datos embebidos

Cada entrada del álbum o publicación guardaría todos los datos del jugador:

```json
{
  "usuario_id": 7,
  "numero": 42,
  "jugador": "Lionel Messi",
  "equipo": "Argentina",
  "posicion": "FW",
  "numero_camiseta": 10,
  "cantidad": 2
}
```

**Por qué se rechazó:**
- **Duplicación masiva**: si 500 usuarios tienen la figurita 42, los datos de Messi se guardan 500 veces.
- **Inconsistencia ante cambios**: si un dato del maestro cambia (ej. corrección de nombre), habría que actualizar miles de documentos de usuario.
- **Mayor tamaño de documentos**: impacto en performance de lectura y almacenamiento.

### Alternativa B — Referencia por `_id` de MongoDB

Guardar el `ObjectId` de MongoDB del maestro como referencia en documentos de usuario.

**Por qué se descartó:**
- El `_id` de MongoDB cambia si la colección se elimina y se regenera (ej. al hacer `refresh()` del maestro).
- Eso rompería todas las referencias en álbumes de usuarios aunque los jugadores sean exactamente los mismos.

### Alternativa C — Referencia por `numero` (decisión adoptada)

Usar el número secuencial de figurita como clave de referencia lógica.

---

## Justificación de la decisión adoptada

El `numero` de figurita es estable por diseño: se asigna una sola vez en el primer scraping y no cambia mientras existan datos de usuario en el sistema. El maestro actúa como tabla de lookup de solo lectura para el resto del sistema.

---

## Consecuencias positivas

- **Una sola fuente de verdad**: los datos del jugador viven en un único lugar.
- **Ciclos de vida independientes**: el scraper puede actualizarse o corregirse sin afectar las colecciones de usuario, siempre que los números de figurita no cambien.
- **Escalabilidad**: agregar nuevos campos al maestro (ej. foto, estadísticas) no requiere migrar documentos de usuario.
- **Consistencia garantizada**: cualquier corrección en el maestro se refleja automáticamente en toda la UI sin tocar datos de usuario.

---

## Riesgos y mitigaciones

### Riesgo principal: desincronización por regeneración del maestro

Si se ejecuta `POST /maestro/refresh` y Wikipedia cambió el orden de los planteles, los números de figurita se reasignan distinto. Esto dejaría los álbumes de usuario apuntando a números incorrectos.

**Mitigación actual:** el endpoint `refresh` está documentado con advertencia explícita y debe usarse solo antes de que existan datos de usuario en producción.

**Mitigación futura sugerida:** generar un `id` determinístico (hash de `equipo + numero_camiseta`) en lugar de un número secuencial como clave primaria, de modo que el maestro pueda regenerarse sin romper referencias.

### Riesgo secundario: múltiples instancias del backend

Al levantar una segunda instancia del backend contra la misma base de datos, `inicializar()` detecta que la colección ya tiene datos (`count() > 0`) y omite el scraping. Ambas instancias comparten el mismo maestro de Atlas sin duplicar datos.
