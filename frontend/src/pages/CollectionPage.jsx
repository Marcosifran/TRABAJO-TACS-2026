import { useState } from 'react'
import Button from '../components/ui/Button'
import Tabs from '../components/ui/Tabs'
import Modal from '../components/ui/Modal'
import Input from '../components/ui/Input'
import Chip from '../components/ui/Chip'
import EmptyState from '../components/ui/EmptyState'
import Snackbar from '../components/ui/Snackbar'

const SELECCIONES = ['Argentina','Brasil','Francia','Alemania','España','Inglaterra','Portugal','México','USA','Canadá','Uruguay','Colombia']
const CATEGORIAS  = ['Escudo','Jugador','Estadio','Leyenda','Especial']

const EMPTY_PUB  = { numero: '', seleccion: SELECCIONES[0], jugador: '', categoria: CATEGORIAS[0], cantidad: '1', tipo: 'intercambio' }
const EMPTY_FALT = { numero: '', seleccion: SELECCIONES[0], jugador: '' }

export default function CollectionPage() {
  const [tab, setTab]           = useState('tengo')
  const [showPub, setShowPub]   = useState(false)
  const [showFalt, setShowFalt] = useState(false)
  const [pubForm, setPubForm]   = useState(EMPTY_PUB)
  const [faltForm, setFaltForm] = useState(EMPTY_FALT)
  const [snack, setSnack]       = useState({ open: false, message: '', type: 'info' })

  function handlePublish() {
    if (!pubForm.numero || !pubForm.jugador) {
      setSnack({ open: true, message: 'Completá número y jugador', type: 'error' })
      return
    }
    setShowPub(false)
    setPubForm(EMPTY_PUB)
    setSnack({ open: true, message: 'Figurita publicada con éxito', type: 'success' })
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

  return (
    <div className="p-8 max-w-[1100px]">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-on-surface m-0">Mi Colección</h1>
          <p className="mt-1 text-on-surface-variant text-sm">0 tengo · 0 me faltan · 0% completado</p>
        </div>
        <div className="flex gap-2.5">
          <Button icon="add" onClick={() => setShowPub(true)}>Publicar figurita</Button>
          <Button variant="outlined" icon="playlist_add" onClick={() => setShowFalt(true)}>Registrar faltante</Button>
        </div>
      </div>

      {/* Progress bar */}
      <div className="h-2 bg-surface-variant rounded-lg mb-6 overflow-hidden">
        <div className="h-full w-0 rounded-lg transition-all duration-500"
          style={{ background: 'linear-gradient(90deg, var(--color-primary), var(--color-tertiary))' }}
        />
      </div>

      <Tabs
        tabs={[
          { id: 'tengo', label: 'Mis figuritas (0)', icon: 'collections_bookmark' },
          { id: 'faltan', label: 'Me faltan (0)',     icon: 'playlist_add' },
        ]}
        active={tab}
        onChange={setTab}
      />

      <div className="mt-5">
        {tab === 'tengo' ? (
          <EmptyState
            icon="collections_bookmark"
            title="Tu álbum está vacío"
            subtitle="Publicá tu primera figurita para empezar a intercambiar"
            action="Publicar figurita"
            onAction={() => setShowPub(true)}
          />
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
      <Modal open={showPub} onClose={() => setShowPub(false)} title="Publicar figurita" width={480}>
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-3">
            <Input label="Número" type="number" value={pubForm.numero} onChange={v => setPubForm({ ...pubForm, numero: v })} icon="tag" placeholder="Ej: 10" />
            <Input label="Cantidad" type="number" value={pubForm.cantidad} onChange={v => setPubForm({ ...pubForm, cantidad: v })} icon="inventory_2" />
          </div>
          <Input label="Selección" value={pubForm.seleccion} onChange={v => setPubForm({ ...pubForm, seleccion: v })} options={SELECCIONES} />
          <Input label="Jugador / Descripción" value={pubForm.jugador} onChange={v => setPubForm({ ...pubForm, jugador: v })} icon="person" placeholder="Ej: Messi" />
          <Input label="Categoría" value={pubForm.categoria} onChange={v => setPubForm({ ...pubForm, categoria: v })} options={CATEGORIAS} />
          <div>
            <label className="block text-xs font-medium text-on-surface-variant mb-2">Disponible para</label>
            <div className="flex gap-2">
              <Chip selected={pubForm.tipo === 'intercambio'} onClick={() => setPubForm({ ...pubForm, tipo: 'intercambio' })} icon="swap_horiz">Intercambio</Chip>
              <Chip selected={pubForm.tipo === 'subasta'}     onClick={() => setPubForm({ ...pubForm, tipo: 'subasta' })}     icon="gavel">Subasta</Chip>
              <Chip selected={pubForm.tipo === 'ambos'}       onClick={() => setPubForm({ ...pubForm, tipo: 'ambos' })}       icon="select_all">Ambos</Chip>
            </div>
          </div>
          <div className="flex gap-2.5 justify-end mt-2">
            <Button variant="text" onClick={() => setShowPub(false)}>Cancelar</Button>
            <Button icon="publish" onClick={handlePublish}>Publicar</Button>
          </div>
        </div>
      </Modal>

      {/* Faltante Modal */}
      <Modal open={showFalt} onClose={() => setShowFalt(false)} title="Registrar faltante" width={420}>
        <div className="flex flex-col gap-4">
          <Input label="Número" type="number" value={faltForm.numero} onChange={v => setFaltForm({ ...faltForm, numero: v })} icon="tag" placeholder="Ej: 321" />
          <Input label="Selección" value={faltForm.seleccion} onChange={v => setFaltForm({ ...faltForm, seleccion: v })} options={SELECCIONES} />
          <Input label="Jugador (opcional)" value={faltForm.jugador} onChange={v => setFaltForm({ ...faltForm, jugador: v })} icon="person" placeholder="Ej: Pedri" />
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
