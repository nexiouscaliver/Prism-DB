"""
Visualization Agent for PrismDB.

This module provides visualization capabilities for SQL query results,
generating charts and graphs using Plotly Express.
"""

import base64
import io
import json
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder

from models.response_models import ChartData, ErrorCode

logger = logging.getLogger(__name__)


class VisualizationError(Exception):
    """Exception raised for errors in the visualization agent."""
    
    def __init__(self, message: str, code: ErrorCode, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)


class VisualizationAgent:
    """
    Agent for generating visualizations from query results.
    
    This agent creates charts and graphs from SQL query results using
    Plotly Express, with various output formats supported.
    """
    
    def __init__(self):
        """Initialize the visualization agent."""
        self.supported_chart_types = {
            "line": self._create_line_chart,
            "bar": self._create_bar_chart,
            "scatter": self._create_scatter_chart,
            "pie": self._create_pie_chart,
            "histogram": self._create_histogram,
            "box": self._create_box_plot,
            "heatmap": self._create_heatmap,
            "area": self._create_area_chart,
            "treemap": self._create_treemap,
            "funnel": self._create_funnel_chart,
            "timeline": self._create_timeline,
            "sunburst": self._create_sunburst,
        }
        
        self.supported_output_formats = ["svg", "json", "html", "markdown", "png"]
    
    def _convert_to_dataframe(self, data: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Convert query result rows to pandas DataFrame.
        
        Args:
            data: List of dictionaries representing query rows
            
        Returns:
            Pandas DataFrame
            
        Raises:
            VisualizationError: If conversion fails
        """
        try:
            if not data:
                raise ValueError("Empty data provided")
            
            df = pd.DataFrame(data)
            
            # Convert numeric strings to numbers
            for col in df.columns:
                # Check if column can be converted to numeric
                if df[col].dtype == 'object':
                    try:
                        numeric_col = pd.to_numeric(df[col], errors='coerce')
                        # Only convert if we don't lose too much data
                        if numeric_col.notna().sum() > 0.8 * len(numeric_col):
                            df[col] = numeric_col
                    except:
                        pass
            
            return df
        except Exception as e:
            logger.error(f"Failed to convert data to DataFrame: {str(e)}")
            raise VisualizationError(
                f"Failed to convert data to DataFrame: {str(e)}",
                ErrorCode.CHART_DATA_ERROR
            )
    
    def _create_line_chart(self, df: pd.DataFrame, options: Dict[str, Any]) -> go.Figure:
        """Create a line chart."""
        x = options.get("x")
        y = options.get("y")
        color = options.get("color")
        title = options.get("title", "Line Chart")
        
        if not x or not y:
            raise VisualizationError(
                "Line chart requires 'x' and 'y' columns",
                ErrorCode.CHART_CONFIG_ERROR
            )
        
        fig = px.line(
            df, 
            x=x, 
            y=y,
            color=color,
            title=title,
            labels=options.get("labels", {}),
            line_shape=options.get("line_shape", "linear"),
            markers=options.get("markers", True)
        )
        
        return fig
    
    def _create_bar_chart(self, df: pd.DataFrame, options: Dict[str, Any]) -> go.Figure:
        """Create a bar chart."""
        x = options.get("x")
        y = options.get("y")
        color = options.get("color")
        title = options.get("title", "Bar Chart")
        orientation = options.get("orientation", "v")
        
        if not x or not y:
            raise VisualizationError(
                "Bar chart requires 'x' and 'y' columns",
                ErrorCode.CHART_CONFIG_ERROR
            )
        
        fig = px.bar(
            df,
            x=x,
            y=y,
            color=color,
            title=title,
            orientation=orientation,
            barmode=options.get("barmode", "group"),
            labels=options.get("labels", {}),
            text_auto=options.get("text_auto", False)
        )
        
        return fig
    
    def _create_scatter_chart(self, df: pd.DataFrame, options: Dict[str, Any]) -> go.Figure:
        """Create a scatter plot."""
        x = options.get("x")
        y = options.get("y")
        color = options.get("color")
        size = options.get("size")
        title = options.get("title", "Scatter Plot")
        
        if not x or not y:
            raise VisualizationError(
                "Scatter plot requires 'x' and 'y' columns",
                ErrorCode.CHART_CONFIG_ERROR
            )
        
        fig = px.scatter(
            df,
            x=x,
            y=y,
            color=color,
            size=size,
            title=title,
            labels=options.get("labels", {}),
            trendline=options.get("trendline"),
            marginal_x=options.get("marginal_x"),
            marginal_y=options.get("marginal_y")
        )
        
        return fig
    
    def _create_pie_chart(self, df: pd.DataFrame, options: Dict[str, Any]) -> go.Figure:
        """Create a pie chart."""
        values = options.get("values")
        names = options.get("names")
        title = options.get("title", "Pie Chart")
        
        if not values or not names:
            raise VisualizationError(
                "Pie chart requires 'values' and 'names' columns",
                ErrorCode.CHART_CONFIG_ERROR
            )
        
        fig = px.pie(
            df,
            values=values,
            names=names,
            title=title,
            hole=options.get("hole", 0),
            labels=options.get("labels", {})
        )
        
        return fig
    
    def _create_histogram(self, df: pd.DataFrame, options: Dict[str, Any]) -> go.Figure:
        """Create a histogram."""
        x = options.get("x")
        nbins = options.get("nbins")
        title = options.get("title", "Histogram")
        
        if not x:
            raise VisualizationError(
                "Histogram requires 'x' column",
                ErrorCode.CHART_CONFIG_ERROR
            )
        
        fig = px.histogram(
            df,
            x=x,
            nbins=nbins,
            title=title,
            color=options.get("color"),
            marginal=options.get("marginal"),
            histnorm=options.get("histnorm")
        )
        
        return fig
    
    def _create_box_plot(self, df: pd.DataFrame, options: Dict[str, Any]) -> go.Figure:
        """Create a box plot."""
        x = options.get("x")
        y = options.get("y")
        title = options.get("title", "Box Plot")
        
        if not y:
            raise VisualizationError(
                "Box plot requires at least 'y' column",
                ErrorCode.CHART_CONFIG_ERROR
            )
        
        fig = px.box(
            df,
            x=x,
            y=y,
            color=options.get("color"),
            title=title,
            points=options.get("points", "outliers"),
            notched=options.get("notched", False)
        )
        
        return fig
    
    def _create_heatmap(self, df: pd.DataFrame, options: Dict[str, Any]) -> go.Figure:
        """Create a heatmap."""
        title = options.get("title", "Heatmap")
        
        # For heatmap, the data typically needs to be pivoted
        x = options.get("x")
        y = options.get("y")
        z = options.get("z")
        
        if not x or not y or not z:
            raise VisualizationError(
                "Heatmap requires 'x', 'y', and 'z' columns",
                ErrorCode.CHART_CONFIG_ERROR
            )
        
        try:
            # Pivot the data for heatmap
            pivot_df = df.pivot(index=y, columns=x, values=z)
            
            fig = px.imshow(
                pivot_df,
                title=title,
                color_continuous_scale=options.get("color_scale", "viridis"),
                labels=options.get("labels", {})
            )
            
            return fig
        except Exception as e:
            raise VisualizationError(
                f"Failed to create heatmap: {str(e)}",
                ErrorCode.CHART_CONFIG_ERROR
            )
    
    def _create_area_chart(self, df: pd.DataFrame, options: Dict[str, Any]) -> go.Figure:
        """Create an area chart."""
        x = options.get("x")
        y = options.get("y")
        title = options.get("title", "Area Chart")
        
        if not x or not y:
            raise VisualizationError(
                "Area chart requires 'x' and 'y' columns",
                ErrorCode.CHART_CONFIG_ERROR
            )
        
        fig = px.area(
            df,
            x=x,
            y=y,
            color=options.get("color"),
            title=title,
            line_shape=options.get("line_shape", "linear"),
            labels=options.get("labels", {})
        )
        
        return fig
    
    def _create_treemap(self, df: pd.DataFrame, options: Dict[str, Any]) -> go.Figure:
        """Create a treemap."""
        path = options.get("path")
        values = options.get("values")
        title = options.get("title", "Treemap")
        
        if not path or not values:
            raise VisualizationError(
                "Treemap requires 'path' and 'values' columns",
                ErrorCode.CHART_CONFIG_ERROR
            )
        
        # Ensure path is a list
        if not isinstance(path, list):
            path = [path]
        
        fig = px.treemap(
            df,
            path=path,
            values=values,
            color=options.get("color"),
            title=title,
            labels=options.get("labels", {})
        )
        
        return fig
    
    def _create_funnel_chart(self, df: pd.DataFrame, options: Dict[str, Any]) -> go.Figure:
        """Create a funnel chart."""
        x = options.get("x")
        y = options.get("y")
        title = options.get("title", "Funnel Chart")
        
        if not x or not y:
            raise VisualizationError(
                "Funnel chart requires 'x' and 'y' columns",
                ErrorCode.CHART_CONFIG_ERROR
            )
        
        fig = px.funnel(
            df,
            x=x,
            y=y,
            color=options.get("color"),
            title=title,
            labels=options.get("labels", {})
        )
        
        return fig
    
    def _create_timeline(self, df: pd.DataFrame, options: Dict[str, Any]) -> go.Figure:
        """Create a timeline chart."""
        x_start = options.get("x_start")
        x_end = options.get("x_end")
        y = options.get("y")
        title = options.get("title", "Timeline")
        
        if not x_start or not x_end or not y:
            raise VisualizationError(
                "Timeline requires 'x_start', 'x_end', and 'y' columns",
                ErrorCode.CHART_CONFIG_ERROR
            )
        
        # Ensure datetime columns
        try:
            df[x_start] = pd.to_datetime(df[x_start])
            df[x_end] = pd.to_datetime(df[x_end])
        except Exception as e:
            raise VisualizationError(
                f"Failed to convert datetime columns: {str(e)}",
                ErrorCode.CHART_DATA_ERROR
            )
        
        fig = px.timeline(
            df,
            x_start=x_start,
            x_end=x_end,
            y=y,
            color=options.get("color"),
            title=title,
            labels=options.get("labels", {})
        )
        
        return fig
    
    def _create_sunburst(self, df: pd.DataFrame, options: Dict[str, Any]) -> go.Figure:
        """Create a sunburst chart."""
        path = options.get("path")
        values = options.get("values")
        title = options.get("title", "Sunburst Chart")
        
        if not path or not values:
            raise VisualizationError(
                "Sunburst chart requires 'path' and 'values' columns",
                ErrorCode.CHART_CONFIG_ERROR
            )
        
        # Ensure path is a list
        if not isinstance(path, list):
            path = [path]
        
        fig = px.sunburst(
            df,
            path=path,
            values=values,
            color=options.get("color"),
            title=title,
            labels=options.get("labels", {})
        )
        
        return fig
    
    def _apply_layout_options(self, fig: go.Figure, options: Dict[str, Any]) -> go.Figure:
        """Apply layout options to a figure."""
        layout_options = options.get("layout", {})
        
        if layout_options:
            fig.update_layout(
                width=layout_options.get("width"),
                height=layout_options.get("height"),
                template=layout_options.get("template", "plotly"),
                title_font_size=layout_options.get("title_font_size"),
                xaxis_title=layout_options.get("xaxis_title"),
                yaxis_title=layout_options.get("yaxis_title"),
                legend_title=layout_options.get("legend_title"),
                showlegend=layout_options.get("showlegend", True),
                margin=layout_options.get("margin"),
                coloraxis_showscale=layout_options.get("coloraxis_showscale", True)
            )
        
        # Apply theme if specified
        theme = options.get("theme")
        if theme:
            if theme in ["plotly", "plotly_white", "plotly_dark", "ggplot2", "seaborn", 
                        "simple_white", "none"]:
                fig.update_layout(template=theme)
        
        return fig
    
    def _render_figure(self, fig: go.Figure, format: str) -> Dict[str, Any]:
        """
        Render figure in the requested format.
        
        Args:
            fig: Plotly figure
            format: Output format (svg, json, html, markdown, png)
            
        Returns:
            Dictionary with rendered content
            
        Raises:
            VisualizationError: If rendering fails
        """
        try:
            if format == "svg":
                svg_str = fig.to_image(format="svg").decode("utf-8")
                return {"format": "svg", "content": svg_str}
            
            elif format == "json":
                json_str = json.dumps(fig.to_dict(), cls=PlotlyJSONEncoder)
                return {"format": "json", "content": json_str}
            
            elif format == "html":
                html_str = fig.to_html(include_plotlyjs="cdn", full_html=False)
                return {"format": "html", "content": html_str}
            
            elif format == "markdown":
                # For markdown, we create a base64 encoded PNG
                img_bytes = fig.to_image(format="png")
                img_base64 = base64.b64encode(img_bytes).decode("utf-8")
                md_content = f"![Chart](data:image/png;base64,{img_base64})"
                return {"format": "markdown", "content": md_content}
            
            elif format == "png":
                img_bytes = fig.to_image(format="png")
                img_base64 = base64.b64encode(img_bytes).decode("utf-8")
                return {"format": "png", "content": img_base64}
            
            else:
                raise VisualizationError(
                    f"Unsupported output format: {format}",
                    ErrorCode.CHART_CONFIG_ERROR
                )
        
        except Exception as e:
            logger.error(f"Failed to render figure: {str(e)}")
            raise VisualizationError(
                f"Failed to render figure in {format} format: {str(e)}",
                ErrorCode.CHART_RENDERING_ERROR
            )
    
    def generate_chart(
        self,
        data: List[Dict[str, Any]],
        chart_type: str,
        options: Dict[str, Any],
        output_format: str = "json"
    ) -> ChartData:
        """
        Generate a chart from data.
        
        Args:
            data: Query result rows
            chart_type: Type of chart to generate
            options: Chart configuration options
            output_format: Output format
            
        Returns:
            ChartData object with rendered chart
            
        Raises:
            VisualizationError: If chart generation fails
        """
        # Validate chart type
        if chart_type not in self.supported_chart_types:
            supported = ", ".join(self.supported_chart_types.keys())
            raise VisualizationError(
                f"Unsupported chart type: {chart_type}. Supported types: {supported}",
                ErrorCode.CHART_CONFIG_ERROR
            )
        
        # Validate output format
        if output_format not in self.supported_output_formats:
            supported = ", ".join(self.supported_output_formats)
            raise VisualizationError(
                f"Unsupported output format: {output_format}. Supported formats: {supported}",
                ErrorCode.CHART_CONFIG_ERROR
            )
        
        # Convert data to DataFrame
        df = self._convert_to_dataframe(data)
        
        # Create chart based on type
        chart_func = self.supported_chart_types[chart_type]
        fig = chart_func(df, options)
        
        # Apply layout options
        fig = self._apply_layout_options(fig, options)
        
        # Render in requested format
        rendered = self._render_figure(fig, output_format)
        
        # Create chart data object
        chart_data = ChartData(
            chart_type=chart_type,
            format=rendered["format"],
            content=rendered["content"],
            config=options
        )
        
        return chart_data


# Global instance for singleton access
_visualization_agent = None


def get_visualization_agent() -> VisualizationAgent:
    """
    Get the visualization agent instance.
    
    Returns:
        VisualizationAgent instance
    """
    global _visualization_agent
    
    if _visualization_agent is None:
        _visualization_agent = VisualizationAgent()
    
    return _visualization_agent 