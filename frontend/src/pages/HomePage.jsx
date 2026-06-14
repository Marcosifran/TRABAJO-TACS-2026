import { useState, useEffect } from 'react'
import { useModalForm } from '../hooks/useModalForm'
import { useNavigate } from 'react-router-dom'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Icon from '../components/ui/Icon'
import EmptyState from '../components/ui/EmptyState'
import Modal from '../components/ui/Modal'
import Snackbar from '../components/ui/Snackbar'
import FiguritaCard from '../components/FiguritaCard'
import SubastaCardRow from '../components/SubastaCardRow'
import { listarMisPublicaciones, buscarPublicaciones } from '../api/publicaciones'
import { listarFaltantes, obtenerReputacion, obtenerSugerencias } from '../api/faltantes'
import { listarIntercambios } from '../api/intercambios'
import { listarMiAlbum } from '../api/album'
import { listarSubastas, ofertarSubasta } from '../api/subastas'
import WorldCupSchedule from '../sections/WorldCupSchedule'
import { useUser } from '../context/UserContext'
import { isAuctionActive } from '../utils/auctionTime'

export default function HomePage() {
  const navigate = useNavigate()
  const { user, users } = useUser()
  const [figuritasCount, setFiguritasCount] = useState('—')
  const [faltanCount, setFaltanCount] = useState('—')
  const [intercambiosCount, setIntercambiosCount] = useState('—')
  const [reputacion, setReputacion] = useState('—')
  const [ultimasPublicadas, setUltimasPublicadas] = useState([])
  const [sugerencias, setSugerencias] = useState([])
  const [subastasPorFinalizar, setSubastasPorFinalizar] = useState([])
  const [pubsMap, setPubsMap] = useState({})

  const bid = useModalForm({ offerIds: [] })
  const [miAlbum, setMiAlbum] = useState([])
  const [snack, setSnack] = useState({
    open: false,
    message: '',
    type: 'info',
  })

  useEffect(() => {
    listarMiAlbum()
      .then((data) => setFiguritasCount((data.figuritas || data).length))
      .catch(() => {})
    listarFaltantes()
      .then((data) => setFaltanCount((data || []).length))
      .catch(() => {})
    listarIntercambios()
      .then((data) =>
        setIntercambiosCount((data.enviados?.length || 0) + (data.recibidos?.length || 0)),
      )
      .catch(() => {})
    // Nota: El ID del usuario debería venir del contexto. Uso 1 como fallback si no hay.
    const userId = users.indexOf(user) + 1
    obtenerReputacion(userId)
      .then((data) =>
        setReputacion(data.promedio_puntuacion != null ? data.promedio_puntuacion.toFixed(1) : '—'),
      )
      .catch(() => {})
    buscarPublicaciones({ incluir_propias: true })
      .then((data) => setUltimasPublicadas(data.slice(0, 4)))
      .catch(() => {})
    obtenerSugerencias()
      .then((data) => setSugerencias(data || []))
      .catch(() => {})
  }, [user])

  useEffect(() => {
    let cancelled = false
    async function loadSubastasYAlbum() {
      try {
        const [subs, pubs, otrasPubs, album] = await Promise.all([
          listarSubastas(),
          listarMisPublicaciones(),
          buscarPublicaciones(),
          listarMiAlbum(),
        ])
        if (cancelled) return
        const map = {}
        ;[...pubs, ...otrasPubs].forEach((p) => {
          map[p.id] = p
        })
        setPubsMap(map)
        setMiAlbum(album.figuritas || album)
        const ahora = Date.now()
        const list = (subs || [])
          .filter((s) => isAuctionActive(s, ahora))
          .sort((a, b) => new Date(a.fin) - new Date(b.fin))
          .slice(0, 4)
        setSubastasPorFinalizar(list)
      } catch {
        /* ignorar */
      }
    }
    loadSubastasYAlbum()
    return () => {
      cancelled = true
    }
  }, [])

  function toggleOferta(id) {
    bid.setForm((f) => ({
      ...f,
      offerIds: f.offerIds.includes(id) ? f.offerIds.filter((x) => x !== id) : [...f.offerIds, id],
    }))
  }

  async function handleOfertar() {
    if (bid.form.offerIds.length === 0) {
      setSnack({ open: true, message: 'Seleccioná al menos una figurita', type: 'error' })
      return
    }
    bid.setPending(true)
    try {
      await ofertarSubasta(bid.open.id, bid.form.offerIds)
      setSnack({ open: true, message: 'Oferta enviada con éxito', type: 'success' })
      bid.close()
    } catch (error) {
      setSnack({ open: true, message: error.message, type: 'error' })
    } finally {
      bid.setPending(false)
    }
  }

  const STATS = [
    {
      icon: 'collections_bookmark',
      label: 'Figuritas',
      value: figuritasCount,
      colorVar: 'var(--color-primary)',
    },
    {
      icon: 'playlist_add',
      label: 'Faltan',
      value: faltanCount,
      colorVar: 'var(--color-secondary)',
    },
    {
      icon: 'swap_horiz',
      label: 'Intercambios',
      value: intercambiosCount,
      colorVar: 'var(--color-tertiary)',
    },
    { icon: 'star', label: 'Reputación', value: reputacion, colorVar: 'var(--color-gold)' },
  ]

  return (
    <div className="p-8 max-w-[1100px]">
      <div className="mb-7">
        <h1 className="text-3xl font-bold text-on-surface m-0">Bienvenido de vuelta 👋</h1>
        <p className="mt-1 text-on-surface-variant text-[15px]">
          Tu resumen de actividad en FiguSwap
        </p>
      </div>

      {/* Estadisticas Figuritas - Faltan - Intercambios - Reputación */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
        {STATS.map((s, i) => (
          <Card key={i} elevated>
            <div className="flex items-center gap-3.5">
              <div
                className="w-11 h-11 rounded-[14px] flex items-center justify-center shrink-0"
                style={{ background: s.colorVar + '18' }}
              >
                <Icon name={s.icon} size={24} style={{ color: s.colorVar }} />
              </div>
              <div>
                <div className="text-2xl font-bold text-on-surface">{s.value}</div>
                <div className="text-xs-plus text-on-surface-variant">{s.label}</div>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Acciones Publicar Figurita - Buscar Figuritas - Ver Subastas */}
      <div className="flex gap-2.5 mb-8">
        <Button icon="add" onClick={() => navigate('/coleccion')}>
          Publicar figurita
        </Button>
        <Button variant="tonal" icon="search" onClick={() => navigate('/buscar')}>
          Buscar figuritas
        </Button>
        <Button variant="outlined" icon="gavel" onClick={() => navigate('/subastas')}>
          Ver subastas
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Últimas publicadas */}
        <div>
          <div className="flex justify-between items-center mb-3.5">
            <h2 className="text-lg font-semibold m-0">Últimas publicadas</h2>
            <Button variant="text" size="sm" onClick={() => navigate('/buscar')}>
              Ver todas
            </Button>
          </div>
          {ultimasPublicadas.length === 0 ? (
            <EmptyState
              icon="style"
              title="Sin figuritas publicadas"
              subtitle="Todavía no hay figuritas disponibles para intercambio"
            />
          ) : (
            <div className="flex flex-col gap-2">
              {ultimasPublicadas.map((pub) => (
                <FiguritaCard
                  key={pub.id}
                  compact
                  figurita={{
                    id: pub.id,
                    numero: pub.numero,
                    seleccion: pub.equipo,
                    jugador: pub.jugador,
                    tipo:
                      pub.tipo_intercambio === 'intercambio_directo' ? 'intercambio' : 'subasta',
                    cantidad: pub.cantidad_disponible,
                    owner: `Usuario ${pub.usuario_id}`,
                  }}
                />
              ))}
            </div>
          )}
        </div>

        <div>
          <div className="flex justify-between items-center mb-3.5">
            <h2 className="text-lg font-semibold m-0">Subastas por finalizar</h2>
            <Button variant="text" size="sm" onClick={() => navigate('/subastas')}>
              Ver todas
            </Button>
          </div>
          {subastasPorFinalizar.length === 0 ? (
            <EmptyState
              icon="gavel"
              title="Sin subastas activas"
              subtitle="No hay subastas próximas a finalizar"
            />
          ) : (
            <div className="flex flex-col gap-3">
              {subastasPorFinalizar.map((sub) => (
                <SubastaCardRow
                  key={sub.id}
                  sub={sub}
                  pubsMap={pubsMap}
                  user={user}
                  users={users}
                  onOfertar={(s) => bid.openWith(s)}
                  showVerOfertasButton={false}
                />
              ))}
            </div>
          )}

          <h2 className="text-lg font-semibold mt-6 mb-3.5">Sugerencias para vos</h2>
          <Card
            style={{
              background:
                'linear-gradient(135deg, var(--color-primary-container), var(--color-tertiary-container))',
              border: 'none',
            }}
          >
            <div className="flex items-center gap-3">
              <Icon name="auto_awesome" size={28} className="text-primary" />
              <div className="flex-1">
                {sugerencias.length === 0 ? (
                  <>
                    <div className="font-semibold text-[14px] text-on-primary-container">
                      Sin sugerencias aún
                    </div>
                    <div className="text-xs-plus text-on-primary-container/80">
                      Registrá tus faltantes para recibir sugerencias automáticas
                    </div>
                  </>
                ) : (
                  <>
                    <div className="font-semibold text-[14px] text-on-primary-container">
                      {sugerencias.length} sugerencia{sugerencias.length > 1 ? 's' : ''} disponible
                      {sugerencias.length > 1 ? 's' : ''}
                    </div>
                    <div className="text-xs-plus text-on-primary-container/80">
                      #{sugerencias[0].publicacion.numero} {sugerencias[0].publicacion.jugador} (
                      {sugerencias[0].publicacion.equipo})
                      {sugerencias.length > 1 ? ` y ${sugerencias.length - 1} más` : ''}
                    </div>
                  </>
                )}
              </div>
              <Button
                size="sm"
                onClick={() => navigate('/intercambios', { state: { tab: 'sugerencias' } })}
              >
                Ver
              </Button>
            </div>
          </Card>
        </div>
      </div>

      <Modal
        open={!!bid.open}
        onClose={bid.close}
        title={`Ofertar en Subasta #${bid.open?.id}`}
        width={520}
      >
        {bid.open && (
          <div className="flex flex-col gap-4">
            <p className="text-sm text-on-surface-variant">
              Seleccioná las figuritas de tu álbum que querés ofrecer a cambio:
            </p>

            {miAlbum.length === 0 ? (
              <div className="p-4 bg-error-container text-on-error-container rounded-lg text-sm">
                No tenés figuritas en tu álbum personal para ofrecer. Agregá figuritas desde Mi
                Colección.
              </div>
            ) : (
              <div className="max-h-[300px] overflow-y-auto grid grid-cols-1 sm:grid-cols-2 gap-2 p-1">
                {miAlbum.map((fig) => (
                  <label
                    key={fig.id}
                    className={`flex items-center gap-3 p-3 border rounded-xl cursor-pointer transition-colors ${bid.form.offerIds.includes(fig.id) ? 'border-primary bg-primary-container/20' : 'border-outline-variant hover:bg-surface-container-low'}`}
                  >
                    <input
                      type="checkbox"
                      className="w-4 h-4 accent-primary"
                      checked={bid.form.offerIds.includes(fig.id)}
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
              <Button variant="text" onClick={bid.close} disabled={bid.pending}>
                Cancelar
              </Button>
              <Button
                icon="gavel"
                onClick={handleOfertar}
                disabled={bid.pending || bid.form.offerIds.length === 0}
              >
                {bid.pending ? 'Enviando...' : `Enviar oferta (${bid.form.offerIds.length})`}
              </Button>
            </div>
          </div>
        )}
      </Modal>

      <Snackbar {...snack} onClose={() => setSnack({ ...snack, open: false })} />

      <WorldCupSchedule />
    </div>
  )
}
