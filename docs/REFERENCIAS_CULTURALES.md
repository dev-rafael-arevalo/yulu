# Referencias culturales y vestuario en YULU

Este documento registra con qué criterio se eligió la apariencia de los personajes, qué
imágenes se usan en el juego, qué se descartó y qué **no** se afirma. Toda la imaginería es
**interpretación artística generada por IA** a partir de prompts; no es una reconstrucción
arqueológica ni etnográfica certificada.

## Qué muestra el juego y por qué

| Recurso | Uso | Criterio |
|---|---|---|
| `characters/portrait_anciana_integrado.png` | Retrato de la anciana cuando habla (viñeta con bordes desvanecidos, imagen íntegra) | Túnica de algodón claro con cenefas tejidas, manta o rebozo, collares de cuentas y orejeras de disco: elementos plausibles en Mesoamérica con fibras naturales, sin símbolos inventados presentados como históricos. |
| `characters/portrait_guardia_integrado.png` | Retrato del guardia cuando habla | Banda tejida en la cabeza, manta anudada al hombro, faja, lanza de madera con punta lítica y escudo circular de madera y fibra. **Sustituye** al recorte anterior, que llevaba un tocado con aspecto de casco europeo. |
| `bg_07_jaguar_encounter.png` | Fondo de la persecución y del momento de parálisis | Jaguar íntegro en su entorno, sin recorte ni transparencia. En el resto de escenas donde acecha fuera de plano solo se dibujan dos ojos ámbar por código; los recortes del jaguar se eliminaron. |
| `bg_09_forest_moonlight.png`, `bg_10_forest_path.png` | Bosque del despertar y sendero de la huida | Imágenes íntegras a resolución completa del paquete de imágenes sólidas. |
| `bg_08_village_fire.png` | Fondo de la deliberación tras la alarma y del amanecer previo a la decisión | Pobladores de la misma comunidad con vestuario coherente (algodón claro, cenefas rojas, collares), casas de palma y empalizada. |
| `characters/npc_nino.png`, `group_familia.png`, `group_fogata.png` | Niño al hablar; grupos en el refugio | Vestuario coherente con los retratos integrados. |
| `reference/concepto_cultural_*.png` | Solo referencia; no se muestran en el juego | Hojas de concepto del paquete de referencias. |

## Qué se retiró

- `group_guardia_anciano.png` (un guardia con tocado rígido tipo casco) ya no aparece en
  ninguna escena. El archivo se conserva por si se regenera sin ese elemento.
- Los penachos grandes de plumas de algunas hojas de concepto no se usan en recursos finales.

## Pueblos y tradiciones a los que alude la historia

La aldea de YULU es **ficticia** y habla náhuat, lengua de los pipiles, pueblo nahua que
habitó el occidente y centro del actual El Salvador antes y después de la conquista. El
guion no identifica la aldea con pocomames (pueblo maya del oriente de Guatemala y zonas de
El Salvador) ni con los toltecas del centro de México, y el arte **no los mezcla a propósito**:
una sola comunidad, un solo registro de vestuario. Si en el futuro la historia incorpora otro
pueblo, deberá distinguirse visualmente y declararse como decisión narrativa.

## Fuentes consultadas para orientar el criterio (no para certificar detalles)

- Fowler, William R. (1989). *The Cultural Evolution of Ancient Nahua Civilizations: The
  Pipil-Nicarao of Central America*. Norman: University of Oklahoma Press. Síntesis
  arqueológica y etnohistórica de los pipiles; útil para el marco general (asentamientos,
  economía del algodón y el cacao, organización social).
- Campbell, Lyle (1985). *The Pipil Language of El Salvador*. Berlin: Mouton. Fuente de la
  lengua; su diccionario documenta términos materiales (por ejemplo, voces para algodón,
  manta, casa) que apoyan la presencia de tejidos de algodón y casas de materiales vegetales.
- Hojas de referencia del estudiante (ChatGPT ImageGen, 18/10/2026), paquete
  `YULU_referencias_culturales_para_claude_code.zip`, y sus instrucciones de vestuario.

**Incertidumbres declaradas**: no se han verificado en fuentes primarias los diseños
concretos de las cenefas, la forma exacta de las orejeras, el tipo de escudo ni los colores
de los tintes. Se presentan como plausibles, no como documentados. Antes de usar el juego
como material didáctico de historia material, conviene revisarlo con especialistas.
