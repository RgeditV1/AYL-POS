import flet as ft

# Paleta "Midnight Pro" (Modo Oscuro)
DARK_SLATE_900 = "#0F172A"
DARK_SLATE_800 = "#1E293B"
SKY_BLUE_400 = "#38BDF8"
EMERALD_500 = "#10B981"
SLATE_50 = "#F8FAFC"
ERROR_RED = "#EF4444"

class ThemeManager:
    @staticmethod
    def get_dark_theme():
        return ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=SKY_BLUE_400,
                on_primary=DARK_SLATE_900,
                secondary=EMERALD_500,
                on_secondary=SLATE_50,
                surface=DARK_SLATE_800,
                on_surface=SLATE_50,
                surface_container=DARK_SLATE_900,
                error=ERROR_RED,
                outline="#334155",
            ),
            visual_density=ft.VisualDensity.COMFORTABLE,
        )

    @staticmethod
    def get_light_theme():
        return ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=SKY_BLUE_400,
                on_primary=DARK_SLATE_900,
                secondary=EMERALD_500,
                on_secondary=SLATE_50,
                surface=DARK_SLATE_800,
                on_surface=SLATE_50,
                surface_container=DARK_SLATE_900,
                error=ERROR_RED,
                outline="#334155",
            ),
            visual_density=ft.VisualDensity.COMFORTABLE,
        )
