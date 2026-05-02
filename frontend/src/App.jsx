import { useState, useEffect, useCallback } from "react";
import Navbar from "./components/Navbar";
import Hero from "./components/Hero";
import StatCards from "./components/StatCards";
import FormFigurita from "./components/FormFigurita";
import GrillaFiguritas from "./components/GrillaFiguritas";
import { getMiAlbum, getMisPublicaciones, getMisFaltantes } from "./api/figuritas";
import SeccionFaltantes from "./components/SeccionFaltantes";
import SeccionBusqueda from "./components/SeccionBusqueda";

function App() {
  const [tabActiva, setTabActiva] = useState("Mi Álbum");
  const [miAlbum, setMiAlbum] = useState([]);
  const [misPublicaciones, setMisPublicaciones] = useState([]);
  const [misFaltantes, setMisFaltantes] = useState([]);

  const cargarDatos = useCallback(() => {
    getMiAlbum()
      .then(setMiAlbum)
      .catch((err) => console.error("Error cargando álbum:", err));

    getMisPublicaciones()
      .then(setMisPublicaciones)
      .catch((err) => console.error("Error cargando publicaciones:", err));

    getMisFaltantes()
      .then((data) => setMisFaltantes(data.faltantes))
      .catch((err) => console.error("Error cargando faltantes:", err));
  }, []);

  useEffect(() => {
    cargarDatos();
  }, [cargarDatos]);

  const duplicadas = miAlbum.filter((f) => f.cantidad > 1);
  const publicadas = miAlbum.filter((f) => f.en_intercambio);


  return (
    <div>
      <Navbar tabActiva={tabActiva} onTabChange={setTabActiva} />
      <Hero
        totalPublicadas={miAlbum.length}
        totalFaltantes={misFaltantes.length}
        totalIntercambios={0}
      />
      <StatCards
        totalAlbum={miAlbum.length}
        totalPublicadas={publicadas.length}
        totalFaltantes={misFaltantes.length}
        totalIntercambios={0}
        onTabChange={setTabActiva}
      />

      <div style={{
        display: "flex",
        gap: "24px",
        padding: "24px 32px",
        alignItems: "flex-start",
      }}>
        <div style={{ flex: 1 }}>
          {tabActiva === "Mi Álbum" && (
            <GrillaFiguritas
              figuritas={miAlbum}
              publicaciones={misPublicaciones}
              onCambio={cargarDatos}
            />
          )}
          {tabActiva === "Duplicadas" && (
            <GrillaFiguritas
              figuritas={duplicadas}
              publicaciones={misPublicaciones}
              onCambio={cargarDatos}
            />
          )}
          {tabActiva === "Faltantes" && (
            <SeccionFaltantes onChange={cargarDatos} />
          )}
          {tabActiva === "Intercambios" && (
            <SeccionBusqueda />
          )}
        </div>

        <div style={{ width: "320px", flexShrink: 0 }}>
          {tabActiva === "Mi Álbum" && (
            <FormFigurita onFiguritaPublicada={cargarDatos} />
          )}
        </div>
      </div>
    </div>
  );
}

export default App;