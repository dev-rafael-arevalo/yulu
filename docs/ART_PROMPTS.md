# Prompts de generación de imágenes para YULU

El juego carga los fondos desde `yulu/assets/images/` según `yulu/assets/manifest.json`.
Mientras un archivo no exista, se muestra un escenario procedural marcado como
**PROVISIONAL**. Comprueba el estado con:

```powershell
.venv\Scripts\python tools\check_assets.py
```

## Especificación común a todas las imágenes

- **Formato**: PNG, 1920 × 1080 (16:9). El juego las ajusta a pantalla recortando los bordes,
  así que deja los elementos importantes dentro del 90 % central.
- **Sin texto, sin letras, sin logotipos, sin marcas de agua, sin personas con rostros reconocibles.**
- **Zona inferior libre**: el tercio inferior (desde el 65 % de la altura) aloja la caja de diálogo.
  Coloca ahí suelo, raíces o niebla, nunca el punto de interés.
- **Luz coherente**: luna arriba a la derecha, luz fría azul-verdosa; antorchas y fogatas como
  única luz cálida ámbar-naranja. Negros profundos con detalle en sombras, nada de cielo gris.
- **Estilo**: fotorrealismo cinematográfico de videojuego de suspense moderno, lente 35 mm,
  niebla volumétrica, humedad en hojas, grano de película sutil. Paleta: azul noche, verde
  profundo, ámbar, fuego.
- **Contexto cultural**: paisaje tropical de Centroamérica (ceibas, helechos, bromelias, plátano
  silvestre, bambú). Arquitectura con materiales naturales (madera, palma, bajareque, piedra).
  No incluir ruinas monumentales ni iconografía de otras culturas.
- **Licencia**: genera las imágenes tú mismo con una herramienta cuyo uso de salida te esté
  permitido (por ejemplo ChatGPT ImageGen) y anota la herramienta y la fecha en
  `yulu/assets/images/CREDITS.md`. No uses imágenes descargadas sin licencia comprobada.

Añade al final de cada prompt: `no text, no watermark, no people, 16:9, 1920x1080`.

## Fondos

### 1. `bg_01_forest_awakening.png` — El despertar (`forest_dense`)
> Vista a ras de suelo dentro de una selva tropical centroamericana de noche. Primer plano con
> raíces húmedas, hojas muertas y helechos mojados. Troncos enormes de ceiba con raíces
> tabulares se pierden en una niebla espesa. Luz de luna fría, azul verdosa, filtrándose en haces
> volumétricos entre el dosel. Sombras muy profundas, atmósfera opresiva de desorientación.
> Sin ningún animal visible. Composición abierta en el centro para que los ojos del jaguar se
> añadan después por software.

### 2. `bg_02_forest_chase.png` — La persecución (`forest_path`)
> Sendero estrecho de tierra pisada que baja por una pendiente entre vegetación tropical densa,
> visto desde la altura de los ojos de alguien que corre. Ligero desenfoque de movimiento en los
> bordes del encuadre. A la izquierda, una ceiba gigantesca; a la derecha, el reflejo de un río
> negro entre los árboles. Luz de luna más intensa, niebla baja arrastrándose por el suelo, gotas
> de lluvia reciente. Sensación de urgencia y peligro. Sin animales ni personas.

### 3. `bg_03_path_to_village.png` — Sendero hacia la aldea (`village_edge`)
> Linde de la selva de noche. El bosque se abre a un claro y al fondo, a unos cien metros, una
> empalizada de troncos con antorchas encendidas en lo alto, cuyo resplandor naranja tiñe la
> niebla. Techos de palma asoman tras la empalizada. Sendero con huellas en barro que conduce
> hacia la luz. Contraste entre la selva fría azul del primer plano y la luz cálida lejana.
> Humo de antorchas elevándose. Sin personas visibles.

### 4. `bg_04_village_gate_torches.png` — La entrada de la aldea (`village_gate`)
> Puerta de una empalizada de troncos afilados, vista de frente a corta distancia, de noche.
> Dos antorchas de madera con resina arden a ambos lados y proyectan sombras duras y
> parpadeantes. Humo denso. Tras la puerta entreabierta se intuyen casas de bajareque con techo
> de palma y una hoguera. Suelo de tierra húmeda con huellas. Materiales naturales creíbles:
> fibras, lianas atando los troncos, madera envejecida. Sin personas ni rostros.

### 5. `bg_05_shelter_interior.png` — Interior del refugio (`shelter`)
> Interior de una casa tradicional de bajareque y techo de palma, de noche. Una hoguera baja en
> el centro ilumina paredes de caña y barro, vigas de madera, petates tejidos, cántaros de
> cerámica sin decorar, mazorcas colgadas. Humo subiendo hacia el techo. Luz cálida ámbar con
> sombras profundas en las esquinas; por una rendija de la puerta entra un filo de luz azul de
> luna. Atmósfera de refugio frágil. Sin personas visibles.

### 6. `bg_06_dawn_clearing.png` — El amanecer (`dawn`)
> El mismo linde de selva del fondo 3, pero en el primer minuto del amanecer: cielo índigo que
> pasa a naranja pálido sobre las copas, niebla dorada en el claro, rocío en las hojas, las
> antorchas de la empalizada ya casi apagadas. Sensación de alivio contenido. Un sendero se
> aleja hacia las montañas azuladas del fondo. Sin personas ni animales.

## Jaguar (PNG con fondo transparente)

Especificación: PNG con canal alfa, 1600 px de ancho aproximado, jaguar (*Panthera onca*)
adulto con anatomía realista, pelaje con rosetas, iluminación lunar fría desde arriba a la
derecha y leve reflejo ámbar en los ojos. Vista desde la altura de un humano.

### 7. `jaguar_eyes_glow.png`
> Solo la cabeza de un jaguar entre helechos oscuros, casi completamente en sombra; únicamente
> se perciben los dos ojos reflejando luz con brillo ámbar-dorado y el contorno húmedo del hocico.
> El resto de la imagen debe ser transparente.

### 8. `jaguar_stalking.png`
> Jaguar completo agachado en postura de acecho, cuerpo bajo, hombros marcados, cola
> extendida, mirando directamente al espectador. Tres cuartos de perfil, avanzando desde la
> izquierda. Pelaje detallado, parcialmente velado por niebla en las patas. Fondo transparente.

### 9. `jaguar_charging.png`
> Jaguar en pleno salto hacia la cámara, boca abierta, garras extendidas, pelaje con gotas de
> agua, ligero desenfoque de movimiento en las patas traseras. Fondo transparente.

## Capas de efectos (PNG con alfa)

### 10. `fx_fog_layer_01.png` y `fx_fog_layer_02.png`
> Capa de niebla volumétrica blanca-grisácea, suave, sin bordes definidos, que **pueda repetirse
> horizontalmente sin costuras** (tileable en X). 2048 × 1080. Densidad distinta en cada capa:
> la 01 ligera, la 02 más densa en la mitad inferior. Fondo transparente.

### 11. `fx_torch_smoke.png`
> Columna de humo de antorcha gris cálido, ascendente, difusa, sobre fondo transparente,
> 512 × 1024, pensada para superponerse con mezcla normal sobre las antorchas.

## Qué hace el código con cada recurso

| Recurso | Uso en el juego |
|---|---|
| Fondos | Ajuste "cover" a 16:9, deriva lenta de cámara (1 a 6 % de zoom), viñeta, tinte por amenaza y calidez según `manifest.json`. |
| `jaguar_eyes_glow` | Amenaza baja: opacidad y tamaño crecen con la amenaza. |
| `jaguar_stalking` | Amenaza media y alta: aparece desde la izquierda con balanceo lento. |
| `jaguar_charging` | Ataques y final malo (FASE 4). |
| Niebla | Dos capas en paralaje a velocidades distintas; la intensidad la fija `manifest.json`. |
| Humo | Sobre cada antorcha declarada, con deriva vertical. |
