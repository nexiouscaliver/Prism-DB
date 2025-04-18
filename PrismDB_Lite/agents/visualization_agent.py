import logging
import json
from typing import Dict, Any, List, Optional
import random
import colorsys

from .base import BaseAgent

logger = logging.getLogger("prismdb.agent.visualization")

# Chart type recommendations based on data characteristics
CHART_RECOMMENDATIONS = {
    "time_series": {
        "criteria": {
            "has_date_column": True,
            "column_count": {"min": 2, "max": None},
            "row_count": {"min": 2, "max": None}
        },
        "chart_type": "line",
        "description": "Shows evolution over time"
    },
    "single_value": {
        "criteria": {
            "column_count": {"min": 1, "max": 1},
            "row_count": {"min": 1, "max": 1}
        },
        "chart_type": "value",
        "description": "Displays a single scalar value"
    },
    "comparison": {
        "criteria": {
            "column_count": {"min": 2, "max": 2},
            "row_count": {"min": 1, "max": 10}
        },
        "chart_type": "bar",
        "description": "Compares values across categories"
    },
    "distribution": {
        "criteria": {
            "column_count": {"min": 1, "max": 2},
            "has_numeric_column": True,
            "row_count": {"min": 10, "max": None}
        },
        "chart_type": "histogram",
        "description": "Shows distribution of values"
    },
    "relationship": {
        "criteria": {
            "column_count": {"min": 2, "max": 3},
            "has_numeric_columns": 2,
            "row_count": {"min": 5, "max": None}
        },
        "chart_type": "scatter",
        "description": "Shows relationship between variables"
    },
    "part_to_whole": {
        "criteria": {
            "column_count": {"min": 2, "max": 2},
            "row_count": {"min": 2, "max": 10}
        },
        "chart_type": "pie",
        "description": "Shows composition of a whole"
    },
    "hierarchical": {
        "criteria": {
            "column_count": {"min": 2, "max": 3},
            "has_hierarchical_data": True,
            "row_count": {"min": 5, "max": None}
        },
        "chart_type": "treemap",
        "description": "Shows hierarchical data"
    }
}

class VisualizationAgent(BaseAgent):
    """
    Visualization Agent generates chart configurations for query results.
    """
    
    def __init__(self, name="visualization_agent", config=None):
        """
        Initialize the visualization agent.
        
        Args:
            name (str): Name of the agent
            config (dict, optional): Configuration for the agent
        """
        super().__init__(name, config)
    
    async def process(self, message, context=None):
        """
        Process a message and generate visualization configurations.
        
        Args:
            message (dict): The message to process
            context (dict, optional): Additional context for processing
            
        Returns:
            dict: Visualization configurations
        """
        context = context or {}
        
        # Get the data to visualize
        data = message.get("data", {})
        if not data:
            self.log_thought("No data provided for visualization")
            return {"error": "No data provided for visualization"}
        
        # Get the intent from context if available
        intent = context.get("intent", {})
        intent_name = intent.get("name", "") if isinstance(intent, dict) else ""
        
        # Get the original query from context if available
        original_query = context.get("original_query", "")
        
        self.log_thought(f"Generating visualization for data with intent: {intent_name}")
        
        try:
            # Analyze the data
            data_analysis = self._analyze_data(data)
            
            # Determine appropriate visualization type
            viz_recommendation = self._recommend_visualization(data_analysis, intent_name, original_query)
            
            # Generate chart configuration
            chart_config = self._generate_chart_config(data, viz_recommendation, data_analysis)
            
            return {
                "visualization": chart_config,
                "data_analysis": data_analysis,
                "recommendation": viz_recommendation
            }
        except Exception as e:
            self.logger.error(f"Error generating visualization: {str(e)}")
            return {"error": f"Visualization generation failed: {str(e)}"}
    
    def _analyze_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the data to determine its characteristics.
        
        Args:
            data (dict): The data to analyze
            
        Returns:
            dict: Analysis of the data
        """
        columns = data.get("columns", [])
        rows = data.get("data", [])
        
        analysis = {
            "column_count": len(columns),
            "row_count": len(rows),
            "columns": {},
            "has_date_column": False,
            "has_numeric_column": False,
            "has_numeric_columns": 0,
            "has_categorical_column": False,
            "has_hierarchical_data": False
        }
        
        # Analyze each column
        for col_idx, col_name in enumerate(columns):
            col_analysis = self._analyze_column(rows, col_idx, col_name)
            analysis["columns"][col_name] = col_analysis
            
            # Update overall analysis based on column
            if col_analysis["type"] == "date":
                analysis["has_date_column"] = True
            elif col_analysis["type"] == "numeric":
                analysis["has_numeric_column"] = True
                analysis["has_numeric_columns"] += 1
            elif col_analysis["type"] == "categorical":
                analysis["has_categorical_column"] = True
        
        # Check if data might be hierarchical
        if analysis["has_categorical_column"] and analysis["column_count"] >= 2:
            # Simple heuristic: if one categorical column has fewer unique values than another
            categorical_cols = [
                col for col, col_data in analysis["columns"].items()
                if col_data["type"] == "categorical"
            ]
            if len(categorical_cols) >= 2:
                unique_counts = [
                    analysis["columns"][col]["unique_count"] for col in categorical_cols
                ]
                if max(unique_counts) / min(unique_counts) > 2:
                    analysis["has_hierarchical_data"] = True
        
        return analysis
    
    def _analyze_column(self, rows: List[Dict[str, Any]], col_idx: int, col_name: str) -> Dict[str, Any]:
        """
        Analyze a specific column in the data.
        
        Args:
            rows (list): The data rows
            col_idx (int): Index of the column
            col_name (str): Name of the column
            
        Returns:
            dict: Analysis of the column
        """
        col_analysis = {
            "type": "unknown",
            "unique_count": 0,
            "min_value": None,
            "max_value": None,
            "avg_value": None,
            "sample_values": []
        }
        
        # Get values for this column
        values = []
        for row in rows:
            try:
                val = row.get(col_name)
                values.append(val)
                
                # Collect sample values (up to 5)
                if len(col_analysis["sample_values"]) < 5 and val is not None:
                    if val not in col_analysis["sample_values"]:
                        col_analysis["sample_values"].append(val)
            except (KeyError, IndexError):
                continue
        
        # Count unique values
        unique_values = set()
        for val in values:
            if val is not None:
                unique_values.add(str(val))
        col_analysis["unique_count"] = len(unique_values)
        
        # Determine column type
        numeric_count = 0
        date_indicators = ["date", "time", "year", "month", "day"]
        
        # Check if column name suggests date
        col_name_lower = col_name.lower()
        is_date_name = any(indicator in col_name_lower for indicator in date_indicators)
        
        # Count numeric values
        for val in values:
            if val is not None:
                try:
                    float(val)
                    numeric_count += 1
                except (ValueError, TypeError):
                    pass
        
        # Determine type based on values
        if is_date_name or (len(values) > 0 and all(self._is_date(val) for val in values if val is not None)):
            col_analysis["type"] = "date"
        elif numeric_count / len(values) > 0.7 if values else False:
            col_analysis["type"] = "numeric"
            
            # Calculate numeric statistics
            numeric_values = []
            for val in values:
                try:
                    if val is not None:
                        numeric_values.append(float(val))
                except (ValueError, TypeError):
                    pass
            
            if numeric_values:
                col_analysis["min_value"] = min(numeric_values)
                col_analysis["max_value"] = max(numeric_values)
                col_analysis["avg_value"] = sum(numeric_values) / len(numeric_values)
        elif col_analysis["unique_count"] < 0.5 * len(values) if values else False:
            col_analysis["type"] = "categorical"
        else:
            col_analysis["type"] = "text"
        
        return col_analysis
    
    def _is_date(self, value) -> bool:
        """
        Check if a value is likely a date.
        
        Args:
            value: The value to check
            
        Returns:
            bool: True if the value is likely a date
        """
        if value is None:
            return False
        
        # Check common date formats
        value_str = str(value).lower()
        
        # Check for date separators
        has_separators = "/" in value_str or "-" in value_str or "." in value_str
        
        # Check for common date patterns
        date_patterns = [
            r"\d{4}-\d{2}-\d{2}",  # YYYY-MM-DD
            r"\d{2}/\d{2}/\d{4}",  # MM/DD/YYYY
            r"\d{2}-\d{2}-\d{4}",  # DD-MM-YYYY
            r"\d{4}/\d{2}/\d{2}"   # YYYY/MM/DD
        ]
        
        # Simple heuristic - if it has separators and 2-4 digits, it might be a date
        if has_separators and sum(c.isdigit() for c in value_str) >= 4:
            return True
        
        # Check for year
        if value_str.isdigit() and 1900 <= int(value_str) <= 2100:
            return True
        
        return False
    
    def _recommend_visualization(self, data_analysis: Dict[str, Any], intent: str, query: str) -> Dict[str, Any]:
        """
        Recommend a visualization type based on data analysis.
        
        Args:
            data_analysis (dict): Analysis of the data
            intent (str): The intent from NLU
            query (str): The original query
            
        Returns:
            dict: Visualization recommendation
        """
        self.log_thought("Recommending visualization type based on data analysis")
        
        # First, check if intent or query explicitly mention chart types
        chart_type = self._extract_chart_type_from_intent(intent, query)
        if chart_type:
            self.log_thought(f"Chart type {chart_type} explicitly requested")
            return {
                "chart_type": chart_type,
                "reason": "Explicitly requested in query",
                "confidence": 0.9
            }
        
        # Score each chart type based on criteria match
        chart_scores = {}
        for chart_name, chart_info in CHART_RECOMMENDATIONS.items():
            score = self._score_chart_match(chart_info["criteria"], data_analysis)
            chart_scores[chart_name] = score
        
        # Get the best matching chart type
        best_match = max(chart_scores.items(), key=lambda x: x[1])
        chart_name, confidence = best_match
        
        if confidence < 0.5:
            # Fall back to a safe default if confidence is low
            if data_analysis["row_count"] <= 10:
                chart_type = "bar"
                reason = "Default for small datasets"
            else:
                chart_type = "table"
                reason = "Default for large datasets"
            confidence = 0.5
        else:
            chart_type = CHART_RECOMMENDATIONS[chart_name]["chart_type"]
            reason = CHART_RECOMMENDATIONS[chart_name]["description"]
        
        return {
            "chart_type": chart_type,
            "reason": reason,
            "confidence": confidence
        }
    
    def _extract_chart_type_from_intent(self, intent: str, query: str) -> Optional[str]:
        """
        Extract explicitly requested chart type from intent or query.
        
        Args:
            intent (str): The intent from NLU
            query (str): The original query
            
        Returns:
            str or None: Explicitly requested chart type
        """
        # Check intent
        intent_lower = intent.lower()
        if "trend" in intent_lower or "over time" in intent_lower:
            return "line"
        elif "compare" in intent_lower:
            return "bar"
        elif "distribution" in intent_lower:
            return "histogram"
        elif "correlation" in intent_lower or "relationship" in intent_lower:
            return "scatter"
        
        # Check query
        query_lower = query.lower()
        chart_keywords = {
            "bar chart": "bar",
            "bar graph": "bar",
            "pie chart": "pie",
            "line chart": "line",
            "line graph": "line",
            "scatter plot": "scatter",
            "histogram": "histogram",
            "treemap": "treemap",
            "heatmap": "heatmap"
        }
        
        for keyword, chart_type in chart_keywords.items():
            if keyword in query_lower:
                return chart_type
        
        return None
    
    def _score_chart_match(self, criteria: Dict[str, Any], data_analysis: Dict[str, Any]) -> float:
        """
        Score how well the data matches the criteria for a chart type.
        
        Args:
            criteria (dict): Criteria for a chart type
            data_analysis (dict): Analysis of the data
            
        Returns:
            float: Score between 0 and 1
        """
        score = 0
        max_possible = 0
        
        # Check each criterion
        for criterion, expected in criteria.items():
            max_possible += 1
            
            if criterion in data_analysis:
                actual = data_analysis[criterion]
                
                if isinstance(expected, bool):
                    if actual == expected:
                        score += 1
                elif isinstance(expected, int):
                    if actual == expected:
                        score += 1
                    elif actual > expected:
                        score += 0.5
                elif isinstance(expected, dict):
                    min_val = expected.get("min")
                    max_val = expected.get("max")
                    
                    if min_val is not None and max_val is not None:
                        if min_val <= actual <= max_val:
                            score += 1
                        elif actual > max_val:
                            score += 0.3
                        elif actual < min_val:
                            score += 0.1
                    elif min_val is not None:
                        if actual >= min_val:
                            score += 1
                        else:
                            score += 0.1
                    elif max_val is not None:
                        if actual <= max_val:
                            score += 1
                        else:
                            score += 0.1
        
        # Normalize score
        return score / max_possible if max_possible > 0 else 0
    
    def _generate_chart_config(self, data: Dict[str, Any], recommendation: Dict[str, Any], 
                              data_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a chart configuration based on the recommendation.
        
        Args:
            data (dict): The data to visualize
            recommendation (dict): The chart recommendation
            data_analysis (dict): Analysis of the data
            
        Returns:
            dict: Chart configuration
        """
        chart_type = recommendation["chart_type"]
        columns = data.get("columns", [])
        rows = data.get("data", [])
        
        # Base configuration
        config = {
            "type": chart_type,
            "data": {
                "labels": [],
                "datasets": []
            },
            "options": {
                "responsive": True,
                "maintainAspectRatio": False,
                "title": {
                    "display": True,
                    "text": "Data Visualization"
                }
            }
        }
        
        # Generate configuration based on chart type
        if chart_type == "bar":
            config = self._generate_bar_chart_config(columns, rows, data_analysis)
        elif chart_type == "line":
            config = self._generate_line_chart_config(columns, rows, data_analysis)
        elif chart_type == "pie":
            config = self._generate_pie_chart_config(columns, rows, data_analysis)
        elif chart_type == "scatter":
            config = self._generate_scatter_chart_config(columns, rows, data_analysis)
        elif chart_type == "histogram":
            config = self._generate_histogram_config(columns, rows, data_analysis)
        elif chart_type == "value":
            config = self._generate_value_display_config(columns, rows, data_analysis)
        elif chart_type == "table":
            config = self._generate_table_config(columns, rows, data_analysis)
        else:
            # Default to table view
            config = self._generate_table_config(columns, rows, data_analysis)
        
        return config
    
    def _generate_bar_chart_config(self, columns, rows, data_analysis):
        """Generate configuration for a bar chart."""
        # Find a categorical column for labels and a numeric column for values
        label_col = None
        value_col = None
        
        for col, analysis in data_analysis["columns"].items():
            if analysis["type"] == "categorical" and not label_col:
                label_col = col
            elif analysis["type"] == "numeric" and not value_col:
                value_col = col
        
        # Fall back to first and second columns if needed
        if not label_col and len(columns) > 0:
            label_col = columns[0]
        if not value_col and len(columns) > 1:
            value_col = columns[1]
        elif not value_col and len(columns) == 1:
            value_col = columns[0]
        
        # Extract data
        labels = []
        values = []
        
        if label_col and value_col:
            for row in rows:
                label = row.get(label_col)
                value = row.get(value_col)
                
                if label is not None:
                    labels.append(str(label))
                    
                    try:
                        values.append(float(value) if value is not None else 0)
                    except (ValueError, TypeError):
                        values.append(0)
        
        # Generate colors
        colors = self._generate_colors(len(values))
        
        return {
            "type": "bar",
            "data": {
                "labels": labels,
                "datasets": [{
                    "label": value_col,
                    "data": values,
                    "backgroundColor": colors,
                    "borderColor": colors,
                    "borderWidth": 1
                }]
            },
            "options": {
                "responsive": True,
                "maintainAspectRatio": False,
                "title": {
                    "display": True,
                    "text": f"{value_col} by {label_col}"
                },
                "scales": {
                    "y": {
                        "beginAtZero": True
                    }
                }
            }
        }
    
    def _generate_line_chart_config(self, columns, rows, data_analysis):
        """Generate configuration for a line chart."""
        # Find a date column for labels and numeric columns for values
        date_col = None
        value_cols = []
        
        for col, analysis in data_analysis["columns"].items():
            if analysis["type"] == "date" and not date_col:
                date_col = col
            elif analysis["type"] == "numeric":
                value_cols.append(col)
        
        # Fall back to first column for labels if no date column
        if not date_col and len(columns) > 0:
            date_col = columns[0]
        
        # Use at least one value column
        if not value_cols and len(columns) > 1:
            value_cols = [columns[1]]
        
        # Extract data
        labels = []
        datasets = []
        
        if date_col:
            # Extract unique labels
            for row in rows:
                label = row.get(date_col)
                if label is not None and label not in labels:
                    labels.append(label)
            
            # Sort labels if they look like dates
            if all(self._is_date(label) for label in labels):
                labels.sort()
            
            # Create a dataset for each value column
            colors = self._generate_colors(len(value_cols))
            
            for i, value_col in enumerate(value_cols):
                data = []
                
                for label in labels:
                    # Find the row with this label
                    value = 0
                    for row in rows:
                        if row.get(date_col) == label:
                            try:
                                val = row.get(value_col)
                                if val is not None:
                                    value = float(val)
                                break
                            except (ValueError, TypeError):
                                pass
                    
                    data.append(value)
                
                datasets.append({
                    "label": value_col,
                    "data": data,
                    "fill": False,
                    "backgroundColor": colors[i],
                    "borderColor": colors[i],
                    "tension": 0.1
                })
        
        return {
            "type": "line",
            "data": {
                "labels": labels,
                "datasets": datasets
            },
            "options": {
                "responsive": True,
                "maintainAspectRatio": False,
                "title": {
                    "display": True,
                    "text": f"Trends over {date_col}"
                }
            }
        }
    
    def _generate_pie_chart_config(self, columns, rows, data_analysis):
        """Generate configuration for a pie chart."""
        # Find a categorical column for labels and a numeric column for values
        label_col = None
        value_col = None
        
        for col, analysis in data_analysis["columns"].items():
            if analysis["type"] == "categorical" and not label_col:
                label_col = col
            elif analysis["type"] == "numeric" and not value_col:
                value_col = col
        
        # Fall back to first and second columns if needed
        if not label_col and len(columns) > 0:
            label_col = columns[0]
        if not value_col and len(columns) > 1:
            value_col = columns[1]
        elif not value_col and len(columns) == 1:
            value_col = columns[0]
        
        # Extract data
        labels = []
        values = []
        
        if label_col and value_col:
            for row in rows:
                label = row.get(label_col)
                value = row.get(value_col)
                
                if label is not None:
                    labels.append(str(label))
                    
                    try:
                        values.append(float(value) if value is not None else 0)
                    except (ValueError, TypeError):
                        values.append(0)
        
        # Generate colors
        colors = self._generate_colors(len(values))
        
        return {
            "type": "pie",
            "data": {
                "labels": labels,
                "datasets": [{
                    "data": values,
                    "backgroundColor": colors,
                    "borderColor": "white",
                    "borderWidth": 1
                }]
            },
            "options": {
                "responsive": True,
                "maintainAspectRatio": False,
                "title": {
                    "display": True,
                    "text": f"Distribution of {value_col} by {label_col}"
                }
            }
        }
    
    def _generate_scatter_chart_config(self, columns, rows, data_analysis):
        """Generate configuration for a scatter plot."""
        # Find two numeric columns for x and y axes
        x_col = None
        y_col = None
        
        for col, analysis in data_analysis["columns"].items():
            if analysis["type"] == "numeric":
                if not x_col:
                    x_col = col
                elif not y_col:
                    y_col = col
                    break
        
        # Fall back to first two columns if needed
        if not x_col and len(columns) > 0:
            x_col = columns[0]
        if not y_col and len(columns) > 1:
            y_col = columns[1]
        
        # Extract data
        data = []
        
        if x_col and y_col:
            for row in rows:
                x_val = row.get(x_col)
                y_val = row.get(y_col)
                
                try:
                    if x_val is not None and y_val is not None:
                        data.append({
                            "x": float(x_val),
                            "y": float(y_val)
                        })
                except (ValueError, TypeError):
                    pass
        
        return {
            "type": "scatter",
            "data": {
                "datasets": [{
                    "label": f"{y_col} vs {x_col}",
                    "data": data,
                    "backgroundColor": "rgba(75, 192, 192, 0.6)",
                    "borderColor": "rgba(75, 192, 192, 1)",
                    "pointRadius": 6,
                    "pointHoverRadius": 8
                }]
            },
            "options": {
                "responsive": True,
                "maintainAspectRatio": False,
                "title": {
                    "display": True,
                    "text": f"Relationship between {x_col} and {y_col}"
                },
                "scales": {
                    "x": {
                        "title": {
                            "display": True,
                            "text": x_col
                        }
                    },
                    "y": {
                        "title": {
                            "display": True,
                            "text": y_col
                        }
                    }
                }
            }
        }
    
    def _generate_histogram_config(self, columns, rows, data_analysis):
        """Generate configuration for a histogram."""
        # Find a numeric column for the histogram
        value_col = None
        
        for col, analysis in data_analysis["columns"].items():
            if analysis["type"] == "numeric":
                value_col = col
                break
        
        # Fall back to first column if needed
        if not value_col and len(columns) > 0:
            value_col = columns[0]
        
        # Extract values
        values = []
        
        if value_col:
            for row in rows:
                value = row.get(value_col)
                
                try:
                    if value is not None:
                        values.append(float(value))
                except (ValueError, TypeError):
                    pass
        
        # Generate bins
        if values:
            min_val = min(values)
            max_val = max(values)
            
            # Create 10 bins
            bin_width = (max_val - min_val) / 10 if max_val > min_val else 1
            bins = [min_val + i * bin_width for i in range(11)]
            
            # Count values in each bin
            bin_counts = [0] * 10
            
            for value in values:
                for i in range(10):
                    if bins[i] <= value < bins[i+1] or (i == 9 and value == bins[i+1]):
                        bin_counts[i] += 1
                        break
            
            # Generate bin labels
            bin_labels = [f"{bins[i]:.1f} - {bins[i+1]:.1f}" for i in range(10)]
            
            # Generate a color
            color = "rgba(75, 192, 192, 0.6)"
            
            return {
                "type": "bar",
                "data": {
                    "labels": bin_labels,
                    "datasets": [{
                        "label": f"Frequency of {value_col}",
                        "data": bin_counts,
                        "backgroundColor": color,
                        "borderColor": "rgba(75, 192, 192, 1)",
                        "borderWidth": 1
                    }]
                },
                "options": {
                    "responsive": True,
                    "maintainAspectRatio": False,
                    "title": {
                        "display": True,
                        "text": f"Distribution of {value_col}"
                    },
                    "scales": {
                        "y": {
                            "beginAtZero": True,
                            "title": {
                                "display": True,
                                "text": "Frequency"
                            }
                        },
                        "x": {
                            "title": {
                                "display": True,
                                "text": value_col
                            }
                        }
                    }
                }
            }
        
        return {
            "type": "bar",
            "data": {
                "labels": [],
                "datasets": [{
                    "label": "No data",
                    "data": []
                }]
            },
            "options": {
                "responsive": True,
                "maintainAspectRatio": False,
                "title": {
                    "display": True,
                    "text": "No numeric data available for histogram"
                }
            }
        }
    
    def _generate_value_display_config(self, columns, rows, data_analysis):
        """Generate configuration for a single value display."""
        # Get the first value from the first column
        value = None
        label = "Value"
        
        if columns and rows:
            col = columns[0]
            value = rows[0].get(col)
            label = col
        
        return {
            "type": "value",
            "data": {
                "value": value,
                "label": label
            },
            "options": {
                "responsive": True,
                "maintainAspectRatio": False,
                "title": {
                    "display": True,
                    "text": label
                },
                "font": {
                    "size": 36
                }
            }
        }
    
    def _generate_table_config(self, columns, rows, data_analysis):
        """Generate configuration for a table display."""
        return {
            "type": "table",
            "data": {
                "columns": columns,
                "rows": rows
            },
            "options": {
                "responsive": True,
                "maintainAspectRatio": False,
                "title": {
                    "display": True,
                    "text": "Data Table"
                },
                "paging": data_analysis["row_count"] > 10,
                "searching": data_analysis["row_count"] > 10,
                "ordering": True
            }
        }
    
    def _generate_colors(self, count):
        """Generate an array of distinct colors."""
        colors = []
        
        for i in range(count):
            hue = i / count
            saturation = 0.7
            value = 0.9
            
            r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
            color = f"rgba({int(r*255)}, {int(g*255)}, {int(b*255)}, 0.7)"
            colors.append(color)
        
        return colors 