import { useState } from 'react'
import Input from '../components/ui/Input'
import Chip from '../components/ui/Chip'
import Modal from '../components/ui/Modal'
import Button from '../components/ui/Button'
import Icon from '../components/ui/Icon'
import EmptyState from '../components/ui/EmptyState'
import Snackbar from '../components/ui/Snackbar'

const SELECCIONES = ['Argentina','Brasil','Francia','Alemania','España','Inglaterra','Portugal','México','USA','Canadá']
const CATEGORIAS  = ['Escudo','Jugador','Estadio','Leyenda','Especial']

export default function SearchPage() {
  const [query,       setQuery]       = useState('')
  const [selFilter,   setSelFilter]   = useState('Todas')
  const [catFilter,   setCatFilter]   = useState('Todas')
  const [tipoFilter,  setTipoFilter]  = useState('todos')
  const [tradeModal,  setTradeModal]  = useState(null)
  const [selectedOffer, setSelectedOffer] = useState([])
  const [snack, setSnack] = useState({ open: false, message: '', type: 'info' })

  function handleSendTrade() {
    if (selectedOffer.length === 0) {
      setSnack({ open: true, message: 'Seleccioná al menos una figurita para ofrecer', type: 'error' })
      return
    }
    setTradeModal(null)
    setSelectedOffer([])
    setSnack({ open: true, message: 'Propuesta enviada con éxito', type: 'success' })
  }

  return (
    <div className="p-8 max-w-[1100px]">
      <h1 className="text-3xl font-bold text-on-surface mb-5">Buscar Figuritas</h1>

      <div className="mb-5">
        <Input value={query} onChange={setQuery} icon="search" placeholder="Buscar por jugador, número o selección..." />
      </div>

      {/* Filtros selección */}
      <div className="flex items-center flex-wrap gap-2 mb-3">
        <span className="text-[13px] text-on-surface-variant font-medium mr-1">Selección:</span>
        {['Todas', ...SELECCIONES.slice(0, 6)].map(s => (
          <Chip key={s} selected={selFilter === s} onClick={() => setSelFilter(s)}>{s}</Chip>
        ))}
      </div>

      {/* Filtros categoría + tipo */}
      <div className="flex items-center flex-wrap gap-2 mb-5">
        <span className="text-[13px] text-on-surface-variant font-medium mr-1">Categoría:</span>
        {['Todas', ...CATEGORIAS].map(c => (
          <Chip key={c} selected={catFilter === c} onClick={() => setCatFilter(c)}>{c}</Chip>
        ))}
        <div className="ml-auto flex gap-1.5">
          <Chip selected={tipoFilter === 'todos'}      onClick={() => setTipoFilter('todos')}>Todos</Chip>
          <Chip selected={tipoFilter === 'intercambio'} onClick={() => setTipoFilter('intercambio')} icon="swap_horiz">Intercambio</Chip>
          <Chip selected={tipoFilter === 'subasta'}    onClick={() => setTipoFilter('subasta')}    icon="gavel">Subasta</Chip>
        </div>
      </div>

      <div className="text-[13px] text-on-surface-variant mb-4">0 resultados</div>

      <EmptyState
        icon="search_off"
        title="Sin resultados"
        subtitle="No hay figuritas publicadas por otros usuarios en este momento"
      />

      {/* Trade Modal */}
      <Modal open={!!tradeModal} onClose={() => { setTradeModal(null); setSelectedOffer([]) }} title="Proponer intercambio" width={560}>
        {tradeModal && (
          <div>
            <div className="bg-surface-container rounded-xl p-3.5 mb-5 flex items-center gap-3.5">
              <Icon name="arrow_forward" size={20} className="text-primary" />
              <div>
                <div className="text-xs text-on-surface-variant">Querés obtener</div>
                <div className="font-semibold text-on-surface">#{tradeModal.numero} {tradeModal.jugador} ({tradeModal.seleccion})</div>
                <div className="text-xs text-on-surface-variant">de {tradeModal.owner}</div>
              </div>
            </div>
            <div className="text-sm font-semibold text-on-surface mb-2.5">Tu álbum está vacío. Publicá figuritas para poder ofrecer en intercambios.</div>
            <div className="flex gap-2.5 justify-end mt-5">
              <Button variant="text" onClick={() => { setTradeModal(null); setSelectedOffer([]) }}>Cancelar</Button>
              <Button icon="send" onClick={handleSendTrade} disabled>Enviar propuesta</Button>
            </div>
          </div>
        )}
      </Modal>

      <Snackbar {...snack} onClose={() => setSnack({ ...snack, open: false })} />
    </div>
  )
}
