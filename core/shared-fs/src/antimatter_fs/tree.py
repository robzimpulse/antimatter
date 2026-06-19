import os
import asyncio
from pathlib import Path
from antimatter_protocol.models import FileNode

IGNORE_LIST = {
    'node_modules', '.git', 'dist', 'build', 'out', 
    '.gradle', '__pycache__', '.venv', 'venv', 
    '.idea', '.DS_Store', '.kotlin'
}

def _build_tree_sync(root_path: str, max_depth: int = 12, current_depth: int = 0) -> list[FileNode]:
    """Synchronous recursive tree builder."""
    if current_depth > max_depth:
        return []

    nodes: list[FileNode] = []
    try:
        with os.scandir(root_path) as it:
            for entry in it:
                if entry.name in IGNORE_LIST:
                    continue
                    
                is_dir = entry.is_dir()
                size = entry.stat().st_size if not is_dir else None
                
                children = None
                if is_dir:
                    children = _build_tree_sync(entry.path, max_depth, current_depth + 1)
                
                nodes.append(FileNode(
                    name=entry.name,
                    is_directory=is_dir,
                    path=entry.path,
                    size=size,
                    children=children
                ))
    except PermissionError:
        pass
    except FileNotFoundError:
        pass
        
    # Sort directories first, then alphabetically
    nodes.sort(key=lambda x: (not x.is_directory, x.name.lower()))
    return nodes

async def build_file_tree(root_path: str, max_depth: int = 12) -> list[FileNode]:
    """Async file tree builder that won't block the event loop."""
    return await asyncio.to_thread(_build_tree_sync, root_path, max_depth, 0)
