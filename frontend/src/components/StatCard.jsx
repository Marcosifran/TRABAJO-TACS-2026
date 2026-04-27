import styles from "./StatCard.module.css";

//Tarjetas

function StatCard({ icono, colorIcono, label, numero, descripcion, onClick }) {
  return (
    <div
      className={styles.card}
      onClick={onClick}
      style={{ cursor: onClick ? "pointer" : "default" }}
    >
      <div className={styles.icono} style={{ backgroundColor: colorIcono }}>
        {icono}
      </div>
      <div className={styles.contenido}>
        <span className={styles.label}>{label}</span>
        <span className={styles.numero}>{numero}</span>
        <span className={styles.descripcion}>{descripcion}</span>
      </div>
    </div>
  );
}

export default StatCard;