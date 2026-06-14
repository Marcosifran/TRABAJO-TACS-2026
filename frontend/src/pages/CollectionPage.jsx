import { useState, useEffect, useCallback, useRef } from 'react'
import { useModalForm } from '../hooks/useModalForm'
import Button from '../components/ui/Button'
import Tabs from '../components/ui/Tabs'
import Modal from '../components/ui/Modal'
import Input from '../components/ui/Input'
import Chip from '../components/ui/Chip'
import EmptyState from '../components/ui/EmptyState'
import Snackbar from '../components/ui/Snackbar'
import FiguritaCard from '../components/FiguritaCard'
import Icon from '../components/ui/Icon'
import { useUser } from '../context/UserContext'
import {
  agregarAlAlbum,
  publicarFigurita,
  listarMisPublicaciones,
  retirarPublicacion,
} from '../api/publicaciones'
import { registrarFaltante, listarFaltantes } from '../api/faltantes'
import { getMaestroJugador } from '../api/maestro'
import { listarMiAlbum } from '../api/album'

const SELECCIONES = [
  'Argentina',
  'Brasil',
  'Francia',
  'Alemania',
  'España',
  'Inglaterra',
  'Portugal',
  'México',
  'USA',
  'Canadá',
  'Uruguay',
  'Colombia',
]
const EMPTY_PUB = {
  numero: '',
  equipo: SELECCIONES[0],
  jugador: '',
  cantidad: '1',
  tipo: 'intercambio_directo',
}
const EMPTY_FALT = { numero: '', seleccion: SELECCIONES[0], jugador: '' }

function figToCard(fig, ownerName, pub) {
  return {
    id: fig.id,
    numero: fig.numero,
    seleccion: fig.equipo,
    jugador: fig.jugador,
    tipo: pub ? (pub.tipo_intercambio === 'intercambio_directo' ? 'intercambio' : 'subasta') : null,
    cantidad: fig.cantidad,
    owner: ownerName,
    _pubId: pub?.id,
  }
}

export default function CollectionPage() {
  const { user } = useUser()
  const pubModal = useModalForm(EMPTY_PUB)
  const faltModal = useModalForm(EMPTY_FALT)
  const [tab, setTab] = useState('tengo')
  const [album, setAlbum] = useState([])
  const [publicaciones, setPublicaciones] = useState([])
  const [faltantes, setFaltantes] = useState([])
  const [loading, setLoading] = useState(false)
  const [loadingFalt, setLoadingFalt] = useState(false)
  const [loadingMaestro, setLoadingMaestro] = useState(false)
  const [snack, setSnack] = useState({ open: false, message: '', type: 'info' })
  const maestroTimer = useRef(null)

  const cargarDatos = useCallback(async () => {
    setLoading(true)
    try {
      const [albumData, pubsData] = await Promise.all([listarMiAlbum(), listarMisPublicaciones()])
      setAlbum(albumData.figuritas || albumData)
      setPublicaciones(pubsData)
    } catch (e) {
      setSnack({ open: true, message: e.message, type: 'error' })
    } finally {
      setLoading(false)
    }
  }, [])

  const cargarFaltantes = useCallback(async () => {
    setLoadingFalt(true)
    try {
      const data = await listarFaltantes()
      setFaltantes(data || [])
    } catch (e) {
      setSnack({ open: true, message: e.message, type: 'error' })
    } finally {
      setLoadingFalt(false)
    }
  }, [])

  useEffect(() => {
    cargarDatos()
    cargarFaltantes()
  }, [cargarDatos, cargarFaltantes])

  async function handlePublish() {
    if (!pubModal.form.numero || !pubModal.form.jugador) {
      setSnack({ open: true, message: 'Completá número y jugador', type: 'error' })
      return
    }
    pubModal.setPending(true)
    try {
      let figId = pubModal.form._figId

      // Si no viene de una figurita existente en el álbum, la agregamos primero
      if (!figId) {
        const albumEntry = await agregarAlAlbum({
          numero: pubModal.form.numero,
          equipo: pubModal.form.equipo,
          jugador: pubModal.form.jugador,
          cantidad: pubModal.form.cantidad,
        })
        figId = albumEntry.id
      }

      await publicarFigurita({
        figurita_personal_id: figId,
        tipo_intercambio: pubModal.form.tipo,
        cantidad_disponible: pubModal.form.cantidad,
      })

      pubModal.close()
      setSnack({ open: true, message: 'Figurita publicada con éxito', type: 'success' })
      cargarDatos()
    } catch (e) {
      setSnack({ open: true, message: e.message, type: 'error' })
    } finally {
      pubModal.setPending(false)
    }
  }

  function openPublishExisting(fig, tipo) {
    pubModal.openWith(true, {
      numero: fig.numero,
      equipo: fig.seleccion,
      jugador: fig.jugador,
      cantidad: fig.cantidad,
      tipo: tipo || 'intercambio_directo',
      _figId: fig.id,
    })
  }

  async function handleRetirar(pubId) {
    try {
      await retirarPublicacion(pubId)
      setSnack({ open: true, message: 'Publicación retirada', type: 'info' })
      cargarDatos()
    } catch (e) {
      setSnack({ open: true, message: e.message, type: 'error' })
    }
  }

  function buscarEnMaestro(numero, setForm) {
    clearTimeout(maestroTimer.current)
    if (!numero || isNaN(numero)) return
    maestroTimer.current = setTimeout(async () => {
      setLoadingMaestro(true)
      try {
        const data = await getMaestroJugador(numero)
        setForm((prev) => ({
          ...prev,
          equipo: data.equipo,
          seleccion: data.equipo,
          jugador: data.jugador,
        }))
      } catch {
        // número no encontrado en el maestro, se deja editar manualmente
      } finally {
        setLoadingMaestro(false)
      }
    }, 500)
  }

  async function handleAddFaltante() {
    if (!faltModal.form.numero) {
      setSnack({ open: true, message: 'Ingresá el número de la figurita', type: 'error' })
      return
    }
    faltModal.setPending(true)
    try {
      await registrarFaltante({
        numero_figurita: faltModal.form.numero,
        equipo: faltModal.form.seleccion,
        jugador: faltModal.form.jugador,
      })
      faltModal.close()
      setSnack({ open: true, message: 'Faltante registrado con éxito', type: 'success' })
      cargarFaltantes()
    } catch (e) {
      setSnack({ open: true, message: e.message, type: 'error' })
    } finally {
      faltModal.setPending(false)
    }
  }

  const cards = album.map((fig) => {
    const pub = publicaciones.find((p) => p.figurita_personal_id === fig.id)
    return figToCard(fig, user.nombre, pub)
  })

  return (
    <div className="p-8 max-w-[1100px]">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-on-surface m-0">Mi Colección</h1>
          <p className="mt-1 text-on-surface-variant text-sm">
            {album.length} figuritas · {publicaciones.length} en oferta · {faltantes.length} me
            faltan
          </p>
        </div>
        <div className="flex gap-2.5">
          <Button icon="add" onClick={() => pubModal.openWith()}>
            Publicar figurita
          </Button>
          <Button variant="outlined" icon="playlist_add" onClick={() => faltModal.openWith()}>
            Registrar faltante
          </Button>
        </div>
      </div>

      {/* Progress bar */}
      <div className="h-2 bg-surface-variant rounded-lg mb-6 overflow-hidden">
        <div
          className="h-full rounded-lg transition-all duration-500"
          style={{
            width: `${Math.min((album.length / 670) * 100, 100)}%`,
            background: 'linear-gradient(90deg, var(--color-primary), var(--color-tertiary))',
          }}
        />
      </div>

      <Tabs
        tabs={[
          { id: 'tengo', label: `Mis figuritas (${album.length})`, icon: 'collections_bookmark' },
          { id: 'faltan', label: `Me faltan (${faltantes.length})`, icon: 'playlist_add' },
        ]}
        active={tab}
        onChange={setTab}
      />

      <div className="mt-5">
        {tab === 'tengo' ? (
          loading ? (
            <div className="flex items-center justify-center gap-3 py-16 text-on-surface-variant">
              <Icon name="progress_activity" size={24} className="animate-spin" />
              Cargando...
            </div>
          ) : cards.length === 0 ? (
            <EmptyState
              icon="collections_bookmark"
              title="Tu álbum está vacío"
              subtitle="Publicá tu primera figurita para empezar a intercambiar"
              action="Publicar figurita"
              onAction={() => pubModal.openWith()}
            />
          ) : (
            <div className="grid grid-cols-[repeat(auto-fill,minmax(136px,1fr))] gap-2">
              {cards.map((f) => (
                <div key={f.id} className="flex flex-col items-center">
                  <FiguritaCard
                    figurita={f}
                    showTradeType={false}
                    size="collection"
                    backActions={
                      <div className="flex flex-col w-full gap-1">
                        <button
                          className="w-full h-6 rounded-lg text-[10px] font-medium leading-none"
                          style={{
                            backgroundColor:
                              f.tipo === 'intercambio'
                                ? 'var(--color-trade)'
                                : 'rgba(255,255,255,0.25)',
                            color: 'white',
                          }}
                          onClick={() =>
                            f.tipo === 'intercambio'
                              ? handleRetirar(f._pubId)
                              : openPublishExisting(f, 'intercambio_directo')
                          }
                        >
                          {f.tipo === 'intercambio' ? '✕ Intercambio' : '+ Intercambio'}
                        </button>
                        <button
                          className="w-full h-6 rounded-lg text-[10px] font-medium leading-none"
                          style={{
                            backgroundColor:
                              f.tipo === 'subasta'
                                ? 'var(--color-auction)'
                                : 'rgba(255,255,255,0.25)',
                            color: 'white',
                          }}
                          onClick={() =>
                            f.tipo === 'subasta'
                              ? handleRetirar(f._pubId)
                              : openPublishExisting(f, 'subasta')
                          }
                        >
                          {f.tipo === 'subasta' ? '✕ Subasta' : '+ Subasta'}
                        </button>
                      </div>
                    }
                  />
                </div>
              ))}
            </div>
          )
        ) : loadingFalt ? (
          <div className="flex items-center justify-center gap-3 py-16 text-on-surface-variant">
            <Icon name="progress_activity" size={24} className="animate-spin" />
            Cargando...
          </div>
        ) : faltantes.length === 0 ? (
          <EmptyState
            icon="playlist_add"
            title="No tenés figuritas faltantes"
            subtitle="Registrá las figuritas que te faltan para recibir sugerencias automáticas"
            action="Registrar faltante"
            onAction={() => faltModal.openWith()}
          />
        ) : (
          <div className="grid grid-cols-[repeat(auto-fill,minmax(136px,1fr))] gap-2">
            {faltantes.map((f) => (
              <div key={f.id} className="flex flex-col items-center">
                <FiguritaCard
                  figurita={{
                    id: f.id,
                    numero: f.numero_figurita,
                    seleccion: f.equipo,
                    jugador: f.jugador,
                    tipo: null,
                    cantidad: null,
                    owner: null,
                  }}
                  showTradeType={false}
                  size="collection"
                />
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Boton Publicar Figurita */}
      <Modal
        open={!!pubModal.open}
        onClose={() => !pubModal.pending && pubModal.close()}
        title={
          pubModal.form._figId ? 'Publicar figurita del álbum' : 'Nueva figurita y publicación'
        }
        width={480}
      >
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <Input
              label="Número"
              type="number"
              icon="tag"
              placeholder="Ej: 10"
              value={pubModal.form.numero}
              onChange={(v) => {
                pubModal.setForm((f) => ({ ...f, numero: v }))
                if (!pubModal.form._figId) buscarEnMaestro(v, pubModal.setForm)
              }}
              disabled={!!pubModal.form._figId}
            />
            <Input
              label="Cantidad"
              type="number"
              icon="inventory_2"
              value={pubModal.form.cantidad}
              onChange={(v) => pubModal.setForm((f) => ({ ...f, cantidad: v }))}
            />
          </div>
          <Input
            label="Selección / Equipo"
            icon="shield"
            placeholder="Se completa al ingresar el número"
            value={pubModal.form.equipo}
            onChange={() => {}}
            disabled
          />
          <Input
            label="Jugador"
            icon="person"
            placeholder="Se completa al ingresar el número"
            value={pubModal.form.jugador}
            onChange={() => {}}
            disabled
          />
          <div>
            <label className="block text-xs font-medium text-on-surface-variant mb-2">
              Disponible para
            </label>
            <div className="flex gap-2">
              <Chip
                selected={pubModal.form.tipo === 'intercambio_directo'}
                onClick={() => pubModal.setForm((f) => ({ ...f, tipo: 'intercambio_directo' }))}
                icon="swap_horiz"
              >
                Intercambio
              </Chip>
              <Chip
                selected={pubModal.form.tipo === 'subasta'}
                onClick={() => pubModal.setForm((f) => ({ ...f, tipo: 'subasta' }))}
                icon="gavel"
              >
                Subasta
              </Chip>
            </div>
          </div>
          <div className="flex gap-2.5 justify-end mt-2">
            <Button variant="text" onClick={pubModal.close} disabled={pubModal.pending}>
              Cancelar
            </Button>
            <Button
              icon={pubModal.pending ? 'progress_activity' : 'publish'}
              onClick={handlePublish}
              disabled={pubModal.pending}
            >
              {pubModal.pending ? 'Publicando...' : 'Publicar'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Boton Registrar Faltante */}
      <Modal
        open={!!faltModal.open}
        onClose={() => !faltModal.pending && faltModal.close()}
        title="Registrar faltante"
        width={420}
      >
        <div className="flex flex-col gap-4">
          <Input
            label={loadingMaestro ? 'Buscando...' : 'Número'}
            type="number"
            icon={loadingMaestro ? 'progress_activity' : 'tag'}
            placeholder="Ej: 321"
            value={faltModal.form.numero}
            onChange={(v) => {
              faltModal.setForm((f) => ({ ...f, numero: v }))
              buscarEnMaestro(v, faltModal.setForm)
            }}
          />
          <Input
            label="Selección / Equipo"
            icon="shield"
            placeholder="Se completa al ingresar el número"
            value={faltModal.form.seleccion}
            onChange={() => {}}
            disabled
          />
          <Input
            label="Jugador"
            icon="person"
            placeholder="Se completa al ingresar el número"
            value={faltModal.form.jugador}
            onChange={() => {}}
            disabled
          />
          <div className="flex gap-2.5 justify-end mt-2">
            <Button variant="text" onClick={faltModal.close} disabled={faltModal.pending}>
              Cancelar
            </Button>
            <Button
              icon={faltModal.pending ? 'progress_activity' : 'playlist_add'}
              onClick={handleAddFaltante}
              disabled={faltModal.pending}
            >
              {faltModal.pending ? 'Registrando...' : 'Registrar'}
            </Button>
          </div>
        </div>
      </Modal>

      <Snackbar {...snack} onClose={() => setSnack({ ...snack, open: false })} />
    </div>
  )
}
