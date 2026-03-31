# My Singing Monsters Ice Age - Android Port

This is an Android-compatible version of the My Singing Monsters Ice Age game, originally written in Python using pygame.

## How to build the APK

The easiest way to build the APK is using GitHub Actions, which will automatically build the APK for you.

### Steps:

1. Create a new GitHub repository.
2. Push this entire folder (including the `.github/workflows/build.yml` file) to the repository.
3. The GitHub Actions workflow will automatically run and build the APK.
4. Once the build completes, download the APK artifact from the Actions page.

### Manual Build (requires Linux):

If you prefer to build locally on Linux, you can use Buildozer:

```bash
pip install buildozer
buildozer android debug
```

The APK will be generated in the `bin/` directory.

## Game Adaptations

The following changes were made to make the game compatible with Android:

- Removed Windows-specific mutex (now only runs on Windows).
- Updated save file path to use Android external storage when available.
- Set display mode to fullscreen automatically on Android.
- Added platform detection to adjust behavior accordingly.

## Notes

- The game still uses the original 800x600 resolution, which will be scaled to fit the device screen.
- Touch input is translated to mouse events by pygame.
- The game uses procedural graphics and sounds, so no external assets are needed.

## Troubleshooting

If the APK crashes on launch:

- Check that you have the correct `requirements` in `buildozer.spec` (currently just `pygame`).
- Ensure your Android device has at least API level 21.
- Try building with a different Python version (3.9 is recommended).