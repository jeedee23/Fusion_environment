#!/usr/bin/env python3
"""Front-end working-model GUI for a copied Fusion PhotoBooth XML definition.

This application intentionally edits only JSON working profiles. It never writes
PhotoBooth.xml. The initial profile is a one-to-one tree translation of
``photoboothxml\\PhotoBooth.xml`` and is watermarked as an unverified base.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import re
import tkinter as tk
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk
from typing import Any, Iterator, Optional, Sequence


APP_NAME = "Fusion PhotoBooth Settings"
SCHEMA_VERSION = 1
ROOT = Path(__file__).resolve().parent
SOURCE_XML = ROOT / "photoboothxml" / "PhotoBooth.xml"
CATALOG_PATH = ROOT / "config" / "settings_catalog.json"
PROFILES_DIRECTORY = ROOT / "profiles"
WATERMARK = "CURRENT FILE IS NOT CHECKED AS CORRECT BASE"
NORMALISED_COLOUR_NAME = re.compile(r"(?:ARGB|RGBA|RGB|COLOR|COLOUR)", re.IGNORECASE)
WIDTH_NAME = re.compile(r"(?:WIDTH|THICKNESS|SIZE)", re.IGNORECASE)
NUMBER_SPLIT = re.compile(r"[\s,]+")
SAFE_FILENAME = re.compile(r"[^A-Za-z0-9._ -]+")


class ModelError(ValueError):
    """Raised when a catalog, profile, or edited working value is invalid."""


@dataclass(frozen=True)
class ColourValue:
    """A normalised editable RGB(A) value in source-channel order."""

    encoding: str
    red: float
    green: float
    blue: float
    alpha: Optional[float]


def sha256_file(path: Path) -> str:
    """Return a content hash for source identity and JSON provenance."""

    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def local_name(value: str) -> str:
    """Return a namespace-free XML name."""

    return value.rsplit("}", 1)[-1].rsplit(":", 1)[-1]


def humanise(value: str) -> str:
    """Create a concise editable draft description from an XML identifier."""

    separated = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", value).replace("_", " ")
    return separated.strip() or value


def field_kind(attribute: str, value: str) -> str:
    """Classify display/edit behaviour without changing XML semantics."""

    if attribute.casefold() == "shadowcolor":
        return "signed-unverified"
    if attribute.casefold() == "direction":
        return "direction-read-only"
    if NORMALISED_COLOUR_NAME.search(attribute):
        try:
            parse_colour(attribute, value)
        except ModelError:
            return "colour-read-only"
        return "colour"
    if WIDTH_NAME.search(attribute):
        try:
            number = float(value.strip())
        except ValueError:
            return "read-only"
        return "width" if math.isfinite(number) and number >= 0 else "read-only"
    return "read-only"


def default_explanation(element_name: str, attribute: str) -> str:
    """Provide an editable, deliberately modest front-end explanation."""

    attribute_words = humanise(attribute).casefold()
    element_words = humanise(element_name)
    if attribute.casefold() == "direction":
        return f"Advanced light direction vector for {element_words}; not a colour."
    if attribute.casefold() == "shadowcolor":
        return (
            f"Unverified signed shadow-lighting triplet for {element_words}; "
            "not shown as a normal colour."
        )
    return f"Draft: controls {attribute_words} for {element_words}."


def indexed_tree_from_xml(source: Path) -> dict[str, Any]:
    """Create a JSON tree that retains every XML element, text value, and attribute."""

    try:
        data = source.read_bytes()
        root = ET.fromstring(data)
    except (OSError, ET.ParseError) as exc:
        raise ModelError(f"Cannot translate {source}: {exc}") from exc

    def convert(element: ET.Element, path: str, index: int) -> dict[str, Any]:
        attributes: list[dict[str, Any]] = []
        for attribute_name, xml_value in element.attrib.items():
            name = local_name(attribute_name)
            field_id = f"{path}/@{name}"
            attributes.append(
                {
                    "field_id": field_id,
                    "attribute": name,
                    "xml_value": xml_value,
                    "working_value": xml_value,
                    "short_label": name,
                    "explanation": default_explanation(local_name(element.tag), name),
                    "mode": "",
                    "kind": field_kind(name, xml_value),
                    "history": [xml_value],
                    "history_index": 0,
                }
            )

        counts: dict[str, int] = {}
        children: list[dict[str, Any]] = []
        for child in element:
            child_name = local_name(child.tag)
            counts[child_name] = counts.get(child_name, 0) + 1
            children.append(
                convert(child, f"{path}/{child_name}[{counts[child_name]}]", counts[child_name])
            )
        text = (element.text or "").strip()
        return {
            "tag": local_name(element.tag),
            "index": index,
            "path": path,
            "text": text or None,
            "attributes": attributes,
            "children": children,
        }

    root_name = local_name(root.tag)
    return convert(root, f"/{root_name}[1]", 1)


def create_catalog(source: Path = SOURCE_XML, profile_name: str = "current-functions") -> dict[str, Any]:
    """Build the initial persistent front-end profile from the repository XML copy."""

    if not source.is_file():
        raise ModelError(f"The copied PhotoBooth source does not exist: {source}")
    return {
        "schema_version": SCHEMA_VERSION,
        "profile_name": profile_name,
        "source": {
            "path": str(source.relative_to(ROOT)),
            "sha256": sha256_file(source),
            "base_status": "unverified_current_file",
            "watermark": WATERMARK,
        },
        "tree": indexed_tree_from_xml(source),
    }


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    """Persist a JSON profile without leaving a partially written file."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
            stream.flush()
        temporary.replace(path)
    except OSError as exc:
        temporary.unlink(missing_ok=True)
        raise ModelError(f"Cannot save front-end JSON {path}: {exc}") from exc


def load_json(path: Path) -> dict[str, Any]:
    """Load a profile and validate only the required outer shape."""

    try:
        with path.open("r", encoding="utf-8") as stream:
            payload = json.load(stream)
    except (OSError, json.JSONDecodeError) as exc:
        raise ModelError(f"Cannot read settings JSON {path}: {exc}") from exc
    if (
        not isinstance(payload, dict)
        or payload.get("schema_version") != SCHEMA_VERSION
        or not isinstance(payload.get("tree"), dict)
        or not isinstance(payload.get("profile_name"), str)
    ):
        raise ModelError(f"{path} is not a supported {APP_NAME} settings file.")
    return payload


def initialise_catalog(path: Path = CATALOG_PATH, source: Path = SOURCE_XML) -> dict[str, Any]:
    """Create the requested translation once, then preserve front-end edits."""

    if path.exists():
        return load_json(path)
    catalog = create_catalog(source)
    write_json_atomic(path, catalog)
    return catalog


def walk_fields(node: dict[str, Any]) -> Iterator[tuple[dict[str, Any], dict[str, Any]]]:
    """Yield each exact attribute leaf together with its source XML node."""

    for attribute in node.get("attributes", []):
        yield node, attribute
    for child in node.get("children", []):
        yield from walk_fields(child)


def find_field(catalog: dict[str, Any], field_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Find one attribute leaf by its canonical identity."""

    for node, attribute in walk_fields(catalog["tree"]):
        if attribute["field_id"] == field_id:
            return node, attribute
    raise ModelError(f"Unknown XML setting: {field_id}")


def parse_colour(attribute: str, raw_value: str) -> ColourValue:
    """Validate normalised RGB, ARGB, and RGBA source values."""

    try:
        values = [float(item) for item in NUMBER_SPLIT.split(raw_value.strip()) if item]
    except ValueError as exc:
        raise ModelError("The colour value must contain numeric channels.") from exc
    if not all(math.isfinite(value) for value in values):
        raise ModelError("Colour channels must be finite numbers.")

    upper = attribute.upper()
    if "ARGB" in upper and len(values) == 4:
        alpha, red, green, blue = values
        encoding = "ARGB"
    elif "RGBA" in upper and len(values) == 4:
        red, green, blue, alpha = values
        encoding = "RGBA"
    elif ("RGB" in upper or "COLOR" in upper or "COLOUR" in upper) and len(values) == 3:
        red, green, blue = values
        alpha = None
        encoding = "RGB"
    else:
        raise ModelError(f"{attribute} is not a recognised RGB, ARGB, or RGBA value.")
    if not all(0.0 <= value <= 1.0 for value in (red, green, blue)):
        raise ModelError("Red, green, and blue must each be between 0.0 and 1.0.")
    if alpha is not None and not 0.0 <= alpha <= 1.0:
        raise ModelError("Alpha must be between 0.0 and 1.0.")
    return ColourValue(encoding, red, green, blue, alpha)


def format_colour(colour: ColourValue, original: str) -> str:
    """Format a revised colour in the original channel order and separator style."""

    values: list[float]
    if colour.encoding == "ARGB":
        assert colour.alpha is not None
        values = [colour.alpha, colour.red, colour.green, colour.blue]
    elif colour.encoding == "RGBA":
        assert colour.alpha is not None
        values = [colour.red, colour.green, colour.blue, colour.alpha]
    else:
        values = [colour.red, colour.green, colour.blue]
    separator = ", " if "," in original else " "
    return separator.join(format(value, ".6g") for value in values)


def colour_hex(colour: ColourValue) -> str:
    """Convert a normalised colour to a Tk-compatible RGB value."""

    return "#%02x%02x%02x" % (
        round(colour.red * 255),
        round(colour.green * 255),
        round(colour.blue * 255),
    )


def validate_working_value(field: dict[str, Any], value: str) -> str:
    """Validate an editable working value without modifying XML."""

    kind = field["kind"]
    if kind == "colour":
        parse_colour(field["attribute"], value)
        return value.strip()
    if kind == "width":
        try:
            width = float(value.strip())
        except ValueError as exc:
            raise ModelError("The width must be a non-negative number.") from exc
        if not math.isfinite(width) or width < 0:
            raise ModelError("The width must be a non-negative finite number.")
        return value.strip()
    raise ModelError(f"{field['attribute']} is read-only in the working model.")


def append_history(field: dict[str, Any], value: str) -> None:
    """Store every changed working value and make it the active history entry."""

    history = field.setdefault("history", [])
    if not history or history[-1] != value:
        history.append(value)
    field["history_index"] = len(history) - 1
    field["working_value"] = value


def profile_path_for_name(name: str) -> Path:
    """Create a safe repository profile file path from a display name."""

    filename = SAFE_FILENAME.sub("-", name).strip(" .-")
    if not filename:
        raise ModelError("Enter a settings-file name containing a letter or number.")
    return PROFILES_DIRECTORY / f"{filename}.json"


def available_profiles() -> dict[str, Path]:
    """Return the default catalog and all cloned front-end settings files."""

    profiles = {"current-functions": CATALOG_PATH}
    if PROFILES_DIRECTORY.is_dir():
        for path in sorted(PROFILES_DIRECTORY.glob("*.json")):
            try:
                payload = load_json(path)
            except ModelError:
                continue
            profiles[payload["profile_name"]] = path
    return profiles


def clone_profile(catalog: dict[str, Any], name: str) -> tuple[Path, dict[str, Any]]:
    """Clone current working values while clearing only fine-tuning histories."""

    destination = profile_path_for_name(name)
    if destination.exists():
        raise ModelError(f"A settings file already exists: {destination.name}")
    cloned = copy.deepcopy(catalog)
    cloned["profile_name"] = name
    for _, field in walk_fields(cloned["tree"]):
        field["history"] = [field["working_value"]]
        field["history_index"] = 0
    write_json_atomic(destination, cloned)
    return destination, cloned


def is_normalised_colour(field: dict[str, Any]) -> bool:
    """Return whether the field can use ordinary colour buttons."""

    return field.get("kind") == "colour"


class ChoiceDialog(tk.Toplevel):
    """A small explicit check/test startup dialog with meaningful button labels."""

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent)
        self.title("PhotoBooth base")
        self.resizable(False, False)
        self.result = "test"
        self.transient(parent)
        self.grab_set()

        ttk.Label(
            self,
            text="Do you want to check or just test the current functions?",
            wraplength=450,
            padding=(18, 18, 18, 10),
        ).pack()
        actions = ttk.Frame(self, padding=(18, 0, 18, 18))
        actions.pack(fill=tk.X)
        ttk.Button(actions, text="Check current base", command=lambda: self.choose("check")).pack(
            side=tk.LEFT
        )
        ttk.Button(actions, text="Test current functions", command=lambda: self.choose("test")).pack(
            side=tk.RIGHT
        )
        self.protocol("WM_DELETE_WINDOW", lambda: self.choose("test"))
        self.wait_window(self)

    def choose(self, result: str) -> None:
        """Close with the selected starting mode."""

        self.result = result
        self.destroy()


class PhotoBoothSettingsApp(tk.Tk):
    """Interactive front-end editor for working JSON values and metadata."""

    def __init__(self, catalog: dict[str, Any], catalog_path: Path) -> None:
        super().__init__()
        self.catalog = catalog
        self.catalog_path = catalog_path
        self.current_field_id: Optional[str] = None
        self.fine_tune_start: dict[str, str] = {}
        self.undo_stack: list[tuple[str, str, Any, Any]] = []
        self.redo_stack: list[tuple[str, str, Any, Any]] = []
        self.profile_var = tk.StringVar(value=catalog["profile_name"])
        self.status_var = tk.StringVar(value="Test mode: using the unverified repository copy.")
        self.short_label_var = tk.StringVar()
        self.value_var = tk.StringVar()
        self.mode_var = tk.StringVar()
        self._metadata_write_after: Optional[str] = None

        self.title(APP_NAME)
        self.geometry("1600x1000")
        self.minsize(1180, 760)
        self._build_ui()
        self.after(100, self._choose_start_mode)
        self.after(150, self.populate_tree)

    def _build_ui(self) -> None:
        """Construct the tree/grid, details, image frame, and control strips."""

        top = ttk.Frame(self, padding=8)
        top.pack(fill=tk.X)
        ttk.Label(top, text="Settings file:").pack(side=tk.LEFT)
        self.profile_box = ttk.Combobox(
            top,
            textvariable=self.profile_var,
            values=tuple(available_profiles()),
            width=30,
            state="readonly",
        )
        self.profile_box.pack(side=tk.LEFT, padx=(5, 8))
        self.profile_box.bind("<<ComboboxSelected>>", self.load_selected_profile)
        self.clone_button = ttk.Button(top, text="Clone new", command=self.clone_current_profile)
        self.clone_button.pack(side=tk.LEFT)
        ttk.Label(top, textvariable=self.status_var).pack(side=tk.LEFT, padx=(18, 0))

        watermark = tk.Label(
            self,
            text=WATERMARK,
            foreground="#a00000",
            background="#fff2f2",
            font=("Segoe UI", 14, "bold"),
            pady=6,
        )
        watermark.pack(fill=tk.X)

        splitter = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        splitter.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        left = ttk.Frame(splitter, padding=4)
        right = ttk.Frame(splitter, padding=4)
        splitter.add(left, weight=5)
        splitter.add(right, weight=6)

        tree_frame = ttk.LabelFrame(left, text="All copied XML values", padding=5)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        columns = ("short", "explanation", "value", "view", "mode")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="tree headings")
        self.tree.heading("#0", text="Setting")
        self.tree.heading("short", text="Short label")
        self.tree.heading("explanation", text="Explanation")
        self.tree.heading("value", text="Current raw value")
        self.tree.heading("view", text="View")
        self.tree.heading("mode", text="Mode")
        self.tree.column("#0", width=220, stretch=True)
        self.tree.column("short", width=110, stretch=False)
        self.tree.column("explanation", width=260, stretch=True)
        self.tree.column("value", width=180, stretch=True)
        self.tree.column("view", width=80, stretch=False)
        self.tree.column("mode", width=115, stretch=False)
        scroll_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scroll_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        scroll_y.grid(row=0, column=1, sticky=tk.NS)
        scroll_x.grid(row=1, column=0, sticky=tk.EW)
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.bind("<Motion>", self.on_tree_hover)
        self.tree.bind("<Leave>", lambda _: self.render_preview())

        detail = ttk.LabelFrame(left, text="Selected attribute", padding=7)
        detail.pack(fill=tk.X, pady=(8, 0))
        ttk.Label(detail, text="Short label").grid(row=0, column=0, sticky=tk.W)
        short_entry = ttk.Entry(detail, textvariable=self.short_label_var)
        short_entry.grid(row=0, column=1, sticky=tk.EW, padx=(8, 0))
        ttk.Label(detail, text="Mode").grid(row=1, column=0, sticky=tk.W, pady=(6, 0))
        mode_entry = ttk.Entry(detail, textvariable=self.mode_var)
        mode_entry.grid(row=1, column=1, sticky=tk.EW, padx=(8, 0), pady=(6, 0))
        ttk.Label(detail, text="Raw value").grid(row=2, column=0, sticky=tk.W, pady=(6, 0))
        self.value_entry = ttk.Entry(detail, textvariable=self.value_var)
        self.value_entry.grid(row=2, column=1, sticky=tk.EW, padx=(8, 0), pady=(6, 0))
        ttk.Label(detail, text="Explanation").grid(row=3, column=0, sticky=tk.NW, pady=(6, 0))
        self.explanation = tk.Text(detail, height=3, wrap=tk.WORD)
        self.explanation.grid(row=3, column=1, sticky=tk.EW, padx=(8, 0), pady=(6, 0))
        detail.columnconfigure(1, weight=1)
        short_entry.bind("<FocusOut>", self.commit_metadata)
        mode_entry.bind("<FocusOut>", self.commit_metadata)
        self.explanation.bind("<FocusOut>", self.commit_metadata)
        self.value_entry.bind("<Return>", self.commit_value)
        self.value_entry.bind("<FocusOut>", self.commit_value)

        controls = ttk.LabelFrame(right, text="Image-frame controls", padding=6)
        controls.pack(fill=tk.X)
        self.control_buttons: list[ttk.Button] = []
        first = ttk.Frame(controls)
        first.pack(fill=tk.X)
        self.add_adjust_button(first, "Darker", "darker", menu_kind="brightness")
        self.add_adjust_button(first, "Lighter", "lighter", menu_kind="brightness")
        second = ttk.Frame(controls)
        second.pack(fill=tk.X, pady=(4, 0))
        for label, action in (
            ("More red", "red+"),
            ("Less red", "red-"),
            ("More green", "green+"),
            ("Less green", "green-"),
            ("More blue", "blue+"),
            ("Less blue", "blue-"),
        ):
            self.add_adjust_button(second, label, action, menu_kind="channel")
        third = ttk.Frame(controls)
        third.pack(fill=tk.X, pady=(4, 0))
        self.alpha_buttons: list[ttk.Button] = []
        self.add_adjust_button(third, "More opaque", "alpha+", menu_kind="alpha", alpha=True)
        self.add_adjust_button(third, "Less opaque", "alpha-", menu_kind="alpha", alpha=True)

        preview_shell = ttk.LabelFrame(right, text="Image frame — logical 3140 × 2100", padding=5)
        preview_shell.pack(fill=tk.BOTH, expand=True, pady=(8, 0))
        self.preview = tk.Canvas(preview_shell, background="#eeeeee", highlightthickness=1)
        self.preview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.history_canvas = tk.Canvas(
            preview_shell, width=82, background="#f5f5f5", highlightthickness=1
        )
        self.history_canvas.pack(side=tk.RIGHT, fill=tk.Y, padx=(6, 0))
        self.preview.bind("<Configure>", lambda _: self.render_preview())
        self.history_canvas.bind("<Button-1>", self.choose_history_entry)

        bottom = ttk.Frame(right)
        bottom.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(bottom, text="Previous", command=lambda: self.step_history(-1)).pack(side=tk.LEFT)
        ttk.Button(bottom, text="Next", command=lambda: self.step_history(1)).pack(
            side=tk.LEFT, padx=(6, 0)
        )
        ttk.Button(bottom, text="Cancel", command=self.cancel_fine_tune).pack(
            side=tk.RIGHT
        )
        ttk.Button(bottom, text="Accept and implement", command=self.accept_and_implement).pack(
            side=tk.RIGHT, padx=(6, 0)
        )
        ttk.Button(bottom, text="Accept", command=self.accept_fine_tune).pack(
            side=tk.RIGHT
        )
        self.bind_all("<Control-z>", self.undo)
        self.bind_all("<Control-y>", self.redo)
        self.bind_all("<Control-Shift-Z>", self.redo)

    def add_adjust_button(
        self, parent: ttk.Frame, label: str, action: str, menu_kind: str, alpha: bool = False
    ) -> None:
        """Create an adjustment button whose menu supplies one of the agreed steps."""

        button = ttk.Button(
            parent,
            text=label,
            command=lambda: self.show_adjustment_menu(button, action, menu_kind),
        )
        button.pack(side=tk.LEFT, padx=(0, 4))
        self.control_buttons.append(button)
        if alpha:
            self.alpha_buttons.append(button)

    def _choose_start_mode(self) -> None:
        """Immediately offer the requested current-base check or test mode."""

        choice = ChoiceDialog(self).result
        if choice == "check":
            self.check_current_base()
        else:
            self.status_var.set("Test mode: current repository copy remains unverified.")

    def check_current_base(self) -> None:
        """Run read-only active-target discovery and compare its candidate hash."""

        try:
            import fusion_environment_editor as finder

            result = finder.discover()
            payload = finder.report_payload(result)
            active = [
                candidate
                for candidate in payload["candidates"]
                if candidate["classification"] == "active"
            ]
            if len(active) != 1:
                self.status_var.set(
                    "Check incomplete: discovery did not prove one active PhotoBooth target."
                )
                messagebox.showwarning(
                    "Base check incomplete",
                    "The read-only finder did not prove one active PhotoBooth target. "
                    "The GUI remains in unverified test mode.",
                    parent=self,
                )
                return
            source_hash = self.catalog["source"]["sha256"]
            active_hash = active[0]["sha256"]
            matches = source_hash.casefold() == active_hash.casefold()
            result_text = (
                "The repository copy hash matches the active candidate."
                if matches
                else "The repository copy hash differs from the active candidate."
            )
            self.status_var.set(
                f"Read-only base check: {result_text} Visual correctness is still unverified."
            )
            messagebox.showinfo(
                "Base check result",
                f"{result_text}\n\nActive target:\n{active[0]['xml_path']}\n\n"
                f"Active SHA-256:\n{active_hash}\n\n"
                "No XML file was changed. The watermark remains until visual validation exists.",
                parent=self,
            )
        except Exception as exc:
            self.status_var.set("Check failed; continuing in unverified test mode.")
            messagebox.showerror(
                "Base check failed",
                f"Could not complete read-only discovery:\n{exc}",
                parent=self,
            )

    def current_field(self) -> Optional[dict[str, Any]]:
        """Return the selected attribute record, if the tree selection is a leaf."""

        if self.current_field_id is None:
            return None
        try:
            _, field = find_field(self.catalog, self.current_field_id)
        except ModelError:
            return None
        return field

    def populate_tree(self) -> None:
        """Display every copied XML element and attribute, omitting only root visually."""

        selected = self.current_field_id
        for item in self.tree.get_children():
            self.tree.delete(item)

        def add_node(node: dict[str, Any], parent: str) -> None:
            node_id = f"node:{node['path']}"
            self.tree.insert(parent, tk.END, iid=node_id, text=node["tag"], open=True)
            if node["text"] is not None:
                self.tree.insert(
                    node_id,
                    tk.END,
                    iid=f"text:{node['path']}",
                    text="#text",
                    values=("", "", node["text"], "", ""),
                )
            for attribute in node["attributes"]:
                view = self.view_text(attribute)
                self.tree.insert(
                    node_id,
                    tk.END,
                    iid=attribute["field_id"],
                    text=f"@{attribute['attribute']}",
                    values=(
                        attribute["short_label"],
                        attribute["explanation"],
                        attribute["working_value"],
                        view,
                        attribute["mode"],
                    ),
                )
            for child in node["children"]:
                add_node(child, node_id)

        for attribute in self.catalog["tree"]["attributes"]:
            self.tree.insert(
                "",
                tk.END,
                iid=attribute["field_id"],
                text=f"@{attribute['attribute']}",
                values=(
                    attribute["short_label"],
                    attribute["explanation"],
                    attribute["working_value"],
                    self.view_text(attribute),
                    attribute["mode"],
                ),
            )
        for child in self.catalog["tree"]["children"]:
            add_node(child, "")
        if selected and self.tree.exists(selected):
            self.tree.selection_set(selected)
            self.tree.focus(selected)
            self.tree.see(selected)
        self.refresh_profile_list()

    def view_text(self, field: dict[str, Any]) -> str:
        """Describe a compact per-row visual cell in the standard tree widget."""

        if field["kind"] == "colour":
            try:
                return f"■ {colour_hex(parse_colour(field['attribute'], field['working_value']))}"
            except ModelError:
                return "invalid"
        if field["kind"] == "width":
            return "━━"
        if field["kind"] == "signed-unverified":
            return "?"
        if field["kind"] == "direction-read-only":
            return "↗"
        return ""

    def on_tree_select(self, _: object = None) -> None:
        """Load a selected attribute leaf into editable metadata/value controls."""

        selected = self.tree.selection()
        if not selected or selected[0].startswith(("node:", "text:")):
            return
        field_id = selected[0]
        try:
            _, field = find_field(self.catalog, field_id)
        except ModelError:
            return
        self.current_field_id = field_id
        self.fine_tune_start.setdefault(field_id, field["working_value"])
        self.short_label_var.set(field["short_label"])
        self.mode_var.set(field["mode"])
        self.value_var.set(field["working_value"])
        self.explanation.delete("1.0", tk.END)
        self.explanation.insert("1.0", field["explanation"])
        editable = field["kind"] in {"colour", "width"}
        self.value_entry.configure(state=tk.NORMAL if editable else tk.DISABLED)
        for button in self.control_buttons:
            button.configure(state=tk.NORMAL if field["kind"] == "colour" else tk.DISABLED)
        for button in self.alpha_buttons:
            button.configure(
                state=tk.NORMAL
                if field["kind"] == "colour"
                and parse_colour(field["attribute"], field["working_value"]).alpha is not None
                else tk.DISABLED
            )
        self.render_preview()
        self.render_history()

    def on_tree_hover(self, event: tk.Event[tk.Misc]) -> None:
        """Temporarily preview a hovered attribute without changing the selection."""

        item = self.tree.identify_row(event.y)
        if item and not item.startswith("node:"):
            self.render_preview(item)

    def commit_metadata(self, _: object = None) -> None:
        """Save changed front-end text immediately, never to the XML source."""

        field = self.current_field()
        if field is None:
            return
        changes = {
            "short_label": self.short_label_var.get().strip() or field["attribute"],
            "mode": self.mode_var.get().strip(),
            "explanation": self.explanation.get("1.0", tk.END).strip(),
        }
        changed = False
        for key, value in changes.items():
            if field[key] != value:
                self.undo_stack.append((field["field_id"], key, field[key], value))
                field[key] = value
                changed = True
        if changed:
            self.redo_stack.clear()
            self.save_catalog()
            self.populate_tree()

    def commit_value(self, _: object = None) -> None:
        """Commit a direct raw-value edit only when it validates."""

        field = self.current_field()
        if field is None or field["kind"] not in {"colour", "width"}:
            return
        previous = field["working_value"]
        try:
            value = validate_working_value(field, self.value_var.get())
        except ModelError as exc:
            self.value_var.set(previous)
            self.bell()
            self.status_var.set(f"Invalid value restored: {exc}")
            return
        if value != previous:
            append_history(field, value)
            self.save_catalog()
            self.status_var.set("Working value updated in the front-end JSON; XML unchanged.")
            self.populate_tree()
            if self.tree.exists(field["field_id"]):
                self.tree.selection_set(field["field_id"])
            self.on_tree_select()

    def show_adjustment_menu(
        self, button: ttk.Button, action: str, menu_kind: str
    ) -> None:
        """Show the agreed method/step choice for a colour adjustment."""

        field = self.current_field()
        if field is None or not is_normalised_colour(field):
            return
        menu = tk.Menu(self, tearoff=False)
        if menu_kind == "brightness":
            for method, label in (
                ("scale", "Preserve hue"),
                ("fixed", "Fixed channel adjustment"),
            ):
                nested = tk.Menu(menu, tearoff=False)
                for amount in (5, 10, 20):
                    nested.add_command(
                        label=f"{amount}%",
                        command=lambda m=method, a=amount: self.adjust_colour(action, a, m),
                    )
                menu.add_cascade(label=label, menu=nested)
        else:
            for amount in (5, 10, 20):
                menu.add_command(
                    label=f"{amount}%",
                    command=lambda a=amount: self.adjust_colour(action, a, "fixed"),
                )
        menu.tk_popup(button.winfo_rootx(), button.winfo_rooty() + button.winfo_height())

    def adjust_colour(self, action: str, percent: int, method: str) -> None:
        """Apply one requested RGB/alpha adjustment to the selected working value."""

        field = self.current_field()
        if field is None:
            return
        try:
            colour = parse_colour(field["attribute"], field["working_value"])
        except ModelError:
            return
        factor = percent / 100
        red, green, blue = colour.red, colour.green, colour.blue
        alpha = colour.alpha
        if action in {"darker", "lighter"}:
            if method == "scale":
                multiplier = 1 - factor if action == "darker" else 1 + factor
                red, green, blue = (
                    max(0.0, min(1.0, channel * multiplier))
                    for channel in (red, green, blue)
                )
            else:
                delta = -factor if action == "darker" else factor
                red, green, blue = (
                    max(0.0, min(1.0, channel + delta))
                    for channel in (red, green, blue)
                )
        elif action.endswith("+") or action.endswith("-"):
            delta = factor if action.endswith("+") else -factor
            if action.startswith("red"):
                red = max(0.0, min(1.0, red + delta))
            elif action.startswith("green"):
                green = max(0.0, min(1.0, green + delta))
            elif action.startswith("blue"):
                blue = max(0.0, min(1.0, blue + delta))
            elif action.startswith("alpha") and alpha is not None:
                alpha = max(0.0, min(1.0, alpha + delta))
            else:
                return
        revised = ColourValue(colour.encoding, red, green, blue, alpha)
        value = format_colour(revised, field["working_value"])
        append_history(field, value)
        self.value_var.set(value)
        self.save_catalog()
        self.status_var.set("Working colour updated in the front-end JSON; XML unchanged.")
        self.populate_tree()
        self.tree.selection_set(field["field_id"])
        self.on_tree_select()

    def step_history(self, direction: int) -> None:
        """Move through the selected row's persisted fine-tuning alternatives."""

        field = self.current_field()
        if field is None:
            return
        history = field.get("history", [])
        index = field.get("history_index", len(history) - 1)
        target = max(0, min(len(history) - 1, index + direction))
        if not history or target == index:
            return
        field["history_index"] = target
        field["working_value"] = history[target]
        self.value_var.set(field["working_value"])
        self.save_catalog()
        self.populate_tree()
        self.tree.selection_set(field["field_id"])
        self.on_tree_select()

    def choose_history_entry(self, event: tk.Event[tk.Misc]) -> None:
        """Restore a clicked history candidate from the vertical strip."""

        field = self.current_field()
        if field is None:
            return
        history = field.get("history", [])
        height = max(1, self.history_canvas.winfo_height())
        if not history:
            return
        index = min(len(history) - 1, int(event.y / max(1, height / len(history))))
        field["history_index"] = index
        field["working_value"] = history[index]
        self.value_var.set(field["working_value"])
        self.save_catalog()
        self.populate_tree()
        self.tree.selection_set(field["field_id"])
        self.on_tree_select()

    def cancel_fine_tune(self) -> None:
        """Restore only the selected row to its value at fine-tune start."""

        field = self.current_field()
        if field is None:
            return
        starting_value = self.fine_tune_start.get(field["field_id"])
        if starting_value is None:
            return
        field["working_value"] = starting_value
        history = field.setdefault("history", [])
        if starting_value in history:
            field["history_index"] = history.index(starting_value)
        else:
            history.append(starting_value)
            field["history_index"] = len(history) - 1
        self.value_var.set(starting_value)
        self.save_catalog()
        self.status_var.set("Cancelled this row's fine-tuning; other profile values remain unchanged.")
        self.populate_tree()
        self.tree.selection_set(field["field_id"])
        self.on_tree_select()

    def accept_fine_tune(self) -> None:
        """Accept the selected working value into the autosaved front-end profile."""

        field = self.current_field()
        if field is None:
            return
        self.fine_tune_start[field["field_id"]] = field["working_value"]
        self.save_catalog()
        self.status_var.set("Accepted in the settings file. No Fusion XML was written.")

    def accept_and_implement(self) -> None:
        """Make the unavailable XML-write route explicit rather than faking it."""

        messagebox.showinfo(
            "Accept and implement",
            "The active settings file is saved, but XML implementation is intentionally "
            "not available yet. It requires the separate validated-copy transaction "
            "workflow and a full preview/confirmation.",
            parent=self,
        )

    def render_preview(self, preview_field_id: Optional[str] = None) -> None:
        """Draw a scalable two-cube approximation with selection emphasis."""

        canvas = self.preview
        canvas.delete("all")
        width = max(1, canvas.winfo_width())
        height = max(1, canvas.winfo_height())
        target_ratio = 3140 / 2100
        if width / height > target_ratio:
            frame_height = height
            frame_width = int(height * target_ratio)
        else:
            frame_width = width
            frame_height = int(width / target_ratio)
        offset_x = (width - frame_width) // 2
        offset_y = (height - frame_height) // 2

        selected_id = preview_field_id or self.current_field_id
        field: Optional[dict[str, Any]] = None
        if selected_id:
            try:
                _, field = find_field(self.catalog, selected_id)
            except ModelError:
                field = None

        background = "#e8e8e8"
        accent = "#2070b8"
        if field and field["kind"] == "colour":
            try:
                candidate = colour_hex(parse_colour(field["attribute"], field["working_value"]))
                identity = field["field_id"].casefold()
                if "background" in identity:
                    background = candidate
                else:
                    accent = candidate
            except ModelError:
                pass
        canvas.create_rectangle(
            offset_x, offset_y, offset_x + frame_width, offset_y + frame_height, fill=background, outline=""
        )
        grid_colour = "#9d9d9d"
        for fraction in range(1, 10):
            x = offset_x + frame_width * fraction // 10
            y = offset_y + frame_height * fraction // 10
            canvas.create_line(x, offset_y, x, offset_y + frame_height, fill=grid_colour)
            canvas.create_line(offset_x, y, offset_x + frame_width, y, fill=grid_colour)

        def cube(left: int, top: int, size: int, line: str, selected: bool, label: str) -> None:
            front = [(left, top), (left + size, top), (left + size, top + size), (left, top + size)]
            shift_x, shift_y = size // 3, -size // 4
            back = [(x + shift_x, y + shift_y) for x, y in front]
            points = [
                *front,
                front[0],
                *back,
                back[0],
            ]
            canvas.create_line(*sum(points, ()), fill=line, width=5 if selected else 2)
            for front_point, back_point in zip(front, back):
                canvas.create_line(*front_point, *back_point, fill=line, width=5 if selected else 2)
            canvas.create_text(left + size // 2, top + size + 35, text=label, font=("Segoe UI", 11, "bold"))

        identity = field["field_id"].casefold() if field else ""
        sketch_selected = "sketch" in identity or "dimension" in identity or "inference" in identity
        design_selected = (
            not sketch_selected
            and any(word in identity for word in ("select", "highlight", "adorner", "grid", "background"))
        )
        cube(
            offset_x + frame_width // 8,
            offset_y + frame_height // 3,
            min(frame_width, frame_height) // 4,
            accent if design_selected else "#454545",
            design_selected,
            "Design cube",
        )
        cube(
            offset_x + frame_width * 5 // 8,
            offset_y + frame_height // 3,
            min(frame_width, frame_height) // 4,
            accent if sketch_selected else "#454545",
            sketch_selected,
            "Sketch cube",
        )
        if field:
            callout = f"{field['short_label']}: {field['working_value']}"
            canvas.create_rectangle(
                offset_x + 18,
                offset_y + 18,
                offset_x + min(frame_width - 18, 550),
                offset_y + 65,
                outline="#ff00b3",
                width=4,
                fill="#ffffff",
            )
            canvas.create_text(
                offset_x + 30,
                offset_y + 41,
                anchor=tk.W,
                text=callout,
                width=min(frame_width - 70, 490),
            )
        canvas.create_text(
            offset_x + frame_width // 2,
            offset_y + frame_height // 2,
            text=WATERMARK,
            fill="#b00000",
            font=("Segoe UI", max(12, min(frame_width, frame_height) // 24), "bold"),
        )

    def render_history(self) -> None:
        """Draw colour swatches or compact samples for the selected row's history."""

        canvas = self.history_canvas
        canvas.delete("all")
        field = self.current_field()
        if field is None:
            return
        history = field.get("history", [])
        if not history:
            return
        height = max(1, canvas.winfo_height())
        entry_height = max(18, height // len(history))
        for index, value in enumerate(history):
            top = index * entry_height
            bottom = min(height, top + entry_height - 2)
            selected = index == field.get("history_index", len(history) - 1)
            if field["kind"] == "colour":
                try:
                    fill = colour_hex(parse_colour(field["attribute"], value))
                except ModelError:
                    fill = "#aaaaaa"
                canvas.create_rectangle(8, top + 4, 72, bottom - 4, fill=fill, outline="#000000", width=3 if selected else 1)
            elif field["kind"] == "width":
                canvas.create_line(12, (top + bottom) // 2, 68, (top + bottom) // 2, width=4 if selected else 2)
            else:
                canvas.create_rectangle(8, top + 4, 72, bottom - 4, fill="#dddddd", outline="#000000", width=3 if selected else 1)

    def refresh_profile_list(self) -> None:
        """Refresh the settings-file dropdown after catalog/profile changes."""

        profiles = available_profiles()
        self.profile_box.configure(values=tuple(profiles))
        if self.profile_var.get() not in profiles:
            self.profile_var.set(self.catalog["profile_name"])

    def load_selected_profile(self, _: object = None) -> None:
        """Load an explicitly selected front-end JSON profile."""

        profiles = available_profiles()
        path = profiles.get(self.profile_var.get())
        if path is None:
            return
        try:
            self.catalog = load_json(path)
            self.catalog_path = path
        except ModelError as exc:
            messagebox.showerror("Cannot load settings file", str(exc), parent=self)
            return
        self.current_field_id = None
        self.fine_tune_start.clear()
        self.status_var.set(f"Loaded settings file {path.name}; XML unchanged.")
        self.populate_tree()

    def clone_current_profile(self) -> None:
        """Prompt for a unique cloned settings-file name."""

        name = simpledialog.askstring(
            "Clone settings file",
            "Display name for the new JSON settings file:",
            parent=self,
        )
        if name is None:
            return
        try:
            path, catalog = clone_profile(self.catalog, name)
        except ModelError as exc:
            messagebox.showerror("Cannot clone settings file", str(exc), parent=self)
            return
        self.catalog = catalog
        self.catalog_path = path
        self.profile_var.set(catalog["profile_name"])
        self.status_var.set(f"Cloned current working values to {path.name}.")
        self.populate_tree()

    def save_catalog(self) -> None:
        """Persist all front-end work immediately to the selected JSON file."""

        write_json_atomic(self.catalog_path, self.catalog)

    def undo(self, _: object = None) -> str:
        """Undo current-session metadata edits while preserving their JSON save."""

        if not self.undo_stack:
            return "break"
        field_id, key, before, after = self.undo_stack.pop()
        _, field = find_field(self.catalog, field_id)
        field[key] = before
        self.redo_stack.append((field_id, key, before, after))
        self.save_catalog()
        self.populate_tree()
        self.tree.selection_set(field_id)
        self.on_tree_select()
        return "break"

    def redo(self, _: object = None) -> str:
        """Redo current-session metadata edits while preserving their JSON save."""

        if not self.redo_stack:
            return "break"
        field_id, key, before, after = self.redo_stack.pop()
        _, field = find_field(self.catalog, field_id)
        field[key] = after
        self.undo_stack.append((field_id, key, before, after))
        self.save_catalog()
        self.populate_tree()
        self.tree.selection_set(field_id)
        self.on_tree_select()
        return "break"


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Initialise the one-to-one translation or run the working-model GUI."""

    parser = argparse.ArgumentParser(description=APP_NAME)
    parser.add_argument(
        "--initialize",
        action="store_true",
        help="create config/settings_catalog.json without opening the GUI",
    )
    arguments = parser.parse_args(argv)
    catalog = initialise_catalog()
    if arguments.initialize:
        print(f"Initialised {CATALOG_PATH}")
        print(f"Source SHA-256: {catalog['source']['sha256']}")
        return 0
    application = PhotoBoothSettingsApp(catalog, CATALOG_PATH)
    application.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
