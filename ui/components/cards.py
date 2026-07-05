"""Componentes reutilizables: Cards KPI, badges de riesgo, etc."""

from __future__ import annotations

import customtkinter as ctk
from tkinter import ttk

from config import COLORS, FONTS


def filter_options(options: list[str], query: str) -> list[str]:
    """Filtra opciones por coincidencia parcial sin distinguir mayúsculas."""
    text = (query or "").strip().lower()
    if not text:
        return list(options)
    return [option for option in options if text in option.lower()]


class AutocompleteEntry(ctk.CTkFrame):
    """Campo de entrada con sugerencias desplegables."""

    def __init__(self, master, values: list[str], placeholder_text: str = "Buscar...", height: int = 38,
                 font=None, on_select=None, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._values = list(values)
        self._on_select = on_select
        self._selected_value = ""
        self._font = font or FONTS["body"]
        self._height = height
        self._build(placeholder_text)

    def _build(self, placeholder_text: str) -> None:
        self._container = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_card"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=8,
        )
        self._container.pack(fill="x")

        self._entry = ctk.CTkEntry(
            self._container,
            placeholder_text=placeholder_text,
            border_width=0,
            fg_color="transparent",
            font=self._font,
            height=self._height,
        )
        self._entry.pack(side="left", fill="x", expand=True, padx=(10, 8), pady=6)
        self._entry.bind("<KeyRelease>", self._on_key_release)

        self._suggestions = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_card"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=8,
        )
        self._suggestions.pack(fill="x", pady=(4, 0))
        self._suggestions.pack_forget()

    def _on_key_release(self, _event=None) -> None:
        query = self._entry.get()
        self._selected_value = query if query in self._values else ""
        self._render_suggestions(query)
        if self._on_select:
            self._on_select(query)

    def _render_suggestions(self, query: str) -> None:
        for child in self._suggestions.winfo_children():
            child.destroy()

        matches = filter_options(self._values, query)
        if not query or not matches:
            self._suggestions.pack_forget()
            return

        for option in matches[:8]:
            ctk.CTkButton(
                self._suggestions,
                text=option,
                fg_color="transparent",
                hover_color=COLORS["bg_main"],
                text_color=COLORS["text_primary"],
                anchor="w",
                height=32,
                corner_radius=6,
                command=lambda value=option: self._select_option(value),
            ).pack(fill="x", padx=6, pady=2)
        self._suggestions.pack(fill="x")

    def _select_option(self, value: str) -> None:
        self._selected_value = value
        self._entry.delete(0, "end")
        self._entry.insert(0, value)
        self._suggestions.pack_forget()

    def set(self, value: str) -> None:
        self._selected_value = value if value in self._values else ""
        self._entry.delete(0, "end")
        self._entry.insert(0, value)

    def get(self) -> str:
        return self._entry.get().strip()

    def get_selected_value(self) -> str:
        current = self.get()
        if current in self._values:
            return current
        return self._selected_value


class KPICard(ctk.CTkFrame):
    """Tarjeta de indicador clave de rendimiento."""

    def __init__(
        self,
        master,
        title: str,
        value: str,
        subtitle: str = "",
        icon: str = "",
        accent_color: str = COLORS["primary"],
        **kwargs,
    ) -> None:
        super().__init__(
            master,
            fg_color=COLORS["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
            **kwargs,
        )
        self._accent_color = accent_color
        self._content = None
        self._icon_label = None
        self._subtitle_label = None
        self._build(title, value, subtitle, icon, accent_color)

    def _build(self, title, value, subtitle, icon, accent):
        # Barra de acento superior
        self._accent_bar = ctk.CTkFrame(self, height=4, fg_color=accent, corner_radius=0)
        self._accent_bar.pack(fill="x", side="top")

        self._content = ctk.CTkFrame(self, fg_color="transparent")
        self._content.pack(fill="both", expand=True, padx=16, pady=12)

        # Icono + título
        header = ctk.CTkFrame(self._content, fg_color="transparent")
        header.pack(fill="x")
        if icon:
            self._icon_label = ctk.CTkLabel(
                header, text=icon, font=("Segoe UI Emoji", 20),
                text_color=accent,
            )
            self._icon_label.pack(side="left", padx=(0, 8))
        self._title_label = ctk.CTkLabel(
            header, text=title, font=FONTS["body"],
            text_color=COLORS["text_secondary"],
        )
        self._title_label.pack(side="left")

        # Valor principal
        self._value_label = ctk.CTkLabel(
            self._content, text=value,
            font=FONTS["heading_lg"],
            text_color=COLORS["text_primary"],
        )
        self._value_label.pack(anchor="w", pady=(6, 0))

        # Subtítulo
        if subtitle:
            self._subtitle_label = ctk.CTkLabel(
                self._content, text=subtitle,
                font=FONTS["body_sm"],
                text_color=COLORS["text_light"],
            )
            self._subtitle_label.pack(anchor="w")

    def update_value(self, new_value: str) -> None:
        self._value_label.configure(text=new_value)

    def update_card(
        self,
        title: str,
        value: str,
        subtitle: str = "",
        icon: str = "",
        accent_color: str | None = None,
    ) -> None:
        self._title_label.configure(text=title)
        self._value_label.configure(text=value)

        if self._subtitle_label is not None:
            self._subtitle_label.configure(text=subtitle)
            if subtitle:
                self._subtitle_label.pack(anchor="w")
            else:
                self._subtitle_label.pack_forget()
        elif subtitle:
            self._subtitle_label = ctk.CTkLabel(
                self._content,
                text=subtitle,
                font=FONTS["caption"],
                text_color=COLORS["text_light"],
            )
            self._subtitle_label.pack(anchor="w")

        if self._icon_label is not None:
            self._icon_label.configure(text=icon)
            if icon:
                self._icon_label.pack(side="left", padx=(0, 8))
            else:
                self._icon_label.pack_forget()
        elif icon:
            self._icon_label = ctk.CTkLabel(
                self._content.winfo_children()[0],
                text=icon,
                font=("Segoe UI Emoji", 20),
                text_color=accent_color or self._accent_color,
            )
            self._icon_label.pack(side="left", padx=(0, 8))

        if accent_color:
            self._accent_color = accent_color
            self._accent_bar.configure(fg_color=accent_color)
            if self._icon_label is not None:
                self._icon_label.configure(text_color=accent_color)


class RiskBadge(ctk.CTkLabel):
    """Badge visual de nivel de riesgo."""

    COLORS_MAP = {
        "Bajo": ("#D1FAE5", "#065F46"),
        "Medio": ("#FEF3C7", "#92400E"),
        "Alto": ("#FEE2E2", "#991B1B"),
    }
    EMOJI = {"Bajo": "🟢", "Medio": "🟡", "Alto": "🔴"}

    def __init__(self, master, nivel: str = "Bajo", **kwargs) -> None:
        bg, fg = self.COLORS_MAP.get(nivel, ("#F1F5F9", "#475569"))
        emoji = self.EMOJI.get(nivel, "⚪")
        super().__init__(
            master,
            text=f"{emoji} {nivel}",
            font=FONTS["body_sm"],
            fg_color=bg,
            text_color=fg,
            corner_radius=20,
            padx=10,
            pady=2,
            **kwargs,
        )


class SectionHeader(ctk.CTkFrame):
    """Cabecera de sección con título y separador."""

    def __init__(self, master, title: str, subtitle: str = "", centered: bool = False, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        anchor = "center" if centered else "w"
        justify = "center" if centered else "left"

        ctk.CTkLabel(
            self,
            text=title,
            font=FONTS["heading_md"],
            text_color=COLORS["text_primary"],
            justify=justify,
        ).pack(anchor=anchor)
        if subtitle:
            ctk.CTkLabel(
                self,
                text=subtitle,
                font=FONTS["body_sm"],
                text_color=COLORS["text_secondary"],
                justify=justify,
            ).pack(anchor=anchor)
        ctk.CTkFrame(self, height=2, fg_color=COLORS["border"]).pack(
            fill="x", pady=(8, 0)
        )


class SearchBar(ctk.CTkFrame):
    """Barra de búsqueda con icono."""

    def __init__(self, master, placeholder: str = "Buscar...", command=None, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._cmd = command

        inner = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_card"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=8,
        )
        inner.pack(fill="x")

        ctk.CTkLabel(inner, text="🔍", font=("Segoe UI Emoji", 14)).pack(
            side="left", padx=(12, 4)
        )
        self._entry = ctk.CTkEntry(
            inner,
            placeholder_text=placeholder,
            border_width=0,
            fg_color="transparent",
            font=FONTS["body"],
            height=36,
        )
        self._entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._entry.bind("<KeyRelease>", self._on_change)

    def _on_change(self, _event=None) -> None:
        if self._cmd:
            self._cmd(self._entry.get())

    def get(self) -> str:
        return self._entry.get()

    def clear(self) -> None:
        self._entry.delete(0, "end")


class ActionButton(ctk.CTkButton):
    """Botón de acción con estilos predefinidos."""

    STYLES = {
        "primary": {"fg_color": COLORS["primary"], "hover_color": COLORS["primary_dark"], "text_color": "white"},
        "success": {"fg_color": COLORS["success"], "hover_color": "#059669", "text_color": "white"},
        "danger": {"fg_color": COLORS["danger"], "hover_color": "#DC2626", "text_color": "white"},
        "secondary": {"fg_color": COLORS["border"], "hover_color": "#CBD5E1", "text_color": COLORS["text_primary"]},
        "ghost": {
            "fg_color": "transparent",
            "hover_color": COLORS["bg_main"],
            "text_color": COLORS["primary"],
            "border_width": 2,
            "border_color": COLORS["primary"],
        },
        "ghost_light": {
            "fg_color": "transparent",
            "hover_color": None,
            "text_color": "white",
            "border_width": 1,
            "border_color": "white",
        },
        "header_action": {
            "fg_color": "white",
            "hover_color": "white",
            "text_color": "black",
            "border_width": 0,
        },
        "pdf_transparent": {
            "fg_color": "transparent",
            "hover_color": "#1249BF",
            "text_color": "white",
            "border_width": 0,
        },
    }

    def __init__(self, master, text: str, style: str = "primary", **kwargs) -> None:
        style_cfg = dict(self.STYLES.get(style, self.STYLES["primary"]))
        override_keys = {"fg_color", "hover_color", "text_color", "border_width", "border_color"}
        for key in override_keys:
            if key in kwargs:
                style_cfg[key] = kwargs.pop(key)

        # Allow callers to override height without causing duplicate-kwarg errors
        height_val = kwargs.pop("height", 36)

        super().__init__(
            master,
            text=text,
            corner_radius=8,
            height=height_val,
            font=FONTS["body_sm"],
            **style_cfg,
            **kwargs,
        )


class DataTable(ctk.CTkFrame):
    """Tabla de datos con scroll basada en Treeview."""

    def __init__(self, master, columns: list[str], **kwargs) -> None:
        super().__init__(master, fg_color=COLORS["bg_card"], **kwargs)
        self._columns = columns
        self._rows: list[list[str]] = []
        self._on_select = None
        self._total_rows = 0
        self._rendered_rows = 0
        self._tree = None
        self._build_header()

    def _build_header(self) -> None:
        container = ctk.CTkFrame(self, fg_color=COLORS["bg_card"])
        container.pack(fill="both", expand=True)

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure(
            "Table.Treeview",
            background=COLORS["bg_card"],
            fieldbackground=COLORS["bg_card"],
            foreground=COLORS["text_primary"],
            rowheight=48,
            borderwidth=0,
            font=FONTS["body_sm"],
        )
        style.configure(
            "Table.Treeview.Heading",
            background=COLORS["primary"],
            foreground="white",
            font=FONTS["heading_sm"],
            relief="flat",
            padding=10,
            borderwidth=0,
        )
        style.map(
            "Table.Treeview",
            background=[("selected", COLORS["primary_light"])],
            foreground=[("selected", COLORS["text_primary"])],
        )
        style.map(
            "Table.Treeview.Heading",
            background=[("active", COLORS["primary"]), ("pressed", COLORS["primary"]), ("!disabled", COLORS["primary"])],
            foreground=[("active", "white"), ("pressed", "white"), ("!disabled", "white")],
        )

        table_frame = ctk.CTkFrame(container, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, padx=1, pady=1)

        self._tree = ttk.Treeview(
            table_frame,
            columns=self._columns,
            show="headings",
            style="Table.Treeview",
            selectmode="browse",
        )
        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self._tree.yview)
        # x_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=y_scroll.set, 
                            #  xscrollcommand=x_scroll.set
                             )

        for i, col in enumerate(self._columns):
            self._tree.heading(col, text=col, anchor="w")
            self._tree.column(col, anchor="w", stretch=True)

        self._tree.tag_configure("odd", background=COLORS["bg_card"])
        self._tree.tag_configure("even", background=COLORS["bg_line_table"])
        self._tree.bind("<<TreeviewSelect>>", self._handle_tree_select)

        self._tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        # x_scroll.grid(row=1, column=0, sticky="ew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

    def load_data(self, rows: list[list[str]], on_select=None, max_rows: int | None = None) -> None:
        """Carga filas en la tabla."""
        self._on_select = on_select
        self._total_rows = len(rows)
        self._rows = [list(map(lambda c: "-" if (c is None or str(c).lower() == "nan") else str(c or ""), row)) for row in rows]

        if not self._tree:
            return

        for item in self._tree.get_children():
            self._tree.delete(item)

        for row_idx, row_data in enumerate(self._rows):
            tag = "even" if row_idx % 2 else "odd"
            self._tree.insert("", "end", iid=str(row_idx), values=row_data, tags=(tag,))

        self._rendered_rows = len(self._rows)
        self._adjust_column_widths()

    def _adjust_column_widths(self) -> None:
        """Ajusta el ancho de las columnas basado en el contenido y ancho disponible del contenedor."""
        if not self._tree or not self._rows:
            return

        # Forzar actualización para obtener el ancho real del Treeview
        self._tree.update_idletasks()
        container_width = self._tree.winfo_width()

        if container_width <= 1:  # Si no tiene ancho válido aún
            container_width = 500  # Valor por defecto

        # Calcular ancho necesario para cada columna (basado en contenido)
        column_widths = []
        total_content_width = 0

        for i, col in enumerate(self._columns):
            # Calcular ancho basado en el encabezado
            header_width = len(col) * 8 + 20

            # Encontrar el contenido más ancho en esa columna
            max_content_width = 0
            for row in self._rows:
                if i < len(row):
                    content_width = len(str(row[i])) * 8 + 20
                    max_content_width = max(max_content_width, content_width)

            # El ancho necesario es el máximo entre encabezado y contenido
            needed_width = max(header_width, max_content_width)
            needed_width = max(50, needed_width)  # Mínimo de 50px

            column_widths.append(needed_width)
            total_content_width += needed_width

        # Distribuir el ancho disponible proporcionalmente
        reserved_width = 30  # Espacio para scrollbar y bordes
        available_width = max(container_width - reserved_width, 100)

        for i, col in enumerate(self._columns):
            # Calcular el ancho proporcional basado en el contenido relativo
            proportion = column_widths[i] / total_content_width if total_content_width > 0 else 1 / len(self._columns)
            final_width = int(available_width * proportion)
            final_width = max(50, final_width)  # Mínimo de 50px

            self._tree.column(col, width=final_width)

    @property
    def total_rows(self) -> int:
        return self._total_rows

    @property
    def rendered_rows(self) -> int:
        return self._rendered_rows

    def _handle_tree_select(self, _event=None) -> None:
        if not self._tree or not self._on_select:
            return
        selected = self._tree.selection()
        if not selected:
            return
        iid = selected[0]
        try:
            row_idx = int(iid)
            row_data = self._rows[row_idx]
        except (ValueError, IndexError):
            return
        self._on_select(row_idx, row_data)

    def _handle_click(self, row_idx: int, row_data: list) -> None:
        if self._on_select:
            self._on_select(row_idx, row_data)
