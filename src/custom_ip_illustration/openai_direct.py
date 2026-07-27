from __future__ import annotations

import base64
import binascii
import json
import os
import secrets
import stat
import struct
import zlib
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
from uuid import uuid4

from .errors import (
    CredentialError,
    RenderError,
    UnsupportedPlatformError,
    ValidationError,
)


API_URL = "https://api.openai.com/v1/images"
MODEL = "gpt-image-2"
CANVAS_DIMENSIONS = {
    "16:9": (1536, 864),
    "1:1": (1024, 1024),
    "9:16": (1152, 2048),
}
MIN_PIXELS = 655_360
MAX_PIXELS = 8_294_400
MAX_EDGE = 3_840
MAX_ASPECT_RATIO = 3
MAX_REFERENCES = 4
MAX_REFERENCE_BYTES = 20 * 1024 * 1024
MAX_TOTAL_REFERENCE_BYTES = 50 * 1024 * 1024
MAX_PROJECT_TEXT_BYTES = 5 * 1024 * 1024
SKILL_ROOT = Path(__file__).resolve().parents[2]
CHARACTER_MASTER_PROMPT = (
    "Create an original cartoon character turnaround sheet from this user-owned "
    "or authorized reference photo. Preserve only non-sensitive visual anchors "
    "such as hairstyle, face shape, and glasses when present. Do not infer, label, "
    "or exaggerate sensitive attributes. Show the character full-body with front, "
    "side, and back views plus common facial expressions on a clean neutral "
    "background. Include no text, watermark, logo, third-party character traits, "
    "or copied franchise styling."
)
Transport = Callable[[str, str, dict[str, str], bytes], dict[str, Any]]
_OPEN_SUPPORTS_DIR_FD = os.open in os.supports_dir_fd
_LINK_SUPPORTS_DIR_FD = os.link in os.supports_dir_fd
_RENAME_SUPPORTS_DIR_FD = os.rename in os.supports_dir_fd
_UNLINK_SUPPORTS_DIR_FD = os.unlink in os.supports_dir_fd


def _user_config_path() -> Path:
    return Path.home() / ".custom-ip-illustration" / ".env"


def _valid_key(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip() or "\n" in value or "\r" in value:
        return None
    return value


def load_api_key(
    *,
    env: Mapping[str, str] | None = None,
    config_path: Path | None = None,
) -> str | None:
    """Load an API key from an explicit environment mapping or user config only."""
    environment = os.environ if env is None else env
    key = _valid_key(environment.get("OPENAI_API_KEY"))
    if key is not None:
        return key

    path = config_path or _user_config_path()
    try:
        contents = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    for line in contents.splitlines():
        if line.startswith("OPENAI_API_KEY="):
            return _valid_key(line[len("OPENAI_API_KEY=") :])
    return None


def write_user_api_key(path: Path, api_key: str) -> Path:
    """Atomically write a single private user-level OpenAI configuration entry."""
    key = _valid_key(api_key)
    if key is None:
        raise CredentialError("API key must be a non-empty single-line value")
    if not _secure_config_supported():
        raise CredentialError("secure credential writes are unavailable on this platform")

    parent = path.parent
    parent_fd = -1
    file_fd = -1
    temporary = f".{path.name}.{secrets.token_hex(16)}.tmp"
    try:
        try:
            details = os.lstat(parent)
        except FileNotFoundError:
            os.mkdir(parent, mode=0o700)
            details = os.lstat(parent)
        if stat.S_ISLNK(details.st_mode) or not stat.S_ISDIR(details.st_mode):
            raise CredentialError("credential configuration parent must be a real directory")

        directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        parent_fd = os.open(parent, directory_flags)
        anchored = os.fstat(parent_fd)
        os.fchmod(parent_fd, 0o700)
        file_fd = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=parent_fd,
        )
        _write_all(file_fd, f"OPENAI_API_KEY={key}\n".encode("utf-8"))
        os.fsync(file_fd)
        os.fchmod(file_fd, 0o600)
        os.close(file_fd)
        file_fd = -1

        current = os.lstat(parent)
        if (
            stat.S_ISLNK(current.st_mode)
            or not stat.S_ISDIR(current.st_mode)
            or (current.st_dev, current.st_ino) != (anchored.st_dev, anchored.st_ino)
        ):
            raise CredentialError("credential configuration directory changed during write")
        os.rename(
            temporary,
            path.name,
            src_dir_fd=parent_fd,
            dst_dir_fd=parent_fd,
        )
    except CredentialError:
        raise
    except OSError as exc:
        raise CredentialError("unable to save API key configuration") from exc
    finally:
        if file_fd != -1:
            os.close(file_fd)
        if parent_fd != -1:
            try:
                os.unlink(temporary, dir_fd=parent_fd)
            except FileNotFoundError:
                pass
            os.close(parent_fd)
    return path


def doctor(
    *,
    env: Mapping[str, str] | None = None,
    config_path: Path | None = None,
) -> dict[str, str]:
    """Report credential readiness without exposing configuration details."""
    if not _secure_output_supported():
        return {"status": "unsupported_platform"}
    try:
        available = load_api_key(env=env, config_path=config_path)
    except (OSError, UnicodeError):
        available = None
    status = "ready" if available else "missing_credentials"
    return {"status": status}


def _write_all(fd: int, data: bytes) -> None:
    offset = 0
    while offset < len(data):
        written = os.write(fd, data[offset:])
        if written <= 0:
            raise OSError("short write")
        offset += written


def _safe_relative_path(value: object, *, field: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ValidationError(f"{field} must be a non-empty relative path")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValidationError(f"{field} must stay inside the request directory")
    return path


def _resolve_within(root: Path, relative: Path, *, field: str) -> Path:
    resolved_root = root.resolve()
    resolved_path = (resolved_root / relative).resolve(strict=False)
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise ValidationError(f"{field} must stay inside the request directory") from exc
    return resolved_path


def _load_render_request(contents: bytes) -> dict[str, Any]:
    try:
        data = json.loads(contents.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValidationError("render request is not valid JSON") from exc
    if not isinstance(data, dict) or data.get("schema") != "render-request/v1":
        raise ValidationError("render request has an unsupported schema")
    images = data.get("images")
    if not isinstance(images, list) or not images:
        raise ValidationError("render request must include images")
    return data


def _http_transport(
    url: str,
    method: str,
    headers: dict[str, str],
    body: bytes,
) -> dict[str, Any]:
    request = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=120) as response:
            return {"status": response.status, "body": response.read()}
    except HTTPError as exc:
        return {"status": exc.code, "body": exc.read()}
    except URLError as exc:
        raise RenderError("image service is unreachable") from exc


def _safe_filename(value: str) -> str:
    filename = "".join(
        character if character.isascii() and (character.isalnum() or character in ".-_") else "_"
        for character in value
    ).strip(".")
    return filename or "reference"


def _reference_mime(contents: bytes) -> str:
    if contents.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if contents.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if len(contents) >= 12 and contents.startswith(b"RIFF") and contents[8:12] == b"WEBP":
        return "image/webp"
    raise ValidationError("authorized reference image has an unsupported format")


def _multipart(
    fields: dict[str, str],
    references: list[tuple[str, str, bytes]],
) -> tuple[str, bytes]:
    boundary = f"----custom-ip-illustration-{uuid4().hex}"
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
                value.encode("utf-8"),
                b"\r\n",
            ]
        )
    for filename, mime, contents in references:
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                (
                    'Content-Disposition: form-data; name="image[]"; '
                    f'filename="{filename}"; filename*=UTF-8\'\'{quote(filename, safe="")}\r\n'
                ).encode(),
                f"Content-Type: {mime}\r\n\r\n".encode(),
                contents,
                b"\r\n",
            ]
        )
    chunks.append(f"--{boundary}--\r\n".encode())
    return boundary, b"".join(chunks)


def _error_classification(status: int) -> str:
    if status == 401:
        return "authentication"
    if status == 403:
        return "authorization"
    if status == 429:
        return "rate_limited"
    if 500 <= status <= 599:
        return "server_error"
    return "request_failed"


def _decode_image(body: object) -> bytes:
    if not isinstance(body, bytes):
        raise RenderError("image service returned an invalid response")
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RenderError("image service returned an invalid response") from exc
    if not isinstance(payload, dict):
        raise RenderError("image service returned an invalid response")
    data = payload.get("data")
    if not isinstance(data, list) or not data or not isinstance(data[0], dict):
        raise RenderError("image service returned an invalid response")
    encoded = data[0].get("b64_json")
    if not isinstance(encoded, str):
        raise RenderError("image service returned an invalid response")
    try:
        image = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError, TypeError) as exc:
        raise RenderError("image service returned an invalid response") from exc
    if not _valid_png(image):
        raise RenderError("image service returned an invalid PNG")
    return image


def _valid_png(image: bytes) -> bool:
    if not image.startswith(b"\x89PNG\r\n\x1a\n"):
        return False
    offset = 8
    seen_ihdr = False
    seen_idat = False
    seen_iend = False
    seen_plte = False
    idat_ended = False
    image_info: tuple[int, int, int, int, int] | None = None
    compressed = bytearray()
    while offset < len(image):
        if offset + 12 > len(image):
            return False
        length = struct.unpack(">I", image[offset : offset + 4])[0]
        chunk_type = image[offset + 4 : offset + 8]
        data_start = offset + 8
        data_end = data_start + length
        crc_end = data_end + 4
        if crc_end > len(image):
            return False
        expected_crc = struct.unpack(">I", image[data_end:crc_end])[0]
        actual_crc = zlib.crc32(chunk_type)
        actual_crc = zlib.crc32(image[data_start:data_end], actual_crc) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            return False
        if not seen_ihdr:
            if chunk_type != b"IHDR" or length != 13:
                return False
            width, height = struct.unpack(">II", image[data_start : data_start + 8])
            if width <= 0 or height <= 0 or width * height > MAX_PIXELS:
                return False
            bit_depth, color_type, compression, filtering, interlace = struct.unpack(
                ">BBBBB", image[data_start + 8 : data_start + 13]
            )
            valid_depths = {
                0: {1, 2, 4, 8, 16},
                2: {8, 16},
                3: {1, 2, 4, 8},
                4: {8, 16},
                6: {8, 16},
            }
            if (
                color_type not in valid_depths
                or bit_depth not in valid_depths[color_type]
                or compression != 0
                or filtering != 0
                or interlace not in {0, 1}
            ):
                return False
            image_info = (width, height, bit_depth, color_type, interlace)
            seen_ihdr = True
        elif chunk_type == b"IHDR":
            return False
        if chunk_type == b"PLTE":
            if seen_plte or seen_idat or image_info is None:
                return False
            _, _, bit_depth, color_type, _ = image_info
            if (
                color_type in {0, 4}
                or length == 0
                or length % 3
                or length > 768
                or (color_type == 3 and length // 3 > 2**bit_depth)
            ):
                return False
            seen_plte = True
        if chunk_type == b"IDAT":
            if seen_iend or idat_ended:
                return False
            seen_idat = True
            compressed.extend(image[data_start:data_end])
        elif seen_idat and chunk_type != b"IEND":
            idat_ended = True
        if chunk_type == b"IEND":
            if length != 0:
                return False
            seen_iend = True
            offset = crc_end
            break
        offset = crc_end
    if (
        not seen_ihdr
        or not seen_idat
        or not seen_iend
        or offset != len(image)
        or image_info is None
    ):
        return False
    width, height, bit_depth, color_type, interlace = image_info
    if color_type == 3 and not seen_plte:
        return False
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color_type]

    def pass_size(pass_width: int, pass_height: int) -> int:
        if pass_width <= 0 or pass_height <= 0:
            return 0
        row_bytes = (pass_width * channels * bit_depth + 7) // 8
        return pass_height * (row_bytes + 1)

    if interlace == 0:
        expected = pass_size(width, height)
        row_widths = [((width * channels * bit_depth + 7) // 8, height)]
    else:
        passes = (
            (0, 0, 8, 8),
            (4, 0, 8, 8),
            (0, 4, 4, 8),
            (2, 0, 4, 4),
            (0, 2, 2, 4),
            (1, 0, 2, 2),
            (0, 1, 1, 2),
        )
        row_widths = []
        expected = 0
        for start_x, start_y, step_x, step_y in passes:
            pass_width = max(0, (width - start_x + step_x - 1) // step_x)
            pass_height = max(0, (height - start_y + step_y - 1) // step_y)
            expected += pass_size(pass_width, pass_height)
            if pass_width and pass_height:
                row_widths.append(
                    ((pass_width * channels * bit_depth + 7) // 8, pass_height)
                )
    try:
        decompressor = zlib.decompressobj()
        raw = decompressor.decompress(bytes(compressed), expected + 1)
    except zlib.error:
        return False
    if (
        len(raw) > expected
        or not decompressor.eof
        or decompressor.unused_data
        or decompressor.unconsumed_tail
    ):
        return False
    if len(raw) != expected:
        return False
    position = 0
    for row_bytes, row_count in row_widths:
        for _ in range(row_count):
            if raw[position] > 4:
                return False
            position += row_bytes + 1
    return position == len(raw)


def _directory_flags() -> int:
    return os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW


@contextmanager
def _directory_anchor(path: Path, *, field: str) -> Iterator[int]:
    try:
        before = os.lstat(path)
        fd = os.open(path, _directory_flags())
        opened = os.fstat(fd)
    except OSError as exc:
        raise ValidationError(f"{field} must be a stable real directory") from exc
    if (
        stat.S_ISLNK(before.st_mode)
        or not stat.S_ISDIR(before.st_mode)
        or not stat.S_ISDIR(opened.st_mode)
        or (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino)
    ):
        os.close(fd)
        raise ValidationError(f"{field} must be a stable real directory")
    try:
        yield fd
    finally:
        os.close(fd)


def _normalized_absolute(path: Path) -> Path:
    candidate = Path(os.path.abspath(path))
    return candidate.parent.resolve(strict=False) / candidate.name


def _lexical_relative(path: Path, root: Path, *, field: str) -> Path:
    absolute = _normalized_absolute(path)
    try:
        relative = absolute.relative_to(root)
    except ValueError as exc:
        raise ValidationError(f"{field} must stay inside the user project") from exc
    if ".." in relative.parts:
        raise ValidationError(f"{field} must stay inside the user project")
    return relative


def _open_directory_relative(
    root_fd: int,
    relative: Path,
    *,
    create: bool,
    field: str,
) -> int:
    current_fd = os.dup(root_fd)
    try:
        for component in relative.parts:
            if component in {"", "."}:
                continue
            try:
                next_fd = os.open(
                    component,
                    _directory_flags(),
                    dir_fd=current_fd,
                )
            except FileNotFoundError:
                if not create:
                    raise
                try:
                    os.mkdir(component, mode=0o700, dir_fd=current_fd)
                except FileExistsError:
                    pass
                next_fd = os.open(
                    component,
                    _directory_flags(),
                    dir_fd=current_fd,
                )
            os.close(current_fd)
            current_fd = next_fd
        return current_fd
    except OSError as exc:
        os.close(current_fd)
        raise ValidationError(f"{field} has an unsafe path component") from exc


@contextmanager
def _output_anchor(
    project: Path,
    project_fd: int,
    output_dir: Path,
) -> Iterator[tuple[int, Path]]:
    relative = _lexical_relative(output_dir, project, field="output directory")
    output_fd = _open_directory_relative(
        project_fd,
        relative,
        create=True,
        field="output directory",
    )
    try:
        yield output_fd, relative
    finally:
        os.close(output_fd)


def _anchored_directory_is_current(
    project_fd: int,
    relative: Path,
    anchored_fd: int,
) -> bool:
    try:
        current_fd = _open_directory_relative(
            project_fd,
            relative,
            create=False,
            field="output directory",
        )
    except ValidationError:
        return False
    try:
        current = os.fstat(current_fd)
        anchored = os.fstat(anchored_fd)
        return (current.st_dev, current.st_ino) == (anchored.st_dev, anchored.st_ino)
    finally:
        os.close(current_fd)


def _preflight_output(root_fd: int, relative: Path) -> bool:
    directory_fd = os.dup(root_fd)
    try:
        try:
            for component in relative.parts[:-1]:
                next_fd = os.open(
                    component,
                    _directory_flags(),
                    dir_fd=directory_fd,
                )
                os.close(directory_fd)
                directory_fd = next_fd
        except FileNotFoundError:
            return False
        try:
            details = os.stat(
                relative.name,
                dir_fd=directory_fd,
                follow_symlinks=False,
            )
        except FileNotFoundError:
            return False
        if stat.S_ISLNK(details.st_mode) or not stat.S_ISREG(details.st_mode):
            raise ValidationError("output_path has an unsafe existing target")
        return True
    except OSError as exc:
        raise ValidationError("output_path has an unsafe parent") from exc
    finally:
        os.close(directory_fd)


def _write_output_fallback(*_args: object, **_kwargs: object) -> None:
    raise UnsupportedPlatformError(
        "secure output writes are unavailable on this platform"
    )


def _write_output_posix(root_fd: int, relative: Path, contents: bytes) -> None:
    directory_fd = os.dup(root_fd)
    temporary = f".{relative.name}.{secrets.token_hex(16)}.tmp"
    file_fd = -1
    try:
        for component in relative.parts[:-1]:
            try:
                next_fd = os.open(
                    component,
                    _directory_flags(),
                    dir_fd=directory_fd,
                )
            except FileNotFoundError:
                os.mkdir(component, mode=0o700, dir_fd=directory_fd)
                next_fd = os.open(
                    component,
                    _directory_flags(),
                    dir_fd=directory_fd,
                )
            os.close(directory_fd)
            directory_fd = next_fd
        try:
            details = os.stat(relative.name, dir_fd=directory_fd, follow_symlinks=False)
        except FileNotFoundError:
            details = None
        if details is not None and (stat.S_ISLNK(details.st_mode) or not stat.S_ISREG(details.st_mode)):
            raise ValidationError("output_path has an unsafe existing target")
        file_fd = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            0o600,
            dir_fd=directory_fd,
        )
        _write_all(file_fd, contents)
        os.fsync(file_fd)
        os.close(file_fd)
        file_fd = -1
        try:
            os.link(
                temporary,
                relative.name,
                src_dir_fd=directory_fd,
                dst_dir_fd=directory_fd,
                follow_symlinks=False,
            )
        except FileExistsError as exc:
            raise ValidationError(
                "render output already exists; choose a new filename"
            ) from exc
        os.unlink(temporary, dir_fd=directory_fd)
    finally:
        if file_fd != -1:
            os.close(file_fd)
        try:
            os.unlink(temporary, dir_fd=directory_fd)
        except FileNotFoundError:
            pass
        os.close(directory_fd)


def _write_output(root_fd: int, relative: Path, contents: bytes) -> None:
    if not _secure_output_supported():
        raise UnsupportedPlatformError(
            "secure output writes are unavailable on this platform"
        )
    _write_output_posix(root_fd, relative, contents)


def _secure_output_supported() -> bool:
    return (
        os.name == "posix"
        and _OPEN_SUPPORTS_DIR_FD
        and _LINK_SUPPORTS_DIR_FD
        and _RENAME_SUPPORTS_DIR_FD
        and _UNLINK_SUPPORTS_DIR_FD
        and hasattr(os, "O_DIRECTORY")
        and hasattr(os, "O_NOFOLLOW")
    )


def _secure_config_supported() -> bool:
    return (
        _secure_output_supported()
        and _UNLINK_SUPPORTS_DIR_FD
        and hasattr(os, "fchmod")
    )


def _validated_render_size(image: Mapping[str, Any]) -> str:
    canvas = image.get("canvas")
    if canvas not in CANVAS_DIMENSIONS:
        raise ValidationError("render request image has an unsupported canvas")
    width = image.get("width")
    height = image.get("height")
    if (
        not isinstance(width, int)
        or isinstance(width, bool)
        or not isinstance(height, int)
        or isinstance(height, bool)
        or width <= 0
        or height <= 0
    ):
        raise ValidationError("render request dimensions must be positive integers")
    pixels = width * height
    if (
        max(width, height) > MAX_EDGE
        or width % 16
        or height % 16
        or max(width, height) > MAX_ASPECT_RATIO * min(width, height)
        or pixels < MIN_PIXELS
        or pixels > MAX_PIXELS
    ):
        raise ValidationError("render request dimensions exceed GPT Image 2 limits")
    if (width, height) != CANVAS_DIMENSIONS[canvas]:
        raise ValidationError("render request dimensions do not match the canvas")
    return f"{width}x{height}"


def _reject_skill_root_output(output: Path) -> None:
    resolved = output.resolve(strict=False)
    try:
        resolved.relative_to(SKILL_ROOT)
    except ValueError:
        return
    raise ValidationError("runtime output must stay outside the installed Skill")


def _project_root_path(project_root: Path | None, fallback: Path) -> Path:
    root = (project_root or fallback).resolve()
    try:
        details = os.lstat(root)
    except OSError as exc:
        raise ValidationError("project root must be an existing directory") from exc
    if stat.S_ISLNK(details.st_mode) or not stat.S_ISDIR(details.st_mode):
        raise ValidationError("project root must be a real directory")
    return root


def _require_project_path(path: Path, project_root: Path, *, field: str) -> Path:
    resolved = path.resolve(strict=False)
    try:
        resolved.relative_to(project_root)
    except ValueError as exc:
        raise ValidationError(f"{field} must stay inside the user project") from exc
    return resolved


def _trusted_tutorial_references() -> set[Path]:
    return {
        (
            SKILL_ROOT
            / "examples"
            / "characters"
            / character
            / "preview.png"
        ).resolve()
        for character in ("wukong", "moon-rabbit")
    }


def _read_anchored_bytes(
    root_fd: int,
    relative: Path,
    *,
    field: str,
    maximum_bytes: int,
) -> bytes:
    if not relative.parts or relative.name in {"", ".", ".."}:
        raise ValidationError(f"{field} must name a regular file")
    parent = Path(*relative.parts[:-1])
    try:
        parent_fd = _open_directory_relative(
            root_fd,
            parent,
            create=False,
            field=field,
        )
    except ValidationError:
        raise
    file_fd = -1
    try:
        file_fd = os.open(
            relative.name,
            os.O_RDONLY | os.O_NOFOLLOW,
            dir_fd=parent_fd,
        )
        details = os.fstat(file_fd)
        if not stat.S_ISREG(details.st_mode):
            raise ValidationError(f"{field} must be a regular file")
        if details.st_size > maximum_bytes:
            raise ValidationError(f"{field} is too large")
        chunks: list[bytes] = []
        remaining = maximum_bytes + 1
        while remaining > 0:
            chunk = os.read(file_fd, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        contents = b"".join(chunks)
        if len(contents) > maximum_bytes:
            raise ValidationError(f"{field} is too large")
        return contents
    except ValidationError:
        raise
    except OSError as exc:
        raise ValidationError(f"{field} file not found or unsafe") from exc
    finally:
        if file_fd != -1:
            os.close(file_fd)
        os.close(parent_fd)


def _read_authorized_reference(
    path: Path,
    *,
    project_root: Path,
    project_fd: int,
) -> tuple[str, str, bytes]:
    lexical = _normalized_absolute(path)
    trusted = _trusted_tutorial_references()
    if lexical in trusted:
        relative = lexical.relative_to(SKILL_ROOT)
        with _directory_anchor(SKILL_ROOT, field="installed Skill") as skill_fd:
            contents = _read_anchored_bytes(
                skill_fd,
                relative,
                field="authorized reference image",
                maximum_bytes=MAX_REFERENCE_BYTES,
            )
    else:
        _require_project_path(path, project_root, field="reference image")
        relative = _lexical_relative(
            path,
            project_root,
            field="reference image",
        )
        contents = _read_anchored_bytes(
            project_fd,
            relative,
            field="authorized reference image",
            maximum_bytes=MAX_REFERENCE_BYTES,
        )
    return _safe_filename(path.name), _reference_mime(contents), contents


def render_request(
    request_path: Path,
    output_dir: Path,
    api_key: str,
    transport: Transport | None = None,
    *,
    project_root: Path | None = None,
) -> dict[str, Any]:
    """Render a compiled request with GPT Image 2 without logging credentials."""
    if _valid_key(api_key) is None:
        raise CredentialError("API key must be a non-empty single-line value")
    if not _secure_output_supported():
        raise UnsupportedPlatformError(
            "secure output writes are unavailable on this platform"
        )
    project = _project_root_path(project_root, request_path.parent)
    _require_project_path(request_path, project, field="render request")
    _reject_skill_root_output(output_dir)
    _require_project_path(output_dir, project, field="output directory")
    sender = transport or _http_transport
    results: list[dict[str, str]] = []
    prepared: list[dict[str, Any]] = []
    request_lexical = _normalized_absolute(request_path)
    request_root = request_lexical.parent

    with _directory_anchor(project, field="project root") as project_fd:
        request_relative = _lexical_relative(
            request_lexical,
            project,
            field="render request",
        )
        request = _load_render_request(
            _read_anchored_bytes(
                project_fd,
                request_relative,
                field="render request",
                maximum_bytes=MAX_PROJECT_TEXT_BYTES,
            )
        )
        with _output_anchor(
            project,
            project_fd,
            output_dir,
        ) as (output_root_fd, output_root_relative):
            seen_output_paths: set[Path] = set()
            for image in request["images"]:
                if not isinstance(image, dict) or not isinstance(image.get("id"), str):
                    raise ValidationError("render request image must have an id")
                image_id = image["id"]
                prompt_path = _safe_relative_path(
                    image.get("prompt_path"),
                    field="prompt_path",
                )
                output_path = _safe_relative_path(
                    image.get("output_path"),
                    field="output_path",
                )
                if output_path in seen_output_paths:
                    raise ValidationError(
                        "render request contains duplicate output paths"
                    )
                seen_output_paths.add(output_path)
                prompt_lexical = request_root / prompt_path
                _resolve_within(request_root, prompt_path, field="prompt_path")
                prompt_relative = _lexical_relative(
                    prompt_lexical,
                    project,
                    field="prompt_path",
                )
                if _preflight_output(output_root_fd, output_path):
                    raise ValidationError(
                        "render output already exists; choose a new filename"
                    )
                size = _validated_render_size(image)
                prompt_bytes = _read_anchored_bytes(
                    project_fd,
                    prompt_relative,
                    field="render request prompt",
                    maximum_bytes=MAX_PROJECT_TEXT_BYTES,
                )
                try:
                    prompt = prompt_bytes.decode("utf-8")
                except UnicodeDecodeError as exc:
                    raise ValidationError(
                        "render request prompt is not valid UTF-8"
                    ) from exc
                references_value = image.get("reference_images", [])
                if not isinstance(references_value, list) or not all(
                    isinstance(item, str) for item in references_value
                ):
                    raise ValidationError("reference_images must be a list of paths")
                if len(references_value) > MAX_REFERENCES:
                    raise ValidationError("too many authorized reference images")
                reference_paths = [
                    Path(item) if Path(item).is_absolute() else request_root / item
                    for item in references_value
                ]
                references = [
                    _read_authorized_reference(
                        reference,
                        project_root=project,
                        project_fd=project_fd,
                    )
                    for reference in reference_paths
                ]
                if (
                    sum(len(contents) for _, _, contents in references)
                    > MAX_TOTAL_REFERENCE_BYTES
                ):
                    raise ValidationError(
                        "authorized reference images are too large"
                    )
                prepared.append(
                    {
                        "id": image_id,
                        "output_path": output_path,
                        "references": references,
                        "fields": {
                            "model": MODEL,
                            "prompt": prompt,
                            "size": size,
                            "quality": "medium",
                            "output_format": "png",
                        },
                    }
                )

            for image in prepared:
                image_id = image["id"]
                output_path = image["output_path"]
                references = image["references"]
                fields = image["fields"]
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Accept": "application/json",
                }
                if references:
                    boundary, body = _multipart(fields, references)
                    url = f"{API_URL}/edits"
                    headers["Content-Type"] = (
                        f"multipart/form-data; boundary={boundary}"
                    )
                else:
                    body = json.dumps(fields, ensure_ascii=False).encode("utf-8")
                    url = f"{API_URL}/generations"
                    headers["Content-Type"] = "application/json"

                try:
                    response = sender(url, "POST", headers, body)
                    status = (
                        response.get("status")
                        if isinstance(response, dict)
                        else None
                    )
                    if not isinstance(status, int) or not 200 <= status < 300:
                        results.append(
                            {
                                "id": image_id,
                                "status": "failed",
                                "error": (
                                    _error_classification(status)
                                    if isinstance(status, int)
                                    else "request_failed"
                                ),
                            }
                        )
                        continue
                    contents = _decode_image(response.get("body"))
                    try:
                        if not _anchored_directory_is_current(
                            project_fd,
                            output_root_relative,
                            output_root_fd,
                        ):
                            raise ValidationError(
                                "output directory changed during render"
                            )
                        _write_output(output_root_fd, output_path, contents)
                    except (OSError, ValidationError):
                        results.append(
                            {
                                "id": image_id,
                                "status": "failed",
                                "error": "output_write_failed",
                            }
                        )
                        continue
                    results.append(
                        {
                            "id": image_id,
                            "status": "rendered",
                            "output_path": output_path.as_posix(),
                        }
                    )
                except RenderError:
                    results.append(
                        {
                            "id": image_id,
                            "status": "failed",
                            "error": "invalid_response",
                        }
                    )

    overall = "complete" if all(item["status"] == "rendered" for item in results) else "partial_failure"
    return {"status": overall, "images": results}


def render_character_master(
    reference_path: Path,
    output_path: Path,
    api_key: str,
    transport: Transport | None = None,
    *,
    project_root: Path | None = None,
) -> dict[str, str]:
    """Create a secure 1:1 character consistency master from an authorized photo."""
    if _valid_key(api_key) is None:
        raise CredentialError("API key must be a non-empty single-line value")
    if not _secure_output_supported():
        raise UnsupportedPlatformError(
            "secure output writes are unavailable on this platform"
        )
    reference = Path(reference_path)
    output = Path(output_path)
    project = _project_root_path(project_root, reference.parent)
    _reject_skill_root_output(output)
    _require_project_path(reference, project, field="reference image")
    _require_project_path(output, project, field="character master output")
    if not output.name or output.name in {".", ".."}:
        raise ValidationError("output_path must name a PNG file")
    if output.suffix.lower() != ".png":
        raise ValidationError("output_path must name a PNG file")
    relative_output = Path(output.name)
    sender = transport or _http_transport
    with _directory_anchor(project, field="project root") as project_fd:
        reference_data = [
            _read_authorized_reference(
                reference,
                project_root=project,
                project_fd=project_fd,
            )
        ]
        with _output_anchor(
            project,
            project_fd,
            output.parent,
        ) as (output_root_fd, output_root_relative):
            if _preflight_output(output_root_fd, relative_output):
                raise ValidationError(
                    "character master output already exists; choose a new filename"
                )
            fields = {
                "model": MODEL,
                "prompt": CHARACTER_MASTER_PROMPT,
                "size": "1024x1024",
                "quality": "medium",
                "output_format": "png",
            }
            boundary, body = _multipart(fields, reference_data)
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            }
            try:
                response = sender(f"{API_URL}/edits", "POST", headers, body)
                status = (
                    response.get("status") if isinstance(response, dict) else None
                )
                if not isinstance(status, int) or not 200 <= status < 300:
                    error = (
                        _error_classification(status)
                        if isinstance(status, int)
                        else "request_failed"
                    )
                    return {"status": "failed", "error": error}
                contents = _decode_image(response.get("body"))
            except RenderError:
                return {"status": "failed", "error": "invalid_response"}
            try:
                if not _anchored_directory_is_current(
                    project_fd,
                    output_root_relative,
                    output_root_fd,
                ):
                    raise ValidationError(
                        "output directory changed during render"
                    )
                _write_output(output_root_fd, relative_output, contents)
            except (OSError, ValidationError):
                return {"status": "failed", "error": "output_write_failed"}
    return {"status": "rendered", "output_path": str(output)}


__all__ = [
    "CredentialError",
    "doctor",
    "load_api_key",
    "render_character_master",
    "render_request",
    "write_user_api_key",
]
