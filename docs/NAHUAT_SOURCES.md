# Fuentes lingüísticas del náhuat usado en YULU

Este documento registra de dónde procede cada expresión del juego y su estado de
validación. El vocabulario completo, con fuente y localizador por entrada, está en
[`yulu/language/data/nahuat_ch1.json`](../yulu/language/data/nahuat_ch1.json).

## Fuentes consultadas (18 de octubre de 2026)

| Clave | Referencia | Cómo se consultó |
|---|---|---|
| KING2011 | King, Alan R. (2011). *Timumachtikan! Curso de lengua náhuat para principiantes adultos*. 170 pp. © Alan R. King. | PDF descargado de `tushik.org/timumachtikan/`. Lecciones 1 a 4 (pp. 19-28). |
| CAMPBELL1985 | Campbell, Lyle (1985). *The Pipil Language of El Salvador*. Mouton Grammar Library 1. Traducción al español de Mauricio Mixco: *El idioma pipil (nahuate) de El Salvador*. | PDF alojado en `tushik.org` (CAM-nahuate.pdf). Búsquedas en diccionario y morfología verbal. |
| HERNANDEZ2016 | Hernández González, Werner (2016). *Nawat Mujmusta*. Diccionario. © Werner Hernández G. | PDF alojado en `tushik.org` (HER-mujmusta.pdf). Entradas individuales. |
| KING2014 | King, Alan R. (2014). *On-line Nawat (Ne Nawat Matapan)*. Léxico para sitios web y aplicaciones. | PDF alojado en `tushik.org` (matapan.pdf). Confirmación de usos como `shikalaki`, `nemi yek`, `ken mutukay`. |

Todas las obras son material con derechos reservados. El juego **no reproduce sus textos**:
toma únicamente palabras y frases cortas con su traducción, citando la fuente, como haría
cualquier glosario escolar.

## Ortografía

Se usa la ortografía práctica de King y Tushik (`sh`, `j`, `w`, `k`, `tz`, cuatro vocales
`a e i u`). Campbell escribe con `x` para el sonido *sh* y marca vocales largas con `:`;
sus formas se transcriben a la ortografía práctica (por ejemplo `xi-nech-pale:wi` →
`shinechpalewi`, `te:kwani` → `tekwani`).

## Estados de validación

- **verificada**: la forma y su traducción aparecen tal cual en al menos una fuente.
- **compuesta**: frase construida con piezas atestiguadas y una regla gramatical explícita de
  las fuentes (por ejemplo `ni-` + `majmawi` = `nimajmawi`). La frase completa no se encontró
  literalmente. El glosario del juego lo indica.
- **provisional**: no verificada. El juego no usa expresiones con este estado.

## Resumen de las 12 expresiones del capítulo 1

| Id | Náhuat | Español | Estado | Fuente principal |
|---|---|---|---|---|
| yek_tunal | Yek tunal! | ¡Buen día! | verificada | KING2011 p. 19 |
| yek_tayua | Yek tayua! | ¡Buena noche! | verificada | KING2011 p. 19 |
| ken_tinemi | Ken tinemi? | ¿Cómo estás? | verificada | KING2011 p. 19 |
| ninemi_yek | Ninemi yek. | Estoy bien. | verificada | KING2011 p. 20 |
| ken_mutukay | Ken mutukay? | ¿Cómo te llamas? | verificada | KING2011 p. 21 |
| nutukay | Naja nutukay Yulu. | Yo me llamo Yulu. | verificada | KING2011 p. 21 |
| e_te | E. / Te. | Sí. / No. | verificada | KING2011 pp. 24-25 |
| tay_tikneki | Tay tikneki? | ¿Qué quieres? | verificada | KING2011 p. 27 |
| padiush | Padiush. | Gracias. | verificada (una fuente, marca NW) | HERNANDEZ2016 |
| tekwani | Tekwani! | ¡Jaguar! | verificada | CAMPBELL1985 (te:kwani) |
| shinechpalewi | Shinechpalewi! | ¡Ayúdame! | verificada | CAMPBELL1985 (xi-nech-pale:wi) |
| nimajmawi | Nimajmawi. | Tengo miedo. | compuesta | HERNANDEZ2016 + KING2011 (ni-) |

## Guía de pronunciación

Solo se incluye pronunciación cuando las reglas generales de King (2011, pp. 20, 22 y 26)
la respaldan: acento en la penúltima sílaba, `sh` como en inglés, `j` como la j salvadoreña,
`w` como *hu*, `tz` como *ts*. Para `Padiush` no se indica acento porque la fuente no lo da.

## Limitaciones declaradas

- No existe en este proyecto ninguna grabación de hablantes nativos de náhuat. La narración
  sintética, si se activa, usa una voz en español y **no** representa la pronunciación nativa.
- El náhuat salvadoreño tiene variación dialectal (Santo Domingo de Guzmán, Cuisnahuat,
  Nahuizalco, Teotepeque…). El juego no afirma pertenecer a una variante concreta.
- Las frases en boca de los personajes se limitan a las expresiones de esta lista. El resto
  del diálogo de la aldea se presenta en español como "lo que el protagonista entiende".
