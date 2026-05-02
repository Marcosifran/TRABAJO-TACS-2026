import { createContext, useContext, useState } from 'react'

const UserContext = createContext()

const USERS = [
  {
    nombre: 'Usuario 1',
    email:  'user1@figuswap',
    token:  import.meta.env.VITE_USER_1_TOKEN || '',
  },
  {
    nombre: 'Usuario 2',
    email:  'user2@figuswap',
    token:  import.meta.env.VITE_USER_2_TOKEN || '',
  },
]

export function UserProvider({ children }) {
  const [index, setIndex] = useState(() => {
    const saved = localStorage.getItem('figuswap-user-index')
    const i = saved !== null ? parseInt(saved) : 0
    // Síncrono: el token queda disponible antes de cualquier efecto hijo
    localStorage.setItem('figuswap-token', USERS[i].token)
    return i
  })

  const user = USERS[index]

  function switchUser(i) {
    localStorage.setItem('figuswap-user-index', i)
    localStorage.setItem('figuswap-token', USERS[i].token)
    setIndex(i)
  }

  return (
    <UserContext.Provider value={{ user, users: USERS, switchUser }}>
      {children}
    </UserContext.Provider>
  )
}

export function useUser() {
  return useContext(UserContext)
}
