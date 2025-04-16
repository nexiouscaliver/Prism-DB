"""
Visualization service for PrismDB.

This module provides the visualization service responsible for generating
charts and visual representations of query results using various charting libraries.
"""

import base64
import io
import json
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.io import to_image, to_json, write_html

from models.response_models import ChartData, ErrorCode, QueryResult


class VisualizationError(Exception):
    """Exception raised for errors during visualization generation."""
    
    def __init__(self, message: str, code: ErrorCode, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)


class VisualizationService:
    """Service for generating visualizations from query results."""
    
    SUPPORTED_FORMATS = ["svg", "png", "json", "html", "markdown"]
    SUPPORTED_CHART_TYPES = [
        "line", "bar", "scatter", "pie", "area", "histogram", 
        "heatmap", "box", "violin", "sunburst", "treemap", "funnel"
    ]
    
    def __init__(self):
        """Initialize the visualization service."""
        self.default_width = 800
        self.default_height = 500
        self.max_width = 1600
        self.max_height = 1200
        self.default_format = "svg"
    
    def _query_result_to_dataframe(self, query_result: QueryResult) -> pd.DataFrame:
        """
        Convert a QueryResult to a pandas DataFrame.
        
        Args:
            query_result: Query result object
            
        Returns:
            DataFrame representation of the query result
            
        Raises:
            VisualizationError: If conversion fails
        """
        try:
            # Convert rows to DataFrame
            df = pd.DataFrame(query_result.rows)
            
            # Handle empty results
            if df.empty and query_result.columns:
                # Create empty DataFrame with column names
                column_names = [col.name for col in query_result.columns]
                df = pd.DataFrame(columns=column_names)
                
            return df
        except Exception as e:
            raise VisualizationError(
                f"Failed to convert query result to DataFrame: {str(e)}",
                ErrorCode.CHART_DATA_ERROR,
                {"error": str(e)}
            )
    
    def _validate_chart_config(self, chart_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and sanitize chart configuration.
        
        Args:
            chart_type: Type of chart to generate
            config: Chart configuration
            
        Returns:
            Validated configuration
            
        Raises:
            VisualizationError: If configuration is invalid
        """
        if chart_type not in self.SUPPORTED_CHART_TYPES:
            raise VisualizationError(
                f"Unsupported chart type: {chart_type}",
                ErrorCode.INVALID_CHART_TYPE,
                {"supported_types": self.SUPPORTED_CHART_TYPES}
            )
        
        # Create a copy of the config
        validated_config = config.copy() if config else {}
        
        # Validate dimensions
        width = validated_config.get("width", self.default_width)
        height = validated_config.get("height", self.default_height)
        
        try:
            width = int(width)
            height = int(height)
        except (ValueError, TypeError):
            width = self.default_width
            height = self.default_height
        
        # Ensure dimensions are within limits
        width = min(max(width, 100), self.max_width)
        height = min(max(height, 100), self.max_height)
        
        validated_config["width"] = width
        validated_config["height"] = height
        
        # Validate title
        title = validated_config.get("title", "")
        if not isinstance(title, str):
            validated_config["title"] = str(title)
        
        # Default layout options
        if "layout" not in validated_config:
            validated_config["layout"] = {}
        
        return validated_config
    
    def _generate_plotly_figure(
        self, 
        df: pd.DataFrame, 
        chart_type: str, 
        config: Dict[str, Any]
    ) -> go.Figure:
        """
        Generate a Plotly figure from DataFrame.
        
        Args:
            df: DataFrame with chart data
            chart_type: Type of chart to generate
            config: Chart configuration
            
        Returns:
            Plotly Figure
            
        Raises:
            VisualizationError: If figure generation fails
        """
        if df.empty:
            # Return empty figure with message
            fig = go.Figure()
            fig.add_annotation(
                text="No data available for visualization", 
                showarrow=False,
                font=dict(size=14)
            )
            fig.update_layout(
                width=config["width"],
                height=config["height"],
                title=config.get("title", "No Data")
            )
            return fig
        
        try:
            # Extract visualization parameters
            x = config.get("x")
            y = config.get("y")
            color = config.get("color")
            size = config.get("size")
            text = config.get("text")
            hover_data = config.get("hover_data")
            animation_frame = config.get("animation_frame")
            
            # Check if required columns exist
            if x and x not in df.columns:
                raise VisualizationError(
                    f"Column '{x}' specified for x-axis does not exist in data",
                    ErrorCode.CHART_DATA_ERROR,
                    {"available_columns": list(df.columns)}
                )
                
            if y and isinstance(y, str) and y not in df.columns:
                raise VisualizationError(
                    f"Column '{y}' specified for y-axis does not exist in data",
                    ErrorCode.CHART_DATA_ERROR,
                    {"available_columns": list(df.columns)}
                )
                
            # If y is a list, validate each column
            if y and isinstance(y, list):
                for col in y:
                    if col not in df.columns:
                        raise VisualizationError(
                            f"Column '{col}' specified for y-axis does not exist in data",
                            ErrorCode.CHART_DATA_ERROR,
                            {"available_columns": list(df.columns)}
                        )
            
            # Default to first column for x if not specified
            if not x and not df.empty:
                x = df.columns[0]
                
            # Default to second column for y if not specified
            if not y and len(df.columns) > 1:
                y = df.columns[1]
                
            # Create figure based on chart type
            if chart_type == "line":
                fig = px.line(df, x=x, y=y, color=color, text=text, 
                              hover_data=hover_data, animation_frame=animation_frame)
            elif chart_type == "bar":
                fig = px.bar(df, x=x, y=y, color=color, text=text, 
                             hover_data=hover_data, animation_frame=animation_frame)
            elif chart_type == "scatter":
                fig = px.scatter(df, x=x, y=y, color=color, size=size, text=text, 
                                 hover_data=hover_data, animation_frame=animation_frame)
            elif chart_type == "pie":
                fig = px.pie(df, names=x, values=y, color=color, hover_data=hover_data)
            elif chart_type == "area":
                fig = px.area(df, x=x, y=y, color=color, text=text, 
                              hover_data=hover_data, animation_frame=animation_frame)
            elif chart_type == "histogram":
                fig = px.histogram(df, x=x, y=y, color=color, 
                                   hover_data=hover_data, animation_frame=animation_frame)
            elif chart_type == "heatmap":
                fig = px.density_heatmap(df, x=x, y=y, z=color if color else None, 
                                        animation_frame=animation_frame)
            elif chart_type == "box":
                fig = px.box(df, x=x, y=y, color=color, hover_data=hover_data)
            elif chart_type == "violin":
                fig = px.violin(df, x=x, y=y, color=color, hover_data=hover_data)
            elif chart_type == "sunburst":
                path_cols = [x]
                if y and isinstance(y, list):
                    path_cols.extend(y)
                elif y:
                    path_cols.append(y)
                fig = px.sunburst(df, path=path_cols, values=size)
            elif chart_type == "treemap":
                path_cols = [x]
                if y and isinstance(y, list):
                    path_cols.extend(y)
                elif y:
                    path_cols.append(y)
                fig = px.treemap(df, path=path_cols, values=size)
            elif chart_type == "funnel":
                fig = px.funnel(df, x=x, y=y)
            else:
                # Default to scatter if type is not recognized
                fig = px.scatter(df, x=x, y=y)
            
            # Apply layout options
            layout_options = config.get("layout", {})
            fig.update_layout(
                width=config["width"],
                height=config["height"],
                title=config.get("title", ""),
                **layout_options
            )
            
            return fig
            
        except Exception as e:
            if isinstance(e, VisualizationError):
                raise
            raise VisualizationError(
                f"Failed to generate chart: {str(e)}",
                ErrorCode.CHART_GENERATION_ERROR,
                {"error": str(e), "chart_type": chart_type}
            )
            
    def _figure_to_output(self, fig: go.Figure, output_format: str) -> Tuple[str, Any]:
        """
        Convert Plotly figure to output format.
        
        Args:
            fig: Plotly figure
            output_format: Output format (svg, png, json, html, markdown)
            
        Returns:
            Tuple of (content_type, content_data)
            
        Raises:
            VisualizationError: If conversion fails
        """
        try:
            if output_format == "svg":
                # Generate SVG
                svg_data = to_image(fig, format="svg")
                svg_str = svg_data.decode("utf-8")
                return "image/svg+xml", svg_str
                
            elif output_format == "png":
                # Generate PNG
                png_data = to_image(fig, format="png")
                b64_png = base64.b64encode(png_data).decode("utf-8")
                return "image/png;base64", b64_png
                
            elif output_format == "json":
                # Generate JSON representation
                json_data = to_json(fig)
                return "application/json", json.loads(json_data)
                
            elif output_format == "html":
                # Generate HTML
                buffer = io.StringIO()
                write_html(fig, file=buffer, include_plotlyjs="cdn", full_html=True)
                return "text/html", buffer.getvalue()
                
            elif output_format == "markdown":
                # Generate Markdown with embedded SVG
                svg_data = to_image(fig, format="svg")
                svg_str = svg_data.decode("utf-8")
                md_content = f"```html\n{svg_str}\n```"
                return "text/markdown", md_content
                
            else:
                raise VisualizationError(
                    f"Unsupported output format: {output_format}",
                    ErrorCode.INVALID_OUTPUT_FORMAT,
                    {"supported_formats": self.SUPPORTED_FORMATS}
                )
                
        except Exception as e:
            if isinstance(e, VisualizationError):
                raise
            raise VisualizationError(
                f"Failed to convert to {output_format}: {str(e)}",
                ErrorCode.CHART_CONVERSION_ERROR,
                {"error": str(e), "format": output_format}
            )
            
    def create_visualization(
        self,
        query_result: QueryResult,
        chart_type: str,
        config: Optional[Dict[str, Any]] = None,
        output_format: Optional[str] = None
    ) -> ChartData:
        """
        Create a visualization from query results.
        
        Args:
            query_result: Query result object
            chart_type: Type of chart to generate
            config: Chart configuration
            output_format: Output format (svg, png, json, html, markdown)
            
        Returns:
            ChartData object with visualization content
            
        Raises:
            VisualizationError: If visualization generation fails
        """
        # Set defaults
        config = config or {}
        output_format = output_format or self.default_format
        output_format = output_format.lower()
        
        if output_format not in self.SUPPORTED_FORMATS:
            raise VisualizationError(
                f"Unsupported output format: {output_format}",
                ErrorCode.INVALID_OUTPUT_FORMAT,
                {"supported_formats": self.SUPPORTED_FORMATS}
            )
        
        # Validate chart configuration
        validated_config = self._validate_chart_config(chart_type, config)
        
        # Convert query result to DataFrame
        df = self._query_result_to_dataframe(query_result)
        
        # Generate Plotly figure
        fig = self._generate_plotly_figure(df, chart_type, validated_config)
        
        # Convert to requested output format
        content_type, content_data = self._figure_to_output(fig, output_format)
        
        # Create chart data object
        chart_data = ChartData(
            chart_type=chart_type,
            format=output_format,
            content_type=content_type,
            content=content_data,
            config=validated_config
        )
        
        return chart_data
    
    def suggest_visualizations(self, query_result: QueryResult) -> List[Dict[str, Any]]:
        """
        Suggest appropriate visualizations based on query results.
        
        Args:
            query_result: Query result object
            
        Returns:
            List of visualization suggestions with chart type and config
            
        Raises:
            VisualizationError: If suggestion generation fails
        """
        try:
            # Convert query result to DataFrame
            df = self._query_result_to_dataframe(query_result)
            
            # If no data, return empty list
            if df.empty:
                return []
            
            suggestions = []
            column_names = list(df.columns)
            
            # Check for numeric columns
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            
            # Check for datetime columns (or string columns that could be dates)
            date_cols = []
            for col in df.columns:
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    date_cols.append(col)
                elif pd.api.types.is_string_dtype(df[col]):
                    # Try to convert to datetime
                    try:
                        pd.to_datetime(df[col], errors='raise')
                        date_cols.append(col)
                    except:
                        pass
            
            # Categorical columns (string columns with few unique values)
            categorical_cols = []
            for col in df.select_dtypes(include=['object']).columns:
                if df[col].nunique() <= 20:  # Limit to columns with reasonable number of categories
                    categorical_cols.append(col)
            
            # Make suggestions based on column types
            
            # If we have datetime and numeric columns, suggest a line chart
            if date_cols and numeric_cols:
                suggestions.append({
                    "chart_type": "line",
                    "config": {
                        "x": date_cols[0],
                        "y": numeric_cols[0],
                        "title": f"{numeric_cols[0]} over time"
                    }
                })
            
            # If we have multiple numeric columns, suggest a scatter plot
            if len(numeric_cols) >= 2:
                suggestions.append({
                    "chart_type": "scatter",
                    "config": {
                        "x": numeric_cols[0],
                        "y": numeric_cols[1],
                        "title": f"{numeric_cols[1]} vs {numeric_cols[0]}"
                    }
                })
            
            # If we have categorical and numeric columns, suggest a bar chart
            if categorical_cols and numeric_cols:
                suggestions.append({
                    "chart_type": "bar",
                    "config": {
                        "x": categorical_cols[0],
                        "y": numeric_cols[0],
                        "title": f"{numeric_cols[0]} by {categorical_cols[0]}"
                    }
                })
                
                # Also suggest a pie chart if the categorical column has few values
                if df[categorical_cols[0]].nunique() <= 8:
                    suggestions.append({
                        "chart_type": "pie",
                        "config": {
                            "x": categorical_cols[0],
                            "y": numeric_cols[0],
                            "title": f"Distribution of {numeric_cols[0]} by {categorical_cols[0]}"
                        }
                    })
            
            # If we have two categorical columns and a numeric column, suggest a heatmap
            if len(categorical_cols) >= 2 and numeric_cols:
                suggestions.append({
                    "chart_type": "heatmap",
                    "config": {
                        "x": categorical_cols[0],
                        "y": categorical_cols[1],
                        "color": numeric_cols[0],
                        "title": f"{numeric_cols[0]} by {categorical_cols[0]} and {categorical_cols[1]}"
                    }
                })
            
            # Suggest a histogram for numeric data
            if numeric_cols:
                suggestions.append({
                    "chart_type": "histogram",
                    "config": {
                        "x": numeric_cols[0],
                        "title": f"Distribution of {numeric_cols[0]}"
                    }
                })
            
            # Suggest a box plot for numeric data with categories
            if numeric_cols and categorical_cols:
                suggestions.append({
                    "chart_type": "box",
                    "config": {
                        "x": categorical_cols[0],
                        "y": numeric_cols[0],
                        "title": f"Distribution of {numeric_cols[0]} by {categorical_cols[0]}"
                    }
                })
            
            return suggestions
            
        except Exception as e:
            # Log error but return empty list rather than failing
            print(f"Error generating visualization suggestions: {str(e)}")
            return []


# Create singleton instance
visualization_service = VisualizationService() 