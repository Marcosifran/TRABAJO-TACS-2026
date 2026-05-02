import { useState } from 'react'
import Button from '../components/ui/Button'
import Tabs from '../components/ui/Tabs'
import Modal from '../components/ui/Modal'
import Input from '../components/ui/Input'
import EmptyState from '../components/ui/EmptyState'
import Snackbar from '../components/ui/Snackbar'

const SELECCIONES = ['Argentina','Brasil','Francia','Alemania','España','Inglaterra','Portugal','México','USA','Canadá']
const EMPTY_AUCTION = { numero: '', seleccion: SELECCIONES[0], jugador: '', duracion: '24', condicion: '' }

export default function AuctionsPage() {
  const [tab, setTab]               = useState('activas')
  const [bidModal, setBidModal]     = useState(null)
  const [createModal, setCreate]    = useState(false)
  const [newAuction, setNewAuction] = useState(EMPTY_AUCTION)
  const [snack, setSnack]           = useState({ open: false, message: '', type: 'info' })

  function handleCreate() {
    if (!newAuction.numero || !newAuction.jugador) {
      setSnack({ open: true, message: 'Completá número y jugador', type: 'error' })
      return
    }
    setCreate(false)
    setNewAuction(EMPTY_AUCTION)
    setSnack({ open: true, message: 'Subasta creada con éxito', type: 'success' })
  }

  return (
    <div className="p-8 max-w-[1000px]">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-on-surface m-0">Subastas</h1>
          <p className="mt-1 text-on-surface-variant text-sm">0 subastas activas</p>
        </div>
        <Button icon="add" onClick={() => setCreate(true)}>Crear subasta</Button>
      </div>

      <Tabs
        tabs={[
          { id: 'activas',  label: 'Activas' },
          { id: 'mis',      label: 'Mis subastas' },
          { id: 'historial',label: 'Historial' },
        ]}
        active={tab}
        onChange={setTab}
      />

      <div className="mt-5">
        <EmptyState
          icon="gavel"
          title={tab === 'historial' ? 'Sin historial' : 'Sin subastas activas'}
          subtitle={
            tab === 'activas'   ? 'No hay subastas activas en este momento' :
            tab === 'mis'       ? 'No tenés subastas creadas. ¡Creá la primera!' :
                                  'Tus subastas finalizadas aparecerán acá'
          }
          action={tab === 'mis' ? 'Crear subasta' : undefined}
          onAction={() => setCreate(true)}
        />
      </div>

      {/* Bid Modal */}
      <Modal open={!!bidModal} onClose={() => setBidModal(null)} title="Ofertar en subasta" width={520}>
        {bidModal && (
          <div>
            <p className="text-sm text-on-surface-variant mb-4">
              Tu álbum está vacío. Publicá figuritas para poder ofertar.
            </p>
            <div className="flex gap-2.5 justify-end">
              <Button variant="text" onClick={() => setBidModal(null)}>Cancelar</Button>
              <Button icon="gavel" disabled>Ofertar</Button>
            </div>
          </div>
        )}
      </Modal>

      {/* Create Modal */}
      <Modal open={createModal} onClose={() => setCreate(false)} title="Crear subasta" width={480}>
        <div className="flex flex-col gap-4">
          <Input label="Número de figurita" type="number" value={newAuction.numero} onChange={v => setNewAuction({ ...newAuction, numero: v })} icon="tag" />
          <Input label="Selección" value={newAuction.seleccion} onChange={v => setNewAuction({ ...newAuction, seleccion: v })} options={SELECCIONES} />
          <Input label="Jugador" value={newAuction.jugador} onChange={v => setNewAuction({ ...newAuction, jugador: v })} icon="person" />
          <Input label="Duración (horas)" type="number" value={newAuction.duracion} onChange={v => setNewAuction({ ...newAuction, duracion: v })} icon="timer" />
          <Input label="Condiciones mínimas (opcional)" value={newAuction.condicion} onChange={v => setNewAuction({ ...newAuction, condicion: v })} multiline placeholder="Ej: Mínimo 2 figuritas, solo selecciones sudamericanas..." />
          <div className="flex gap-2.5 justify-end mt-2">
            <Button variant="text" onClick={() => setCreate(false)}>Cancelar</Button>
            <Button icon="gavel" onClick={handleCreate}>Crear subasta</Button>
          </div>
        </div>
      </Modal>

      <Snackbar {...snack} onClose={() => setSnack({ ...snack, open: false })} />
    </div>
  )
}
