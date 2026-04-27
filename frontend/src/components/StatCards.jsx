import styles from "./StatCards.module.css";
import StatCard from "./StatCard";

function StatCards({totalAlbum, totalPublicadas, totalFaltantes, totalIntercambios, onTabChange }) {
  return (
    <div className={styles.fila}>
      <StatCard
        icono="📚"
        colorIcono="#f4a261"
        label="Mi Álbum"
        numero={totalAlbum}
        descripcion={`${totalPublicadas} en oferta`}
        onClick={() => onTabChange && onTabChange("Mi Álbum")}
      />
      <StatCard
        icono="🎯"
        colorIcono="#e63946"
        label="Faltantes"
        numero={totalFaltantes}
        descripcion="Todavía las necesito"
        onClick={() => onTabChange && onTabChange("Faltantes")}
      />
      <StatCard
        icono="🔄"
        colorIcono="#4361ee"
        label="Intercambios"
        numero={totalIntercambios}
        descripcion="Propuestas pendientes"
        onClick={() => onTabChange && onTabChange("Intercambios")}
      />
      <StatCard
        icono="⭐"
        colorIcono="#2a9d8f"
        label="Reputación"
        numero="—"
        descripcion="Sin calificaciones aún"
      />
    </div>
  );
}

export default StatCards;