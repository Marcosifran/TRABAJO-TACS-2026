import { useState, useEffect } from "react";
import { getPublicaciones } from "../api/figuritas";
import styles from "./SeccionBusqueda.module.css";

function SeccionBusqueda() {
  const [publicaciones, setPublicaciones] = useState([]);
  const [cargando, setCargando] = useState(false);
  const [filtros, setFiltros] = useState({
    numero: "",
    equipo: "",
    jugador: "",
    tipo_intercambio: "",
  });

  function cargar(filtrosActuales) {
    setCargando(true);
    getPublicaciones(filtrosActuales)
      .then(setPublicaciones)
      .catch((err) => console.error(err))
      .finally(() => setCargando(false));
  }

  useEffect(() => {
    cargar(filtros);
  }, []);

  function handleFiltro(e) {
    const { name, value } = e.target;
    const nuevos = { ...filtros, [name]: value };
    setFiltros(nuevos);
    cargar(nuevos);
  }

  function handleLimpiar() {
    const vacios = { numero: "", equipo: "", jugador: "", tipo_intercambio: "" };
    setFiltros(vacios);
    cargar(vacios);
  }

  return (
    <div className={styles.contenedor}>

      <div className={styles.filtros}>
        <input
          className={styles.input}
          type="number"
          name="numero"
          placeholder="Número"
          value={filtros.numero}
          onChange={handleFiltro}
          min="1"
        />
        <input
          className={styles.input}
          type="text"
          name="equipo"
          placeholder="Equipo"
          value={filtros.equipo}
          onChange={handleFiltro}
        />
        <input
          className={styles.input}
          type="text"
          name="jugador"
          placeholder="Jugador"
          value={filtros.jugador}
          onChange={handleFiltro}
        />
        <select
          className={styles.select}
          name="tipo_intercambio"
          value={filtros.tipo_intercambio}
          onChange={handleFiltro}
        >
          <option value="">Todos los tipos</option>
          <option value="intercambio_directo">Intercambio directo</option>
          <option value="subasta">Subasta</option>
        </select>
        <button className={styles.botonLimpiar} onClick={handleLimpiar}>
          Limpiar
        </button>
      </div>

      <div className={styles.cabecera}>
        <h2 className={styles.titulo}>Figuritas disponibles</h2>
        <span className={styles.contador}>{publicaciones.length} encontradas</span>
      </div>

      {cargando ? (
        <p className={styles.vacio}>Cargando...</p>
      ) : publicaciones.length === 0 ? (
        <p className={styles.vacio}>No hay figuritas disponibles con esos filtros.</p>
      ) : (
        <div className={styles.grilla}>
          {publicaciones.map((pub) => (
            <CardPublicacion key={pub.id} publicacion={pub} />
          ))}
        </div>
      )}

    </div>
  );
}

function CardPublicacion({ publicacion }) {
  const esSubasta = publicacion.tipo_intercambio === "subasta";

  return (
    <div className={styles.card}>
      <span className={styles.cardNumero}>#{publicacion.numero}</span>
      <span className={styles.cardJugador}>{publicacion.jugador}</span>
      <span className={styles.cardEquipo}>{publicacion.equipo}</span>
      <span className={styles.cardCantidad}>
        Cantidad: {publicacion.cantidad_disponible}
      </span>
      <span className={esSubasta ? styles.badgeSubasta : styles.badgeIntercambio}>
        {esSubasta ? "Subasta" : "Intercambio directo"}
      </span>
    </div>
  );
}

export default SeccionBusqueda;