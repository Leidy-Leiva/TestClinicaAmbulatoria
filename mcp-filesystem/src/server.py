"""
MCP Filesystem Server usando FastMCP
Permite leer, escribir y listar archivos de forma segura
dentro de un directorio raíz configurable.
"""

import os
import shutil
import hashlib
import mimetypes
import stat
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP

# ── Configuración ──────────────────────────────────────────────────────────────
FS_ROOT = Path(os.getenv("FS_ROOT", "/workspace")).resolve()
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
MAX_FILE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

mcp = FastMCP(
    name="filesystem-mcp",
    instructions=(
        "Servidor MCP para gestionar archivos y directorios de forma segura. "
        "Todas las operaciones están restringidas al directorio raíz configurado. "
        "Usa las herramientas disponibles para leer, escribir, listar, copiar, "
        "mover y eliminar archivos y carpetas."
    ),
)


# ── Helpers de filesystem ──────────────────────────────────────────────────────

def safe_path(relative_path: str) -> Path:
    """
    Resuelve una ruta relativa dentro de FS_ROOT y verifica que no escape
    del sandbox mediante path traversal (e.g. ../../etc/passwd).
    """
    clean = relative_path.strip().lstrip("/\\")
    resolved = (FS_ROOT / clean).resolve()

    if not str(resolved).startswith(str(FS_ROOT)):
        raise PermissionError(
            f"Acceso denegado: la ruta '{relative_path}' está fuera del directorio raíz."
        )
    return resolved


def format_size(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def file_info(path: Path) -> dict:
    """Construye un dict con metadatos de un archivo o directorio."""
    s = path.stat()
    mime, _ = mimetypes.guess_type(str(path))
    return {
        "name": path.name,
        "path": str(path.relative_to(FS_ROOT)),
        "type": "directory" if path.is_dir() else "file",
        "size_bytes": s.st_size if path.is_file() else None,
        "size_human": format_size(s.st_size) if path.is_file() else None,
        "mime_type": mime,
        "modified_at": datetime.fromtimestamp(s.st_mtime).isoformat(),
        "created_at": datetime.fromtimestamp(s.st_ctime).isoformat(),
        "permissions": oct(stat.S_IMODE(s.st_mode)),
    }


# ── Herramientas MCP ───────────────────────────────────────────────────────────

@mcp.tool()
def read_file(path: str, encoding: str = "utf-8") -> dict:
    """
    Lee el contenido de un archivo de texto.

    Args:
        path: Ruta relativa al archivo (desde el directorio raíz).
        encoding: Codificación del archivo (default: utf-8).

    Returns:
        Contenido del archivo, número de líneas y metadatos básicos.
    """
    target = safe_path(path)

    if not target.exists():
        raise FileNotFoundError(f"Archivo no encontrado: '{path}'")
    if target.is_dir():
        raise IsADirectoryError(f"'{path}' es un directorio, no un archivo.")
    if target.stat().st_size > MAX_FILE_BYTES:
        raise ValueError(
            f"Archivo demasiado grande ({format_size(target.stat().st_size)}). "
            f"Máximo permitido: {MAX_FILE_SIZE_MB} MB."
        )

    content = target.read_text(encoding=encoding)
    return {
        "path": str(target.relative_to(FS_ROOT)),
        "content": content,
        "lines": content.count("\n") + 1,
        "size_bytes": target.stat().st_size,
        "encoding": encoding,
    }


@mcp.tool()
def write_file(
    path: str,
    content: str,
    encoding: str = "utf-8",
    overwrite: bool = True,
    create_dirs: bool = True,
) -> dict:
    """
    Escribe o sobreescribe un archivo de texto.

    Args:
        path: Ruta relativa donde guardar el archivo.
        content: Contenido a escribir.
        encoding: Codificación (default: utf-8).
        overwrite: Si False, falla si el archivo ya existe (default: True).
        create_dirs: Crea los directorios intermedios si no existen (default: True).

    Returns:
        Información del archivo creado/actualizado.
    """
    target = safe_path(path)

    if target.exists() and not overwrite:
        raise FileExistsError(
            f"El archivo '{path}' ya existe. Usa overwrite=True para sobreescribir."
        )
    if target.is_dir():
        raise IsADirectoryError(f"'{path}' es un directorio.")
    if len(content.encode(encoding)) > MAX_FILE_BYTES:
        raise ValueError(f"Contenido demasiado grande. Máximo: {MAX_FILE_SIZE_MB} MB.")

    if create_dirs:
        target.parent.mkdir(parents=True, exist_ok=True)

    target.write_text(content, encoding=encoding)

    return {
        "path": str(target.relative_to(FS_ROOT)),
        "size_bytes": target.stat().st_size,
        "size_human": format_size(target.stat().st_size),
        "lines": content.count("\n") + 1,
        "encoding": encoding,
    }


@mcp.tool()
def append_file(path: str, content: str, encoding: str = "utf-8") -> dict:
    """
    Agrega contenido al final de un archivo existente (o lo crea si no existe).

    Args:
        path: Ruta relativa del archivo.
        content: Texto a agregar al final.
        encoding: Codificación (default: utf-8).

    Returns:
        Tamaño final del archivo y líneas totales.
    """
    target = safe_path(path)

    if target.is_dir():
        raise IsADirectoryError(f"'{path}' es un directorio.")

    target.parent.mkdir(parents=True, exist_ok=True)

    with target.open("a", encoding=encoding) as f:
        f.write(content)

    full_content = target.read_text(encoding=encoding)
    return {
        "path": str(target.relative_to(FS_ROOT)),
        "size_bytes": target.stat().st_size,
        "total_lines": full_content.count("\n") + 1,
        "appended_lines": content.count("\n") + 1,
    }


@mcp.tool()
def list_directory(
    path: str = ".",
    recursive: bool = False,
    show_hidden: bool = False,
    pattern: Optional[str] = None,
) -> dict:
    """
    Lista el contenido de un directorio.

    Args:
        path: Ruta relativa del directorio (default: raíz).
        recursive: Si True, lista recursivamente todos los subdirectorios.
        show_hidden: Si True, incluye archivos que empiezan con punto.
        pattern: Patrón glob para filtrar (e.g. '*.py', '*.txt').

    Returns:
        Lista de archivos y directorios con sus metadatos.
    """
    target = safe_path(path)

    if not target.exists():
        raise FileNotFoundError(f"Directorio no encontrado: '{path}'")
    if not target.is_dir():
        raise NotADirectoryError(f"'{path}' es un archivo, no un directorio.")

    if recursive:
        glob_pattern = f"**/{pattern}" if pattern else "**/*"
        entries = list(target.glob(glob_pattern))
    else:
        glob_pattern = pattern if pattern else "*"
        entries = list(target.glob(glob_pattern))

    if not show_hidden:
        entries = [e for e in entries if not e.name.startswith(".")]

    entries.sort(key=lambda e: (e.is_file(), e.name.lower()))

    items = [file_info(e) for e in entries]
    dirs = [i for i in items if i["type"] == "directory"]
    files = [i for i in items if i["type"] == "file"]
    total_size = sum(f["size_bytes"] or 0 for f in files)

    return {
        "path": str(target.relative_to(FS_ROOT)) if target != FS_ROOT else ".",
        "total_items": len(items),
        "directories": len(dirs),
        "files": len(files),
        "total_size_human": format_size(total_size),
        "items": items,
    }


@mcp.tool()
def create_directory(path: str, exist_ok: bool = True) -> dict:
    """
    Crea un directorio (y sus padres si no existen).

    Args:
        path: Ruta relativa del directorio a crear.
        exist_ok: Si False, falla si el directorio ya existe (default: True).

    Returns:
        Información del directorio creado.
    """
    target = safe_path(path)

    if target.exists() and not exist_ok:
        raise FileExistsError(f"El directorio '{path}' ya existe.")

    target.mkdir(parents=True, exist_ok=exist_ok)

    return {
        "path": str(target.relative_to(FS_ROOT)),
        "created": True,
    }


@mcp.tool()
def delete_file(path: str) -> dict:
    """
    Elimina un archivo.

    Args:
        path: Ruta relativa del archivo a eliminar.

    Returns:
        Confirmación de eliminación.
    """
    target = safe_path(path)

    if not target.exists():
        raise FileNotFoundError(f"Archivo no encontrado: '{path}'")
    if target.is_dir():
        raise IsADirectoryError(f"'{path}' es un directorio. Usa delete_directory.")

    size = target.stat().st_size
    target.unlink()

    return {"deleted": True, "path": path, "freed_bytes": size}


@mcp.tool()
def delete_directory(path: str, recursive: bool = False) -> dict:
    """
    Elimina un directorio.

    Args:
        path: Ruta relativa del directorio.
        recursive: Si True, elimina el contenido también (default: False).

    Returns:
        Confirmación de eliminación.
    """
    target = safe_path(path)

    if not target.exists():
        raise FileNotFoundError(f"Directorio no encontrado: '{path}'")
    if not target.is_dir():
        raise NotADirectoryError(f"'{path}' es un archivo.")
    if str(target) == str(FS_ROOT):
        raise PermissionError("No se puede eliminar el directorio raíz.")

    if recursive:
        shutil.rmtree(target)
    else:
        target.rmdir()

    return {"deleted": True, "path": path, "recursive": recursive}


@mcp.tool()
def copy_file(source: str, destination: str, overwrite: bool = True) -> dict:
    """
    Copia un archivo a otra ubicación.

    Args:
        source: Ruta relativa del archivo origen.
        destination: Ruta relativa del destino.
        overwrite: Si False, falla si el destino ya existe (default: True).

    Returns:
        Información del archivo copiado.
    """
    src = safe_path(source)
    dst = safe_path(destination)

    if not src.exists():
        raise FileNotFoundError(f"Origen no encontrado: '{source}'")
    if src.is_dir():
        raise IsADirectoryError(f"'{source}' es un directorio.")
    if dst.exists() and not overwrite:
        raise FileExistsError(f"El destino '{destination}' ya existe.")

    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

    return {
        "source": source,
        "destination": str(dst.relative_to(FS_ROOT)),
        "size_bytes": dst.stat().st_size,
    }


@mcp.tool()
def move_file(source: str, destination: str, overwrite: bool = True) -> dict:
    """
    Mueve o renombra un archivo.

    Args:
        source: Ruta relativa del archivo origen.
        destination: Ruta relativa del destino.
        overwrite: Si False, falla si el destino ya existe (default: True).

    Returns:
        Rutas origen y destino.
    """
    src = safe_path(source)
    dst = safe_path(destination)

    if not src.exists():
        raise FileNotFoundError(f"Origen no encontrado: '{source}'")
    if dst.exists() and not overwrite:
        raise FileExistsError(f"El destino '{destination}' ya existe.")

    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))

    return {"moved": True, "source": source, "destination": str(dst.relative_to(FS_ROOT))}


@mcp.tool()
def get_file_info(path: str) -> dict:
    """
    Devuelve metadatos completos de un archivo o directorio.

    Args:
        path: Ruta relativa del archivo o directorio.

    Returns:
        Metadatos: tamaño, fechas, permisos, mime type y hashes (si es archivo).
    """
    target = safe_path(path)

    if not target.exists():
        raise FileNotFoundError(f"No encontrado: '{path}'")

    info = file_info(target)

    if target.is_file() and target.stat().st_size <= MAX_FILE_BYTES:
        raw = target.read_bytes()
        info["md5"] = hashlib.md5(raw).hexdigest()
        info["sha256"] = hashlib.sha256(raw).hexdigest()

    return info


@mcp.tool()
def search_files(
    query: str,
    path: str = ".",
    search_content: bool = False,
    case_sensitive: bool = False,
) -> dict:
    """
    Busca archivos por nombre o por contenido.

    Args:
        query: Texto a buscar.
        path: Directorio donde buscar (default: raíz).
        search_content: Si True, busca dentro del contenido de archivos de texto.
        case_sensitive: Si True, distingue mayúsculas (default: False).

    Returns:
        Lista de archivos que coinciden con la búsqueda y total.
    """
    target = safe_path(path)

    if not target.is_dir():
        raise NotADirectoryError(f"'{path}' no es un directorio.")

    q = query if case_sensitive else query.lower()
    matches = []

    for entry in target.rglob("*"):
        if entry.is_dir():
            continue

        name = entry.name if case_sensitive else entry.name.lower()
        matched_name = q in name

        matched_content = False
        content_preview = None
        if search_content and entry.stat().st_size <= MAX_FILE_BYTES:
            try:
                text = entry.read_text(encoding="utf-8", errors="ignore")
                haystack = text if case_sensitive else text.lower()
                if q in haystack:
                    matched_content = True
                    for i, line in enumerate(text.splitlines(), 1):
                        if q in (line if case_sensitive else line.lower()):
                            content_preview = f"L{i}: {line.strip()[:100]}"
                            break
            except Exception:
                pass

        if matched_name or matched_content:
            info = file_info(entry)
            info["matched_name"] = matched_name
            info["matched_content"] = matched_content
            if content_preview:
                info["content_preview"] = content_preview
            matches.append(info)

    return {"query": query, "total_matches": len(matches), "matches": matches}


@mcp.tool()
def get_disk_usage(path: str = ".") -> dict:
    """
    Calcula el uso de disco de un directorio.

    Args:
        path: Ruta relativa del directorio (default: raíz).

    Returns:
        Tamaño total, número de archivos y subdirectorios.
    """
    target = safe_path(path)

    if not target.is_dir():
        raise NotADirectoryError(f"'{path}' no es un directorio.")

    total_size = 0
    file_count = 0
    dir_count = 0

    for entry in target.rglob("*"):
        if entry.is_file():
            total_size += entry.stat().st_size
            file_count += 1
        elif entry.is_dir():
            dir_count += 1

    return {
        "path": str(target.relative_to(FS_ROOT)) if target != FS_ROOT else ".",
        "total_size_bytes": total_size,
        "total_size_human": format_size(total_size),
        "file_count": file_count,
        "directory_count": dir_count,
    }


# ── Recursos MCP ───────────────────────────────────────────────────────────────

@mcp.resource("fs://root")
def resource_root_listing() -> str:
    """Vista del directorio raíz."""
    result = list_directory(".")
    lines = [f"📁 Directorio raíz ({result['total_items']} elementos)", ""]
    for item in result["items"]:
        icon = "📁" if item["type"] == "directory" else "📄"
        size = f" ({item['size_human']})" if item["size_human"] else ""
        lines.append(f"{icon} {item['name']}{size}")
    return "\n".join(lines)


@mcp.resource("fs://file/{path}")
def resource_file_content(path: str) -> str:
    """Lee el contenido de un archivo como recurso."""
    try:
        result = read_file(path)
        return result["content"]
    except Exception as e:
        return f"Error leyendo '{path}': {e}"


# ── Prompts MCP ────────────────────────────────────────────────────────────────

@mcp.prompt()
def filesystem_guide() -> str:
    """Guía de uso del servidor de filesystem."""
    return f"""
Eres un asistente que gestiona archivos y directorios a través de un servidor MCP de filesystem.

Directorio raíz: {FS_ROOT}
Tamaño máximo de archivo: {MAX_FILE_SIZE_MB} MB

Herramientas disponibles:

📖 LECTURA
- read_file(path)        → Lee un archivo de texto
- get_file_info(path)    → Metadatos completos (tamaño, fechas, hashes)
- get_disk_usage(path)   → Uso de disco de un directorio

📂 LISTADO Y BÚSQUEDA
- list_directory(path)   → Lista archivos y carpetas con metadatos
- search_files(query)    → Busca por nombre o contenido

✏️ ESCRITURA
- write_file(path, content)   → Escribe o sobreescribe un archivo
- append_file(path, content)  → Agrega al final de un archivo
- create_directory(path)      → Crea una carpeta

🗂️ ORGANIZACIÓN
- copy_file(src, dst)    → Copia un archivo
- move_file(src, dst)    → Mueve o renombra

🗑️ ELIMINACIÓN
- delete_file(path)           → Elimina un archivo
- delete_directory(path)      → Elimina un directorio (vacío por defecto)

Recursos:
- fs://root           → Listado rápido del directorio raíz
- fs://file/{{path}}  → Contenido de cualquier archivo

Seguridad: Todas las rutas están restringidas al directorio raíz.
"""


# ── Punto de entrada ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    FS_ROOT.mkdir(parents=True, exist_ok=True)
    mcp.run(transport="http", host="0.0.0.0", port=8003)
