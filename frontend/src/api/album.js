import { apiFetch } from "./client"

export function listarMiAlbum(){
    return apiFetch('/album')
}
