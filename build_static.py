from __future__ import annotations

import os
import shutil
from pathlib import Path

# Let the views know we are producing a static preview (turns off pagination).
os.environ.setdefault("STATIC_BUILD", "1")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django

django.setup()

from django.conf import settings
from django.test import Client
from django.urls import reverse

from adocoes.models import Pet

OUTPUT_DIR = Path("netlify_dist")


def copy_media() -> None:
    media_root = Path(settings.MEDIA_ROOT)
    dest = OUTPUT_DIR / "media"
    if media_root.exists():
        shutil.copytree(media_root, dest, dirs_exist_ok=True)


def save_response(response, destination: Path, url: str) -> None:
    if response.status_code != 200:
        raise RuntimeError(f"Failed to render {url}: status {response.status_code}")
    response.render()  # Ensure TemplateResponse is processed
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(response.content)


def main() -> None:
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    client = Client()
    session = client.session
    session["is_visitor"] = True
    session.save()
    client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key

    save_response(client.get(reverse("landing")), OUTPUT_DIR / "index.html", "/")
    save_response(
        client.get(reverse("galeria_pets")), OUTPUT_DIR / "galeria" / "index.html", "/galeria/"
    )

    for pet in Pet.objects.all():
        dest = OUTPUT_DIR / "pet" / pet.slug / "index.html"
        save_response(client.get(pet.get_absolute_url()), dest, pet.get_absolute_url())

    copy_media()
    print(f"Static site generated at: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
