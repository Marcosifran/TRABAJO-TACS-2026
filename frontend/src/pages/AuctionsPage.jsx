import { useState, useEffect } from "react";
import Button from "../components/ui/Button";
import Tabs from "../components/ui/Tabs";
import Modal from "../components/ui/Modal";
import Input from "../components/ui/Input";
import EmptyState from "../components/ui/EmptyState";
import Snackbar from "../components/ui/Snackbar";
import { listarSubastas, listarMisSubastas, crearSubasta, ofertarSubasta, listarOfertas, listarMisOfertas, cancelarOferta } from "../api/subastas";
import { listarMisPublicaciones, buscarPublicaciones } from "../api/publicaciones";
import { listarMiAlbum } from "../api/album";
import { useUser } from "../context/UserContext";

const EMPTY_AUCTION = { figurita_id: "", duracion: "24" };

export default function AuctionsPage() {
  const { user, users } = useUser()
  const [tab, setTab] = useState("activas");
  const [subastas, setSubastas] = useState([]);
  const [misSubastas, setMisSubastas] = useState([]);
  const [misPublicaciones, setMisPublicaciones] = useState([]);
  const [miAlbum, setMiAlbum] = useState([]);
  const [pubsMap, setPubsMap] = useState({});

  const [bidModal, setBidModal] = useState(null);
  const [offerIds, setOfferIds] = useState([]);
  const [offersModal, setOffersModal] = useState(null);
  const [ofertas, setOfertas] = useState([]);
  const [loadingOfertas, setLoadingOfertas] = useState(false);
  const [misOfertas, setMisOfertas] = useState([]);
  const [loadingMisOfertas, setLoadingMisOfertas] = useState(false);

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
      const [subs, misSubs, pubs, otrasPubs, album] = await Promise.all([
        listarSubastas(),
        listarMisSubastas(),
        listarMisPublicaciones(),
        buscarPublicaciones(),
        listarMiAlbum(),
      ]);
      setSubastas(subs.subastas || []);
      setMisSubastas(misSubs.subastas || []);
      setMisPublicaciones(pubs.filter((p) => p.tipo_intercambio === "subasta"));
      setMiAlbum(album);
      const map = {}
      ;[...pubs, ...otrasPubs].forEach(p => { map[p.id] = p })
      setPubsMap(map);
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

  async function cargarMisOfertas() {
    setLoadingMisOfertas(true)
    try {
      const data = await listarMisOfertas()
      setMisOfertas(data.ofertas || [])
    } catch (e) {
      setSnack({ open: true, message: e.message, type: 'error' })
    } finally {
      setLoadingMisOfertas(false)
    }
  }

  async function handleCancelarOferta(oferta) {
    try {
      await cancelarOferta(oferta.subasta_id, oferta.id)
      setMisOfertas(prev => prev.filter(o => o.id !== oferta.id))
      setSnack({ open: true, message: 'Oferta cancelada', type: 'info' })
    } catch (e) {
      setSnack({ open: true, message: e.message, type: 'error' })
    }
  }

  async function abrirOfertas(sub) {
    setOffersModal(sub)
    setOfertas([])
    setLoadingOfertas(true)
    try {
      const data = await listarOfertas(sub.id)
      setOfertas(data.ofertas || [])
    } catch (e) {
      setSnack({ open: true, message: e.message, type: 'error' })
    } finally {
      setLoadingOfertas(false)
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
          { id: "ofertas", label: "Mis ofertas" },
        ]}
        active={tab}
        onChange={t => { setTab(t); if (t === 'ofertas') cargarMisOfertas() }}
      />

      <div className="mt-5">
        {tab === 'ofertas' ? (
          loadingMisOfertas ? (
            <div className="flex items-center justify-center gap-3 py-16 text-on-surface-variant">
              <span className="material-symbols-outlined animate-spin text-2xl">progress_activity</span>
              Cargando...
            </div>
          ) : misOfertas.length === 0 ? (
            <EmptyState
              icon="gavel"
              title="Sin ofertas enviadas"
              subtitle="Todavía no enviaste ninguna oferta a una subasta."
            />
          ) : (
            <div className="flex flex-col gap-3">
              {misOfertas.map(oferta => (
                <div
                  key={oferta.id}
                  className="p-5 bg-surface rounded-2xl border border-outline-variant shadow-sm flex justify-between items-start"
                >
                  <div className="flex flex-col gap-1">
                    <span className="font-bold text-primary text-base">Subasta #{oferta.subasta_id}</span>
                    <span className="text-sm text-on-surface-variant">
                      Figurita subastada:{' '}
                      {oferta.figurita_subastada
                        ? `${oferta.figurita_subastada.jugador} (${oferta.figurita_subastada.equipo})`
                        : `#${oferta.subasta_id}`}
                    </span>
                    <span className="text-sm text-on-surface-variant">
                      Ofreciste:{' '}
                      {(oferta.ofrecidas_detalle?.length
                        ? oferta.ofrecidas_detalle.map(f => `${f.jugador} (${f.equipo})`)
                        : oferta.ofrecidas.map(id => `#${id}`)
                      ).join(', ')}
                    </span>
                    <span className={`text-xs font-medium mt-0.5 ${oferta.subasta?.estado === 'activa' ? 'text-green-600' : 'text-error'}`}>
                      Subasta {oferta.subasta?.estado ?? '—'}
                    </span>
                  </div>
                  {oferta.subasta?.estado === 'activa' && (
                    <Button
                      variant="outlined"
                      icon="cancel"
                      onClick={() => handleCancelarOferta(oferta)}
                    >
                      Cancelar
                    </Button>
                  )}
                </div>
              ))}
            </div>
          )
        ) : (tab === 'activas' ? subastas : misSubastas).length === 0 ? (
          <EmptyState
            icon="gavel"
            title="Sin subastas"
            subtitle={tab === 'activas' ? "No hay subastas en este momento." : "No creaste ninguna subasta aún."}
            action="Iniciar subasta"
            onAction={() => setCreate(true)}
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {(tab === 'activas' ? subastas : misSubastas).map((sub) => (
              <div
                key={sub.id}
                className="p-5 bg-surface rounded-2xl border border-outline-variant flex justify-between items-center shadow-sm"
              >
                <div>
                  <h3 className="font-bold text-lg text-primary">
                    Subasta #{sub.id}
                  </h3>
                  <p className="text-on-surface-variant text-sm mt-1">
                    Figurita: {pubsMap[sub.figurita_id]
                      ? `${pubsMap[sub.figurita_id].jugador} (${pubsMap[sub.figurita_id].equipo})`
                      : `#${sub.figurita_id}`} <br />
                    Propietario: {users[sub.usuario_id - 1]?.nombre ?? `Usuario ${sub.usuario_id}`} <br />
                    Estado:{" "}
                    <span className={`capitalize font-medium ${sub.estado === 'activa' ? 'text-green-600' : 'text-error'}`}>
                      {sub.estado}
                    </span>
                  </p>
                </div>
                {sub.usuario_id !== (users.indexOf(user) + 1) ? (
                  <Button
                    variant="tonal"
                    icon="gavel"
                    onClick={() => { setBidModal(sub); setOfferIds([]) }}
                  >
                    Ofertar
                  </Button>
                ) : (
                  <Button
                    variant="outlined"
                    icon="format_list_bulleted"
                    onClick={() => abrirOfertas(sub)}
                  >
                    Ver ofertas
                  </Button>
                )}
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

      {/* Ofertas recibidas Modal */}
      <Modal
        open={!!offersModal}
        onClose={() => setOffersModal(null)}
        title={`Ofertas recibidas — Subasta #${offersModal?.id}`}
        width={500}
      >
        {offersModal && (
          <div className="flex flex-col gap-3">
            {loadingOfertas ? (
              <div className="flex items-center justify-center gap-3 py-8 text-on-surface-variant">
                <span className="material-symbols-outlined animate-spin text-2xl">progress_activity</span>
                Cargando...
              </div>
            ) : ofertas.length === 0 ? (
              <div className="py-8 text-center text-on-surface-variant text-sm">
                Todavía no recibiste ninguna oferta para esta subasta.
              </div>
            ) : (
              ofertas.map((oferta) => (
                <div
                  key={oferta.id}
                  className="p-4 rounded-xl border border-outline-variant bg-surface-container flex flex-col gap-1.5"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-sm text-on-surface">
                      {users[oferta.usuario_id - 1]?.nombre ?? `Usuario ${oferta.usuario_id}`}
                    </span>
                    <span className="text-xs text-on-surface-variant">Oferta #{oferta.id}</span>
                  </div>
                  <div className="text-xs text-on-surface-variant">
                    Figuritas ofrecidas:{' '}
                    {(oferta.ofrecidas_detalle?.length
                      ? oferta.ofrecidas_detalle.map(f => `${f.jugador} (${f.equipo})`)
                      : oferta.ofrecidas.map(id => `#${id}`)
                    ).join(', ')}
                  </div>
                </div>
              ))
            )}
            <div className="flex justify-end mt-2">
              <Button variant="text" onClick={() => setOffersModal(null)}>Cerrar</Button>
            </div>
          </div>
        )}
      </Modal>

      <Snackbar
        {...snack}
        onClose={() => setSnack({ ...snack, open: false })}
      />
    </div>
  );
}
