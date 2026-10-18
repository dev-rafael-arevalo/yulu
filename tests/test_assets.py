"""Los recursos gráficos ausentes no deben interrumpir la partida."""
from __future__ import annotations

import os

import pygame
import pytest

from yulu.ui.assets import ImageStore, cover_fit, load_manifest


@pytest.fixture(scope="module", autouse=True)
def headless_pygame():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    pygame.display.set_mode((64, 64))
    yield
    pygame.quit()


def test_manifest_declares_required_backgrounds():
    manifest = load_manifest()
    required = {"forest_dense", "forest_path", "village_edge", "village_gate", "shelter", "dawn"}
    assert required <= set(manifest["backgrounds"])


def test_missing_images_return_none_without_raising(tmp_path):
    store = ImageStore(images_dir=tmp_path)
    assert store.background("forest_dense") is None
    assert store.jaguar("stalk") is None
    assert store.fog_layers() == []
    assert store.smoke() is None
    assert len(store.missing_files()) == len(store.expected_files())


def test_corrupt_image_is_tolerated(tmp_path):
    (tmp_path / "bg_01_forest_awakening.png").write_bytes(b"no soy un png")
    store = ImageStore(images_dir=tmp_path)
    assert store.background("forest_dense") is None


def test_present_image_is_cover_fitted(tmp_path):
    image = pygame.Surface((400, 300))  # 4:3, debe recortarse a 16:9
    pygame.image.save(image, str(tmp_path / "bg_01_forest_awakening.png"))
    store = ImageStore(images_dir=tmp_path)
    surface = store.background("forest_dense", overscan=1.0)
    assert surface is not None
    assert surface.get_size() == (1280, 720)


def test_cover_fit_keeps_aspect_and_overscan():
    wide = pygame.Surface((3840, 1600))
    result = cover_fit(wide, overscan=1.06)
    assert result.get_size() == (round(1280 * 1.06), round(720 * 1.06))


def test_background_falls_back_to_placeholder(tmp_path):
    from yulu.ui.background import Background

    background = Background("village_gate", ImageStore(images_dir=tmp_path))
    assert background.is_provisional
    surface = pygame.Surface((1280, 720))
    background.update(0.016)
    background.draw(surface, 0.0)  # no debe lanzar
