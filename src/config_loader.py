from pathlib import Path


def load_yaml(path):
    try:
        import yaml
    except ImportError:
        yaml = None

    try:
        text = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise SystemExit(f"No se encuentra el archivo de configuración: {path}") from exc
    except Exception as exc:
        raise SystemExit(f"No se pudo leer la configuración {path}: {exc}") from exc

    if yaml:
        try:
            return yaml.safe_load(text) or {}
        except Exception as exc:
            raise SystemExit(f"No se pudo interpretar la configuración {path}: {exc}") from exc

    try:
        return SimpleYamlParser(text).parse()
    except Exception as exc:
        raise SystemExit(
            f"No se pudo interpretar la configuración {path}. "
            f"Instala PyYAML o revisa el formato del archivo: {exc}"
        ) from exc


class SimpleYamlParser:
    def __init__(self, text):
        self.tokens = self.tokenize(text)

    def parse(self):
        if not self.tokens:
            return {}
        value, _ = self.parse_node(0, self.tokens[0][0])
        return value or {}

    def tokenize(self, text):
        tokens = []
        for raw_line in text.splitlines():
            if not raw_line.strip() or raw_line.lstrip().startswith("#"):
                continue
            indent = len(raw_line) - len(raw_line.lstrip(" "))
            tokens.append((indent, raw_line.strip()))
        return tokens

    def parse_node(self, index, indent):
        if index >= len(self.tokens):
            return None, index

        current_indent, content = self.tokens[index]
        if current_indent < indent:
            return None, index
        if content.startswith("- "):
            return self.parse_list(index, current_indent)
        return self.parse_mapping(index, current_indent)

    def parse_list(self, index, indent):
        result = []
        while index < len(self.tokens):
            current_indent, content = self.tokens[index]
            if current_indent != indent or not content.startswith("- "):
                break

            item_content = content[2:].strip()
            index += 1

            if not item_content:
                value, index = self.parse_node(index, indent + 2)
            elif self.is_key_value(item_content):
                key, raw_value = self.split_key_value(item_content)
                value = {key: self.parse_scalar(raw_value)}
                if index < len(self.tokens) and self.tokens[index][0] > indent:
                    extra, index = self.parse_node(index, indent + 2)
                    if isinstance(extra, dict):
                        value.update(extra)
            else:
                value = self.parse_scalar(item_content)

            result.append(value)

        return result, index

    def parse_mapping(self, index, indent):
        result = {}
        while index < len(self.tokens):
            current_indent, content = self.tokens[index]
            if current_indent != indent or content.startswith("- "):
                break

            key, raw_value = self.split_key_value(content)
            index += 1

            if raw_value == "":
                value, index = self.parse_node(index, indent + 2)
            else:
                value = self.parse_scalar(raw_value)
            result[key] = value

        return result, index

    def is_key_value(self, content):
        if content.startswith(("'", '"')):
            return False
        if ":" not in content:
            return False
        key = content.split(":", 1)[0]
        return bool(key.strip()) and "://" not in key

    def split_key_value(self, content):
        if ":" not in content:
            raise ValueError(f"línea sin clave YAML: {content}")
        key, raw_value = content.split(":", 1)
        return key.strip(), raw_value.strip()

    def parse_scalar(self, value):
        if value == "":
            return ""
        if value == "[]":
            return []
        if value.lower() == "true":
            return True
        if value.lower() == "false":
            return False
        if value.lower() in ("null", "none"):
            return None
        if (
            (value.startswith('"') and value.endswith('"'))
            or (value.startswith("'") and value.endswith("'"))
        ):
            return value[1:-1]
        try:
            return int(value)
        except ValueError:
            pass
        try:
            return float(value)
        except ValueError:
            return value
