"""Diagnóstico local de arquivos de foto, sem exibir CPFs."""
from pathlib import Path
pasta=Path("fotos")
if pasta.is_dir():
    total=sum(1 for x in pasta.iterdir() if x.suffix.lower() in {".jpg",".jpeg",".png"})
    print(f"Fotos encontradas: {total} arquivo(s).")
else:
    print("Diretório local de fotos não encontrado.")
