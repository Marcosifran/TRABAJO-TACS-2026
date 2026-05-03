import { apiFetch } from './client'

/*
    Lista las subastas
*/
export function listarSubastas() {
    return apiFetch('/subastas')
}

/*
    se crea una subasta
*/

export function crearSubasta(data) {
    return apiFetch('/subastas', {
        method: "POST",
        body: JSON.stringify(data)
    })
}

/*
    ofertar en una subasta
*/

export function ofertarSubasta(subastaId, figuritasIds){
    return apiFetch(`/subastas/${subastaId}/ofertar`, {
        method: 'POST',
        body: JSON.stringify({ figuritas_ofrecidas: figuritasIds})
    })
}