# En Busca del Salmón Perdido — Arcade

Juego de lucha estilo *Street Fighter* con los 9 personajes de la película
**En Busca del Salmón Perdido**. Todo en un único archivo HTML: se dibuja en un
`<canvas>`, el audio se genera con la Web Audio API y no hay dependencias ni
proceso de compilación.

## Cómo ejecutarlo

Abre `index.html` en cualquier navegador moderno (doble clic).

```bash
# opcional, para servirlo por HTTP
python -m http.server
# luego abre http://localhost:8000
```

> Necesita teclado: en móvil solo muestra un aviso.

## Modos

- **1 jugador** contra la CPU.
- **2 jugadores** en el mismo teclado.
- Selección en rejilla 3×3, al mejor de 3 asaltos, con medidor de súper.

## Controles

| Acción | Jugador 1 | Jugador 2 |
|---|---|---|
| Mover | `A` / `D` | `←` / `→` |
| Saltar | `W` | `↑` |
| Agacharse | `S` | `↓` |
| Golpe | `F` | `1` |
| Patada | `G` | `2` |
| Bloquear (alto y bajo) | `V` | `3` |
| Especial | `B` | `4` |

Globales: `Enter` confirmar · `M` silenciar · `P` pausa · `R` reiniciar combate.

## Personajes y especiales

El especial se activa con el medidor ★ lleno (se carga peleando).

| Personaje | Especial | Tipo |
|---|---|---|
| Michiloco | Capa Fantasma | embestida con invencibilidad |
| Lupita | Orbe de Salmón | proyectil |
| Bruce | Latigazo de Cuerda | agarre a distancia que atrae |
| Kai | Danza de Katanas | embestida multigolpe |
| Atlas | Llave del Laberinto | agarre imbloqueable (lento, aguanta más) |
| Nocturna | Ilusión Lunar | proyectil creciente |
| Viper | Mordisco Rápido | embestida baja |
| Maestro Yubari | Contra del Sensei | parry con contragolpe |
| Ratín | Campanilla Cegadora | dash veloz con invencibilidad |

## Escenarios

Dojo · Laberinto submarino · Palacio lunar · Templo en la jungla · Mercado.

## Estructura

- `index.html` — todo el juego (HTML, CSS y JavaScript).

Los luchadores se dibujan de forma procedural (figuras en canvas) respetando los
colores y rasgos de cada hoja de personaje. Para usar sprites reales, se pueden
añadir PNG en una carpeta `assets/` y conectarlos en el código.
