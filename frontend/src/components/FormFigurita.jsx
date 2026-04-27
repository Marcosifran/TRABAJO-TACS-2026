import { useState } from "react";
import styles from "./FormFigurita.module.css";
import { agregarAlAlbum, publicarFigurita } from "../api/figuritas";

const estadoInicial = {
  numero: "",
  equipo: "",
  jugador: "",
  cantidad: 1,
  tipo_intercambio: "intercambio_directo",
  publicar: true,
};

function FormFigurita({ onFiguritaPublicada }) {
  const [form, setForm] = useState(estadoInicial);
  const [cargando, setCargando] = useState(false);
  const [mensaje, setMensaje] = useState(null);

  function handleChange(e) {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  }

async function handleSubmit(e) {
  e.preventDefault();
  setCargando(true);
  setMensaje(null);

  try {
    const figuritaCreada = await agregarAlAlbum({
      numero: parseInt(form.numero),
      equipo: form.equipo,
      jugador: form.jugador,
      cantidad: parseInt(form.cantidad),
    });

    if (form.publicar) {
      await publicarFigurita(
        figuritaCreada.id,
        form.tipo_intercambio,
        parseInt(form.cantidad),
      );
    }

    const mensaje = form.publicar
      ? "¡Figurita agregada y publicada con éxito!"
      : "¡Figurita agregada al álbum!";

    setMensaje({ tipo: "exito", texto: mensaje });
    setForm(estadoInicial);
    if (onFiguritaPublicada) onFiguritaPublicada();

  } catch (error) {
    setMensaje({ tipo: "error", texto: error.message });
  } finally {
    setCargando(false);
  }
}

  return (
    <div className={styles.panel}>
      <h2 className={styles.titulo}>Publicar Figurita</h2>
      <p className={styles.subtitulo}>Agregá una repetida para intercambiar</p>

      <form className={styles.form} onSubmit={handleSubmit}>

        <div className={styles.fila}>
          <div className={styles.grupo}>
            <label className={styles.label}>Número</label>
            <input
              className={styles.input}
              type="number"
              name="numero"
              min="1"
              required
              value={form.numero}
              onChange={handleChange}
            />
          </div>
          <div className={styles.grupo}>
            <label className={styles.label}>Cantidad</label>
            <input
              className={styles.input}
              type="number"
              name="cantidad"
              min="1"
              required
              value={form.cantidad}
              onChange={handleChange}
            />
          </div>
        </div>

        <div className={styles.grupo}>
          <label className={styles.label}>Equipo</label>
          <input
            className={styles.input}
            type="text"
            name="equipo"
            required
            value={form.equipo}
            onChange={handleChange}
          />
        </div>

        <div className={styles.grupo}>
          <label className={styles.label}>Jugador</label>
          <input
            className={styles.input}
            type="text"
            name="jugador"
            required
            value={form.jugador}
            onChange={handleChange}
          />
        </div>
        <div className={styles.grupo} style={{ flexDirection: "row", alignItems: "center", gap: "10px" }}>
        <input
            type="checkbox"
            id="publicar"
            name="publicar"
            checked={form.publicar}
            onChange={(e) => setForm((prev) => ({ ...prev, publicar: e.target.checked }))}
            style={{ width: "18px", height: "18px", accentColor: "#e63946", cursor: "pointer" }}
        />
        <label htmlFor="publicar" className={styles.label} style={{ cursor: "pointer", marginBottom: 0 }}>
            Publicar para intercambio
        </label>
        </div>

        {form.publicar && (
        <div className={styles.grupo}>
            <label className={styles.label}>Tipo de intercambio</label>
            <select
            className={styles.select}
            name="tipo_intercambio"
            value={form.tipo_intercambio}
            onChange={handleChange}
            >
            <option value="intercambio_directo">Intercambio directo</option>
            <option value="subasta">Subasta</option>
            </select>
        </div>
        )}
        {mensaje && (
          <div className={mensaje.tipo === "exito" ? styles.mensajeExito : styles.mensajeError}>
            {mensaje.texto}
          </div>
        )}
        <button
          type="submit"
          className={styles.boton}
          disabled={cargando}
        >
          {cargando ? "Publicando..." : "Publicar Figurita"}
        </button>

      </form>
    </div>
  );
}

export default FormFigurita;