"""Definición del capítulo 1. Identificadores estables para escenas y opciones.

Convención de identificadores: `s<escena>_<nombre>`; las opciones usan verbos cortos.
FASE 2: escenas 1 (El despertar) y 2 (La persecución). Las escenas 3 a 5 llegan en la FASE 3.
"""
from __future__ import annotations

from yulu.narrative.schema import Choice, DialogueLine, Effect, Scene

NARRATOR = "Narrador"
YOU = "Tú"

START_SCENE = "s1_despertar"


def _scene(*args, **kwargs) -> Scene:
    return Scene(*args, **kwargs)


_SCENES: list[Scene] = [
    # ---------------- ESCENA 1: EL DESPERTAR ----------------
    _scene(
        id="s1_despertar",
        chapter_step=1,
        title="El despertar",
        background="forest_dense",
        jaguar_visible=False,
        lines=(
            DialogueLine(NARRATOR, "Despiertas con la cara contra la tierra húmeda. No recuerdas cómo llegaste aquí."),
            DialogueLine(NARRATOR, "Es de noche. El bosque respira a tu alrededor: insectos, hojas, un viento que no ves."),
            DialogueLine(NARRATOR, "Entre los árboles, algo se mueve sin hacer ruido. Luego, silencio."),
            DialogueLine(YOU, "¿Dónde estoy...? Tengo que pensar. Tengo que moverme antes de que amanezca."),
        ),
        choices=(
            Choice(
                id="escuchar",
                text="Quedarte inmóvil y escuchar el bosque.",
                next_scene="s1_escuchar",
                effect=Effect(threat=0, flags=("observador",)),
                feedback="Respiras despacio. Cuando dejas de moverte, el bosque empieza a hablarte.",
            ),
            Choice(
                id="gritar",
                text="Gritar pidiendo ayuda.",
                next_scene="s1_grito",
                effect=Effect(threat=20),
                feedback="Tu voz rompe la noche. Todo calla de golpe... y luego un rugido bajo responde a lo lejos.",
            ),
            Choice(
                id="caminar",
                text="Caminar hacia la oscuridad sin esperar.",
                next_scene="s1_camino",
                effect=Effect(threat=10),
                feedback="Avanzas a tientas. Las raíces te hacen tropezar y cada rama rota suena como un disparo.",
            ),
        ),
    ),
    _scene(
        id="s1_escuchar",
        chapter_step=1,
        title="El despertar",
        background="forest_dense",
        jaguar_visible=True,
        lines=(
            DialogueLine(NARRATOR, "A tu derecha corre agua. A tu izquierda, muy lejos, un tambor marca un ritmo lento."),
            DialogueLine(NARRATOR, "Y detrás de ti, dos puntos ámbar se encienden entre los helechos. Te están mirando."),
            DialogueLine(YOU, "Un tambor significa gente. El agua significa un camino. Pero no puedo quedarme aquí."),
        ),
        choices=(
            Choice(
                id="tambor",
                text="Seguir el sonido del tambor.",
                next_scene="s2_persecucion",
                effect=Effect(threat=0, flags=("rumbo_aldea",)),
                feedback="Caminas hacia el ritmo. Los ojos ámbar se mueven contigo, a la misma distancia.",
            ),
            Choice(
                id="agua",
                text="Seguir el sonido del agua.",
                next_scene="s2_persecucion",
                effect=Effect(threat=5),
                feedback="El río te guía, pero el suelo blando deja huellas... y algo las sigue.",
            ),
        ),
    ),
    _scene(
        id="s1_grito",
        chapter_step=1,
        title="El despertar",
        background="forest_dense",
        jaguar_visible=True,
        lines=(
            DialogueLine(NARRATOR, "El eco de tu grito muere. Nadie responde, salvo el bosque."),
            DialogueLine(NARRATOR, "Ahora sabes que no estás solo. Y lo que te acompaña ya sabe dónde estás."),
        ),
        choices=(
            Choice(
                id="correr",
                text="Echar a correr en cualquier dirección.",
                next_scene="s2_persecucion",
                effect=Effect(threat=15),
                feedback="Corres. Las ramas te azotan la cara. Oyes las zarpas golpear la tierra detrás de ti.",
            ),
            Choice(
                id="agacharse",
                text="Agacharte y esperar en silencio.",
                next_scene="s2_persecucion",
                effect=Effect(threat=5, flags=("observador",)),
                feedback="Te haces pequeño entre las raíces. El jaguar pasa cerca, olfatea... y sigue de largo. Por ahora.",
            ),
        ),
    ),
    _scene(
        id="s1_camino",
        chapter_step=1,
        title="El despertar",
        background="forest_dense",
        jaguar_visible=True,
        lines=(
            DialogueLine(NARRATOR, "Tras unos pasos el suelo se abre en un claro. La luna ilumina un sendero de tierra pisada."),
            DialogueLine(NARRATOR, "Al otro lado del claro, dos ojos ámbar flotan a la altura de tu cintura."),
            DialogueLine(YOU, "Un sendero. Alguien lo usa. Pero ese animal está justo entre el camino y yo."),
        ),
        choices=(
            Choice(
                id="rodear",
                text="Rodear el claro por la sombra.",
                next_scene="s2_persecucion",
                effect=Effect(threat=5, flags=("rumbo_aldea",)),
                feedback="Avanzas pegado a los troncos. Los ojos giran siguiéndote, pero no se acercan.",
            ),
            Choice(
                id="cruzar",
                text="Cruzar el claro directo hacia el sendero.",
                next_scene="s2_persecucion",
                effect=Effect(threat=15, flags=("rumbo_aldea",)),
                feedback="Cruzas bajo la luna, a la vista. El jaguar baja la cabeza y empieza a moverse.",
            ),
        ),
    ),
    # ---------------- ESCENA 2: LA PERSECUCIÓN ----------------
    _scene(
        id="s2_persecucion",
        chapter_step=2,
        title="La persecución",
        background="forest_path",
        jaguar_visible=True,
        ambient="forest_tense",
        timer_seconds=15.0,
        timeout_choice="paralizarse",
        lines=(
            DialogueLine(NARRATOR, "Un rugido corto, muy cerca. El jaguar ya no se esconde."),
            DialogueLine(NARRATOR, "Delante de ti el sendero se bifurca: una ceiba enorme, un río negro y la pendiente que baja hacia el tambor."),
            DialogueLine(YOU, "No hay tiempo. Decide."),
        ),
        choices=(
            Choice(
                id="correr",
                text="Correr pendiente abajo sin mirar atrás.",
                next_scene="s2_corrida",
                effect=Effect(threat=25),
                feedback="Corres hasta que los pulmones arden. El jaguar corre más rápido que tú, pero el ruido de abajo lo frena.",
            ),
            Choice(
                id="ceiba",
                text="Trepar a la ceiba.",
                next_scene="s2_ceiba",
                effect=Effect(threat=-10, flags=("observador",)),
                feedback="Subes por las raíces tabulares hasta una rama alta. Abajo, el jaguar da vueltas y gruñe.",
            ),
            Choice(
                id="rio",
                text="Meterte en el río.",
                next_scene="s2_rio",
                effect=Effect(threat=-15, flags=("mojado",)),
                feedback="El agua está helada y te llega al pecho. En la orilla, el jaguar duda y no entra.",
            ),
            Choice(
                id="paralizarse",
                text="Quedarte paralizado.",
                next_scene="s2_paralizado",
                effect=Effect(threat=30),
                feedback="No te mueves. El jaguar tampoco... hasta que salta. Caes, ruedas y echas a correr.",
            ),
        ),
    ),
    _scene(
        id="s2_corrida",
        chapter_step=2,
        title="La persecución",
        background="forest_path",
        jaguar_visible=True,
        ambient="forest_tense",
        lines=(
            DialogueLine(NARRATOR, "La pendiente termina de golpe. Frente a ti, entre los árboles, arde una línea de antorchas."),
            DialogueLine(NARRATOR, "Detrás, las zarpas se detienen. El jaguar no se acerca al fuego. Todavía."),
        ),
        choices=(
            Choice(
                id="antorchas",
                text="Acercarte a las antorchas.",
                next_scene="s2_claro",
                effect=Effect(threat=-5),
                feedback="Caminas hacia la luz con las piernas temblando.",
            ),
        ),
    ),
    _scene(
        id="s2_ceiba",
        chapter_step=2,
        title="La persecución",
        background="forest_path",
        jaguar_visible=True,
        lines=(
            DialogueLine(NARRATOR, "Desde la rama ves lo que el suelo escondía: un resplandor naranja al fondo del valle. Antorchas. Una aldea."),
            DialogueLine(NARRATOR, "El jaguar se aburre de esperar y se aleja entre la niebla. Sabes que volverá."),
        ),
        choices=(
            Choice(
                id="bajar",
                text="Bajar y caminar hacia el resplandor.",
                next_scene="s2_claro",
                effect=Effect(threat=0, flags=("rumbo_aldea",)),
                feedback="Bajas con cuidado y sigues la luz a través de la niebla.",
            ),
        ),
    ),
    _scene(
        id="s2_rio",
        chapter_step=2,
        title="La persecución",
        background="forest_path",
        jaguar_visible=True,
        lines=(
            DialogueLine(NARRATOR, "La corriente te arrastra río abajo. Cuando por fin tocas fondo, el bosque se ha abierto."),
            DialogueLine(NARRATOR, "En la otra orilla, a lo lejos, antorchas. Y en tu orilla, muy atrás, un rugido frustrado."),
        ),
        choices=(
            Choice(
                id="salir",
                text="Salir del agua y caminar hacia las antorchas.",
                next_scene="s2_claro",
                effect=Effect(threat=0, flags=("rumbo_aldea",)),
                feedback="Empapado y tiritando, sigues la luz.",
            ),
        ),
    ),
    _scene(
        id="s2_paralizado",
        chapter_step=2,
        title="La persecución",
        background="forest_path",
        jaguar_visible=True,
        ambient="forest_tense",
        lines=(
            DialogueLine(NARRATOR, "Tienes un corte en el brazo y el corazón en la garganta, pero sigues vivo."),
            DialogueLine(NARRATOR, "Corres sin rumbo hasta que una luz naranja aparece entre los troncos. Fuego. Gente."),
        ),
        choices=(
            Choice(
                id="luz",
                text="Ir hacia la luz.",
                next_scene="s2_claro",
                effect=Effect(threat=5),
                feedback="Te sujetas el brazo y caminas hacia el fuego.",
            ),
        ),
    ),
    _scene(
        id="s2_claro",
        chapter_step=2,
        title="La persecución",
        background="village_edge",
        jaguar_visible=True,
        ambient="village_distant",
        lines=(
            DialogueLine(NARRATOR, "Una empalizada de troncos. Antorchas en lo alto. Detrás, techos de palma y el tambor que oíste al despertar."),
            DialogueLine(NARRATOR, "Una figura con lanza se asoma sobre la empalizada y te grita algo en una lengua que no entiendes."),
            DialogueLine(YOU, "No entiendo nada de lo que dice. Pero si no consigo que me abran, el jaguar me alcanzará aquí mismo."),
        ),
        choices=(
            Choice(
                id="acercarse",
                text="Levantar las manos y acercarte a la puerta.",
                next_scene="s3_puerta_demo",
                effect=Effect(threat=0),
                feedback="Avanzas despacio, con las manos a la vista.",
            ),
        ),
    ),
    # Nodo terminal provisional de la FASE 2. Se reemplaza en la FASE 3 por la escena 3 (La aldea).
    _scene(
        id="s3_puerta_demo",
        chapter_step=3,
        title="Fin de la demo (FASE 2)",
        background="village_edge",
        jaguar_visible=False,
        ambient="village_distant",
        ending="demo_fase2",
        lines=(
            DialogueLine(NARRATOR, "[Demo FASE 2] Aquí comenzará la escena 3: La aldea. Pulsa R para volver a jugar o Esc para salir."),
        ),
    ),
]

SCENES: dict[str, Scene] = {scene.id: scene for scene in _SCENES}
