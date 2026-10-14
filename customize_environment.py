from __future__ import annotations

import os
import re
import stat
import tempfile
from dataclasses import dataclass
from xml.etree import ElementTree


COLOR_VALUE = re.compile(r"(?P<prefix>#|0[xX])(?P<hex>[0-9a-fA-F]{6}(?:[0-9a-fA-F]{2})?)$")


@dataclass
class ColorReference:
    element: ElementTree.Element
    location: str
    value: str
    attribute: str | None = None

    def set_value(self, value: str) -> None:
        if self.attribute is None:
            self.element.text = value
        else:
            self.element.set(self.attribute, value)
        self.value = value


def find_colors(root: ElementTree.Element) -> list[ColorReference]:
    colors = []

    def visit(element: ElementTree.Element, path: str) -> None:
        for attribute, value in element.attrib.items():
            if COLOR_VALUE.fullmatch(value.strip()):
                colors.append(
                    ColorReference(element, f"{path}/@{attribute}", value, attribute)
                )
        if element.text and COLOR_VALUE.fullmatch(element.text.strip()):
            colors.append(ColorReference(element, path, element.text))

        counts = {}
        for child in element:
            counts[child.tag] = counts.get(child.tag, 0) + 1
            child_path = f"{path}/{child.tag}[{counts[child.tag]}]"
            visit(child, child_path)

    visit(root, f"/{root.tag}[1]")
    return colors


def choose_color(reference: ColorReference, chosen: str) -> str:
    original = reference.value
    stripped_value = original.strip()
    match = COLOR_VALUE.fullmatch(stripped_value)
    if not match:
        raise ValueError(f"Unsupported color value: {reference.value}")
    hex_value = chosen.lstrip("#")
    if not re.fullmatch(r"[0-9a-fA-F]{6}", hex_value):
        raise ValueError(f"Expected an RGB color, got: {chosen}")
    if len(match.group("hex")) == 8:
        hex_value += match.group("hex")[6:]
    if match.group("hex") == match.group("hex").upper():
        hex_value = hex_value.upper()
    leading_whitespace = original[: len(original) - len(original.lstrip())]
    trailing_whitespace = original[len(original.rstrip()) :]
    return (
        f"{leading_whitespace}{match.group('prefix')}{hex_value}"
        f"{trailing_whitespace}"
    )


def save_xml(tree: ElementTree.ElementTree, path: str) -> None:
    directory = os.path.dirname(os.path.abspath(path))
    permissions = stat.S_IMODE(os.stat(path).st_mode) if os.path.exists(path) else None
    file_descriptor, temporary_path = tempfile.mkstemp(
        dir=directory, prefix=".photobooth-", suffix=".xml"
    )
    os.close(file_descriptor)
    try:
        tree.write(temporary_path, encoding="utf-8", xml_declaration=True)
        if permissions is not None:
            os.chmod(temporary_path, permissions)
        os.replace(temporary_path, path)
    except Exception:
        if os.path.exists(temporary_path):
            os.remove(temporary_path)
        raise


class CustomizeEnvironment:
    def __init__(self, root: tk.Tk):
        from tkinter import colorchooser, filedialog, messagebox, ttk

        self.root = root
        self.colorchooser = colorchooser
        self.filedialog = filedialog
        self.messagebox = messagebox
        self.root.title("Customize Fusion Environment")
        self.tree: ElementTree.ElementTree | None = None
        self.path: str | None = None
        self.colors: list[ColorReference] = []

        toolbar = ttk.Frame(root, padding=8)
        toolbar.pack(fill="x")
        ttk.Button(toolbar, text="Open PhotoBooth.xml", command=self.open_file).pack(
            side="left"
        )
        ttk.Button(toolbar, text="Save", command=self.save_file).pack(side="left", padx=8)

        self.table = ttk.Treeview(
            root, columns=("location", "value"), show="headings", height=18
        )
        self.table.heading("location", text="XML location")
        self.table.heading("value", text="Color")
        self.table.column("location", width=500)
        self.table.column("value", width=130)
        self.table.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.table.bind("<Double-1>", self.edit_color)

        self.status = ttk.Label(root, text="Open a PhotoBooth.xml file to get started.")
        self.status.pack(fill="x", padx=8, pady=(0, 8))

    def open_file(self) -> None:
        path = self.filedialog.askopenfilename(
            title="Open PhotoBooth.xml",
            filetypes=(("XML files", "*.xml"), ("All files", "*")),
        )
        if not path:
            return
        try:
            tree = ElementTree.parse(path)
        except (OSError, ElementTree.ParseError) as error:
            self.messagebox.showerror("Unable to open XML", str(error))
            return
        self.tree = tree
        self.path = path
        self.colors = find_colors(tree.getroot())
        self.refresh_table()
        self.status.configure(
            text=f"{os.path.basename(path)} — {len(self.colors)} editable colors"
        )

    def refresh_table(self) -> None:
        self.table.delete(*self.table.get_children())
        for index, reference in enumerate(self.colors):
            self.table.insert(
                "", "end", iid=str(index), values=(reference.location, reference.value)
            )

    def edit_color(self, _event: tk.Event) -> None:
        selected = self.table.selection()
        if not selected:
            return
        reference = self.colors[int(selected[0])]
        value = reference.value.strip()
        matched = COLOR_VALUE.fullmatch(value)
        current_color = f"#{matched.group('hex')[:6]}" if matched else None
        chosen, _ = self.colorchooser.askcolor(color=current_color, parent=self.root)
        if chosen is None:
            return
        reference.set_value(choose_color(reference, chosen))
        self.refresh_table()
        self.table.selection_set(selected[0])

    def save_file(self) -> None:
        if self.tree is None or self.path is None:
            self.messagebox.showinfo("Nothing to save", "Open a PhotoBooth.xml file first.")
            return
        try:
            save_xml(self.tree, self.path)
        except OSError as error:
            self.messagebox.showerror("Unable to save XML", str(error))
            return
        self.status.configure(text=f"Saved {os.path.basename(self.path)}")


def main() -> None:
    import tkinter as tk

    root = tk.Tk()
    CustomizeEnvironment(root)
    root.mainloop()


if __name__ == "__main__":
    main()
