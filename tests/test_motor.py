from ubicate.chat.motor import Conversacion, MotorChat
from ubicate.chat.proveedores import Mensaje, ProveedorEco


class ProveedorFalso:
    """Devuelve un texto fijo; sirve para probar la extracción de la marca."""

    nombre = "falso"

    def __init__(self, salida: str) -> None:
        self.salida = salida
        self.ultimo_sistema = ""

    def responder(self, sistema: str, mensajes: list[Mensaje]) -> str:
        self.ultimo_sistema = sistema
        return self.salida


def _motor(settings, repo, kb, proveedor):
    return MotorChat(settings, repo, kb, proveedor)


def test_extrae_marca_de_lugar_y_la_borra_del_texto(settings, repo, kb):
    proveedor = ProveedorFalso("La sala B04 está en el piso -1.\n[[LUGAR:B04]]")
    respuesta = _motor(settings, repo, kb, proveedor).responder("dónde queda B04", Conversacion())
    assert [d.id for d in respuesta.destinos] == ["B04"]
    assert respuesta.destino.id == "B04"
    assert "[[LUGAR" not in respuesta.texto


def test_extrae_varias_marcas_en_orden_y_sin_repetir(settings, repo, kb):
    proveedor = ProveedorFalso(
        "Puede ser en la B04 o en la B03.\n[[LUGAR:B04]]\n[[LUGAR:B03]]\n[[LUGAR:B04]]"
    )
    respuesta = _motor(settings, repo, kb, proveedor).responder(
        "dónde rindo la evaluación", Conversacion()
    )
    assert [d.id for d in respuesta.destinos] == ["B04", "B03"]
    assert "[[LUGAR" not in respuesta.texto


def test_marca_invalida_no_rompe(settings, repo, kb):
    proveedor = ProveedorFalso("Texto cualquiera.\n[[LUGAR:NO_EXISTE]]")
    respuesta = _motor(settings, repo, kb, proveedor).responder("hola", Conversacion())
    assert respuesta.destinos == ()
    assert respuesta.destino is None
    assert "[[LUGAR" not in respuesta.texto


def test_coincidencia_espacial_llega_al_prompt(settings, repo, kb):
    proveedor = ProveedorFalso("ok")
    _motor(settings, repo, kb, proveedor).responder("B04", Conversacion())
    assert "COINCIDENCIA DIRECTA EN EL PLANO" in proveedor.ultimo_sistema


def test_modo_eco_responde_sin_llm(settings, repo, kb):
    respuesta = _motor(settings, repo, kb, ProveedorEco(settings)).responder(
        "dónde consigo paletas de ping pong", Conversacion()
    )
    assert "ping pong" in respuesta.texto.lower()
    assert respuesta.proveedor == "eco"


def test_historial_se_acota(settings, repo, kb):
    conversacion = Conversacion()
    for i in range(50):
        conversacion.agregar("user", f"m{i}")
        conversacion.agregar("assistant", f"r{i}")
    recientes = conversacion.recientes(settings.historial_max_turnos)
    assert len(recientes) == settings.historial_max_turnos * 2
