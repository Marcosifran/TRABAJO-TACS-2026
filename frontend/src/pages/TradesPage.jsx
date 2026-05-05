import { useState, useEffect, useCallback } from 'react'
import { useLocation } from 'react-router-dom'
import Tabs from '../components/ui/Tabs'
import Modal from '../components/ui/Modal'
import Button from '../components/ui/Button'
import Avatar from '../components/ui/Avatar'
import StarRating from '../components/ui/StarRating'
import EmptyState from '../components/ui/EmptyState'
import Snackbar from '../components/ui/Snackbar'
import Card from '../components/ui/Card'
import Icon from '../components/ui/Icon'
import Chip from '../components/ui/Chip'
import { listarIntercambios, responderIntercambio, calificarIntercambio, proponerIntercambio } from '../api/intercambios'
import { obtenerSugerencias } from '../api/faltantes'
import { listarMiAlbum } from '../api/album'

export default function TradesPage() {
  const location = useLocation()
  const [tab, setTab]             = useState(location.state?.tab || 'recibidas')
  const [recibidas, setRecibidas] = useState([])
  const [enviadas, setEnviadas]   = useState([])
  const [sugerencias, setSugerencias] = useState([])
  const [loading, setLoading]     = useState(false)
  const [ratingModal, setRatingModal] = useState(null)
  const [rating, setRating]       = useState(0)
  const [comment, setComment]     = useState('')
  const [calificados, setCalificados] = useState(new Set())
  const [snack, setSnack]         = useState({ open: false, message: '', type: 'info' })

  // Estados para el modal de propuesta desde sugerencias
  const [sugTradeModal, setSugTradeModal]     = useState(null)
  const [sugAlbum, setSugAlbum]               = useState([])
  const [sugSelectedOffer, setSugSelectedOffer] = useState([])
  const [sugSubmitting, setSugSubmitting]     = useState(false)

  const fetchIntercambios = useCallback(async () => {
    setLoading(true)
    try {
      const data = await listarIntercambios()
      setRecibidas(data.recibidos || [])
      setEnviadas(data.enviados || [])

      const sugsData = await obtenerSugerencias()
      setSugerencias(sugsData.sugerencias || [])
    } catch (e) {
      setSnack({ open: true, message: 'Error cargando intercambios: ' + e.message, type: 'error' })
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchIntercambios()
  }, [fetchIntercambios])

  useEffect(() => {
    if (sugTradeModal) {
      listarMiAlbum()
        .then(setSugAlbum)
        .catch(e => setSnack({ open: true, message: 'Error cargando álbum: ' + e.message, type: 'error' }))
    }
  }, [sugTradeModal])

  async function handleResponse(id, decision) {
    try {
      await responderIntercambio(id, decision)
      setSnack({ open: true, message: `Intercambio ${decision} exitosamente`, type: 'success' })
      fetchIntercambios()
    } catch (e) {
      setSnack({ open: true, message: 'Error al responder intercambio: ' + e.message, type: 'error' })
    }
  }

  async function handleRate() {
    if (rating === 0) {
      setSnack({ open: true, message: 'Por favor, seleccioná una puntuación', type: 'error' })
      return
    }
    try {
      await calificarIntercambio(ratingModal.id, { puntuacion: rating, comentario: comment })
      setCalificados(prev => new Set([...prev, ratingModal.id]))
      setSnack({ open: true, message: 'Calificación enviada', type: 'success' })
      setRatingModal(null)
      setRating(0)
      setComment('')
    } catch (e) {
      setSnack({ open: true, message: 'Error al enviar calificación: ' + e.message, type: 'error' })
    }
  }

  async function handleSugTrade() {
    if (sugSelectedOffer.length === 0) {
      setSnack({ open: true, message: 'Seleccioná al menos una figurita para ofrecer', type: 'error' })
      return
    }
    setSugSubmitting(true)
    try {
      await proponerIntercambio({
        figuritas_ofrecidas_numero: sugSelectedOffer,
        figurita_solicitada_numero: sugTradeModal.publicacion.numero,
        solicitado_a_id: sugTradeModal.publicacion.usuario_id,
      })
      setSnack({ open: true, message: 'Propuesta enviada con éxito', type: 'success' })
      setSugTradeModal(null)
      setSugSelectedOffer([])
    } catch (e) {
      setSnack({ open: true, message: 'Error al enviar propuesta: ' + e.message, type: 'error' })
    } finally {
      setSugSubmitting(false)
    }
  }

  function toggleSugOffer(numero) {
    setSugSelectedOffer(prev =>
      prev.includes(numero) ? prev.filter(n => n !== numero) : [...prev, numero]
    )
  }

  const currentList = tab === 'recibidas' ? recibidas : enviadas

  return (
    <div className="p-8 max-w-[900px]">
      <h1 className="text-3xl font-bold text-on-surface mb-5">Intercambios</h1>

      <Tabs
        tabs={[
          { id: 'recibidas',   label: `Recibidas (${recibidas.length})` },
          { id: 'enviadas',    label: `Enviadas (${enviadas.length})` },
          { id: 'sugerencias', label: 'Sugerencias automáticas' },
        ]}
        active={tab}
        onChange={setTab}
      />

      <div className="mt-5">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Icon name="progress_activity" size={32} className="animate-spin text-on-surface-variant" />
          </div>
        ) : tab === 'sugerencias' ? (
          <div>
            <Card
              style={{
                background: 'linear-gradient(135deg, var(--color-primary-container), var(--color-tertiary-container))',
                border: 'none',
                marginBottom: 16,
              }}
            >
              <div className="flex items-center gap-3">
                <Icon name="auto_awesome" size={28} className="text-primary" />
                <div>
                  <div className="font-semibold text-[15px] text-on-primary-container">Sugerencias inteligentes</div>
                  <div className="text-[13px] text-on-primary-container/80">Basadas en tus faltantes y las repetidas de otros usuarios</div>
                </div>
              </div>
            </Card>
            {sugerencias.length === 0 ? (
              <EmptyState
                icon="auto_awesome"
                title="Sin sugerencias por ahora"
                subtitle="Registrá tus faltantes y publicá tus repetidas para recibir sugerencias automáticas"
              />
            ) : (
              <div className="grid grid-cols-1 gap-3">
                {sugerencias.map((sug, idx) => (
                  <Card key={idx} className="flex items-center justify-between p-4">
                    <div className="flex items-center gap-4">
                      <div className="bg-primary-container text-on-primary-container w-12 h-12 rounded-lg flex items-center justify-center font-bold text-xl">
                        #{sug.publicacion.numero}
                      </div>
                      <div>
                        <div className="font-semibold">{sug.publicacion.jugador} ({sug.publicacion.equipo})</div>
                        <div className="text-sm text-on-surface-variant">Ofrecida por {sug.ofrecida_por}</div>
                        <div className="text-xs text-primary font-medium mt-0.5">Cubre tu faltante #{sug.cubre_tu_faltante}</div>
                      </div>
                    </div>
                    <Button variant="tonal" size="sm" icon="swap_horiz" onClick={() => setSugTradeModal(sug)}>
                      Proponer intercambio
                    </Button>
                  </Card>
                ))}
              </div>
            )}
          </div>
        ) : (
          currentList.length === 0 ? (
            <EmptyState
              icon="swap_horiz"
              title={tab === 'recibidas' ? 'Sin propuestas recibidas' : 'Sin propuestas enviadas'}
              subtitle={tab === 'recibidas'
                ? 'Cuando alguien te proponga un intercambio aparecerá acá'
                : 'Las propuestas que enviés a otros usuarios aparecerán acá'
              }
            />
          ) : (
            <div className="flex flex-col gap-3">
              {currentList.map(item => (
                <Card key={item.id} className="p-4">
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex items-center gap-2">
                      <Avatar name={tab === 'recibidas' ? `Usuario ${item.propuesto_por}` : `Usuario ${item.solicitado_a}`} size={32} />
                      <span className="font-medium">
                        {tab === 'recibidas' ? `Usuario ${item.propuesto_por}` : `Usuario ${item.solicitado_a}`}
                      </span>
                    </div>
                    <span className={`text-xs font-bold uppercase px-2 py-1 rounded-full ${
                      item.estado === 'pendiente' ? 'bg-surface-variant text-on-surface-variant' :
                      item.estado === 'aceptado' ? 'bg-success/20 text-success' : 'bg-error/20 text-error'
                    }`}>
                      {item.estado}
                    </span>
                  </div>

                  <div className="flex items-center gap-4 bg-surface-container/50 p-3 rounded-lg mb-4">
                    <div className="flex-1 text-center">
                      <div className="text-[10px] text-on-surface-variant uppercase font-bold mb-1">Te ofrece</div>
                      <div className="font-bold text-primary">#{item.figuritas_ofrecidas.join(', #')}</div>
                    </div>
                    <Icon name="swap_horiz" className="text-on-surface-variant" />
                    <div className="flex-1 text-center">
                      <div className="text-[10px] text-on-surface-variant uppercase font-bold mb-1">Tu Ofreces</div>
                      <div className="font-bold text-secondary">#{item.figurita_solicitada}</div>
                    </div>
                  </div>

                  {tab === 'recibidas' && item.estado === 'pendiente' && (
                    <div className="flex gap-2">
                      <Button variant="tonal" className="flex-1" icon="close" onClick={() => handleResponse(item.id, 'rechazado')}>
                        Rechazar
                      </Button>
                      <Button className="flex-1" icon="check" onClick={() => handleResponse(item.id, 'aceptado')}>
                        Aceptar
                      </Button>
                    </div>
                  )}

                  {item.estado === 'aceptado' && !item.ya_calificado && !calificados.has(item.id) && (
                    <Button variant="tonal" className="w-full" icon="star" onClick={() => setRatingModal({
                      id: item.id,
                      user: tab === 'recibidas' ? `Usuario ${item.propuesto_por}` : `Usuario ${item.solicitado_a}`
                    })}>
                      Calificar intercambio
                    </Button>
                  )}
                  {item.estado === 'aceptado' && (item.ya_calificado || calificados.has(item.id)) && (
                    <div className="flex items-center justify-center gap-1.5 text-xs text-on-surface-variant py-1">
                      <Icon name="check_circle" size={14} className="text-green-600" />
                      Ya calificaste este intercambio
                    </div>
                  )}
                </Card>
              ))}
            </div>
          )
        )}
      </div>

      {/* Modal proponer intercambio desde sugerencia */}
      <Modal
        open={!!sugTradeModal}
        onClose={() => { setSugTradeModal(null); setSugSelectedOffer([]) }}
        title="Proponer intercambio"
        width={560}
      >
        {sugTradeModal && (
          <div>
            <div className="bg-surface-container rounded-xl p-3.5 mb-5 flex items-center gap-3.5">
              <Icon name="arrow_forward" size={20} className="text-primary" />
              <div>
                <div className="text-xs text-on-surface-variant">Querés obtener</div>
                <div className="font-semibold text-on-surface">
                  #{sugTradeModal.publicacion.numero} {sugTradeModal.publicacion.jugador} ({sugTradeModal.publicacion.equipo})
                </div>
                <div className="text-xs text-on-surface-variant">de {sugTradeModal.ofrecida_por}</div>
              </div>
            </div>

            <div className="mb-4">
              <div className="text-sm font-semibold text-on-surface mb-2.5">Tus figuritas (seleccioná para ofrecer):</div>
              {sugAlbum.length === 0 ? (
                <div className="text-sm text-on-surface-variant italic py-2">No tenés figuritas en tu álbum para ofrecer.</div>
              ) : (
                <div className="flex flex-wrap gap-2 max-h-[200px] overflow-y-auto p-1">
                  {sugAlbum.map(fig => (
                    <Chip
                      key={fig.id}
                      selected={sugSelectedOffer.includes(fig.numero)}
                      onClick={() => toggleSugOffer(fig.numero)}
                    >
                      #{fig.numero} {fig.jugador || fig.equipo}
                    </Chip>
                  ))}
                </div>
              )}
            </div>

            <div className="flex gap-2.5 justify-end mt-5">
              <Button variant="text" onClick={() => { setSugTradeModal(null); setSugSelectedOffer([]) }}>
                Cancelar
              </Button>
              <Button
                icon={sugSubmitting ? 'progress_activity' : 'send'}
                onClick={handleSugTrade}
                disabled={sugSelectedOffer.length === 0 || sugSubmitting}
              >
                {sugSubmitting ? 'Enviando...' : 'Enviar propuesta'}
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* Rating Modal */}
      <Modal open={!!ratingModal} onClose={() => setRatingModal(null)} title="Calificar usuario" width={380}>
        {ratingModal && (
          <div className="text-center py-2.5">
            <Avatar name={ratingModal.user} size={56} />
            <div className="font-semibold text-base mt-2.5 text-on-surface">{ratingModal.user}</div>
            <p className="text-on-surface-variant text-sm mt-2 mb-4">¿Cómo fue la experiencia de intercambio?</p>

            <div className="flex justify-center mb-4">
              <StarRating value={rating} onChange={setRating} size={36} />
            </div>

            <textarea
              className="w-full bg-surface-container border border-outline rounded-lg p-3 text-sm text-on-surface focus:outline-primary mb-4"
              rows={3}
              placeholder="Escribe un comentario opcional..."
              value={comment}
              onChange={(e) => setComment(e.target.value)}
            />

            <div className="mt-2">
              <Button onClick={handleRate} className="w-full" disabled={rating === 0}>
                Enviar calificación
              </Button>
            </div>
          </div>
        )}
      </Modal>

      <Snackbar {...snack} onClose={() => setSnack({ ...snack, open: false })} />
    </div>
  )
}
