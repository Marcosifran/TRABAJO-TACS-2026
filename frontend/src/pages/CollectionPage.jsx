import { useState, useEffect, useCallback } from 'react'
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

const SELECCIONES = [
  'Argentina','Brasil','Francia','Alemania','España',
  'Inglaterra','Portugal','México','USA','Canadá','Uruguay','Colombia',
]
const EMPTY_PUB  = { numero: '', equipo: SELECCIONES[0], jugador: '', cantidad: '1', tipo: 'intercambio_directo' }
const EMPTY_FALT = { numero: '', seleccion: SELECCIONES[0], jugador: '' }

function pubToCard(pub, ownerName) {
  return {
    id: pub.id,
    numero: pub.numero,
    seleccion: pub.equipo,
    jugador: pub.jugador,
    tipo: pub.tipo_intercambio === 'intercambio_directo' ? 'intercambio' : 'subasta',
    cantidad: pub.cantidad_disponible,
    owner: ownerName,
  }
}

export default function CollectionPage() {
  const { user }  = useUser()
  const [tab, setTab]           = useState('tengo')
  const [showPub, setShowPub]   = useState(false)
  const [showFalt, setShowFalt] = useState(false)
  const [pubForm, setPubForm]   = useState(EMPTY_PUB)
  const [faltForm, setFaltForm] = useState(EMPTY_FALT)
  const [publicaciones, setPublicaciones] = useState([])
  const [loading, setLoading]   = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [snack, setSnack]       = useState({ open: false, message: '', type: 'info' })

  const cargarPublicaciones = useCallback(async () => {
    setLoading(true)
    try {
      const data = await listarMisPublicaciones()
      setPublicaciones(data)
    } catch (e) {
      setSnack({ open: true, message: e.message, type: 'error' })
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { cargarPublicaciones() }, [cargarPublicaciones])

  async function handlePublish() {
    if (!pubForm.numero || !pubForm.jugador) {
      setSnack({ open: true, message: 'Completá número y jugador', type: 'error' })
      return
    }
    setSubmitting(true)
    try {
      const albumEntry = await agregarAlAlbum({
        numero:   pubForm.numero,
        equipo:   pubForm.equipo,
        jugador:  pubForm.jugador,
        cantidad: pubForm.cantidad,
      })
      await publicarFigurita({
        figurita_personal_id: albumEntry.id,
        tipo_intercambio:     pubForm.tipo,
        cantidad_disponible:  pubForm.cantidad,
      })
      setShowPub(false)
      setPubForm(EMPTY_PUB)
      setSnack({ open: true, message: 'Figurita publicada con éxito', type: 'success' })
      cargarPublicaciones()
    } catch (e) {
      setSnack({ open: true, message: e.message, type: 'error' })
    } finally {
      setSubmitting(false)
    }
  }

  async function handleRetirar(pubId) {
    try {
      await retirarPublicacion(pubId)
      setPublicaciones(prev => prev.filter(p => p.id !== pubId))
      setSnack({ open: true, message: 'Publicación retirada', type: 'info' })
    } catch (e) {
      setSnack({ open: true, message: e.message, type: 'error' })
    }
  }

  function handleAddFaltante() {
    if (!faltForm.numero) {
      setSnack({ open: true, message: 'Ingresá el número de la figurita', type: 'error' })
      return
    }
    setShowFalt(false)
    setFaltForm(EMPTY_FALT)
    setSnack({ open: true, message: 'Faltante registrado', type: 'success' })
  }

  const cards = publicaciones.map(p => pubToCard(p, user.nombre))

  return (
    <div className="p-8 max-w-[1100px]">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-on-surface m-0">Mi Colección</h1>
          <p className="mt-1 text-on-surface-variant text-sm">
            {publicaciones.length} publicadas · 0 me faltan
          </p>
        </div>
        <div className="flex gap-2.5">
          <Button icon="add" onClick={() => setShowPub(true)}>Publicar figurita</Button>
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
            width: `${Math.min((publicaciones.length / 670) * 100, 100)}%`,
            background: 'linear-gradient(90deg, var(--color-primary), var(--color-tertiary))',
          }}
        />
      </div>

      <Tabs
        tabs={[
          { id: 'tengo',  label: `Mis figuritas (${publicaciones.length})`, icon: 'collections_bookmark' },
          { id: 'faltan', label: 'Me faltan (0)', icon: 'playlist_add' },
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
              onAction={() => setShowPub(true)}
            />
          ) : (
            <div className="grid grid-cols-[repeat(auto-fill,minmax(200px,1fr))] gap-3.5">
              {cards.map(f => (
                <div key={f.id} className="relative group">
                  <FiguritaCard figurita={f} />
                  <button
                    onClick={() => handleRetirar(f.id)}
                    className="absolute top-2 left-2 opacity-0 group-hover:opacity-100 transition-opacity
                               bg-error/90 text-white rounded-full p-1 cursor-pointer border-0"
                    title="Retirar publicación"
                  >
                    <Icon name="close" size={14} className="text-white" />
                  </button>
                </div>
              ))}
            </div>
          )
        ) : (
          <EmptyState
            icon="playlist_add"
            title="No tenés figuritas faltantes"
            subtitle="Registrá las figuritas que te faltan para recibir sugerencias automáticas"
            action="Registrar faltante"
            onAction={() => setShowFalt(true)}
          />
        )}
      </div>

      {/* Publish Modal */}
      <Modal open={showPub} onClose={() => !submitting && setShowPub(false)} title="Publicar figurita" width={480}>
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Número" type="number" icon="tag" placeholder="Ej: 10"
              value={pubForm.numero}
              onChange={v => setPubForm({ ...pubForm, numero: v })}
            />
            <Input
              label="Cantidad" type="number" icon="inventory_2"
              value={pubForm.cantidad}
              onChange={v => setPubForm({ ...pubForm, cantidad: v })}
            />
          </div>
          <Input
            label="Selección / Equipo"
            value={pubForm.equipo}
            onChange={v => setPubForm({ ...pubForm, equipo: v })}
            options={SELECCIONES}
          />
          <Input
            label="Jugador / Descripción" icon="person" placeholder="Ej: Messi"
            value={pubForm.jugador}
            onChange={v => setPubForm({ ...pubForm, jugador: v })}
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
            <Button variant="text" onClick={() => setShowPub(false)} disabled={submitting}>
              Cancelar
            </Button>
            <Button icon={submitting ? 'progress_activity' : 'publish'} onClick={handlePublish} disabled={submitting}>
              {submitting ? 'Publicando...' : 'Publicar'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Faltante Modal */}
      <Modal open={showFalt} onClose={() => setShowFalt(false)} title="Registrar faltante" width={420}>
        <div className="flex flex-col gap-4">
          <Input
            label="Número" type="number" icon="tag" placeholder="Ej: 321"
            value={faltForm.numero}
            onChange={v => setFaltForm({ ...faltForm, numero: v })}
          />
          <Input
            label="Selección"
            value={faltForm.seleccion}
            onChange={v => setFaltForm({ ...faltForm, seleccion: v })}
            options={SELECCIONES}
          />
          <Input
            label="Jugador (opcional)" icon="person" placeholder="Ej: Pedri"
            value={faltForm.jugador}
            onChange={v => setFaltForm({ ...faltForm, jugador: v })}
          />
          <div className="flex gap-2.5 justify-end mt-2">
            <Button variant="text" onClick={() => setShowFalt(false)}>Cancelar</Button>
            <Button icon="playlist_add" onClick={handleAddFaltante}>Registrar</Button>
          </div>
        </div>
      </Modal>

      <Snackbar {...snack} onClose={() => setSnack({ ...snack, open: false })} />
    </div>
  )
}
