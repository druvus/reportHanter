"""
Advanced layout engine for responsive and adaptive report layouts.
"""
from typing import Any, Dict, List, Optional, Tuple, Union
import panel as pn
import altair as alt
from pathlib import Path


class ResponsiveLayoutEngine:
    """Creates responsive, adaptive layouts for bioinformatics reports."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.breakpoints = {
            "small": 768,
            "medium": 1024, 
            "large": 1440,
            "xlarge": 1920
        }
    
    def create_adaptive_grid(self, components: List[pn.pane.HTML], 
                           grid_type: str = "auto") -> pn.GridBox:
        """Create adaptive grid layout based on content and screen size."""
        
        if grid_type == "auto":
            # Automatically determine best layout
            n_components = len(components)
            if n_components <= 2:
                ncols = min(2, n_components)
            elif n_components <= 4:
                ncols = 2
            elif n_components <= 6:
                ncols = 3
            else:
                ncols = 4
        elif grid_type == "dashboard":
            # Dashboard style: feature chart + smaller supporting charts
            ncols = 3
        elif grid_type == "report":
            # Report style: stacked vertical layout
            ncols = 1
        else:
            ncols = int(grid_type) if str(grid_type).isdigit() else 2
        
        return pn.GridBox(*components, ncols=ncols, sizing_mode="stretch_both")
    
    def create_tabbed_interface(self, sections: List[Tuple[str, pn.pane.HTML]],
                               tab_location: str = "above") -> pn.Tabs:
        """Create tabbed interface with enhanced styling."""
        tabs = pn.Tabs(
            *sections,
            tabs_location=tab_location,
            sizing_mode="stretch_both",
            margin=(10, 10)
        )
        
        # Custom CSS for enhanced tab styling
        tabs.stylesheets = ["""
            .bk-tabs-header .bk-tab {
                padding: 12px 20px;
                margin-right: 2px;
                border-radius: 8px 8px 0 0;
                font-weight: 500;
                transition: all 0.3s ease;
            }
            .bk-tabs-header .bk-tab.bk-active {
                background-color: #1f77b4;
                color: white;
            }
            .bk-tabs-header .bk-tab:hover {
                background-color: #f0f0f0;
            }
        """]
        
        return tabs
    
    def create_collapsible_sections(self, sections: List[Tuple[str, pn.pane.HTML]]) -> pn.Accordion:
        """Create collapsible accordion sections."""
        accordion = pn.Accordion(
            *sections,
            sizing_mode="stretch_width",
            margin=(5, 10)
        )
        
        # Enhanced accordion styling
        accordion.stylesheets = ["""
            .bk-panel-models-accordion .bk-accordion-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px;
                font-weight: 600;
                border-radius: 5px;
                margin-bottom: 2px;
            }
            .bk-panel-models-accordion .bk-accordion-header:hover {
                opacity: 0.9;
            }
        """]
        
        return accordion
    
    def create_sidebar_layout(self, sidebar_content: pn.pane.HTML,
                            main_content: pn.pane.HTML,
                            sidebar_width: int = 300) -> pn.Row:
        """Create sidebar layout with responsive behavior."""
        
        # Sidebar with enhanced styling
        sidebar = pn.Column(
            sidebar_content,
            width=sidebar_width,
            sizing_mode="stretch_height",
            margin=(10, 5, 10, 10),
            background="#f8f9fa"
        )
        
        # Main content area
        main = pn.Column(
            main_content,
            sizing_mode="stretch_both",
            margin=(10, 10, 10, 5)
        )
        
        return pn.Row(sidebar, main, sizing_mode="stretch_both")
    
    def create_card_layout(self, title: str, content: pn.pane.HTML,
                         card_type: str = "default") -> pn.Column:
        """Create card-style containers for content."""
        
        # Card header based on type
        header_styles = {
            "default": {"background": "#ffffff", "color": "#333"},
            "primary": {"background": "#007bff", "color": "white"},
            "success": {"background": "#28a745", "color": "white"},
            "warning": {"background": "#ffc107", "color": "#212529"},
            "danger": {"background": "#dc3545", "color": "white"},
            "info": {"background": "#17a2b8", "color": "white"}
        }
        
        style = header_styles.get(card_type, header_styles["default"])
        
        header = pn.pane.HTML(
            f"""<div style="
                background: {style['background']};
                color: {style['color']};
                padding: 15px 20px;
                font-weight: 600;
                font-size: 16px;
                border-radius: 8px 8px 0 0;
                border-bottom: 1px solid #e9ecef;
            ">{title}</div>""",
            sizing_mode="stretch_width"
        )
        
        # Card body
        body = pn.Column(
            content,
            margin=(20, 20, 20, 20),
            sizing_mode="stretch_both"
        )
        
        # Complete card
        card = pn.Column(
            header,
            body,
            sizing_mode="stretch_both",
            margin=10,
            styles={
                "border": "1px solid #e9ecef",
                "border-radius": "8px",
                "box-shadow": "0 2px 4px rgba(0,0,0,0.1)",
                "background": "white"
            }
        )
        
        return card


class DashboardTemplates:
    """Pre-built dashboard templates for different use cases."""
    
    @staticmethod
    def scientific_report_template(sections: Dict[str, pn.pane.HTML]) -> pn.Column:
        """Template for scientific publication-style reports."""
        layout = ResponsiveLayoutEngine()
        
        # Header section
        header = pn.pane.HTML("""
            <div style="
                text-align: center;
                padding: 30px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                margin-bottom: 20px;
                border-radius: 10px;
            ">
                <h1 style="margin: 0; font-size: 28px; font-weight: 300;">
                    Bioinformatics Analysis Report
                </h1>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">
                    Generated with reportHanter v0.3.0
                </p>
            </div>
        """)
        
        # Create cards for each section
        cards = []
        for title, content in sections.items():
            card = layout.create_card_layout(title, content, "default")
            cards.append(card)
        
        # Arrange in responsive grid
        grid = layout.create_adaptive_grid(cards, grid_type="report")
        
        return pn.Column(header, grid, sizing_mode="stretch_both")
    
    @staticmethod
    def executive_dashboard_template(sections: Dict[str, pn.pane.HTML]) -> pn.Column:
        """Template for executive dashboard with key metrics."""
        layout = ResponsiveLayoutEngine()
        
        # KPI header with key metrics
        kpi_section = DashboardTemplates._create_kpi_section(sections)
        
        # Main dashboard grid
        main_sections = {k: v for k, v in sections.items() if not k.startswith("kpi_")}
        cards = [layout.create_card_layout(title, content, "primary") 
                for title, content in main_sections.items()]
        
        grid = layout.create_adaptive_grid(cards, grid_type="dashboard")
        
        return pn.Column(kpi_section, grid, sizing_mode="stretch_both")
    
    @staticmethod
    def comparison_template(sections: Dict[str, pn.pane.HTML]) -> pn.Row:
        """Template for side-by-side comparisons."""
        layout = ResponsiveLayoutEngine()
        
        # Split sections into two columns
        section_items = list(sections.items())
        mid_point = len(section_items) // 2
        
        left_sections = section_items[:mid_point]
        right_sections = section_items[mid_point:]
        
        # Create columns
        left_cards = [layout.create_card_layout(title, content, "info") 
                     for title, content in left_sections]
        right_cards = [layout.create_card_layout(title, content, "success")
                      for title, content in right_sections]
        
        left_column = pn.Column(*left_cards, sizing_mode="stretch_both")
        right_column = pn.Column(*right_cards, sizing_mode="stretch_both") 
        
        return pn.Row(left_column, right_column, sizing_mode="stretch_both")
    
    @staticmethod
    def _create_kpi_section(sections: Dict[str, pn.pane.HTML]) -> pn.Row:
        """Create KPI summary section."""
        kpi_html = """
        <div style="
            display: flex;
            justify-content: space-around;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        ">
            <div style="text-align: center;">
                <h3 style="color: #28a745; margin: 0;">1,234</h3>
                <p style="margin: 5px 0 0 0; color: #666;">Total Reads</p>
            </div>
            <div style="text-align: center;">
                <h3 style="color: #007bff; margin: 0;">89.5%</h3>
                <p style="margin: 5px 0 0 0; color: #666;">Classified</p>
            </div>
            <div style="text-align: center;">
                <h3 style="color: #ffc107; margin: 0;">45</h3>
                <p style="margin: 5px 0 0 0; color: #666;">Species</p>
            </div>
            <div style="text-align: center;">
                <h3 style="color: #17a2b8; margin: 0;">2.34</h3>
                <p style="margin: 5px 0 0 0; color: #666;">Diversity</p>
            </div>
        </div>
        """
        
        return pn.pane.HTML(kpi_html, sizing_mode="stretch_width")


class InteractiveFeatures:
    """Add interactive features to reports."""
    
    @staticmethod
    def add_filter_controls(data_columns: List[str]) -> pn.Column:
        """Create filter controls for data exploration."""
        filters = []
        
        # Add various filter widgets
        for col in data_columns:
            if col.lower() in ["domain", "species", "category"]:
                # Categorical filter
                filter_widget = pn.widgets.MultiChoice(
                    name=f"Filter by {col}",
                    options=["Viruses", "Bacteria", "Archaea", "Eukaryota"],
                    margin=(5, 20)
                )
                filters.append(filter_widget)
            elif col.lower() in ["percent", "percentage", "abundance"]:
                # Range slider for numerical data
                range_slider = pn.widgets.RangeSlider(
                    name=f"{col} Range",
                    start=0,
                    end=100,
                    value=(0, 100),
                    step=0.1,
                    margin=(5, 20)
                )
                filters.append(range_slider)
        
        return pn.Column(*filters, width=250, margin=(10, 5))
    
    @staticmethod
    def create_export_controls() -> pn.Row:
        """Create export and download controls."""
        export_buttons = pn.Row(
            pn.widgets.Button(name="Export PNG", button_type="primary", margin=5),
            pn.widgets.Button(name="Export PDF", button_type="default", margin=5),
            pn.widgets.Button(name="Export Data", button_type="outline", margin=5),
            margin=(10, 0)
        )
        
        return export_buttons