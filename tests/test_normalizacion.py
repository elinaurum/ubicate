from ubicate.busqueda.normalizacion import clave, normalizar, tokens


def test_variantes_ortograficas_colapsan_a_una_clave():
    assert clave("B-04") == clave("b 04") == clave("B04") == clave("sala B04") == "b04"


def test_quita_tildes_y_puntuacion():
    assert normalizar("¿Dónde queda Ingeniería Química?") == "ingenieria quimica"


def test_palabras_vacias_no_vacian_el_texto():
    # "sala" sola es una palabra vacía, pero no debe devolver cadena vacía.
    assert normalizar("sala") == "sala"


def test_tokens_descarta_palabras_de_relleno():
    assert tokens("¿Dónde queda la sala F-21?") == ["f", "21"]
