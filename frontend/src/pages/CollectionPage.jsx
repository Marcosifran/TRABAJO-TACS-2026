import { useState, useEffect, useCallback, useRef } from 'react'
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
import { agregarAlAlbum, publicarFigurita, listarMisPublicaciones, retirarPublicacion } from '../api/publicaciones'
import { registrarFaltante, listarFaltantes } from '../api/faltantes'
import { getMaestroJugador } from '../api/maestro'
import { listarMiAlbum } from '../api/album'

const SELECCIONES = [
  'Argentina', 'Brasil', 'Francia', 'Alemania', 'España',
  'Inglaterra', 'Portugal', 'México', 'USA', 'Canadá', 'Uruguay', 'Colombia',
]
const EMPTY_PUB = { numero: '', equipo: SELECCIONES[0], jugador: '', cantidad: '1', tipo: 'intercambio_directo' }
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
  const [tab, setTab] = useState('tengo')
  const [showPub, setShowPub] = useState(false)
  const [showFalt, setShowFalt] = useState(false)
  const [pubForm, setPubForm] = useState(EMPTY_PUB)
  const [faltForm, setFaltForm] = useState(EMPTY_FALT)
  const [album, setAlbum] = useState([])
  const [publicaciones, setPublicaciones] = useState([])
  const [faltantes, setFaltantes] = useState([])
  const [loading, setLoading] = useState(false)
  const [loadingFalt, setLoadingFalt] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [submittingFalt, setSubmittingFalt] = useState(false)
  const [loadingMaestro, setLoadingMaestro] = useState(false)
  const [snack, setSnack] = useState({ open: false, message: '', type: 'info' })
  const maestroTimer = useRef(null)

  const cargarDatos = useCallback(async () => {
    setLoading(true)
    try {
      const [albumData, pubsData] = await Promise.all([
        listarMiAlbum(),
        listarMisPublicaciones()
      ])
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
    if (!pubForm.numero || !pubForm.jugador) {
      setSnack({ open: true, message: 'Completá número y jugador', type: 'error' })
      return
    }
    setSubmitting(true)
    try {
      let figId = pubForm._figId
      
      // Si no viene de una figurita existente en el álbum, la agregamos primero
      if (!figId) {
        const albumEntry = await agregarAlAlbum({
          numero: pubForm.numero,
          equipo: pubForm.equipo,
          jugador: pubForm.jugador,
          cantidad: pubForm.cantidad,
        })
        figId = albumEntry.id
      }

      await publicarFigurita({
        figurita_personal_id: figId,
        tipo_intercambio: pubForm.tipo,
        cantidad_disponible: pubForm.cantidad,
      })
      
      setShowPub(false)
      setPubForm(EMPTY_PUB)
      setSnack({ open: true, message: 'Figurita publicada con éxito', type: 'success' })
      cargarDatos()
    } catch (e) {
      setSnack({ open: true, message: e.message, type: 'error' })
    } finally {
      setSubmitting(false)
    }
  }

  function openPublishExisting(fig, tipo) {
    setPubForm({
      numero: fig.numero,
      equipo: fig.seleccion,
      jugador: fig.jugador,
      cantidad: fig.cantidad,
      tipo: tipo || 'intercambio_directo',
      _figId: fig.id, // Guardamos el ID para saber que ya existe
    })
    setShowPub(true)
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
        setForm(prev => ({ ...prev, equipo: data.equipo, seleccion: data.equipo, jugador: data.jugador }))
      } catch {
        // número no encontrado en el maestro, se deja editar manualmente
      } finally {
        setLoadingMaestro(false)
      }
    }, 500)
  }

  async function handleAddFaltante() {
    if (!faltForm.numero) {
      setSnack({ open: true, message: 'Ingresá el número de la figurita', type: 'error' })
      return
    }
    setSubmittingFalt(true)
    try {
      await registrarFaltante({
        numero_figurita: faltForm.numero,
        equipo: faltForm.seleccion,
        jugador: faltForm.jugador,
      })
      setShowFalt(false)
      setFaltForm(EMPTY_FALT)
      setSnack({ open: true, message: 'Faltante registrado con éxito', type: 'success' })
      cargarFaltantes()
    } catch (e) {
      setSnack({ open: true, message: e.message, type: 'error' })
    } finally {
      setSubmittingFalt(false)
    }
  }

  const cards = album.map(fig => {
    const pub = publicaciones.find(p => p.figurita_personal_id === fig.id)
    return figToCard(fig, user.nombre, pub)
  })

  return (
    <div className="p-8 max-w-[1100px]">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-on-surface m-0">Mi Colección</h1>
          <p className="mt-1 text-on-surface-variant text-sm">
            {album.length} figuritas · {publicaciones.length} en oferta · {faltantes.length} me faltan
          </p>
        </div>
        <div className="flex gap-2.5">
          <Button icon="add" onClick={() => { setPubForm(EMPTY_PUB); setShowPub(true) }}>
            Publicar figurita
          </Button>
          <Button variant="outlined" icon="playlist_add" onClick={() => setShowFalt(true)}>
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
              onAction={() => { setPubForm(EMPTY_PUB); setShowPub(true) }}
            />
          ) : (
            <div className="grid grid-cols-[repeat(auto-fill,minmax(160px,1fr))] gap-2">
              {cards.map(f => (
                <div key={f.id} className="flex flex-col items-center">
                  <FiguritaCard
                    figurita={f}
                    showTradeType={false}
                    size="collection"
                    backActions={(
                      <div className="flex w-full gap-1">
                        <Button
                          size="sm"
                          className="flex-1 min-w-0 h-7 px-0 py-0 text-[10px] leading-none whitespace-nowrap border-0"
                          style={{
                            backgroundColor: f.tipo === 'intercambio' ? 'var(--color-trade)' : 'var(--color-surface-variant)',
                            color: f.tipo === 'intercambio' ? 'white' : 'var(--color-on-surface-variant)',
                          }}
                          onClick={() => f.tipo === 'intercambio' ? handleRetirar(f._pubId) : openPublishExisting(f, 'intercambio_directo')}
                        >
                          Intercambio
                        </Button>
                        <Button
                          size="sm"
                          className="flex-1 min-w-0 h-7 px-0 py-0 text-[10px] leading-none whitespace-nowrap border-0"
                          style={{
                            backgroundColor: f.tipo === 'subasta' ? 'var(--color-auction)' : 'var(--color-surface-variant)',
                            color: f.tipo === 'subasta' ? 'white' : 'var(--color-on-surface-variant)',
                          }}
                          onClick={() => f.tipo === 'subasta' ? handleRetirar(f._pubId) : openPublishExisting(f, 'subasta')}
                        >
                          Subasta
                        </Button>
                      </div>
                    )}
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
            onAction={() => setShowFalt(true)}
          />
        ) : (
          <div className="grid grid-cols-[repeat(auto-fill,minmax(200px,1fr))] gap-3.5">
            {faltantes.map(f => (
              <div
                key={f.id}
                className="rounded-2xl border border-outline-variant bg-surface-container p-4 flex flex-col gap-1"
              >
                <div className="flex items-center justify-between">
                  <span className="text-2xl font-bold text-primary">#{f.numero_figurita}</span>
                  <Icon name="playlist_add" size={20} className="text-on-surface-variant" />
                </div>
                {f.equipo && (
                  <span className="text-sm font-medium text-on-surface">{f.equipo}</span>
                )}
                {f.jugador && (
                  <span className="text-xs text-on-surface-variant">{f.jugador}</span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Boton Publicar Figurita */}
      <Modal 
        open={showPub} 
        onClose={() => {
          if (!submitting) {
            setShowPub(false)
            setPubForm(EMPTY_PUB)
          }
        }} 
        title={pubForm._figId ? "Publicar figurita del álbum" : "Nueva figurita y publicación"} 
        width={480}
      >
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Número" type="number" icon="tag" placeholder="Ej: 10"
              value={pubForm.numero}
              onChange={v => {
                setPubForm({ ...pubForm, numero: v })
                if (!pubForm._figId) buscarEnMaestro(v, setPubForm)
              }}
              disabled={!!pubForm._figId}
            />
            <Input
              label="Cantidad" type="number" icon="inventory_2"
              value={pubForm.cantidad}
              onChange={v => setPubForm({ ...pubForm, cantidad: v })}
            />
          </div>
          <Input
            label="Selección / Equipo" icon="shield"
            placeholder="Se completa al ingresar el número"
            value={pubForm.equipo}
            onChange={() => {}}
            disabled
          />
          <Input
            label="Jugador" icon="person"
            placeholder="Se completa al ingresar el número"
            value={pubForm.jugador}
            onChange={() => {}}
            disabled
          />
          <div>
            <label className="block text-xs font-medium text-on-surface-variant mb-2">
              Disponible para
            </label>
            <div className="flex gap-2">
              <Chip
                selected={pubForm.tipo === 'intercambio_directo'}
                onClick={() => setPubForm({ ...pubForm, tipo: 'intercambio_directo' })}
                icon="swap_horiz"
              >
                Intercambio
              </Chip>
              <Chip
                selected={pubForm.tipo === 'subasta'}
                onClick={() => setPubForm({ ...pubForm, tipo: 'subasta' })}
                icon="gavel"
              >
                Subasta
              </Chip>
            </div>
          </div>
          <div className="flex gap-2.5 justify-end mt-2">
            <Button variant="text" onClick={() => { setShowPub(false); setPubForm(EMPTY_PUB) }} disabled={submitting}>
              Cancelar
            </Button>
            <Button icon={submitting ? 'progress_activity' : 'publish'} onClick={handlePublish} disabled={submitting}>
              {submitting ? 'Publicando...' : 'Publicar'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Boton Registrar Faltante */}
      <Modal open={showFalt} onClose={() => !submittingFalt && setShowFalt(false)} title="Registrar faltante" width={420}>
        <div className="flex flex-col gap-4">
          <Input
            label={loadingMaestro ? 'Buscando...' : 'Número'}
            type="number" icon={loadingMaestro ? 'progress_activity' : 'tag'} placeholder="Ej: 321"
            value={faltForm.numero}
            onChange={v => {
              setFaltForm({ ...faltForm, numero: v })
              buscarEnMaestro(v, setFaltForm)
            }}
          />
          <Input
            label="Selección / Equipo" icon="shield"
            placeholder="Se completa al ingresar el número"
            value={faltForm.seleccion}
            onChange={() => {}}
            disabled
          />
          <Input
            label="Jugador" icon="person"
            placeholder="Se completa al ingresar el número"
            value={faltForm.jugador}
            onChange={() => {}}
            disabled
          />
          <div className="flex gap-2.5 justify-end mt-2">
            <Button variant="text" onClick={() => setShowFalt(false)} disabled={submittingFalt}>Cancelar</Button>
            <Button
              icon={submittingFalt ? 'progress_activity' : 'playlist_add'}
              onClick={handleAddFaltante}
              disabled={submittingFalt}
            >
              {submittingFalt ? 'Registrando...' : 'Registrar'}
            </Button>
          </div>
        </div>
      </Modal>

      <Snackbar {...snack} onClose={() => setSnack({ ...snack, open: false })} />
    </div>
  )
}
