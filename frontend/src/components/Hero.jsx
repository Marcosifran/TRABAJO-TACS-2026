import styles from "./Hero.module.css";

function Hero({ totalPublicadas = 0, totalFaltantes = 0, totalIntercambios = 0 }) {
  return (
    <div className={styles.hero}>
      <div className={styles.etiqueta}>⭐ FIFA WORLD CUP 2026</div>

      <div className={styles.fila}>
        <div className={styles.izquierda}>
          <div className={styles.anillo}>
            <span className={styles.anilloPorcentaje}>0%</span>
            <span className={styles.anilloLabel}>completo</span>
          </div>
          <div>
            <h1 className={styles.titulo}>Tu Álbum de Figuritas</h1>
            <p className={styles.subtitulo}>
              Publicá tus repetidas, registrá tus faltantes
              <br />
              e intercambiá con otros coleccionistas.
            </p>
          </div>
        </div>

        <div className={styles.stats}>
          <div className={styles.stat}>
            <span className={styles.statNumero}>{totalPublicadas}</span>
            <span className={styles.statLabel}>En mi álbum</span>
          </div>
          <div className={styles.separador}></div>
          <div className={styles.stat}>
            <span className={styles.statNumeroRojo}>{totalFaltantes}</span>
            <span className={styles.statLabel}>Faltantes</span>
          </div>
          <div className={styles.separador}></div>
          <div className={styles.stat}>
            <span className={styles.statNumeroVerde}>{totalIntercambios}</span>
            <span className={styles.statLabel}>Intercambio/s</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Hero;