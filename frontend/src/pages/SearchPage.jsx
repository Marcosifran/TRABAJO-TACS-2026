import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import useSWR from 'swr'
import Input from '../components/ui/Input'
import Chip from '../components/ui/Chip'
import Icon from '../components/ui/Icon'
import EmptyState from '../components/ui/EmptyState'
import Snackbar from '../components/ui/Snackbar'
import FiguritaCard from '../components/FiguritaCard'
import { buscarPublicaciones } from '../api/publicaciones'
import { isAuctionActive } from '../utils/auctionTime'
import { useAuth } from '../context/AuthContext'

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
]
const CATEGORIAS = ['Escudo', 'Jugador', 'Estadio', 'Leyenda', 'Especial']

function pubToCard(pub, users = []) {
  return {
    id: pub.id,
    numero: pub.numero,
    seleccion: pub.equipo,
    jugador: pub.jugador,
    tipo: pub.tipo_intercambio === 'intercambio_directo' ? 'intercambio' : 'subasta',
    cantidad: pub.cantidad_disponible,
    owner: users.find((u) => u.id === pub.usuario_id)?.nombre ?? `Usuario ${pub.usuario_id}`,
    _usuarioId: pub.usuario_id,
  }
}

export default function SearchPage() {
  const navigate = useNavigate()
  const { users } = useAuth()
  const { data: subastasCache = [] } = useSWR('/subastas')
  const [query, setQuery] = useState('')
  const [selFilter, setSelFilter] = useState('Todas')
  const [catFilter, setCatFilter] = useState('Todas')
  const [tipoFilter, setTipoFilter] = useState('todos')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
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
          const matchSeleccion = SELECCIONES.find(
            (s) =>
              s.toLowerCase().includes(q.toLowerCase()) ||
              q.toLowerCase().includes(s.toLowerCase()),
          )
          if (matchSeleccion) params.equipo = matchSeleccion
          else params.jugador = q
        }
      }
      if (sel !== 'Todas') params.equipo = sel
      if (tipo !== 'todos')
        params.tipo_intercambio = tipo === 'intercambio' ? 'intercambio_directo' : 'subasta'
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

  function handleIntercambio(card) {
    navigate('/intercambios', {
      state: {
        proponer: {
          publicacion: {
            numero: card.numero,
            jugador: card.jugador,
            equipo: card.seleccion,
            usuario_id: card._usuarioId,
          },
          ofrecida_por: card.owner,
        },
      },
    })
  }

  function handleSubasta(pub) {
    const activa = subastasCache.find(
      (s) => s.figurita_id === pub.id && isAuctionActive(s, Date.now()),
    )
    if (activa) {
      navigate('/subastas', { state: { subastaId: activa.id } })
    } else {
      setSnack({ open: true, message: 'No hay subasta activa para esta figurita', type: 'info' })
    }
  }

  return (
    <div className="p-4 sm:p-6">
      <h1 className="text-2xl font-bold text-on-surface mb-4">Buscar Figuritas</h1>

      <div className="flex flex-wrap gap-3 mb-6">
        <div className="flex items-center gap-2">
          <Input
            value={query}
            onChange={setQuery}
            icon="search"
            placeholder="Buscar por jugador, número o selección..."
          />
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs-plus text-on-surface-variant font-medium mr-1">Selección:</span>
          {['Todas', ...SELECCIONES.slice(0, 6)].map((s) => (
            <Chip key={s} selected={selFilter === s} onClick={() => setSelFilter(s)}>
              {s}
            </Chip>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs-plus text-on-surface-variant font-medium mr-1">Categoría:</span>
          {['Todas', ...CATEGORIAS].map((c) => (
            <Chip key={c} selected={catFilter === c} onClick={() => setCatFilter(c)} disabled>
              {c}
            </Chip>
          ))}
          <div className="ml-auto flex gap-1.5">
            <Chip selected={tipoFilter === 'todos'} onClick={() => setTipoFilter('todos')}>
              Todos
            </Chip>
            <Chip
              selected={tipoFilter === 'intercambio'}
              onClick={() => setTipoFilter('intercambio')}
              icon="swap_horiz"
            >
              Intercambio
            </Chip>
            <Chip
              selected={tipoFilter === 'subasta'}
              onClick={() => setTipoFilter('subasta')}
              icon="gavel"
            >
              Subasta
            </Chip>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12">
          <Icon name="progress_activity" className="text-primary animate-spin" />
        </div>
      ) : results.length > 0 ? (
        <div className="grid grid-cols-[repeat(auto-fill,minmax(160px,1fr))] gap-2">
          {results.map((pub) => {
            const card = pubToCard(pub, users)
            return (
              <FiguritaCard
                key={pub.id}
                figurita={card}
                size="collection"
                onAction={
                  card.tipo === 'intercambio'
                    ? () => handleIntercambio(card)
                    : () => handleSubasta(pub)
                }
              />
            )
          })}
        </div>
      ) : (
        <EmptyState
          icon="search_off"
          title="Sin resultados"
          subtitle="No hay figuritas publicadas por otros usuarios en este momento"
        />
      )}

      <Snackbar {...snack} onClose={() => setSnack({ ...snack, open: false })} />
    </div>
  )
}
