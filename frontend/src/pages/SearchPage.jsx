import { useState, useEffect, useCallback, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import useSWR from 'swr'
import Input from '../components/ui/Input'
import Chip from '../components/ui/Chip'
import Icon from '../components/ui/Icon'
import Autocomplete from '../components/ui/Autocomplete'
import EmptyState from '../components/ui/EmptyState'
import Snackbar from '../components/ui/Snackbar'
import FiguritaCard from '../components/FiguritaCard'
import { buscarPublicaciones } from '../api/publicaciones'
import { buscarJugadores } from '../api/maestro'
import { isAuctionActive } from '../utils/auctionTime'
import { useAuth } from '../context/AuthContext'

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

function jugadorLabel(j) {
  return `${j.jugador} — ${j.equipo} (#${j.numero})`
}

export default function SearchPage() {
  const navigate = useNavigate()
  const { users } = useAuth()
  const { data: subastasCache = [] } = useSWR('/subastas')
  const { data: equiposData } = useSWR('/maestro/equipos')
  const equipos = equiposData?.equipos ?? []

  const [nameQuery, setNameQuery] = useState('')
  const [countryQuery, setCountryQuery] = useState('')
  const [selFilter, setSelFilter] = useState('Todas')
  const [catFilter, setCatFilter] = useState('Todas')
  const [tipoFilter, setTipoFilter] = useState('todos')
  // Jugador elegido desde cualquiera de los autocompletados (filtra por número).
  const [selectedPlayer, setSelectedPlayer] = useState(null)
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [snack, setSnack] = useState({ open: false, message: '', type: 'info' })
  const debounceRef = useRef(null)

  const fetchResults = useCallback(async ({ player, rawQuery, sel, tipo }) => {
    setLoading(true)
    try {
      const params = {}
      if (player) {
        params.numero = player.numero
      } else if (rawQuery) {
        const num = parseInt(rawQuery)
        if (!isNaN(num) && String(num) === rawQuery.trim()) params.numero = num
        else params.jugador = rawQuery
      }
      if (!player && sel !== 'Todas') params.equipo = sel
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
    const delay = nameQuery && !selectedPlayer ? 300 : 0
    debounceRef.current = setTimeout(
      () => fetchResults({ player: selectedPlayer, rawQuery: nameQuery, sel: selFilter, tipo: tipoFilter }),
      delay,
    )
    return () => clearTimeout(debounceRef.current)
  }, [nameQuery, selectedPlayer, selFilter, tipoFilter, fetchResults])

  function handleSelectPlayer(j) {
    setSelectedPlayer(j)
    setNameQuery(j.jugador)
    setCountryQuery('')
  }

  function clearSelection() {
    setSelectedPlayer(null)
    setNameQuery('')
    setCountryQuery('')
  }

  function handleSelectCountry(value) {
    setSelFilter(value)
    setSelectedPlayer(null)
    setCountryQuery('')
  }

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

  const equipoOptions = ['Todas', ...equipos].map((e) => ({ value: e, label: e }))

  return (
    <div className="p-4 sm:p-6">
      <h1 className="text-2xl font-bold text-on-surface mb-4">Buscar Figuritas</h1>

      <div className="flex flex-col gap-3 mb-6">
        {/* Búsqueda por nombre de jugador o número, con autocompletado del maestro */}
        <div className="max-w-md">
          <Autocomplete
            value={nameQuery}
            onChange={(v) => {
              setNameQuery(v)
              if (selectedPlayer) setSelectedPlayer(null)
            }}
            fetchSuggestions={(q) => buscarJugadores(q)}
            getOptionKey={(j) => j.numero}
            getOptionLabel={jugadorLabel}
            renderOption={(j) => (
              <span>
                <span className="font-medium">{j.jugador}</span>
                <span className="text-on-surface-variant"> — {j.equipo} (#{j.numero})</span>
              </span>
            )}
            onSelect={handleSelectPlayer}
            placeholder="Buscar por jugador o número..."
          />
        </div>

        {/* Búsqueda por país: elegir selección y luego jugador de ese país */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs-plus text-on-surface-variant font-medium">Selección:</span>
          <div className="w-44">
            <Input value={selFilter} onChange={handleSelectCountry} options={equipoOptions} />
          </div>
          {selFilter !== 'Todas' && (
            <div className="w-64">
              <Autocomplete
                value={countryQuery}
                onChange={setCountryQuery}
                fetchSuggestions={(q) => buscarJugadores(q, selFilter)}
                getOptionKey={(j) => j.numero}
                getOptionLabel={jugadorLabel}
                renderOption={(j) => (
                  <span>
                    <span className="font-medium">{j.jugador}</span>
                    <span className="text-on-surface-variant"> (#{j.numero})</span>
                  </span>
                )}
                onSelect={handleSelectPlayer}
                icon="person_search"
                placeholder={`Jugador de ${selFilter}...`}
              />
            </div>
          )}
        </div>

        {selectedPlayer && (
          <div className="flex items-center gap-2">
            <Chip selected icon="check">
              {selectedPlayer.jugador} · {selectedPlayer.equipo} · #{selectedPlayer.numero}
            </Chip>
            <button
              type="button"
              onClick={clearSelection}
              className="text-xs-plus text-on-surface-variant hover:text-on-surface flex items-center gap-1"
            >
              <Icon name="close" size={16} /> Limpiar
            </button>
          </div>
        )}

        {/* Filtros de categoría (pendientes) y tipo de intercambio */}
        <div className="flex flex-wrap items-center gap-2">
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
