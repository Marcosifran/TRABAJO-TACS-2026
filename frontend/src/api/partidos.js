import { apiFetch } from './client'

export async function getPartidos() {
  const data = await apiFetch('/partidos/')
  return data.partidos ?? []
}
