# Follow Cam

A [RuneLite](https://runelite.net) plugin that automatically rotates the camera to face the direction your character is moving.

## What it does

When you walk or run, the camera yaw smoothly follows your character's facing direction. Turn north — the camera faces north. Turn east — the camera swings east. Because OSRS characters snap between 8 discrete directions (N, NE, E, SE, S, SW, W, NW), the smooth interpolation removes any jarring jumps between angles.

Disabling the plugin instantly returns full manual camera control.

## Configuration

| Option | Values | Default | Description |
|---|---|---|---|
| Smoothing Speed | Instant, Fast, Medium, Slow | Medium | How quickly the camera rotates to match the player's direction |

## Installation

Available on the [RuneLite Plugin Hub](https://runelite.net/plugin-hub). Search for **Follow Cam** in the Plugin Hub tab inside RuneLite.

## Building locally

Requires JDK 11+.

```
./gradlew build
```

## License

BSD 2-Clause — see [LICENSE](LICENSE).
