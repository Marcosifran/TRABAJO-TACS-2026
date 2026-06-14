import { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { loginRequest, registerRequest } from '../api/auth'
import { listarUsuarios } from '../api/usuarios'

const AuthContext = createContext()

// El token (JWT) se guarda bajo la misma clave que leía el cliente HTTP,
// de modo que apiFetch lo encuentra sin cambios adicionales.
const TOKEN_KEY = 'figuswap-token'
const USER_KEY = 'figuswap-usuario'

function readStoredUser() {
  try {
    const raw = sessionStorage.getItem(USER_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

// Lee una sesión consistente: solo es válida si están el token y el usuario.
// Una sesión incompleta (p. ej. un token viejo previo a la migración a JWT,
// sin usuario guardado) se descarta para no renderizar con user = null.
function readSession() {
  const storedToken = sessionStorage.getItem(TOKEN_KEY)
  const storedUser = readStoredUser()
  if (!storedToken || !storedUser) {
    sessionStorage.removeItem(TOKEN_KEY)
    sessionStorage.removeItem(USER_KEY)
    return { token: null, user: null }
  }
  return { token: storedToken, user: storedUser }
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => readSession().token)
  const [user, setUser] = useState(() => readSession().user)
  // Lista de todos los usuarios, para resolver nombres a partir de ids en la UI.
  const [users, setUsers] = useState([])

  const persistSession = useCallback((accessToken, usuario) => {
    sessionStorage.setItem(TOKEN_KEY, accessToken)
    sessionStorage.setItem(USER_KEY, JSON.stringify(usuario))
    setToken(accessToken)
    setUser(usuario)
  }, [])

  const login = useCallback(async (email, password) => {
    const { access_token, usuario } = await loginRequest(email, password)
    persistSession(access_token, usuario)
    return usuario
  }, [persistSession])

  const register = useCallback(async (nombre, email, password) => {
    const { access_token, usuario } = await registerRequest(nombre, email, password)
    persistSession(access_token, usuario)
    return usuario
  }, [persistSession])

  const logout = useCallback(() => {
    sessionStorage.removeItem(TOKEN_KEY)
    sessionStorage.removeItem(USER_KEY)
    setToken(null)
    setUser(null)
    setUsers([])
  }, [])

  // Si una llamada a la API responde 401 (token expirado/inválido), cerramos la
  // sesión; ProtectedLayout se encarga de redirigir al login en el próximo render.
  useEffect(() => {
    window.addEventListener('figuswap:unauthorized', logout)
    return () => window.removeEventListener('figuswap:unauthorized', logout)
  }, [logout])

  // Cuando hay sesión activa, traemos la lista de usuarios para los lookups por id.
  // Se reintenta al cambiar el token (login / cambio de sesión). Al cerrar sesión,
  // logout() ya deja la lista vacía, así que no hace falta limpiarla acá.
  useEffect(() => {
    if (!token) return
    let cancelado = false
    listarUsuarios()
      .then(data => { if (!cancelado) setUsers(data || []) })
      .catch(() => { /* lookups caen al fallback "Usuario N" */ })
    return () => { cancelado = true }
  }, [token])

  return (
    <AuthContext.Provider
      value={{ user, users, token, isAuthenticated: !!token, login, register, logout }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
