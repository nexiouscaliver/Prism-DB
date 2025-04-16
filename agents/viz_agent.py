"""
VizAgent for PrismDB.

This agent is responsible for generating visualizations from query results.
It supports various chart types and output formats.
"""
from typing import Dict, Any, List, Optional, Tuple, Set, Union
from io import BytesIO
import base64
import json
import re
from datetime import datetime

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import markdown

from agents.base import PrismAgent


# Maximum visualization size in KB
MAX_VIZ_SIZE = 500

# Supported chart types
class ChartType:
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    SCATTER = "scatter"
    HISTOGRAM = "histogram"
    HEATMAP = "heatmap"
    TABLE = "table"


class VizAgent(PrismAgent):
    """Agent for generating visualizations from query results.
    
    This agent creates data visualizations based on query results
    and can output in various formats including SVG, JSON, and Markdown.
    """
    
    def __init__(self):
        """Initialize the VizAgent with appropriate tools and instructions."""
        super().__init__(
            name="VizAgent",
            system_prompt="""You are a VizAgent responsible for creating
            insightful visualizations from SQL query results. You analyze 
            the data structure and select the most appropriate visualization 
            type to convey insights effectively.""",
            instructions=[
                "Analyze data structure to select appropriate chart type",
                "Handle time series data intelligently with line charts",
                "Use bar charts for categorical comparisons",
                "Apply pie charts only for proportion analysis with few categories",
                "Ensure visualizations are clean, labeled, and informative",
                "Provide data-driven insights alongside visualizations",
                "Keep SVG outputs under 500KB for performance"
            ]
        )
    
    def process(self, input_text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process visualization request and generate appropriate chart.
        
        Args:
            input_text: Natural language prompt for visualization
            context: Additional context, including query results and preferences
            
        Returns:
            Dictionary with visualization data
        """
        try:
            # Extract context information
            data = context.get("data", {})
            chart_type = context.get("chart_type", None)
            title = context.get("title", "Query Results")
            
            # If no specific chart type, auto-detect based on data
            if not chart_type:
                chart_type, confidence = self._auto_detect_chart_type(data)
            else:
                confidence = 0.9  # High confidence for user-specified chart type
            
            # Convert to DataFrame if not already
            if isinstance(data, dict) and "rows" in data:
                df = pd.DataFrame(data["rows"])
            elif isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, pd.DataFrame):
                df = data
            else:
                return self.error_response("Invalid data format. Expected DataFrame, dict with 'rows', or list.")
            
            # Validate data is not empty
            if df.empty:
                return self.error_response("No data available for visualization.")
            
            # Generate visualization
            viz_result = self.generate_chart(df, chart_type, title=title)
            
            # Add metadata
            viz_result["data_summary"] = self._generate_data_summary(df)
            viz_result["confidence"] = confidence
            viz_result["chart_type"] = chart_type
            
            return self.success_response(
                "Visualization generated successfully",
                viz_result
            )
        except Exception as e:
            return self.error_response(f"Failed to generate visualization: {str(e)}")
    
    def generate_chart(self, data: pd.DataFrame, chart_type: str, **kwargs) -> Dict[str, Any]:
        """Generate chart visualization from DataFrame.
        
        Args:
            data: Pandas DataFrame with query results
            chart_type: Type of chart to generate (line, bar, pie, etc.)
            **kwargs: Additional arguments for chart configuration
            
        Returns:
            Dictionary with visualization data in various formats
        """
        # Process kwargs
        title = kwargs.get("title", "Query Results")
        width = kwargs.get("width", 800)
        height = kwargs.get("height", 500)
        
        # Convert categorical datetime columns to datetime type
        for col in data.columns:
            # Check if column might contain dates
            if data[col].dtype == 'object' and data[col].notna().any():
                try:
                    # Try to convert to datetime
                    data[col] = pd.to_datetime(data[col])
                except (ValueError, TypeError):
                    # Not a datetime column, continue
                    pass
        
        # Select chart generation method based on type
        if chart_type == ChartType.LINE:
            fig = self._create_line_chart(data, **kwargs)
        elif chart_type == ChartType.BAR:
            fig = self._create_bar_chart(data, **kwargs)
        elif chart_type == ChartType.PIE:
            fig = self._create_pie_chart(data, **kwargs)
        elif chart_type == ChartType.SCATTER:
            fig = self._create_scatter_chart(data, **kwargs)
        elif chart_type == ChartType.HISTOGRAM:
            fig = self._create_histogram(data, **kwargs)
        elif chart_type == ChartType.HEATMAP:
            fig = self._create_heatmap(data, **kwargs)
        elif chart_type == ChartType.TABLE:
            fig = self._create_table(data, **kwargs)
        else:
            # Default to a table if chart type not recognized
            fig = self._create_table(data, **kwargs)
        
        # Apply common layout settings
        fig.update_layout(
            title=title,
            width=width,
            height=height,
            template="plotly_white",  # Clean, modern template
            margin=dict(l=50, r=50, t=80, b=50),
        )
        
        # Generate outputs in different formats
        svg_data = self._fig_to_svg(fig)
        
        # Check SVG size and compress if needed
        svg_size_kb = len(svg_data) / 1024
        if svg_size_kb > MAX_VIZ_SIZE:
            # Reduce quality or size
            width = int(width * (MAX_VIZ_SIZE / svg_size_kb) * 0.9)
            height = int(height * (MAX_VIZ_SIZE / svg_size_kb) * 0.9)
            fig.update_layout(width=width, height=height)
            svg_data = self._fig_to_svg(fig)
        
        # Generate a simplified markdown representation
        markdown_data = self._fig_to_markdown(fig, data)
        
        # Generate a JSON representation for API responses
        json_data = self._fig_to_json(fig)
        
        # Generate summary insights from the data
        insights = self._generate_insights(data, chart_type)
        
        return {
            "svg": svg_data,
            "markdown": markdown_data,
            "json": json_data,
            "insights": insights,
            "size_kb": len(svg_data) / 1024
        }
    
    def _auto_detect_chart_type(self, data: Union[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]]]) -> Tuple[str, float]:
        """Auto-detect the most appropriate chart type based on data structure.
        
        Args:
            data: Data to visualize
            
        Returns:
            Tuple of (chart_type, confidence)
        """
        # Convert to DataFrame if not already
        if isinstance(data, dict) and "rows" in data:
            df = pd.DataFrame(data["rows"])
        elif isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, pd.DataFrame):
            df = data
        else:
            return ChartType.TABLE, 0.6  # Default to table with low confidence
        
        # Check if empty dataset
        if df.empty:
            return ChartType.TABLE, 0.9
        
        # Count different column types
        num_columns = len([col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])])
        date_columns = len([col for col in df.columns if pd.api.types.is_datetime64_dtype(df[col]) or 
                          (df[col].dtype == 'object' and self._might_be_date(df[col]))])
        cat_columns = len(df.columns) - num_columns - date_columns
        
        # Small number of rows with categorical data suggests pie chart
        if len(df) <= 10 and cat_columns >= 1 and num_columns >= 1:
            return ChartType.PIE, 0.8
        
        # Time series data suggests line chart
        if date_columns >= 1 and num_columns >= 1:
            return ChartType.LINE, 0.9
        
        # Multiple numerical columns suggest bar chart
        if num_columns >= 2 and cat_columns >= 1:
            return ChartType.BAR, 0.8
        
        # Two numerical columns suggest scatter plot
        if num_columns == 2 and cat_columns == 0:
            return ChartType.SCATTER, 0.7
        
        # Single numerical column suggests histogram
        if num_columns == 1 and len(df) > 10:
            return ChartType.HISTOGRAM, 0.8
        
        # Multiple categorical columns with numerical data might suggest heatmap
        if cat_columns >= 2 and num_columns >= 1:
            return ChartType.HEATMAP, 0.6
        
        # Default to table for other cases
        return ChartType.TABLE, 0.8
    
    def _might_be_date(self, series: pd.Series) -> bool:
        """Check if a string series might contain dates.
        
        Args:
            series: Pandas Series to check
            
        Returns:
            True if series likely contains dates, False otherwise
        """
        if series.dtype != 'object':
            return False
            
        # Sample the series to check if values look like dates
        sample = series.dropna().head(5).tolist()
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # ISO format: 2023-01-01
            r'\d{2}/\d{2}/\d{4}',  # US format: 01/01/2023
            r'\d{2}-\d{2}-\d{4}',  # Alternative format: 01-01-2023
        ]
        
        for value in sample:
            if not isinstance(value, str):
                continue
            for pattern in date_patterns:
                if re.match(pattern, value):
                    return True
        
        return False
    
    def _create_line_chart(self, df: pd.DataFrame, **kwargs) -> go.Figure:
        """Create a line chart.
        
        Args:
            df: DataFrame with data
            **kwargs: Additional configuration options
            
        Returns:
            Plotly figure
        """
        # Identify potential x-axis (prefer date/time column)
        x_col = kwargs.get("x_col")
        y_cols = kwargs.get("y_cols", [])
        
        if not x_col:
            # Try to find a date column for x-axis
            date_cols = [col for col in df.columns if pd.api.types.is_datetime64_dtype(df[col])]
            if date_cols:
                x_col = date_cols[0]
            else:
                # Fall back to first column
                x_col = df.columns[0]
        
        # If no y_cols specified, use all numeric columns
        if not y_cols:
            y_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col]) and col != x_col]
        
        # If we have multiple y columns, create a line for each
        if len(y_cols) > 1:
            fig = go.Figure()
            for col in y_cols:
                fig.add_trace(go.Scatter(
                    x=df[x_col],
                    y=df[col],
                    mode='lines+markers',
                    name=col
                ))
        else:
            # Single line chart
            y_col = y_cols[0] if y_cols else df.columns[1]
            fig = px.line(
                df, 
                x=x_col, 
                y=y_col,
                markers=True,
                labels={x_col: x_col, y_col: y_col}
            )
        
        return fig
    
    def _create_bar_chart(self, df: pd.DataFrame, **kwargs) -> go.Figure:
        """Create a bar chart.
        
        Args:
            df: DataFrame with data
            **kwargs: Additional configuration options
            
        Returns:
            Plotly figure
        """
        x_col = kwargs.get("x_col")
        y_cols = kwargs.get("y_cols", [])
        orientation = kwargs.get("orientation", "v")  # v for vertical, h for horizontal
        
        # If no columns specified, try to infer them
        if not x_col:
            # Choose first non-numeric column for x
            for col in df.columns:
                if not pd.api.types.is_numeric_dtype(df[col]):
                    x_col = col
                    break
            # If no non-numeric column, use first column
            if not x_col:
                x_col = df.columns[0]
        
        # If no y_cols specified, use all numeric columns
        if not y_cols:
            y_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col]) and col != x_col]
            if not y_cols and len(df.columns) > 1:
                y_cols = [df.columns[1]]
        
        # If we have a single y column
        if len(y_cols) == 1:
            y_col = y_cols[0]
            if orientation == "h":
                fig = px.bar(
                    df, 
                    y=x_col, 
                    x=y_col, 
                    orientation="h",
                    labels={x_col: x_col, y_col: y_col}
                )
            else:
                fig = px.bar(
                    df, 
                    x=x_col, 
                    y=y_col,
                    labels={x_col: x_col, y_col: y_col}
                )
        else:
            # Multiple y columns - group bars
            fig = go.Figure()
            for col in y_cols:
                if orientation == "h":
                    fig.add_trace(go.Bar(
                        y=df[x_col],
                        x=df[col],
                        name=col,
                        orientation="h"
                    ))
                else:
                    fig.add_trace(go.Bar(
                        x=df[x_col],
                        y=df[col],
                        name=col
                    ))
            
            # Update layout for grouped bars
            fig.update_layout(barmode='group')
        
        return fig
    
    def _create_pie_chart(self, df: pd.DataFrame, **kwargs) -> go.Figure:
        """Create a pie chart.
        
        Args:
            df: DataFrame with data
            **kwargs: Additional configuration options
            
        Returns:
            Plotly figure
        """
        label_col = kwargs.get("label_col")
        value_col = kwargs.get("value_col")
        
        # If columns not specified, try to infer them
        if not label_col:
            # Look for non-numeric column for labels
            for col in df.columns:
                if not pd.api.types.is_numeric_dtype(df[col]):
                    label_col = col
                    break
            # If no non-numeric column, use first column
            if not label_col:
                label_col = df.columns[0]
        
        if not value_col:
            # Look for numeric column for values
            for col in df.columns:
                if pd.api.types.is_numeric_dtype(df[col]) and col != label_col:
                    value_col = col
                    break
            # If no numeric column, use second column or count
            if not value_col and len(df.columns) > 1:
                value_col = df.columns[1]
            elif not value_col:
                # Add a count column if no appropriate value column
                df['count'] = 1
                value_col = 'count'
        
        # Ensure we don't have too many slices (limit to 10)
        if len(df) > 10:
            # Sort by value, keep top 9 and group rest as "Other"
            df = df.sort_values(by=value_col, ascending=False)
            top_df = df.head(9)
            other_sum = df.iloc[9:][value_col].sum()
            
            if other_sum > 0:
                other_row = pd.DataFrame({label_col: ['Other'], value_col: [other_sum]})
                df = pd.concat([top_df, other_row])
        
        # Create pie chart
        fig = px.pie(
            df,
            names=label_col,
            values=value_col,
            labels={label_col: label_col, value_col: value_col}
        )
        
        # Improve pie chart appearance
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hole=0.3,  # Donut hole
            pull=[0.05] + [0] * (len(df) - 1),  # Pull out the largest slice slightly
        )
        
        return fig
    
    def _create_scatter_chart(self, df: pd.DataFrame, **kwargs) -> go.Figure:
        """Create a scatter plot.
        
        Args:
            df: DataFrame with data
            **kwargs: Additional configuration options
            
        Returns:
            Plotly figure
        """
        x_col = kwargs.get("x_col")
        y_col = kwargs.get("y_col")
        color_col = kwargs.get("color_col")
        size_col = kwargs.get("size_col")
        
        # If columns not specified, try to infer them
        if not x_col or not y_col:
            # Look for numeric columns
            num_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
            
            if len(num_cols) >= 2:
                if not x_col:
                    x_col = num_cols[0]
                if not y_col:
                    y_col = num_cols[1]
            else:
                # Fall back to first two columns
                if not x_col:
                    x_col = df.columns[0]
                if not y_col and len(df.columns) > 1:
                    y_col = df.columns[1]
                else:
                    y_col = x_col  # Last resort
        
        # Create scatter plot
        fig = px.scatter(
            df,
            x=x_col,
            y=y_col,
            color=color_col if color_col and color_col in df.columns else None,
            size=size_col if size_col and size_col in df.columns else None,
            labels={
                x_col: x_col,
                y_col: y_col,
                color_col: color_col if color_col else "",
                size_col: size_col if size_col else ""
            }
        )
        
        # Add trendline if both axes are numeric
        if (pd.api.types.is_numeric_dtype(df[x_col]) and 
            pd.api.types.is_numeric_dtype(df[y_col])):
            fig.add_trace(
                px.scatter(
                    df, x=x_col, y=y_col, trendline="ols"
                ).data[1]
            )
        
        return fig
    
    def _create_histogram(self, df: pd.DataFrame, **kwargs) -> go.Figure:
        """Create a histogram.
        
        Args:
            df: DataFrame with data
            **kwargs: Additional configuration options
            
        Returns:
            Plotly figure
        """
        value_col = kwargs.get("value_col")
        bins = kwargs.get("bins", 20)
        
        # If column not specified, try to infer it
        if not value_col:
            # Look for numeric column
            for col in df.columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    value_col = col
                    break
            # If no numeric column, use first column
            if not value_col:
                value_col = df.columns[0]
        
        # Create histogram
        fig = px.histogram(
            df,
            x=value_col,
            nbins=bins,
            labels={value_col: value_col}
        )
        
        # Enhance appearance
        fig.update_traces(
            opacity=0.75,
            marker_line=dict(width=1, color="white")
        )
        
        return fig
    
    def _create_heatmap(self, df: pd.DataFrame, **kwargs) -> go.Figure:
        """Create a heatmap.
        
        Args:
            df: DataFrame with data
            **kwargs: Additional configuration options
            
        Returns:
            Plotly figure
        """
        x_col = kwargs.get("x_col")
        y_col = kwargs.get("y_col")
        value_col = kwargs.get("value_col")
        
        # If columns not specified, try to infer them
        if not x_col or not y_col:
            # Look for categorical columns
            cat_cols = [col for col in df.columns if not pd.api.types.is_numeric_dtype(df[col])]
            
            if len(cat_cols) >= 2:
                if not x_col:
                    x_col = cat_cols[0]
                if not y_col:
                    y_col = cat_cols[1]
            else:
                # Fall back to first two columns
                if not x_col:
                    x_col = df.columns[0]
                if not y_col and len(df.columns) > 1:
                    y_col = df.columns[1]
                else:
                    y_col = x_col  # Last resort
        
        if not value_col:
            # Look for numeric column for values
            for col in df.columns:
                if (pd.api.types.is_numeric_dtype(df[col]) and 
                    col != x_col and col != y_col):
                    value_col = col
                    break
            # If no numeric column, use count of occurrences
            if not value_col:
                pivot_df = pd.crosstab(df[y_col], df[x_col])
            else:
                pivot_df = df.pivot_table(
                    values=value_col, 
                    index=y_col, 
                    columns=x_col, 
                    aggfunc='mean'
                )
        else:
            pivot_df = df.pivot_table(
                values=value_col, 
                index=y_col, 
                columns=x_col, 
                aggfunc='mean'
            )
        
        # Create heatmap
        fig = px.imshow(
            pivot_df, 
            labels=dict(x=x_col, y=y_col, color=value_col or "Count"),
            color_continuous_scale="YlGnBu"
        )
        
        return fig
    
    def _create_table(self, df: pd.DataFrame, **kwargs) -> go.Figure:
        """Create a table visualization.
        
        Args:
            df: DataFrame with data
            **kwargs: Additional configuration options
            
        Returns:
            Plotly figure
        """
        # Limit rows for performance
        max_rows = kwargs.get("max_rows", 20)
        if len(df) > max_rows:
            df = df.head(max_rows)
        
        # Create table
        fig = go.Figure(data=[go.Table(
            header=dict(
                values=list(df.columns),
                fill_color='lightgrey',
                align='left',
                font=dict(size=12, color='black')
            ),
            cells=dict(
                values=[df[col] for col in df.columns],
                fill_color='white',
                align='left',
                font=dict(size=11, color='black')
            )
        )])
        
        return fig
    
    def _fig_to_svg(self, fig: go.Figure) -> str:
        """Convert Plotly figure to SVG string.
        
        Args:
            fig: Plotly figure
            
        Returns:
            SVG as string
        """
        return fig.to_image(format="svg").decode("utf-8")
    
    def _fig_to_json(self, fig: go.Figure) -> Dict[str, Any]:
        """Convert Plotly figure to JSON for API responses.
        
        Args:
            fig: Plotly figure
            
        Returns:
            Figure as JSON
        """
        return json.loads(fig.to_json())
    
    def _fig_to_markdown(self, fig: go.Figure, df: pd.DataFrame) -> str:
        """Convert Plotly figure to Markdown representation.
        
        For Markdown, we can't include the actual visualization,
        so we provide a summary and a small sample of the data.
        
        Args:
            fig: Plotly figure
            df: DataFrame with the data
            
        Returns:
            Markdown string
        """
        # Get figure title
        title = fig.layout.title.text if fig.layout.title.text else "Data Visualization"
        
        # Generate summary statistics
        summary = self._generate_data_summary(df)
        
        # Convert a small sample of the dataframe to markdown table
        sample_df = df.head(5)
        table_md = sample_df.to_markdown(index=False) if hasattr(df, 'to_markdown') else str(sample_df)
        
        # Build markdown content
        md_content = f"""
# {title}

## Data Summary
- **Rows**: {summary['row_count']}
- **Columns**: {summary['column_count']}
- **Types**: {', '.join(f"{k}: {v}" for k, v in summary['column_types'].items())}

## Data Sample
{table_md}

*Note: This is a text representation. The actual visualization would be shown in the UI.*
        """
        
        return md_content
    
    def _generate_data_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate summary statistics for the data.
        
        Args:
            df: DataFrame with data
            
        Returns:
            Dictionary with data summary
        """
        # Count column types
        column_types = {}
        for col in df.columns:
            dtype = str(df[col].dtype)
            if dtype in column_types:
                column_types[dtype] += 1
            else:
                column_types[dtype] = 1
        
        # Generate basic summary
        summary = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "column_types": column_types,
            "column_names": list(df.columns),
            "timestamp": datetime.now().isoformat()
        }
        
        # Add numerical column statistics if present
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if num_cols:
            # Calculate statistics only for numerical columns
            num_stats = df[num_cols].describe().to_dict()
            summary["numerical_stats"] = num_stats
        
        # Add categorical column statistics if present
        cat_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()
        if cat_cols:
            cat_stats = {}
            for col in cat_cols:
                # Get top 5 most frequent values
                value_counts = df[col].value_counts().head(5).to_dict()
                cat_stats[col] = {
                    "top_values": value_counts,
                    "unique_count": df[col].nunique()
                }
            summary["categorical_stats"] = cat_stats
        
        return summary
    
    def _generate_insights(self, df: pd.DataFrame, chart_type: str) -> List[str]:
        """Generate data-driven insights based on the visualization.
        
        Args:
            df: DataFrame with data
            chart_type: Type of chart being generated
            
        Returns:
            List of insight strings
        """
        insights = []
        
        # Basic data statistics
        row_count = len(df)
        col_count = len(df.columns)
        insights.append(f"Dataset contains {row_count} records with {col_count} attributes.")
        
        # Specific insights based on chart type
        if chart_type == ChartType.LINE:
            # Find date/time columns
            date_cols = [col for col in df.columns if pd.api.types.is_datetime64_dtype(df[col])]
            if date_cols:
                date_col = date_cols[0]
                insights.append(f"Time range spans from {df[date_col].min()} to {df[date_col].max()}.")
                
                # Find numeric columns to analyze trends
                num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                for col in num_cols[:2]:  # Limit to first 2 numeric columns
                    # Check if we can calculate trend
                    if len(df) > 2:
                        # Simplistic trend analysis
                        first_val = df[col].iloc[0]
                        last_val = df[col].iloc[-1]
                        if first_val != 0:
                            percent_change = ((last_val - first_val) / abs(first_val)) * 100
                            trend = "increased" if percent_change > 0 else "decreased"
                            insights.append(f"{col} {trend} by {abs(percent_change):.1f}% over the period.")
        
        elif chart_type == ChartType.BAR:
            # Analyze categorical distributions
            cat_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()
            num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            
            if cat_cols and num_cols:
                cat_col = cat_cols[0]
                num_col = num_cols[0]
                
                # Find top category
                if len(df) > 0:
                    try:
                        top_category = df.groupby(cat_col)[num_col].sum().idxmax()
                        insights.append(f"'{top_category}' has the highest total for {num_col}.")
                    except:
                        pass
        
        elif chart_type == ChartType.PIE:
            # Analyze part-to-whole relationships
            if len(df.columns) >= 2:
                # Assume first column is category, second is value
                cat_col = df.columns[0]
                val_col = df.columns[1]
                
                if pd.api.types.is_numeric_dtype(df[val_col]):
                    # Calculate how much top 3 categories contribute
                    total = df[val_col].sum()
                    if total > 0:
                        top3 = df.nlargest(3, val_col)
                        top3_pct = (top3[val_col].sum() / total) * 100
                        insights.append(f"Top 3 categories account for {top3_pct:.1f}% of the total.")
        
        # Add general quality warnings if needed
        if row_count > 1000 and chart_type not in [ChartType.TABLE, ChartType.HEATMAP]:
            insights.append("Large dataset detected - visualization may benefit from filtering or aggregation.")
        
        missing_data = df.isnull().sum().sum()
        if missing_data > 0:
            insights.append(f"Dataset contains {missing_data} missing values that might affect visualization quality.")
        
        return insights 