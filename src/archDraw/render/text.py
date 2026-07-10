import html

class TextRenderer:
    """Helper class to handle partition/wrapping options, text dimensions, and rendering."""

    @staticmethod
    def get_wrapping_options(text: str) -> list[list[str]]:
        """Generates all sequential groupings of words (line splits) for the text,
        sorted from fewest lines (unwrapped) to most lines (fully wrapped).
        """
        words = [w for w in text.split(" ") if w]
        if not words:
            return [[""]]
            
        def partition(index):
            if index == len(words):
                return [[]]
            res = []
            for i in range(index + 1, len(words) + 1):
                line = " ".join(words[index:i])
                for tail in partition(i):
                    res.append([line] + tail)
            return res
            
        options = partition(0)
        # Sort options: fewer lines first (unwrapped), then by length of the longest line as a tie-breaker
        options.sort(key=lambda opt: (len(opt), max(len(l) for l in opt)))
        return options

    @staticmethod
    def calculate_text_dimensions(lines: list[str], char_width_factor: float, line_height: float = 15.0) -> tuple[float, float]:
        """Computes the overall bounding width and height for a set of text lines."""
        if not lines:
            return 0, 0
        max_line_len = max(len(l) for l in lines)
        width = max_line_len * char_width_factor
        height = len(lines) * line_height
        return width, height

    @staticmethod
    def choose_wrapping(text: str, target_width: float, target_height: float, char_width_factor: float, line_height: float = 15.0) -> list[str]:
        """Selects the best fitting line grouping of text based on target_width and target_height."""
        options = TextRenderer.get_wrapping_options(text)
        # We look for the first option (least wrapped) that fits within the target_width and target_height
        best_option = None
        for opt in options:
            w, h = TextRenderer.calculate_text_dimensions(opt, char_width_factor, line_height)
            if w <= target_width:
                best_option = opt
                break
        if best_option is None:
            # If none fit within the target_width, choose the one with the smallest width (most wrapped)
            best_option = options[-1]
        return best_option

    @staticmethod
    def render_text(text: str, x: float, y: float, target_width: float, target_height: float, theme_params: dict, text_anchor: str = "middle", char_width_factor: float = 7.5, line_height: float = 15.0) -> str:
        """Renders the text wrapped based on provided target_width and target_height and theme attributes."""
        font_size = theme_params.get("text_size", 12)
        font_weight = theme_params.get("font_weight", "normal")
        text_color = theme_params.get("text_color", "#000000")
        
        lines = TextRenderer.choose_wrapping(text, target_width, target_height, char_width_factor, line_height)
        
        label_svg = ""
        for i, line in enumerate(lines):
            dy = line_height if i > 0 else 0
            label_svg += f'<tspan x="{x}" dy="{dy}">{html.escape(line)}</tspan>'
            
        return f"""
        <text x="{x}" y="{y}" 
              font-family="sans-serif" font-size="{font_size}" fill="{text_color}" 
              font-weight="{font_weight}" text-anchor="{text_anchor}">
            {label_svg}
        </text>
        """
