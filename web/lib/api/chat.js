/*Esta clase define la estructura de una solicitud de chat, envia un mensaje al backend y devuelve el ReadableStream SSE. 
El formato de los eventos del backend es : 
 data: {"content": "...", "agent": "educador|demostrador|evaluador|critico"}\n\n
 *   data: [DONE]\n\n
 */

export async function sendChatMessage(message, signal) {
    const response = await fetch("/backend/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ message }),
        signal,
    });

    //Si nos devuelve el error 401, es un error de autenticación, por lo que lanzamos un error específico para manejarlo en el frontend
    if (response.status === 401) throw new Error("NO_AUTH");
    // Si la respuesta no es exitosa, intentamos obtener el mensaje de error del cuerpo de la respuesta y lanzamos un error con ese mensaje.
    if (!response.ok) {
        const errorText = await response.json().catch(() => ({}));
        throw new Error(errorText.error || errorText.detail || `Error: ${response.status}`);
    }

    return response.body; // Devolvemos el ReadableStream para procesar los eventos SSE
}
