"""Definición del capítulo 1. Identificadores estables para escenas y opciones.

Convención: `s<escena>_<nombre>` para los nodos; las opciones usan verbos o la expresión
pronunciada. Las frases en náhuat de los personajes se limitan a las expresiones del léxico
(`yulu/language/data/nahuat_ch1.json`), que lleva fuente y estado de validación.
"""
from __future__ import annotations

from yulu.narrative.schema import Branch, Choice, DialogueLine, Effect, Scene

NARRATOR = "Narrador"
YOU = "Tú"
GUARD = "Guardia"
ELDER = "Anciana"
CHILD = "Niño"

T_DESPERTAR = "El despertar"
T_PERSECUCION = "La persecución"
T_ALDEA = "La aldea"
T_CONFIANZA = "La confianza"
T_AMANECER = "El amanecer"

START_SCENE = "s1_despertar"
GOOD_ENDING = "amanecer_aldea"
BAD_ENDING = "amanecer_solo"
TRUST_FOR_GOOD_ENDING = 40
THREAT_LIMIT_FOR_GOOD_ENDING = 84

_SCENES: list[Scene] = [
    # ---------------- ESCENA 1: EL DESPERTAR ----------------
    Scene(
        id="s1_despertar", chapter_step=1, title=T_DESPERTAR, background="forest_dense", jaguar_visible=False,
        lines=(
            DialogueLine(NARRATOR, "Despiertas con la cara contra la tierra húmeda. No recuerdas cómo llegaste aquí."),
            DialogueLine(NARRATOR, "Es de noche. El bosque respira a tu alrededor: insectos, hojas, un viento que no ves."),
            DialogueLine(NARRATOR, "Entre los árboles, algo se mueve sin hacer ruido. Luego, silencio."),
            DialogueLine(YOU, "¿Dónde estoy...? Tengo que pensar. Tengo que moverme antes de que amanezca."),
        ),
        choices=(
            Choice("escuchar", "Quedarte inmóvil y escuchar el bosque.", "s1_escuchar", Effect(flags=("observador",)),
                   "Respiras despacio. Cuando dejas de moverte, el bosque empieza a hablarte."),
            Choice("gritar", "Gritar pidiendo ayuda.", "s1_grito", Effect(threat=20),
                   "Tu voz rompe la noche. Todo calla de golpe... y luego un rugido bajo responde a lo lejos."),
            Choice("caminar", "Caminar hacia la oscuridad sin esperar.", "s1_camino", Effect(threat=10),
                   "Avanzas a tientas. Las raíces te hacen tropezar y cada rama rota suena como un disparo."),
        ),
    ),
    Scene(
        id="s1_escuchar", chapter_step=1, title=T_DESPERTAR, background="forest_dense",
        lines=(
            DialogueLine(NARRATOR, "A tu derecha corre agua. A tu izquierda, muy lejos, un tambor marca un ritmo lento."),
            DialogueLine(NARRATOR, "Y detrás de ti, dos puntos ámbar se encienden entre los helechos. Te están mirando."),
            DialogueLine(YOU, "Un tambor significa gente. El agua significa un camino. Pero no puedo quedarme aquí."),
        ),
        choices=(
            Choice("tambor", "Seguir el sonido del tambor.", "s2_persecucion", Effect(flags=("rumbo_aldea",)),
                   "Caminas hacia el ritmo. Los ojos ámbar se mueven contigo, a la misma distancia."),
            Choice("agua", "Seguir el sonido del agua.", "s2_persecucion", Effect(threat=5),
                   "El río te guía, pero el suelo blando deja huellas... y algo las sigue."),
        ),
    ),
    Scene(
        id="s1_grito", chapter_step=1, title=T_DESPERTAR, background="forest_dense",
        lines=(
            DialogueLine(NARRATOR, "El eco de tu grito muere. Nadie responde, salvo el bosque."),
            DialogueLine(NARRATOR, "Ahora sabes que no estás solo. Y lo que te acompaña ya sabe dónde estás."),
        ),
        choices=(
            Choice("correr", "Echar a correr en cualquier dirección.", "s2_persecucion", Effect(threat=15),
                   "Corres. Las ramas te azotan la cara. Oyes las zarpas golpear la tierra detrás de ti."),
            Choice("agacharse", "Agacharte y esperar en silencio.", "s2_persecucion", Effect(threat=5, flags=("observador",)),
                   "Te haces pequeño entre las raíces. El jaguar pasa cerca, olfatea... y sigue de largo. Por ahora."),
        ),
    ),
    Scene(
        id="s1_camino", chapter_step=1, title=T_DESPERTAR, background="forest_dense",
        lines=(
            DialogueLine(NARRATOR, "Tras unos pasos el suelo se abre en un claro. La luna ilumina un sendero de tierra pisada."),
            DialogueLine(NARRATOR, "Al otro lado del claro, dos ojos ámbar flotan a la altura de tu cintura."),
            DialogueLine(YOU, "Un sendero. Alguien lo usa. Pero ese animal está justo entre el camino y yo."),
        ),
        choices=(
            Choice("rodear", "Rodear el claro por la sombra.", "s2_persecucion", Effect(threat=5, flags=("rumbo_aldea",)),
                   "Avanzas pegado a los troncos. Los ojos giran siguiéndote, pero no se acercan."),
            Choice("cruzar", "Cruzar el claro directo hacia el sendero.", "s2_persecucion", Effect(threat=15, flags=("rumbo_aldea",)),
                   "Cruzas bajo la luna, a la vista. El jaguar baja la cabeza y empieza a moverse."),
        ),
    ),
    # ---------------- ESCENA 2: LA PERSECUCIÓN ----------------
    Scene(
        id="s2_persecucion", chapter_step=2, title=T_PERSECUCION, background="jaguar_close", ambient="forest_tense", jaguar_visible=False,
        timer_seconds=15.0, timeout_choice="paralizarse",
        lines=(
            DialogueLine(NARRATOR, "Un rugido corto, muy cerca. El jaguar ya no se esconde."),
            DialogueLine(NARRATOR, "Delante de ti el sendero se bifurca: una ceiba enorme, un río negro y la pendiente que baja hacia el tambor."),
            DialogueLine(YOU, "No hay tiempo. Decide."),
        ),
        choices=(
            Choice("correr", "Correr pendiente abajo sin mirar atrás.", "s2_corrida", Effect(threat=25),
                   "Corres hasta que los pulmones arden. El jaguar corre más rápido que tú, pero el ruido de abajo lo frena."),
            Choice("ceiba", "Trepar a la ceiba.", "s2_ceiba", Effect(threat=-10, flags=("observador",)),
                   "Subes por las raíces tabulares hasta una rama alta. Abajo, el jaguar da vueltas y gruñe."),
            Choice("rio", "Meterte en el río.", "s2_rio", Effect(threat=-15, flags=("mojado",)),
                   "El agua está helada y te llega al pecho. En la orilla, el jaguar duda y no entra."),
            Choice("paralizarse", "Quedarte paralizado.", "s2_paralizado", Effect(threat=30),
                   "No te mueves. El jaguar tampoco... hasta que salta. Caes, ruedas y echas a correr."),
        ),
    ),
    Scene(
        id="s2_corrida", chapter_step=2, title=T_PERSECUCION, background="forest_path", ambient="forest_tense",
        lines=(
            DialogueLine(NARRATOR, "La pendiente termina de golpe. Frente a ti, entre los árboles, arde una línea de antorchas."),
            DialogueLine(NARRATOR, "Detrás, las zarpas se detienen. El jaguar no se acerca al fuego. Todavía."),
        ),
        choices=(Choice("antorchas", "Acercarte a las antorchas.", "s2_claro", Effect(threat=-5), "Caminas hacia la luz con las piernas temblando."),),
    ),
    Scene(
        id="s2_ceiba", chapter_step=2, title=T_PERSECUCION, background="forest_path", jaguar_visible=False,
        lines=(
            DialogueLine(NARRATOR, "Desde la rama ves lo que el suelo escondía: un resplandor naranja al fondo del valle. Antorchas. Una aldea."),
            DialogueLine(NARRATOR, "El jaguar se aburre de esperar y se aleja entre la niebla. Sabes que volverá."),
        ),
        choices=(Choice("bajar", "Bajar y caminar hacia el resplandor.", "s2_claro", Effect(flags=("rumbo_aldea",)), "Bajas con cuidado y sigues la luz a través de la niebla."),),
    ),
    Scene(
        id="s2_rio", chapter_step=2, title=T_PERSECUCION, background="forest_path", jaguar_visible=False,
        lines=(
            DialogueLine(NARRATOR, "La corriente te arrastra río abajo. Cuando por fin tocas fondo, el bosque se ha abierto."),
            DialogueLine(NARRATOR, "En la otra orilla, a lo lejos, antorchas. Y en tu orilla, muy atrás, un rugido frustrado."),
        ),
        choices=(Choice("salir", "Salir del agua y caminar hacia las antorchas.", "s2_claro", Effect(flags=("rumbo_aldea",)), "Empapado y tiritando, sigues la luz."),),
    ),
    Scene(
        id="s2_paralizado", chapter_step=2, title=T_PERSECUCION, background="jaguar_close", ambient="forest_tense", jaguar_visible=False,
        lines=(
            DialogueLine(NARRATOR, "Tienes un corte en el brazo y el corazón en la garganta, pero sigues vivo."),
            DialogueLine(NARRATOR, "Corres sin rumbo hasta que una luz naranja aparece entre los troncos. Fuego. Gente."),
        ),
        choices=(Choice("luz", "Ir hacia la luz.", "s2_claro", Effect(threat=5), "Te sujetas el brazo y caminas hacia el fuego."),),
    ),
    Scene(
        id="s2_claro", chapter_step=2, title=T_PERSECUCION, background="village_edge", ambient="village_distant", jaguar_visible=False,
        lines=(
            DialogueLine(NARRATOR, "Una empalizada de troncos. Antorchas en lo alto. Detrás, techos de palma y el tambor que oíste al despertar."),
            DialogueLine(NARRATOR, "Una figura con lanza se asoma sobre la empalizada y te grita algo en una lengua que no entiendes."),
            DialogueLine(YOU, "No entiendo nada de lo que dice. Pero si no consigo que me abran, el jaguar me alcanzará aquí mismo."),
        ),
        choices=(Choice("acercarse", "Levantar las manos y acercarte a la puerta.", "s3_puerta", Effect(), "Avanzas despacio, con las manos a la vista."),),
    ),
    # ---------------- ESCENA 3: LA ALDEA ----------------
    Scene(
        id="s3_puerta", chapter_step=3, title=T_ALDEA, background="village_gate", ambient="village_gate", jaguar_visible=False,
        lines=(
            DialogueLine(NARRATOR, "La puerta de troncos se abre apenas un palmo. Una lanza asoma por la rendija."),
            DialogueLine(GUARD, "Tay tikneki?!", nahuat_id="tay_tikneki"),
            DialogueLine(NARRATOR, "No entiendes ni una palabra. El guardia repite más fuerte, señalando con la lanza hacia el bosque."),
        ),
        choices=(
            Choice("repetir", "Repetir sus palabras, despacio: «Tay... tikneki?»", "s3_anciana", Effect(trust=5, learn=("tay_tikneki",)),
                   "El guardia parpadea. Una voz de mujer, detrás de él, ríe bajito y te lo explica con gestos: «tay tikneki» es «¿qué quieres?». Acabas de entender tu primera frase."),
            Choice("gritar", "Gritar en tu idioma que te persigue un jaguar.", "s3_anciana", Effect(threat=5, trust=-5, learn=("tay_tikneki",)),
                   "Tus gritos no significan nada para él. La lanza avanza un palmo. Detrás, alguien le pone una mano en el hombro y repite despacio la pregunta: «tay tikneki», ¿qué quieres?"),
            Choice("manos", "Arrodillarte con las manos abiertas y en silencio.", "s3_anciana", Effect(trust=5, learn=("tay_tikneki",)),
                   "El gesto no necesita idioma. La lanza baja un poco. Una anciana se asoma por encima del hombro del guardia y repite su pregunta con suavidad: «tay tikneki», ¿qué quieres?"),
        ),
    ),
    Scene(
        id="s3_anciana", chapter_step=3, title=T_ALDEA, background="village_gate", ambient="village_gate", jaguar_visible=False,
        lines=(
            DialogueLine(NARRATOR, "La anciana lleva una antorcha. Te mira las manos vacías, el barro, la sangre del brazo."),
            DialogueLine(ELDER, "Yek tayua.", nahuat_id="yek_tayua"),
            DialogueLine(NARRATOR, "Lo dice con calma, inclinando la cabeza. Señala la luna y repite: «tayua». Luego espera tu respuesta."),
        ),
        choices=(
            Choice("yek_tayua", "Responder: «Yek tayua.»", "s3_nombre", Effect(trust=10), nahuat_id="yek_tayua",
                   feedback="La anciana sonríe. Has devuelto el saludo de la noche: «yek» es bueno, «tayua» es noche. El guardia relaja la lanza."),
            Choice("yek_tunal", "Responder: «Yek tunal.»", "s3_nombre", Effect(trust=3, learn=("yek_tayua",)), nahuat_id="yek_tunal",
                   feedback="La anciana ríe y niega con la cabeza. Señala la luna: «tayua», noche. «Tunal» es el día, el sol. Lo intentaste, y eso cuenta."),
            Choice("silencio", "Callar y bajar la mirada.", "s3_nombre", Effect(trust=-5, learn=("yek_tayua",)),
                   "La anciana espera. Al no responder, suspira y repite una vez más: «yek tayua». Buena noche. Ahora lo sabes."),
        ),
    ),
    Scene(
        id="s3_nombre", chapter_step=3, title=T_ALDEA, background="village_gate", ambient="village_gate", jaguar_visible=False,
        lines=(
            DialogueLine(ELDER, "Ken mutukay?", nahuat_id="ken_mutukay"),
            DialogueLine(NARRATOR, "Se toca el pecho y dice su propio nombre. Luego te señala a ti y levanta las cejas."),
        ),
        choices=(
            Choice("nombre", "Tocarte el pecho y decir: «Naja nutukay Yulu.»", "s3_tekwani", Effect(trust=10, learn=("ken_mutukay",)), nahuat_id="nutukay",
                   feedback="«Yulu», repite ella, y tu nombre suena distinto en su boca. Te ha preguntado cómo te llamas y le has respondido."),
            Choice("ninemi", "Decir: «Ninemi yek.»", "s3_nombre_otra_vez", Effect(learn=("ken_mutukay",)),
                   "La anciana ladea la cabeza. «Ken mutukay» pregunta tu nombre, no cómo estás. Vuelve a señalarte, paciente."),
            Choice("callar", "Señalarte a ti mismo sin hablar.", "s3_nombre_otra_vez", Effect(learn=("ken_mutukay",)),
                   "Ella repite despacio, sílaba a sílaba: «mu-tu-kay». Tu nombre. Quiere saber cómo te llamas."),
        ),
    ),
    Scene(
        id="s3_nombre_otra_vez", chapter_step=3, title=T_ALDEA, background="village_gate", ambient="village_gate", jaguar_visible=False,
        lines=(
            DialogueLine(ELDER, "Ken mutukay?", nahuat_id="ken_mutukay"),
            DialogueLine(NARRATOR, "Ahora sabes qué te pregunta. Para responder: «naja» es yo, «nutukay» es mi nombre."),
        ),
        choices=(
            Choice("nombre", "Decir: «Naja nutukay Yulu.»", "s3_tekwani", Effect(trust=5), nahuat_id="nutukay",
                   feedback="«Yulu», repite la anciana, y asiente. Segunda vez, pero lo has dicho bien."),
            Choice("huir", "Dar media vuelta hacia el bosque.", "s3_tekwani", Effect(threat=15, trust=-10),
                   "Das dos pasos y un rugido te detiene en seco. Vuelves corriendo a la puerta."),
        ),
    ),
    Scene(
        id="s3_tekwani", chapter_step=3, title=T_ALDEA, background="village_gate", ambient="village_gate",
        timer_seconds=12.0, timeout_choice="paralizarse",
        lines=(
            DialogueLine(NARRATOR, "Un rugido corto sale del bosque, muy cerca. El guardia levanta la antorcha y escruta la oscuridad."),
            DialogueLine(GUARD, "Tekwani!", nahuat_id="tekwani"),
            DialogueLine(NARRATOR, "Lo grita hacia dentro de la aldea mientras señala los ojos ámbar que brillan al borde del claro."),
        ),
        choices=(
            Choice("tekwani", "Señalar los ojos y gritar: «Tekwani!»", "s4_refugio", Effect(trust=10, flags=("aviso_jaguar",)), nahuat_id="tekwani",
                   feedback="El guardia te mira, luego al bosque, y por primera vez os miráis como aliados. «Tekwani»: el que come gente. El jaguar."),
            Choice("nimajmawi", "Decir: «Nimajmawi.»", "s4_refugio", Effect(trust=5, learn=("tekwani",)), nahuat_id="nimajmawi",
                   feedback="«Tengo miedo.» La anciana asiente: ella también. Te toma del brazo y te mete dentro. Al jaguar lo llaman «tekwani»."),
            Choice("correr", "Correr dentro de la aldea sin esperar permiso.", "s4_refugio", Effect(threat=5, trust=-10, learn=("tekwani",)),
                   "Empujas al guardia y entras. La anciana grita algo que no entiendes. Nadie te detiene, pero nadie te mira bien. Solo retienes una palabra: «tekwani»."),
            Choice("paralizarse", "Quedarte quieto.", "s4_refugio", Effect(threat=15, learn=("tekwani",)),
                   "El jaguar da un paso al claro. La anciana te agarra y tira de ti hacia dentro. El guardia cierra la puerta gritando «tekwani» una y otra vez."),
        ),
    ),
    # ---------------- ESCENA 4: LA CONFIANZA ----------------
    Scene(
        id="s4_refugio", chapter_step=4, title=T_CONFIANZA, background="shelter", ambient="shelter", jaguar_visible=False,
        lines=(
            DialogueLine(NARRATOR, "Una casa de caña y barro. Una hoguera baja. Varias personas te miran en silencio desde la sombra."),
            DialogueLine(ELDER, "Ken tinemi?", nahuat_id="ken_tinemi"),
            DialogueLine(NARRATOR, "Te ofrece sentarte junto al fuego. Suena a cortesía, pero todos esperan tu respuesta."),
        ),
        choices=(
            Choice("ninemi_yek", "Responder: «Ninemi yek.»", "s4_sed", Effect(trust=10, learn=("ken_tinemi",)), nahuat_id="ninemi_yek",
                   feedback="«Estoy bien». Varias cabezas asienten. Una mujer te acerca un paño para el brazo."),
            Choice("te", "Responder: «Te.»", "s4_sed", Effect(trust=5, learn=("ken_tinemi",)), nahuat_id="e_te",
                   feedback="«No». Es honesto: no estás bien. La anciana murmura algo y una mujer te limpia la herida."),
            Choice("tay", "Responder: «Tay tikneki?»", "s4_refugio_otra_vez", Effect(trust=-5, learn=("ken_tinemi",)),
                   "Le has preguntado «¿qué quieres?» a quien te acoge. Alguien ríe. La anciana, paciente, repite: «ken tinemi?», ¿cómo estás?"),
        ),
    ),
    Scene(
        id="s4_refugio_otra_vez", chapter_step=4, title=T_CONFIANZA, background="shelter", ambient="shelter", jaguar_visible=False,
        lines=(
            DialogueLine(ELDER, "Ken tinemi?", nahuat_id="ken_tinemi"),
            DialogueLine(NARRATOR, "Para decir «estoy bien»: «ninemi yek». Para decir que no: «te»."),
        ),
        choices=(
            Choice("ninemi_yek", "Responder: «Ninemi yek.»", "s4_sed", Effect(trust=5), nahuat_id="ninemi_yek",
                   feedback="«Estoy bien». La anciana asiente despacio. Aprendes rápido, dice su gesto."),
            Choice("te", "Responder: «Te.»", "s4_sed", Effect(trust=3), nahuat_id="e_te",
                   feedback="«No». Ella entiende. Una mujer se acerca con un paño."),
        ),
    ),
    Scene(
        id="s4_sed", chapter_step=4, title=T_CONFIANZA, background="shelter", ambient="shelter", jaguar_visible=False,
        lines=(
            DialogueLine(NARRATOR, "Un niño trae un cántaro de agua y se lo entrega a la anciana."),
            DialogueLine(CHILD, "Padiush.", nahuat_id="padiush"),
            DialogueLine(NARRATOR, "Ella le acaricia la cabeza. Luego sostiene el cántaro frente a ti y te mira."),
            DialogueLine(ELDER, "Tay tikneki?", nahuat_id="tay_tikneki"),
        ),
        choices=(
            Choice("e", "Señalar el cántaro y decir: «E.»", "s4_alarma", Effect(trust=5, learn=("padiush",)), nahuat_id="e_te",
                   feedback="«Sí». Te da el cántaro. El agua está fría y sabe a barro y a vida. Oyes de nuevo al niño: «padiush». Gracias."),
            Choice("padiush", "Tomar el agua y repetir la palabra del niño: «Padiush.»", "s4_alarma", Effect(trust=10), nahuat_id="padiush",
                   feedback="«Gracias». La anciana ríe con ganas y te aprieta el hombro. Has usado una palabra de la aldea para agradecer a la aldea."),
            Choice("pedir_mas", "Beber sin decir nada y pedir más con la mano.", "s4_alarma", Effect(trust=-5, learn=("padiush",)),
                   "Bebes. Nadie dice nada, pero el niño se aleja. Lo último que oyes de él es la palabra que repetía: «padiush»."),
        ),
    ),
    Scene(
        id="s4_alarma", chapter_step=4, title=T_CONFIANZA, background="shelter", ambient="shelter_alarm", jaguar_visible=False,
        timer_seconds=10.0, timeout_choice="paralizarse",
        lines=(
            DialogueLine(NARRATOR, "Un golpe seco contra la empalizada. Luego otro. Los perros enloquecen."),
            DialogueLine(GUARD, "Tekwani! Tekwani!", nahuat_id="tekwani"),
            DialogueLine(NARRATOR, "La anciana se levanta. Los hombres toman antorchas. El jaguar está dentro del claro."),
        ),
        choices=(
            Choice("shinechpalewi", "Gritar: «Shinechpalewi!»", "s4_fuego", Effect(trust=10, flags=("pidio_ayuda",)), nahuat_id="shinechpalewi",
                   feedback="«¡Ayúdame!» La anciana te pone una antorcha en la mano y te coloca entre dos hombres. Ya no eres un extraño: eres uno más en el círculo de fuego."),
            Choice("fuego", "Tomar una antorcha y ponerte junto a los hombres.", "s4_fuego", Effect(trust=10, threat=-10, flags=("pidio_ayuda",), learn=("shinechpalewi",)),
                   "No hacen falta palabras. El círculo de fuego avanza hacia la puerta y el jaguar retrocede entre gruñidos. Alguien grita «shinechpalewi» y dos hombres acuden: ayúdame."),
            Choice("esconderse", "Esconderte en el rincón más oscuro.", "s4_fuego", Effect(trust=-10, threat=5, learn=("shinechpalewi",)),
                   "Nadie te lo reprocha en voz alta. Oyes gritar «shinechpalewi», ¡ayúdame!, y no te mueves. Cuando el peligro pasa, nadie te busca con la mirada."),
            Choice("paralizarse", "Quedarte paralizado.", "s4_fuego", Effect(threat=15, learn=("shinechpalewi",)),
                   "El rugido entra por la rendija de la puerta. Alguien grita «shinechpalewi» y te empuja al suelo. El fuego hace el resto."),
        ),
    ),
    Scene(
        id="s4_fuego", chapter_step=4, title=T_CONFIANZA, background="village_fire", ambient="shelter", jaguar_visible=False,
        lines=(
            DialogueLine(NARRATOR, "El jaguar se retira a la selva. Las antorchas tiemblan. La anciana te mira largo rato y dice algo a los demás."),
            DialogueLine(NARRATOR, "No entiendes la discusión, pero entiendes las miradas. Deciden qué hacer contigo cuando amanezca."),
        ),
        choices=(
            Choice("padiush", "Mirar a todos y decir: «Padiush.»", "s5_decision", Effect(trust=5), nahuat_id="padiush",
                   feedback="«Gracias». La palabra cae en el silencio y lo ablanda un poco."),
            Choice("esperar", "Esperar en silencio junto al fuego.", "s5_decision", Effect(),
                   "El fuego crepita. Nadie habla. La noche se hace larga."),
        ),
    ),
    # ---------------- ESCENA 5: EL AMANECER ----------------
    Scene(
        id="s5_decision", chapter_step=5, title=T_AMANECER, background="village_fire", ambient="shelter", jaguar_visible=False,
        lines=(
            DialogueLine(NARRATOR, "El cielo cambia de negro a índigo. Los insectos callan uno a uno. La anciana se levanta y hace una señal."),
        ),
        branches=(
            Branch("s5_final_aldea", min_trust=TRUST_FOR_GOOD_ENDING, max_threat=THREAT_LIMIT_FOR_GOOD_ENDING),
            Branch("s5_final_solo"),
        ),
    ),
    Scene(
        id="s5_final_aldea", chapter_step=5, title=T_AMANECER, background="dawn", ambient="dawn", jaguar_visible=False,
        ending=GOOD_ENDING,
        lines=(
            DialogueLine(ELDER, "Yek tunal.", nahuat_id="yek_tunal"),
            DialogueLine(NARRATOR, "«Buen día». Ya no es de noche. La aldea te acompaña hasta el sendero con agua, tortillas y una antorcha apagada, por si vuelves a perderte."),
            DialogueLine(NARRATOR, "Al borde de la selva, entre la niebla dorada, el tekwani te observa una última vez. No te sigue."),
            DialogueLine(NARRATOR, "Has sobrevivido a la noche del jaguar. Y no lo hiciste solo: lo hiciste con palabras."),
        ),
    ),
    Scene(
        id="s5_final_solo", chapter_step=5, title=T_AMANECER, background="dawn", ambient="dawn", jaguar_visible=False,
        ending=BAD_ENDING,
        lines=(
            DialogueLine(NARRATOR, "Antes de que salga el sol, el guardia abre la puerta y señala el sendero. No hay rencor en su gesto, pero tampoco compañía."),
            DialogueLine(NARRATOR, "Caminas solo hacia la luz gris. Detrás, en la niebla, unas huellas grandes siguen las tuyas a la misma distancia de siempre."),
            DialogueLine(NARRATOR, "Has sobrevivido a la noche. Pero la aldea no confió en ti, y el jaguar lo sabe. Quizá la próxima vez entiendas mejor sus palabras."),
        ),
    ),
]

SCENES: dict[str, Scene] = {scene.id: scene for scene in _SCENES}
