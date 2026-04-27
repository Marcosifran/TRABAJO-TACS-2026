import { useState } from "react";
import styles from "./GrillaFiguritas.module.css";
import { eliminarDelAlbum, retirarPublicacion } from "../api/figuritas";

const TABS = ["Todas", "En intercambio", "Sin publicar"];

/**
 * Grilla de figuritas del álbum personal del usuario.
 *
 * Props:
 *   figuritas          - lista de figuritas del álbum (con campo en_intercambio)
 *   publicaciones      - lista de publicaciones activas del usuario
 *   onCambio           - función que el padre ejecuta cuando hay un cambio
 *                        (publicar, retirar o eliminar) para recargar los datos
 */
function GrillaFiguritas({ figuritas, publicaciones, onCambio }) {
  const [tabActiva, setTabActiva] = useState("Todas");
  const [cargando, setCargando] = useState(null);
  // cargando guarda el id de la figurita que está en proceso
  // para mostrar feedback visual solo en esa card

  // Filtramos según la tab activa
  const figuritasFiltradas = figuritas.filter((f) => {
    if (tabActiva === "En intercambio") return f.en_intercambio;
    if (tabActiva === "Sin publicar")   return !f.en_intercambio;
    return true;
  });

  // Busca la publicación activa de una figurita del álbum
  function getPublicacion(figurita_id) {
    return publicaciones.find((p) => p.figurita_personal_id === figurita_id);
  }

  async function handleRetirar(figurita) {
    const pub = getPublicacion(figurita.id);
    if (!pub) return;
    setCargando(figurita.id);
    try {
      await retirarPublicacion(pub.id);
      onCambio();
    } catch (err) {
      console.error(err);
    } finally {
      setCargando(null);
    }
  }

  async function handleEliminar(figurita) {
    setCargando(figurita.id);
    try {
      await eliminarDelAlbum(figurita.id);
      onCambio();
    } catch (err) {
      console.error(err);
    } finally {
      setCargando(null);
    }
  }

  return (
    <div className={styles.contenedor}>

      {/* Cabecera con título y tabs */}
      <div className={styles.cabecera}>
        <h2 className={styles.titulo}>Mi Álbum</h2>
        <div className={styles.tabs}>
          {TABS.map((tab) => (
            <button
              key={tab}
              onClick={() => setTabActiva(tab)}
              className={tab === tabActiva ? styles.tabActiva : styles.tab}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Grilla de cards */}
      <div className={styles.grilla}>
        {figuritasFiltradas.length === 0 ? (
          <p className={styles.vacio}>
            {tabActiva === "Todas"
              ? "Tu álbum está vacío. ¡Publicá tu primera figurita!"
              : "No hay figuritas en esta categoría."}
          </p>
        ) : (
          figuritasFiltradas.map((figurita) => (
            <CardFigurita
              key={figurita.id}
              figurita={figurita}
              publicacion={getPublicacion(figurita.id)}
              cargando={cargando === figurita.id}
              onRetirar={() => handleRetirar(figurita)}
              onEliminar={() => handleEliminar(figurita)}
            />
          ))
        )}
      </div>

    </div>
  );
}

/**
 * Card individual de una figurita del álbum.
 * Muestra el badge según su estado y los botones de acción correspondientes.
 */
function CardFigurita({ figurita, publicacion, cargando, onRetirar, onEliminar }) {
  const tipo = publicacion?.tipo_intercambio;

  return (
    <div className={styles.card}>

      <span className={styles.cardNumero}>#{figurita.numero}</span>
      <span className={styles.cardJugador}>{figurita.jugador}</span>
      <span className={styles.cardEquipo}>{figurita.equipo}</span>

      {/* Badge de estado */}
      {figurita.en_intercambio ? (
        <span className={tipo === "subasta" ? styles.badgeSubasta : styles.badgeIntercambio}>
          {tipo === "subasta" ? "Subasta" : "En oferta"}
        </span>
      ) : (
        <span className={styles.badgeSinPublicar}>Sin publicar</span>
      )}

      {/* Botones de acción */}
      {figurita.en_intercambio ? (
        <button
          className={styles.botonRetirar}
          onClick={onRetirar}
          disabled={cargando}
        >
          {cargando ? "..." : "Retirar oferta"}
        </button>
      ) : (
        <button
          className={styles.botonEliminar}
          onClick={onEliminar}
          disabled={cargando}
        >
          {cargando ? "..." : "Eliminar"}
        </button>
      )}

    </div>
  );
}

export default GrillaFiguritas;