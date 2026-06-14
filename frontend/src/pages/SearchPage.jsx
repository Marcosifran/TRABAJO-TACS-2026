import { useState, useEffect, useCallback, useRef } from 'react'
import Input from '../components/ui/Input'
import Chip from '../components/ui/Chip'
import Modal from '../components/ui/Modal'
import Button from '../components/ui/Button'
import Icon from '../components/ui/Icon'
import EmptyState from '../components/ui/EmptyState'
import Snackbar from '../components/ui/Snackbar'
import FiguritaCard from '../components/FiguritaCard'
import { buscarPublicaciones, listarMisPublicaciones } from '../api/publicaciones'
import { listarMiAlbum } from '../api/album'
import { proponerIntercambio } from '../api/intercambios'

const SELECCIONES = ['Argentina','Brasil','Francia','Alemania','España','Inglaterra','Portugal','México','USA','Canadá']
const CATEGORIAS  = ['Escudo','Jugador','Estadio','Leyenda','Especial']

function pubToCard(pub) {
  return {
    id: pub.id,
    numero: pub.numero,
    seleccion: pub.equipo,
    jugador: pub.jugador,
    tipo: pub.tipo_intercambio === 'intercambio_directo' ? 'intercambio' : 'subasta',
    cantidad: pub.cantidad_disponible,
    owner: `Usuario ${pub.usuario_id}`,
    _usuarioId: pub.usuario_id,
  }
}

export default function SearchPage() {
  const [query,       setQuery]       = useState('')
  const [selFilter,   setSelFilter]   = useState('Todas')
  const [catFilter,   setCatFilter]   = useState('Todas')
  const [tipoFilter,  setTipoFilter]  = useState('todos')
  const [results,     setResults]     = useState([])
  const [loading,     setLoading]     = useState(false)
  const [tradeModal,  setTradeModal]  = useState(null)
  const [myAlbum,     setMyAlbum]     = useState([])
  const [myPubs,      setMyPubs]      = useState([])
  const [selectedOffer, setSelectedOffer] = useState([])
  const [submitting,  setSubmitting]  = useState(false)
  const [snack, setSnack] = useState({ open: false, message: '', type: 'info' })
  const debounceRef = useRef(null)

  const fetchResults = useCallback(async (q, sel, tipo) => {
    setLoading(true)
    try {
      const params = {}
      if (q) {
        const num = parseInt(q)
        if (!isNaN(num)) {
          params.numero = num
        } else {
          const matchSeleccion = SELECCIONES.find(s =>
            s.toLowerCase().includes(q.toLowerCase()) || q.toLowerCase().includes(s.toLowerCase())
          )
          if (matchSeleccion) params.equipo = matchSeleccion
          else params.jugador = q
        }
      }
      if (sel !== 'Todas') params.equipo = sel
      if (tipo !== 'todos') params.tipo_intercambio = tipo === 'intercambio' ? 'intercambio_directo' : 'subasta'
      const data = await buscarPublicaciones(params)
      setResults(data)
    } catch (e) {
      setSnack({ open: true, message: e.message, type: 'error' })
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    const delay = query ? 300 : 0
    debounceRef.current = setTimeout(() => fetchResults(query, selFilter, tipoFilter), delay)
    return () => clearTimeout(debounceRef.current)
  }, [query, selFilter, tipoFilter, fetchResults])

  useEffect(() => {
    if (tradeModal) {
      Promise.all([listarMiAlbum(), listarMisPublicaciones()])
        .then(([album, pubs]) => {
          setMyAlbum(album)
          setMyPubs(pubs)
        })
        .catch(e => setSnack({ open: true, message: 'Error cargando datos: ' + e.message, type: 'error' }))
    }
  }, [tradeModal])

  async function handleSendTrade() {
    if (selectedOffer.length === 0) {
      setSnack({ open: true, message: 'Seleccioná al menos una figurita para ofrecer', type: 'error' })
      return
    }
    setSubmitting(true)
    try {
      await proponerIntercambio({
        figuritas_ofrecidas_numero: selectedOffer,
        figurita_solicitada_numero: tradeModal.numero,
        solicitado_a_id: tradeModal._usuarioId
      })
      setSnack({ open: true, message: 'Propuesta enviada con éxito', type: 'success' })
      setTradeModal(null)
      setSelectedOffer([])
    } catch (e) {
      setSnack({ open: true, message: 'Error al enviar propuesta: ' + e.message, type: 'error' })
    } finally {
      setSubmitting(false)
    }
  }

  function toggleOffer(numero) {
    if (selectedOffer.includes(numero)) {
      setSelectedOffer(prev => prev.filter(n => n !== numero))
    } else {
      setSelectedOffer(prev => [...prev, numero])
    }
  }

  const cards = results.map(pubToCard)

  return (
    <div className="p-4 sm:p-6 md:p-8 max-w-[1100px]">
      <h1 className="text-3xl font-bold text-on-surface mb-5">Buscar Figuritas</h1>

      <div className="mb-5">
        <Input value={query} onChange={setQuery} icon="search" placeholder="Buscar por jugador, número o selección..." />
      </div>

      <div className="flex items-center flex-wrap gap-2 mb-3">
        <span className="text-[13px] text-on-surface-variant font-medium mr-1">Selección:</span>
        {['Todas', ...SELECCIONES.slice(0, 6)].map(s => (
          <Chip key={s} selected={selFilter === s} onClick={() => setSelFilter(s)}>{s}</Chip>
        ))}
      </div>

      <div className="flex items-center flex-wrap gap-2 mb-5">
        <span className="text-[13px] text-on-surface-variant font-medium mr-1">Categoría:</span>
        {['Todas', ...CATEGORIAS].map(c => (
          <Chip key={c} selected={catFilter === c} onClick={() => setCatFilter(c)} disabled>{c}</Chip>
        ))}
        <div className="ml-auto flex gap-1.5">
          <Chip selected={tipoFilter === 'todos'}       onClick={() => setTipoFilter('todos')}>Todos</Chip>
          <Chip selected={tipoFilter === 'intercambio'} onClick={() => setTipoFilter('intercambio')} icon="swap_horiz">Intercambio</Chip>
          <Chip selected={tipoFilter === 'subasta'}     onClick={() => setTipoFilter('subasta')}     icon="gavel">Subasta</Chip>
        </div>
      </div>

      <div className="text-[13px] text-on-surface-variant mb-4">
        {loading ? 'Buscando...' : `${results.length} resultado${results.length !== 1 ? 's' : ''}`}
      </div>

      {loading ? (
        <div className="flex items-center justify-center gap-3 py-16 text-on-surface-variant">
          <Icon name="progress_activity" size={24} className="animate-spin" />
          Buscando...
        </div>
      ) : cards.length === 0 ? (
        <EmptyState
          icon="search_off"
          title="Sin resultados"
          subtitle="No hay figuritas publicadas por otros usuarios en este momento"
        />
      ) : (
        <div className="grid grid-cols-[repeat(auto-fill,minmax(200px,1fr))] gap-3.5">
          {cards.map(f => (
            <FiguritaCard 
              key={f.id} 
              figurita={f} 
              onTrade={f.tipo === 'intercambio' ? setTradeModal : null} 
            />
          ))}
        </div>
      )}

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

            <div className="mb-4">
              <div className="text-sm font-semibold text-on-surface mb-2.5">Tus figuritas (seleccioná para ofrecer):</div>
              {myAlbum.length === 0 ? (
                <div className="text-sm text-on-surface-variant italic py-2">No tenés figuritas en tu álbum para ofrecer.</div>
              ) : (
                <div className="flex flex-wrap gap-2 max-h-[200px] overflow-y-auto p-1">
                  {myAlbum.map(fig => {
                    const isSubasta = myPubs.find(p => p.figurita_personal_id === fig.id && p.tipo_intercambio === 'subasta')
                    return (
                      <Chip
                        key={fig.id}
                        selected={selectedOffer.includes(fig.numero)}
                        onClick={() => toggleOffer(fig.numero)}
                        disabled={!!isSubasta}
                        title={isSubasta ? "Esta figurita está en subasta" : ""}
                      >
                        #{fig.numero} {fig.jugador || fig.equipo}
                      </Chip>
                    )
                  })}
                </div>
              )}
            </div>

            <div className="flex gap-2.5 justify-end mt-5">
              <Button variant="text" onClick={() => { setTradeModal(null); setSelectedOffer([]) }}>Cancelar</Button>
              <Button
                icon={submitting ? "progress_activity" : "send"}
                onClick={handleSendTrade}
                disabled={selectedOffer.length === 0 || submitting}
              >
                {submitting ? "Enviando..." : "Enviar propuesta"}
              </Button>
            </div>
          </div>
        )}
      </Modal>

      <Snackbar {...snack} onClose={() => setSnack({ ...snack, open: false })} />
    </div>
  )
}
