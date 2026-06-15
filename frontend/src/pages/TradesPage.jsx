import { useState, useEffect, useCallback, useRef } from 'react'
import useSWR from 'swr'
import { useModalForm } from '../hooks/useModalForm'
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
import {
  responderIntercambio,
  calificarIntercambio,
  proponerIntercambio,
  obtenerMensajesChat,
  enviarMensajeChat,
} from '../api/intercambios'
import { listarMiAlbum } from '../api/album'
import { useAuth } from '../context/AuthContext'

export default function TradesPage() {
  const location = useLocation()
  const { user, users } = useAuth()
  const userId = user.id
  const getNombre = (id) => users.find((u) => u.id === id)?.nombre ?? `Usuario ${id}`

  const [tab, setTab] = useState(location.state?.tab || 'recibidas')
  const [calificados, setCalificados] = useState(new Set())
  const [snack, setSnack] = useState({ open: false, message: '', type: 'info' })
  const [sugAlbum, setSugAlbum] = useState([])

  // Estados para el Chat
  const [chatModal, setChatModal] = useState(null)
  const [chatMessages, setChatMessages] = useState([])
  const [chatInput, setChatInput] = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  const [chatSending, setChatSending] = useState(false)
  const messagesEndRef = useRef(null)

  const ratingForm = useModalForm({ puntuacion: 0, comentario: '' })
  const sugTrade = useModalForm({ selectedOffer: [] })

  const {
    data: intercambiosData,
    isLoading: loading,
    mutate: mutateIntercambios,
  } = useSWR(['/intercambios/', userId])
  const { data: sugerencias = [], mutate: mutateSugerencias } = useSWR([
    '/publicaciones/sugerencias',
    userId,
  ])

  const recibidas = intercambiosData?.recibidos || []
  const enviadas = intercambiosData?.enviados || []

  useEffect(() => {
    if (location.state?.proponer) {
      sugTrade.openWith(location.state.proponer)
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (sugTrade.open) {
      listarMiAlbum()
        .then((data) => setSugAlbum(data.figuritas || data))
        .catch((e) =>
          setSnack({ open: true, message: 'Error cargando álbum: ' + e.message, type: 'error' }),
        )
    }
  }, [sugTrade.open])

  async function handleResponse(id, decision) {
    try {
      await responderIntercambio(id, decision)
      setSnack({ open: true, message: `Intercambio ${decision} exitosamente`, type: 'success' })
      if (chatModal?.id === id) setChatModal(null)
      mutateIntercambios()
    } catch (e) {
      setSnack({
        open: true,
        message: 'Error al responder intercambio: ' + e.message,
        type: 'error',
      })
    }
  }

  async function handleRate() {
    if (ratingForm.form.puntuacion === 0) {
      setSnack({ open: true, message: 'Por favor, seleccioná una puntuación', type: 'error' })
      return
    }
    try {
      await calificarIntercambio(ratingForm.open.id, {
        puntuacion: ratingForm.form.puntuacion,
        comentario: ratingForm.form.comentario,
      })
      setCalificados((prev) => new Set([...prev, ratingForm.open.id]))
      setSnack({ open: true, message: 'Calificación enviada', type: 'success' })
      ratingForm.close()
    } catch (e) {
      setSnack({ open: true, message: 'Error al enviar calificación: ' + e.message, type: 'error' })
    }
  }

  async function handleSugTrade() {
    if (sugTrade.form.selectedOffer.length === 0) {
      setSnack({
        open: true,
        message: 'Seleccioná al menos una figurita para ofrecer',
        type: 'error',
      })
      return
    }
    sugTrade.setPending(true)
    try {
      await proponerIntercambio({
        figuritas_ofrecidas_numero: sugTrade.form.selectedOffer,
        figurita_solicitada_numero: sugTrade.open.publicacion.numero,
        solicitado_a_id: sugTrade.open.publicacion.usuario_id,
      })
      setSnack({ open: true, message: 'Propuesta enviada con éxito', type: 'success' })
      sugTrade.close()
      mutateIntercambios()
      mutateSugerencias()
    } catch (e) {
      setSnack({ open: true, message: 'Error al enviar propuesta: ' + e.message, type: 'error' })
    } finally {
      sugTrade.setPending(false)
    }
  }

  function toggleSugOffer(numero) {
    sugTrade.setForm((f) => ({
      ...f,
      selectedOffer: f.selectedOffer.includes(numero)
        ? f.selectedOffer.filter((n) => n !== numero)
        : [...f.selectedOffer, numero],
    }))
  }

  const fetchMessages = useCallback(async (id) => {
    try {
      const data = await obtenerMensajesChat(id)
      setChatMessages(data || [])
    } catch (e) {
      console.error('Error cargando mensajes:', e)
    }
  }, [])

  useEffect(() => {
    if (!chatModal) {
      setChatMessages([])
      return
    }

    setChatLoading(true)
    fetchMessages(chatModal.id).finally(() => setChatLoading(false))

    const interval = setInterval(() => {
      fetchMessages(chatModal.id)
    }, 4000)

    return () => clearInterval(interval)
  }, [chatModal, fetchMessages])

  useEffect(() => {
    if (chatModal) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [chatMessages, chatModal])

  async function handleSendMessage(e) {
    if (e) e.preventDefault()
    if (!chatInput.trim() || chatSending || !chatModal) return

    setChatSending(true)
    const content = chatInput.trim()
    setChatInput('')

    try {
      await enviarMensajeChat(chatModal.id, content)
      await fetchMessages(chatModal.id)
    } catch (e) {
      setSnack({ open: true, message: 'Error al enviar mensaje: ' + e.message, type: 'error' })
      setChatInput(content)
    } finally {
      setChatSending(false)
    }
  }

  const [filtroEstado, setFiltroEstado] = useState('todos')

  const currentList = tab === 'recibidas' ? recibidas : enviadas
  const filteredList =
    filtroEstado === 'todos'
      ? currentList
      : currentList.filter((item) => item.estado === filtroEstado)

  function handleTabChange(newTab) {
    setTab(newTab)
    setFiltroEstado('todos')
  }

  const FILTROS = [
    { id: 'todos', label: 'Todos' },
    { id: 'pendiente', label: 'Pendiente' },
    { id: 'aceptado', label: 'Aceptado' },
    { id: 'rechazado', label: 'Rechazado' },
  ]

  return (
    <div className="p-8 max-w-[900px]">
      <h1 className="text-3xl font-bold text-on-surface mb-5">Intercambios</h1>

      <Tabs
        tabs={[
          { id: 'recibidas', label: `Recibidas (${recibidas.length})` },
          { id: 'enviadas', label: `Enviadas (${enviadas.length})` },
          { id: 'sugerencias', label: 'Sugerencias automáticas' },
        ]}
        active={tab}
        onChange={handleTabChange}
      />

      {tab !== 'sugerencias' && (
        <div className="flex gap-2 mt-4 flex-wrap">
          {FILTROS.map((f) => {
            const conteo =
              f.id === 'todos'
                ? currentList.length
                : currentList.filter((i) => i.estado === f.id).length
            return (
              <button
                key={f.id}
                onClick={() => setFiltroEstado(f.id)}
                className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-colors ${
                  filtroEstado === f.id
                    ? 'bg-primary text-on-primary border-primary'
                    : 'bg-surface border-outline text-on-surface-variant hover:bg-surface-container'
                }`}
              >
                {f.label}
                {conteo > 0 && (
                  <span
                    className={`ml-1.5 px-1.5 py-0.5 rounded-full text-[10px] ${
                      filtroEstado === f.id ? 'bg-on-primary/20' : 'bg-surface-container-high'
                    }`}
                  >
                    {conteo}
                  </span>
                )}
              </button>
            )
          })}
        </div>
      )}

      <div className="mt-4">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Icon
              name="progress_activity"
              size={32}
              className="animate-spin text-on-surface-variant"
            />
          </div>
        ) : tab === 'sugerencias' ? (
          <div>
            <Card
              style={{
                background:
                  'linear-gradient(135deg, var(--color-primary-container), var(--color-tertiary-container))',
                border: 'none',
                marginBottom: 16,
              }}
            >
              <div className="flex items-center gap-3">
                <Icon name="auto_awesome" size={28} className="text-primary" />
                <div>
                  <div className="font-semibold text-[15px] text-on-primary-container">
                    Sugerencias inteligentes
                  </div>
                  <div className="text-xs-plus text-on-primary-container/80">
                    Basadas en tus faltantes y las repetidas de otros usuarios
                  </div>
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
                        <div className="font-semibold">
                          {sug.publicacion.jugador} ({sug.publicacion.equipo})
                        </div>
                        <div className="text-sm text-on-surface-variant">
                          Ofrecida por {sug.ofrecida_por}
                        </div>
                        <div className="text-xs text-primary font-medium mt-0.5">
                          Cubre tu faltante #{sug.cubre_tu_faltante}
                        </div>
                      </div>
                    </div>
                    <Button
                      variant="tonal"
                      size="sm"
                      icon="swap_horiz"
                      onClick={() => sugTrade.openWith(sug)}
                    >
                      Proponer intercambio
                    </Button>
                  </Card>
                ))}
              </div>
            )}
          </div>
        ) : filteredList.length === 0 ? (
          <EmptyState
            icon="swap_horiz"
            title={
              currentList.length === 0
                ? tab === 'recibidas'
                  ? 'Sin propuestas recibidas'
                  : 'Sin propuestas enviadas'
                : `Sin intercambios ${filtroEstado === 'todos' ? '' : filtroEstado + 's'}`
            }
            subtitle={
              currentList.length === 0
                ? tab === 'recibidas'
                  ? 'Cuando alguien te proponga un intercambio aparecerá acá'
                  : 'Las propuestas que enviés a otros usuarios aparecerán acá'
                : 'Probá con otro filtro'
            }
          />
        ) : (
          <div className="flex flex-col gap-3">
            {filteredList.map((item) => (
              <Card key={item.id} className="p-4">
                <div className="flex justify-between items-start mb-3">
                  <div className="flex items-center gap-2">
                    <Avatar
                      name={
                        tab === 'recibidas'
                          ? getNombre(item.propuesto_por)
                          : getNombre(item.solicitado_a)
                      }
                      size={32}
                    />
                    <span className="font-medium truncate max-w-[160px]">
                      {tab === 'recibidas'
                        ? getNombre(item.propuesto_por)
                        : getNombre(item.solicitado_a)}
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span
                      className={`text-xs font-bold uppercase px-2 py-1 rounded-full ${
                        item.estado === 'pendiente'
                          ? 'bg-surface-variant text-on-surface-variant'
                          : item.estado === 'aceptado'
                            ? 'bg-success/20 text-success'
                            : 'bg-error/20 text-error'
                      }`}
                    >
                      {item.estado}
                    </span>
                    {item.estado === 'pendiente' && (
                      <Button
                        variant="tonal"
                        size="sm"
                        icon="chat"
                        onClick={() => setChatModal({ ...item, isReceived: tab === 'recibidas' })}
                        className="!p-1 !h-7 !w-7 !min-w-0 !rounded-full"
                        title="Chatear sobre este intercambio"
                      />
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-4 bg-surface-container/50 p-3 rounded-lg mb-4">
                  <div className="flex-1 text-center">
                    <div className="text-[10px] text-on-surface-variant uppercase font-bold mb-1">
                      {tab === 'recibidas' ? 'Te ofrece' : 'Tú ofreces'}
                    </div>
                    <div className="font-bold text-primary">
                      #{item.figuritas_ofrecidas.join(', #')}
                    </div>
                  </div>
                  <Icon name="swap_horiz" className="text-on-surface-variant" />
                  <div className="flex-1 text-center">
                    <div className="text-[10px] text-on-surface-variant uppercase font-bold mb-1">
                      {tab === 'recibidas' ? 'Tú ofreces' : 'Te piden'}
                    </div>
                    <div className="font-bold text-secondary">#{item.figurita_solicitada}</div>
                  </div>
                </div>

                {tab === 'recibidas' && item.estado === 'pendiente' && (
                  <div className="flex gap-2">
                    <Button
                      variant="tonal"
                      className="flex-1"
                      icon="close"
                      onClick={() => handleResponse(item.id, 'rechazado')}
                    >
                      Rechazar
                    </Button>
                    <Button
                      className="flex-1"
                      icon="check"
                      onClick={() => handleResponse(item.id, 'aceptado')}
                    >
                      Aceptar
                    </Button>
                  </div>
                )}

                {item.estado === 'aceptado' && !item.ya_calificado && !calificados.has(item.id) && (
                  <Button
                    variant="tonal"
                    className="w-full"
                    icon="star"
                    onClick={() =>
                      ratingForm.openWith({
                        id: item.id,
                        user:
                          tab === 'recibidas'
                            ? getNombre(item.propuesto_por)
                            : getNombre(item.solicitado_a),
                      })
                    }
                  >
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
        )}
      </div>

      {/* Modal proponer intercambio desde sugerencia */}
      <Modal
        open={!!sugTrade.open}
        onClose={sugTrade.close}
        title="Proponer intercambio"
        width={560}
      >
        {sugTrade.open && (
          <div>
            <div className="bg-surface-container rounded-xl p-3.5 mb-5 flex items-center gap-3.5">
              <Icon name="arrow_forward" size={20} className="text-primary" />
              <div>
                <div className="text-xs text-on-surface-variant">Querés obtener</div>
                <div className="font-semibold text-on-surface">
                  #{sugTrade.open.publicacion.numero} {sugTrade.open.publicacion.jugador} (
                  {sugTrade.open.publicacion.equipo})
                </div>
                <div className="text-xs text-on-surface-variant">
                  de {sugTrade.open.ofrecida_por}
                </div>
              </div>
            </div>

            <div className="mb-4">
              <div className="text-sm font-semibold text-on-surface mb-2.5">
                Tus figuritas (seleccioná para ofrecer):
              </div>
              {sugAlbum.length === 0 ? (
                <div className="text-sm text-on-surface-variant italic py-2">
                  No tenés figuritas en tu álbum para ofrecer.
                </div>
              ) : (
                <div className="flex flex-wrap gap-2 max-h-[200px] overflow-y-auto p-1">
                  {sugAlbum.map((fig) => (
                    <Chip
                      key={fig.id}
                      selected={sugTrade.form.selectedOffer.includes(fig.numero)}
                      onClick={() => toggleSugOffer(fig.numero)}
                    >
                      #{fig.numero} {fig.jugador || fig.equipo}
                    </Chip>
                  ))}
                </div>
              )}
            </div>

            <div className="flex gap-2.5 justify-end mt-5">
              <Button variant="text" onClick={sugTrade.close}>
                Cancelar
              </Button>
              <Button
                icon={sugTrade.pending ? 'progress_activity' : 'send'}
                onClick={handleSugTrade}
                disabled={sugTrade.form.selectedOffer.length === 0 || sugTrade.pending}
              >
                {sugTrade.pending ? 'Enviando...' : 'Enviar propuesta'}
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* Rating Modal */}
      <Modal
        open={!!ratingForm.open}
        onClose={ratingForm.close}
        title="Calificar usuario"
        width={380}
      >
        {ratingForm.open && (
          <div className="text-center py-2.5">
            <Avatar name={ratingForm.open.user} size={56} />
            <div className="font-semibold text-base mt-2.5 text-on-surface">
              {ratingForm.open.user}
            </div>
            <p className="text-on-surface-variant text-sm mt-2 mb-4">
              ¿Cómo fue la experiencia de intercambio?
            </p>

            <div className="flex justify-center mb-4">
              <StarRating
                value={ratingForm.form.puntuacion}
                onChange={(v) => ratingForm.setForm((f) => ({ ...f, puntuacion: v }))}
                size={36}
              />
            </div>

            <textarea
              className="w-full bg-surface-container border border-outline rounded-lg p-3 text-sm text-on-surface focus:outline-primary mb-4"
              rows={3}
              placeholder="Escribe un comentario opcional..."
              value={ratingForm.form.comentario}
              onChange={(e) => ratingForm.setForm((f) => ({ ...f, comentario: e.target.value }))}
            />

            <div className="mt-2">
              <Button
                onClick={handleRate}
                className="w-full"
                disabled={ratingForm.form.puntuacion === 0}
              >
                Enviar calificación
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* Chat Modal */}
      <Modal
        open={!!chatModal}
        onClose={() => setChatModal(null)}
        title={
          chatModal
            ? `Chat con ${getNombre(chatModal.isReceived ? chatModal.propuesto_por : chatModal.solicitado_a)}`
            : 'Chat'
        }
        width={500}
      >
        {chatModal && (
          <div className="flex flex-col h-[450px]">
            {/* Cabecera del chat con info del intercambio */}
            <div className="bg-surface-container/60 p-3 rounded-lg flex items-center justify-between text-xs mb-3 border border-outline/35">
              <div>
                <span className="font-semibold text-primary">Te ofrece:</span> #
                {chatModal.figuritas_ofrecidas.join(', #')}
              </div>
              <Icon name="swap_horiz" className="text-on-surface-variant mx-1" size={16} />
              <div>
                <span className="font-semibold text-secondary">Ofreces:</span> #
                {chatModal.figurita_solicitada}
              </div>
            </div>

            {/* Area de mensajes */}
            <div className="flex-1 overflow-y-auto mb-4 p-2 bg-surface-container/30 rounded-lg border border-outline/20 space-y-3 flex flex-col min-h-0">
              {chatLoading && chatMessages.length === 0 ? (
                <div className="flex items-center justify-center flex-1 py-8">
                  <Icon name="progress_activity" size={24} className="animate-spin text-primary" />
                </div>
              ) : chatMessages.length === 0 ? (
                <div className="text-center text-on-surface-variant/60 text-xs my-auto italic py-8">
                  No hay mensajes aún. ¡Escribe el primero!
                </div>
              ) : (
                chatMessages.map((msg) => {
                  const isMe =
                    msg.remitente_id !==
                    (chatModal.isReceived ? chatModal.propuesto_por : chatModal.solicitado_a)
                  return (
                    <div
                      key={msg.id}
                      className={`max-w-[75%] p-3 rounded-2xl text-[13px] leading-relaxed shadow-sm ${
                        isMe
                          ? 'bg-primary text-on-primary rounded-tr-none self-end'
                          : 'bg-surface-container text-on-surface rounded-tl-none self-start border border-outline/10'
                      }`}
                    >
                      <div className="font-semibold text-[10px] opacity-75 mb-0.5">
                        {isMe ? 'Tú' : getNombre(msg.remitente_id)}
                      </div>
                      <div>{msg.contenido}</div>
                      <div className="text-[9px] opacity-60 text-right mt-1">
                        {new Date(msg.fecha_envio).toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </div>
                    </div>
                  )
                })
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input del chat */}
            <form
              onSubmit={handleSendMessage}
              className="flex gap-2 border-t border-outline/25 pt-3"
            >
              <input
                type="text"
                className="flex-1 bg-surface-container border border-outline/35 rounded-full px-4 py-2 text-sm text-on-surface focus:outline-none focus:border-primary placeholder:text-on-surface-variant/50"
                placeholder="Escribe un mensaje..."
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                disabled={chatSending}
              />
              <Button
                type="submit"
                variant="filled"
                className="!rounded-full p-2 h-10 w-10 flex items-center justify-center min-w-0"
                disabled={!chatInput.trim() || chatSending}
              >
                <Icon
                  name={chatSending ? 'progress_activity' : 'send'}
                  size={18}
                  className={chatSending ? 'animate-spin' : ''}
                />
              </Button>
            </form>
          </div>
        )}
      </Modal>

      <Snackbar {...snack} onClose={() => setSnack({ ...snack, open: false })} />
    </div>
  )
}
