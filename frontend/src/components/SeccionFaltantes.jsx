import { useState, useEffect } from "react";
import { getMisFaltantes, registrarFaltante } from "../api/figuritas";
import styles from "./SeccionFaltantes.module.css";

function SeccionFaltantes({onChange}) {
  const [faltantes, setFaltantes] = useState([]);
  const [numero, setNumero] = useState("");
  const [mensaje, setMensaje] = useState(null);
  const [cargando, setCargando] = useState(false);


  function cargarFaltantes() {
    getMisFaltantes()
      .then((data) => setFaltantes(data.faltantes))
      .catch((err) => console.error(err));
  }

  useEffect(() => {
    cargarFaltantes();
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!numero) return;
    setCargando(true);
    setMensaje(null);

    try {
      await registrarFaltante(parseInt(numero));
      setMensaje({ tipo: "exito", texto: `Figurita #${numero} registrada como faltante` });
      setNumero("");
      cargarFaltantes();
      if(onChange) onChange();
    } catch (err) {
      setMensaje({ tipo: "error", texto: err.message });
    } finally {
      setCargando(false);
    }
  }

  return (
    <div className={styles.contenedor}>

      {/* Formulario */}
      <div className={styles.panel}>
        <h2 className={styles.titulo}>Registrar Faltante</h2>
        <p className={styles.subtitulo}>Anotá las figuritas que te faltan para completar el álbum</p>

        <form className={styles.form} onSubmit={handleSubmit}>
          <div className={styles.fila}>
            <input
              className={styles.input}
              type="number"
              min="1"
              placeholder="Número de figurita"
              value={numero}
              onChange={(e) => setNumero(e.target.value)}
              required
            />
            <button
              type="submit"
              className={styles.boton}
              disabled={cargando}
            >
              {cargando ? "..." : "Agregar"}
            </button>
          </div>

          {mensaje && (
            <div className={mensaje.tipo === "exito" ? styles.mensajeExito : styles.mensajeError}>
              {mensaje.texto}
            </div>
          )}
        </form>
      </div>

      {/* Lista de faltantes */}
      <div className={styles.lista}>
        <h3 className={styles.listaTitulo}>
          Mis Faltantes
          <span className={styles.contador}>{faltantes.length}</span>
        </h3>

        {faltantes.length === 0 ? (
          <p className={styles.vacio}>No tenés faltantes registrados.</p>
        ) : (
          <div className={styles.chips}>
            {faltantes.map((f) => (
              <span key={f.id} className={styles.chip}>
                #{f.numero_figurita}
              </span>
            ))}
          </div>
        )}
      </div>

    </div>
  );
}

export default SeccionFaltantes;