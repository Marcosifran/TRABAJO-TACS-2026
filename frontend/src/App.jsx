import { useState, useEffect } from "react";
import {
  Container,
  Typography,
  TextField,
  Button,
  Card,
  CardContent,
  Grid,
  List,
  ListItem,
  ListItemText,
  Divider,
  Box,
  Paper,
  IconButton,
} from "@mui/material";
import DeleteIcon from "@mui/icons-material/Delete";

// TODO: token hardcodeado temporalmente para desarrollo. Reemplazar por login real.
const API_BASE = "http://localhost:8000/api/v1";
const DEV_TOKEN = "test-token-user1";

function App() {
  const [figuritas, setFiguritas] = useState([]);
  const [nuevaFigurita, setNuevaFigurita] = useState({
    numero: "",
    equipo: "",
    jugador: "",
    cantidad: 1,
    permite_subasta: false,
  });

  useEffect(() => {
    fetch(`${API_BASE}/figuritas/`)
      .then((respuesta) => respuesta.json())
      .then((datos) => setFiguritas(datos.figuritasDisponibles))
      .catch((error) => console.error("Error al cargar:", error));
  }, []);

  const handleSubmit = async (evento) => {
    evento.preventDefault();
    const respuesta = await fetch(`${API_BASE}/figuritas/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-User-Token": DEV_TOKEN,
      },
      body: JSON.stringify(nuevaFigurita),
    });

    if (respuesta.ok) {
      const datosNuevos = await fetch(`${API_BASE}/figuritas/`).then(
        (res) => res.json(),
      );
      setFiguritas(datosNuevos.figuritasDisponibles);
      alert("¡Figurita guardada con éxito!");
      setNuevaFigurita({
        numero: "",
        equipo: "",
        jugador: "",
        cantidad: 1,
        permite_subasta: false,
      });
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm("¿Estás seguro de que querés borrar esta figurita?")) {
      const respuesta = await fetch(`${API_BASE}/figuritas/${id}`, {
        method: "DELETE",
        headers: { "X-User-Token": DEV_TOKEN },
      });
      if (respuesta.ok) {
        const datosNuevos = await fetch(`${API_BASE}/figuritas/`).then(
          (res) => res.json(),
        );
        setFiguritas(datosNuevos.figuritasDisponibles);
      } else {
        alert("Error al borrar");
      }
    }
  };

  return (
    <Box sx={{ bgcolor: "#f5f5f5", minHeight: "100vh", py: 4 }}>
      <Container maxWidth="lg">
        <Paper
          elevation={3}
          sx={{
            p: 3,
            mb: 4,
            textAlign: "center",
            bgcolor: "#1976d2",
            color: "white",
          }}
        >
          <Typography variant="h3" fontWeight="bold">
            🏆 Mundial Figuritas
          </Typography>
          <Typography variant="subtitle1">Plataforma de intercambio</Typography>
        </Paper>

        <Grid container spacing={4}>
          <Grid item xs={12} md={5}>
            <Card elevation={4} sx={{ borderRadius: 2 }}>
              <CardContent sx={{ p: 3 }}>
                <Typography
                  variant="h5"
                  color="primary"
                  fontWeight="bold"
                  gutterBottom
                >
                  Publicar Repetida
                </Typography>
                <Box
                  component="form"
                  onSubmit={handleSubmit}
                  sx={{
                    display: "flex",
                    flexDirection: "column",
                    gap: 2,
                    mt: 2,
                  }}
                >
                  <TextField
                    label="Número de figurita"
                    type="number"
                    variant="outlined"
                    required
                    value={nuevaFigurita.numero}
                    onChange={(e) =>
                      setNuevaFigurita({
                        ...nuevaFigurita,
                        numero: parseInt(e.target.value) || "",
                      })
                    }
                  />
                  <TextField
                    label="Equipo"
                    variant="outlined"
                    required
                    value={nuevaFigurita.equipo}
                    onChange={(e) =>
                      setNuevaFigurita({
                        ...nuevaFigurita,
                        equipo: e.target.value,
                      })
                    }
                  />
                  <TextField
                    label="Jugador"
                    variant="outlined"
                    required
                    value={nuevaFigurita.jugador}
                    onChange={(e) =>
                      setNuevaFigurita({
                        ...nuevaFigurita,
                        jugador: e.target.value,
                      })
                    }
                  />
                  <Button
                    type="submit"
                    variant="contained"
                    size="large"
                    sx={{ mt: 1, py: 1.5 }}
                  >
                    Guardar Figurita
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={7}>
            <Card elevation={4} sx={{ borderRadius: 2 }}>
              <CardContent sx={{ p: 3 }}>
                <Typography
                  variant="h5"
                  color="primary"
                  fontWeight="bold"
                  gutterBottom
                >
                  Disponibles para Intercambio
                </Typography>
                {figuritas.length === 0 ? (
                  <Typography color="text.secondary" sx={{ mt: 2 }}>
                    No hay figuritas cargadas todavía.
                  </Typography>
                ) : (
                  <List sx={{ mt: 1 }}>
                    {figuritas.map((figu, index) => (
                      <div key={figu.id}>
                        <ListItem
                          secondaryAction={
                            <IconButton
                              edge="end"
                              color="error"
                              onClick={() => handleDelete(figu.id)}
                            >
                              <DeleteIcon />
                            </IconButton>
                          }
                        >
                          <ListItemText
                            primary={
                              <Typography variant="h6">
                                #{figu.numero} - {figu.jugador}
                              </Typography>
                            }
                            secondary={
                              <Typography color="text.secondary">
                                Equipo: {figu.equipo}
                              </Typography>
                            }
                          />
                        </ListItem>
                        {index !== figuritas.length - 1 && <Divider />}
                      </div>
                    ))}
                  </List>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
}

export default App;
