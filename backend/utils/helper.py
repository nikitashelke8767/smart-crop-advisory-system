def read_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()
