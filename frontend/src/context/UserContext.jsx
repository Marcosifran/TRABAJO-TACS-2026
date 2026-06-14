import { createContext, useContext, useState, useEffect } from 'react'

export const STORAGE_KEY_INDEX = 'figuswap-user-index'

export const USERS = [
  {
    nombre: 'Usuario 1',
    email: 'user1@figuswap',
    token: import.meta.env.VITE_USER_1_TOKEN || '',
    es_admin: true,
  },
  {
    nombre: 'Usuario 2',
    email: 'user2@figuswap',
    token: import.meta.env.VITE_USER_2_TOKEN || '',
    es_admin: false,
  },
]

const UserContext = createContext()

export function UserProvider({ children }) {
  const [index, setIndex] = useState(() => {
    const saved = sessionStorage.getItem(STORAGE_KEY_INDEX)
    return saved !== null ? parseInt(saved, 10) : 0
  })

  useEffect(() => {
    sessionStorage.setItem(STORAGE_KEY_INDEX, String(index))
  }, [index])

  const user = USERS[index]

  return (
    <UserContext.Provider value={{ user, users: USERS, switchUser: setIndex }}>
      {children}
    </UserContext.Provider>
  )
}

export function useUser() {
  return useContext(UserContext)
}
