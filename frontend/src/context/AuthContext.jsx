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

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => sessionStorage.getItem(TOKEN_KEY) || null)
  const [user, setUser] = useState(readStoredUser)
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
