import { useState, useEffect } from "react";
import Button from "../components/ui/Button";
import Tabs from "../components/ui/Tabs";
import Modal from "../components/ui/Modal";
import Input from "../components/ui/Input";
import EmptyState from "../components/ui/EmptyState";
import Snackbar from "../components/ui/Snackbar";
import { listarSubastas, crearSubasta, ofertarSubasta } from "../api/subastas";
import { listarMisPublicaciones } from "../api/publicaciones";
import { listarMiAlbum } from "../api/album";

const EMPTY_AUCTION = { figurita_id: "", duracion: "24" };

export default function AuctionsPage() {
  const [tab, setTab] = useState("activas");
  const [subastas, setSubastas] = useState([]);
  const [misPublicaciones, setMisPublicaciones] = useState([]);
  const [miAlbum, setMiAlbum] = useState([]);

  const [bidModal, setBidModal] = useState(null);
  const [offerIds, setOfferIds] = useState([]); // Array de IDs seleccionados

  const [createModal, setCreate] = useState(false);
  const [newAuction, setNewAuction] = useState(EMPTY_AUCTION);

  const [snack, setSnack] = useState({
    open: false,
    message: "",
    type: "info",
  });
  const [loading, setLoading] = useState(false);

  const cargarDatos = async () => {
    try {
      const [subs, pubs, album] = await Promise.all([
        listarSubastas(),
        listarMisPublicaciones(),
        listarMiAlbum(),
      ]);
      setSubastas(subs.subastas || []);
      // Filtro las publicaciones que el usuario marcó para subasta
      setMisPublicaciones(pubs.filter((p) => p.tipo_intercambio === "subasta"));
      setMiAlbum(album);
    } catch (error) {
      setSnack({
        open: true,
        message: "Error al cargar datos: " + error.message,
        type: "error",
      });
    }
  };

  useEffect(() => {
    cargarDatos();
  }, []);

  async function handleCreate() {
    if (!newAuction.figurita_id) {
      setSnack({
        open: true,
        message: "Seleccioná una publicación",
        type: "error",
      });
      return;
    }

    setLoading(true);
    try {
      const inicio = new Date();
      const fin = new Date();
      fin.setHours(fin.getHours() + Number(newAuction.duracion));

      await crearSubasta({
        figurita_id: Number(newAuction.figurita_id),
        inicio: inicio.toISOString(),
        fin: fin.toISOString(),
      });

      setSnack({
        open: true,
        message: "Subasta iniciada con éxito",
        type: "success",
      });
      setCreate(false);
      setNewAuction(EMPTY_AUCTION);
      cargarDatos();
    } catch (error) {
      setSnack({ open: true, message: error.message, type: "error" });
    } finally {
      setLoading(false);
    }
  }

  function toggleOferta(id) {
    setOfferIds((prev) =>
      prev.includes(id)
        ? prev.filter((offerId) => offerId !== id)
        : [...prev, id],
    );
  }

  async function handleOfertar() {
    if (offerIds.length === 0) {
      setSnack({
        open: true,
        message: "Seleccioná al menos una figurita",
        type: "error",
      });
      return;
    }

    setLoading(true);
    try {
      await ofertarSubasta(bidModal.id, offerIds);
      setSnack({
        open: true,
        message: "Oferta enviada con éxito",
        type: "success",
      });
      setBidModal(null);
      setOfferIds([]);
    } catch (error) {
      setSnack({ open: true, message: error.message, type: "error" });
    } finally {
      setLoading(false);
    }
  }

  // Preparamos las opciones para el select (solo publicaciones tipo subasta)
  const opcionesSubasta = misPublicaciones.map((p) => ({
    value: p.id,
    label: `Pub #${p.id} - ${p.jugador} (${p.equipo})`,
  }));
  opcionesSubasta.unshift({ value: "", label: "Seleccioná una figurita..." });

  return (
    <div className="p-8 max-w-[1000px]">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-on-surface m-0">Subastas</h1>
          <p className="mt-1 text-on-surface-variant text-sm">
            {subastas.length} subastas activas
          </p>
        </div>
        <Button icon="add" onClick={() => setCreate(true)}>
          Iniciar subasta
        </Button>
      </div>

      <Tabs
        tabs={[
          { id: "activas", label: "Activas" },
          { id: "mis", label: "Mis subastas" },
        ]}
        active={tab}
        onChange={setTab}
      />

      <div className="mt-5">
        {subastas.length === 0 ? (
          <EmptyState
            icon="gavel"
            title="Sin subastas"
            subtitle="No hay subastas en este momento."
            action="Iniciar subasta"
            onAction={() => setCreate(true)}
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {subastas.map((sub) => (
              <div
                key={sub.id}
                className="p-5 bg-surface rounded-2xl border border-outline-variant flex justify-between items-center shadow-sm"
              >
                <div>
                  <h3 className="font-bold text-lg text-primary">
                    Subasta #{sub.id}
                  </h3>
                  <p className="text-on-surface-variant text-sm mt-1">
                    Figurita Publicada: #{sub.figurita_id} <br />
                    Estado:{" "}
                    <span className="capitalize font-medium text-secondary">
                      {sub.estado}
                    </span>
                  </p>
                </div>
                <Button
                  variant="tonal"
                  icon="gavel"
                  onClick={() => {
                    setBidModal(sub);
                    setOfferIds([]);
                  }}
                >
                  Ofertar
                </Button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Bid Modal */}
      <Modal
        open={!!bidModal}
        onClose={() => setBidModal(null)}
        title={`Ofertar en Subasta #${bidModal?.id}`}
        width={520}
      >
        {bidModal && (
          <div className="flex flex-col gap-4">
            <p className="text-sm text-on-surface-variant">
              Seleccioná las figuritas de tu álbum que querés ofrecer a cambio:
            </p>

            {miAlbum.length === 0 ? (
              <div className="p-4 bg-error-container text-on-error-container rounded-lg text-sm">
                No tenés figuritas en tu álbum personal para ofrecer. Agregá
                figuritas desde Mi Colección.
              </div>
            ) : (
              <div className="max-h-[300px] overflow-y-auto grid grid-cols-2 gap-2 p-1">
                {miAlbum.map((fig) => (
                  <label
                    key={fig.id}
                    className={`flex items-center gap-3 p-3 border rounded-xl cursor-pointer transition-colors ${offerIds.includes(fig.id) ? "border-primary bg-primary-container/20" : "border-outline-variant hover:bg-surface-container-low"}`}
                  >
                    <input
                      type="checkbox"
                      className="w-4 h-4 accent-primary"
                      checked={offerIds.includes(fig.id)}
                      onChange={() => toggleOferta(fig.id)}
                    />
                    <div className="flex flex-col">
                      <span className="text-sm font-medium">{fig.jugador}</span>
                      <span className="text-xs text-on-surface-variant">
                        #{fig.numero} - {fig.equipo}
                      </span>
                    </div>
                  </label>
                ))}
              </div>
            )}

            <div className="flex gap-2.5 justify-end mt-4 pt-4 border-t border-outline-variant">
              <Button
                variant="text"
                onClick={() => setBidModal(null)}
                disabled={loading}
              >
                Cancelar
              </Button>
              <Button
                icon="gavel"
                onClick={handleOfertar}
                disabled={loading || offerIds.length === 0}
              >
                {loading ? "Enviando..." : `Enviar oferta (${offerIds.length})`}
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* Create Modal */}
      <Modal
        open={createModal}
        onClose={() => setCreate(false)}
        title="Iniciar subasta"
        width={480}
      >
        <div className="flex flex-col gap-4">
          <p className="text-sm text-on-surface-variant">
            Seleccioná una de tus publicaciones marcadas como "Subasta" para
            activarla.
          </p>

          {misPublicaciones.length === 0 ? (
            <div className="p-4 bg-error-container text-on-error-container rounded-lg text-sm">
              No tenés figuritas publicadas con tipo "Subasta". Ve a "Mi
              Colección", publicá una figurita y elegí la opción "Subasta".
            </div>
          ) : (
            <>
              <Input
                label="Figurita a Subastar"
                value={newAuction.figurita_id}
                onChange={(v) =>
                  setNewAuction({ ...newAuction, figurita_id: v })
                }
                options={opcionesSubasta}
              />
              <Input
                label="Duración (horas)"
                type="number"
                value={newAuction.duracion}
                onChange={(v) => setNewAuction({ ...newAuction, duracion: v })}
                icon="timer"
              />
            </>
          )}

          <div className="flex gap-2.5 justify-end mt-2 pt-4 border-t border-outline-variant">
            <Button
              variant="text"
              onClick={() => setCreate(false)}
              disabled={loading}
            >
              Cancelar
            </Button>
            <Button
              icon="gavel"
              onClick={handleCreate}
              disabled={loading || misPublicaciones.length === 0}
            >
              {loading ? "Iniciando..." : "Iniciar subasta"}
            </Button>
          </div>
        </div>
      </Modal>

      <Snackbar
        {...snack}
        onClose={() => setSnack({ ...snack, open: false })}
      />
    </div>
  );
}
