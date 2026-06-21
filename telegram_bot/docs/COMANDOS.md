# FiguSwap Bot — Comandos de Telegram

## Inicio rápido

1. Buscá el bot en Telegram
2. Iniciá sesión: `/login email contraseña`
3. Explorá tus figuritas: `/mi_album`

---

## 🔐 Autenticación

| Comando | Descripción | Ejemplo |
|---|---|---|
| `/start` | Muestra la lista completa de comandos | `/start` |
| `/login email contraseña` | Inicia sesión con tu cuenta | `/login marcos@utn figuswap123` |
| `/logout` | Cierra la sesión actual | `/logout` |
| `/registro nombre email contraseña` | Crea una cuenta nueva | `/registro Marcos marcos@utn figuswap123` |

> La sesión se mantiene mientras el bot esté activo. Al reiniciar el bot, tenés que volver a hacer `/login`.

---

## 📚 Álbum

| Comando | Descripción | Ejemplo |
|---|---|---|
| `/mi_album` | Lista las figuritas de tu álbum con sus IDs | `/mi_album` |
| `/agregar numero cantidad` | Agrega una figurita al álbum (busca los datos en el maestro automáticamente) | `/agregar 10 2` |
| `/eliminar_figurita id` | Elimina una figurita del álbum | `/eliminar_figurita abc123` |

> El ID de cada figurita se muestra en `/mi_album`. Lo vas a necesitar para publicar.

---

## 🔍 Faltantes

| Comando | Descripción | Ejemplo |
|---|---|---|
| `/faltantes` | Lista tus figuritas faltantes | `/faltantes` |
| `/agregar_faltante numero` | Marca una figurita como faltante | `/agregar_faltante 42` |

---

## 📢 Publicaciones

Las publicaciones son figuritas que ponés a disposición para intercambio directo o subasta.

| Comando | Descripción | Ejemplo |
|---|---|---|
| `/publicaciones` | Lista las publicaciones de otros usuarios | `/publicaciones` |
| `/mis_publicaciones` | Lista tus publicaciones activas | `/mis_publicaciones` |
| `/publicar figurita_id tipo cantidad` | Publica una figurita de tu álbum | `/publicar abc123 directo 1` |
| `/retirar id` | Retira una publicación | `/retirar xyz789` |
| `/sugerencias` | Muestra publicaciones que cubren tus faltantes | `/sugerencias` |

**Tipos de publicación:**
- `directo` — intercambio directo con otro usuario
- `subasta` — subasta pública

> El `figurita_id` se obtiene en `/mi_album`. El `id` de la publicación se obtiene en `/mis_publicaciones`.

---

## 🔄 Intercambios directos

| Comando | Descripción | Ejemplo |
|---|---|---|
| `/intercambios` | Lista tus intercambios (enviados y recibidos) | `/intercambios` |
| `/proponer usuario_id num_ofrecida num_solicitada` | Propone un intercambio a otro usuario | `/proponer 2 10 42` |
| `/proponer usuario_id num1,num2,num3 num_solicitada` | Propone un intercambio ofreciendo varias figuritas | `/proponer 2 10,15,20 42` |
| `/aceptar_intercambio id` | Acepta un intercambio recibido | `/aceptar_intercambio abc123` |
| `/rechazar_intercambio id` | Rechaza un intercambio recibido | `/rechazar_intercambio abc123` |

> Los números de figuritas ofrecidas se separan con coma y sin espacios: `10,15,20`.
> Encontrá los IDs de usuario en `/usuarios` y los IDs de intercambio en `/intercambios`.

---

## 🏷 Subastas

| Comando | Descripción | Ejemplo |
|---|---|---|
| `/subastas` | Lista las subastas activas | `/subastas` |
| `/mis_subastas` | Lista tus subastas | `/mis_subastas` |
| `/crear_subasta publicacion_id horas` | Crea una subasta que dura N horas | `/crear_subasta abc123 24` |
| `/ofertar subasta_id figurita_id` | Oferta en una subasta con una o más figuritas de tu álbum | `/ofertar abc123 xyz456` |
| `/ofertar subasta_id fig1 fig2 fig3` | Oferta con varias figuritas | `/ofertar abc123 id1 id2 id3` |
| `/cancelar_subasta id` | Cancela una subasta propia | `/cancelar_subasta abc123` |

> El `publicacion_id` se obtiene en `/mis_publicaciones`.
> Los IDs de figuritas para ofertar se obtienen en `/mi_album`.

---

## 🔎 Maestro de figuritas

Consultas de referencia sobre el catálogo oficial. No requieren sesión iniciada.

| Comando | Descripción | Ejemplo |
|---|---|---|
| `/buscar numero` | Muestra los datos de una figurita por número | `/buscar 10` |
| `/equipos` | Lista todos los equipos del álbum | `/equipos` |

---

## 👥 Usuarios

| Comando | Descripción | Ejemplo |
|---|---|---|
| `/usuarios` | Lista todos los usuarios registrados con sus IDs | `/usuarios` |

---

## 📊 Administración

Solo disponible para usuarios con rol administrador.

| Comando | Descripción | Ejemplo |
|---|---|---|
| `/estadisticas` | Muestra estadísticas generales del sistema | `/estadisticas` |

---

## Flujo de ejemplo completo

```
# 1. Iniciar sesión
/login marcos@utn figuswap123

# 2. Ver mis figuritas y anotar el ID de una duplicada
/mi_album

# 3. Publicarla para intercambio directo
/publicar <figurita_id> directo 1

# 4. Ver qué hay disponible de otros usuarios
/publicaciones

# 5. Ver sugerencias que cubren mis faltantes
/sugerencias

# 6. Proponer un intercambio (ofrezco la #10, pido la #42, al usuario 2)
/proponer 2 10 42

# 7. El usuario 2 acepta
/aceptar_intercambio <id>
```
