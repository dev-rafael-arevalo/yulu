# Pruebas manuales de YULU: La noche del jaguar

Lista de comprobación para ejecutar en un equipo real con pantalla, altavoces, teclado y
ratón. Las pruebas automatizadas (`pytest`) cubren la lógica; estas cubren lo que solo una
persona puede juzgar. Marca cada fila con el resultado observado y la fecha. **No marques
como superada una prueba que no hayas ejecutado.**

Equipo: ____________________   Fecha: ____________   Versión (commit): ____________

## Arranque y pantalla

| # | Prueba | Cómo | Esperado | Resultado |
|---|---|---|---|---|
| 1 | Arranque a pantalla completa | `.venv\Scripts\python main.py` | Pantalla completa sin bordes, texto nítido, sin ventana colgada al salir | Éxito |
| 2 | Modo ventana | `main.py --windowed` | Ventana 1280×720 redimensionable con proporciones conservadas | Éxito |
| 3 | Alternar F11 | Pulsar F11 varias veces | Cambia entre pantalla completa y ventana sin cerrar el juego | Éxito |
| 4 | Cierre limpio | Esc → Salir del juego, y también cerrar con la X de la ventana | El proceso termina sin errores en consola | Éxito |

## Controles

| # | Prueba | Cómo | Esperado | Resultado |
|---|---|---|---|---|
| 5 | Avanzar diálogo | Enter, Espacio y clic | Primera pulsación completa el texto; segunda avanza | Éxito |
| 6 | Elegir con teclado | Flechas y Enter; números 1-4 | Selección visible; número elige directamente | Éxito |
| 7 | Elegir con ratón | Mover sobre las opciones y clic | La opción bajo el cursor se resalta y se confirma con clic | Éxito |
| 8 | Glosario | G durante un temporizador | Se abre el glosario y el temporizador se detiene; G o Esc lo cierran | Éxito |
| 9 | Repetir voz | V durante una línea | La narración de la línea actual vuelve a sonar | Éxito |
| 10 | Pausa | Esc | Menú con Continuar, cuatro volúmenes, Volver a empezar y Salir | Éxito |

## Audio

| # | Prueba | Cómo | Esperado | Resultado |
|---|---|---|---|---|
| 11 | Volúmenes independientes | En pausa, bajar Música a 0 % y subir Ambiente | Solo cambia la categoría ajustada; el valor persiste al reiniciar el juego | Éxito |
| 12 | Mezcla por escena | Recorrer escenas 1 a 5 | Bosque: insectos y viento; persecución: tambores que crecen con la amenaza; aldea: antorchas y murmullo; refugio: fogata con exterior amortiguado; amanecer: aves | Éxito |
| 13 | Jaguar | Subir la amenaza (gritar, correr) | Gruñidos ocasionales desde un lado, nunca continuos; rugido en subidas bruscas | Éxito |
| 14 | Atenuación por voz | Escuchar una línea narrada | La música baja mientras habla la voz y vuelve después | Éxito |
| 15 | Voces | Guardia, niño y protagonista frente a narradora y anciana | Voces masculina y femenina distintas; sin picos de volumen en palabras sueltas en náhuat | Éxito |
| 16 | Recurso ausente | Renombrar temporalmente `yulu/assets/audio/music/exploracion.mp3` y arrancar | El juego sigue; aparece una advertencia en consola; restaurar el archivo después | Éxito |

## Narrativa y aprendizaje

| # | Prueba | Cómo | Esperado | Resultado |
|---|---|---|---|---|
| 17 | Final con la aldea | Responder bien en náhuat en las escenas 3 y 4 | Resumen "El amanecer con la aldea", confianza ≥ 40 | Éxito |
| 18 | Final en soledad | Responder mal o callar; esconderse en la alarma | Resumen "El amanecer en soledad" | Éxito |
| 19 | Error que enseña | Responder «Ninemi yek» a «Ken mutukay?» | Explicación y segunda oportunidad; la expresión queda en el glosario | Éxito |
| 20 | Temporizador | Dejar agotar el tiempo en la persecución | Se aplica la opción por defecto y la amenaza sube | Éxito |
| 21 | Volver a jugar | R en un final | La partida reinicia desde el despertar con estado limpio | Éxito |

## Presentación

| # | Prueba | Cómo | Esperado | Resultado |
|---|---|---|---|---|
| 22 | Jaguar | Escenas de bosque con amenaza media y alta | Figura sólida, sin recuadro ni transparencia; ausente en aldea, refugio y finales | Éxito |
| 23 | Personajes | Líneas de anciana, guardia y niño | Retrato completo dentro de la pantalla, sin tapar el HUD ni el menú de decisiones | Éxito |
| 24 | Transiciones | Cambios de escena | Fundido a negro, sin parpadeos ni restos de la escena anterior | Éxito |
| 25 | Texto | Todas las cajas de diálogo | Sin cortes de palabras ni caracteres en forma de cuadro | Éxito |

## Incidencias encontradas

| Fecha | Prueba | Descripción | Estado |
|---|---|---|---|
| | | | |
