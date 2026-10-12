"""Optional mixer support: missing devices or files never stop the game."""

from pathlib import Path
import pygame


class AudioManager:
    """Load original WAV assets and manage independent music/SFX toggles."""

    def __init__(self, assets=None):
        self.assets = Path(assets) if assets else Path(__file__).resolve().parents[1] / "assets"
        self.music_enabled = True
        self.sfx_enabled = True
        self.available = False
        self.music_loaded = False
        self.sounds = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050)
            self.available = True
            for name in ("click", "correct", "wrong"):
                path = self.assets / "sounds" / f"{name}.wav"
                if path.exists():
                    try:
                        sound = pygame.mixer.Sound(str(path))
                        sound.set_volume(0.5)
                        self.sounds[name] = sound
                    except (pygame.error, OSError):
                        pass
            music = self.assets / "music" / "background.wav"
            if music.exists():
                pygame.mixer.music.load(str(music))
                pygame.mixer.music.set_volume(0.3)
                pygame.mixer.music.play(-1)
                self.music_loaded = True
        except (pygame.error, OSError):
            # Video and gameplay still work without usable audio.
            pass

    def play(self, name):
        """Play a loaded cue only if sound effects are enabled."""
        if self.available and self.sfx_enabled and name in self.sounds:
            try:
                self.sounds[name].play()
            except pygame.error:
                pass

    def toggle_music(self):
        """Pause/resume the loop without changing its playback position."""
        self.music_enabled = not self.music_enabled
        if self.music_loaded:
            try:
                if self.music_enabled:
                    pygame.mixer.music.unpause()
                else:
                    pygame.mixer.music.pause()
            except pygame.error:
                pass

    def toggle_sfx(self):
        """Mute/unmute effects and stop currently playing cues when muted."""
        self.sfx_enabled = not self.sfx_enabled
        if self.available and not self.sfx_enabled:
            try:
                pygame.mixer.stop()
            except pygame.error:
                pass
