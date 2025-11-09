"""
Data Processing Script
A comprehensive Python script for data processing with CSV/JSON support,
data cleaning, transformation, analysis, and visualization.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_processing.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class DataProcessor:
    """Main class for data processing operations"""
    
    def __init__(self, input_file, output_dir='output'):
        """
        Initialize the DataProcessor
        
        Args:
            input_file (str): Path to input data file (CSV or JSON)
            output_dir (str): Directory for output files
        """
        self.input_file = Path(input_file)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.df = None
        self.original_shape = None
        
        logger.info(f"DataProcessor initialized with input: {input_file}")
    
    def load_data(self):
        """Load data from CSV or JSON file"""
        try:
            if self.input_file.suffix.lower() == '.csv':
                self.df = pd.read_csv(self.input_file)
                logger.info(f"Loaded CSV file: {self.input_file}")
            elif self.input_file.suffix.lower() == '.json':
                self.df = pd.read_json(self.input_file)
                logger.info(f"Loaded JSON file: {self.input_file}")
            else:
                raise ValueError(f"Unsupported file format: {self.input_file.suffix}")
            
            self.original_shape = self.df.shape
            logger.info(f"Data shape: {self.df.shape[0]} rows, {self.df.shape[1]} columns")
            logger.info(f"Columns: {list(self.df.columns)}")
            
            return self.df
        
        except FileNotFoundError:
            logger.error(f"File not found: {self.input_file}")
            raise
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            raise
    
    def explore_data(self):
        """Perform initial data exploration"""
        if self.df is None:
            logger.error("No data loaded. Call load_data() first.")
            return
        
        logger.info("\n" + "="*50)
        logger.info("DATA EXPLORATION")
        logger.info("="*50)
        
        # Basic information
        logger.info(f"\nDataset Shape: {self.df.shape}")
        logger.info(f"\nData Types:\n{self.df.dtypes}")
        logger.info(f"\nMissing Values:\n{self.df.isnull().sum()}")
        logger.info(f"\nBasic Statistics:\n{self.df.describe()}")
        
        # Duplicate rows
        duplicates = self.df.duplicated().sum()
        logger.info(f"\nDuplicate Rows: {duplicates}")
        
        return {
            'shape': self.df.shape,
            'dtypes': self.df.dtypes.to_dict(),
            'missing_values': self.df.isnull().sum().to_dict(),
            'duplicates': duplicates
        }
    
    def clean_data(self, strategy='drop', fill_value=None):
        """
        Clean the dataset
        
        Args:
            strategy (str): Strategy for handling missing values ('drop', 'fill', 'mean', 'median', 'mode')
            fill_value: Value to fill missing data (if strategy='fill')
        """
        if self.df is None:
            logger.error("No data loaded. Call load_data() first.")
            return
        
        logger.info("\n" + "="*50)
        logger.info("DATA CLEANING")
        logger.info("="*50)
        
        initial_rows = len(self.df)
        
        # Remove duplicate rows
        duplicates_before = self.df.duplicated().sum()
        self.df = self.df.drop_duplicates()
        duplicates_removed = duplicates_before - self.df.duplicated().sum()
        logger.info(f"Removed {duplicates_removed} duplicate rows")
        
        # Handle missing values
        missing_before = self.df.isnull().sum().sum()
        
        if strategy == 'drop':
            self.df = self.df.dropna()
            logger.info(f"Dropped rows with missing values")
        
        elif strategy == 'fill':
            self.df = self.df.fillna(fill_value)
            logger.info(f"Filled missing values with: {fill_value}")
        
        elif strategy == 'mean':
            numeric_cols = self.df.select_dtypes(include=[np.number]).columns
            self.df[numeric_cols] = self.df[numeric_cols].fillna(self.df[numeric_cols].mean())
            logger.info(f"Filled missing numeric values with mean")
        
        elif strategy == 'median':
            numeric_cols = self.df.select_dtypes(include=[np.number]).columns
            self.df[numeric_cols] = self.df[numeric_cols].fillna(self.df[numeric_cols].median())
            logger.info(f"Filled missing numeric values with median")
        
        elif strategy == 'mode':
            for col in self.df.columns:
                if self.df[col].isnull().any():
                    mode_value = self.df[col].mode()[0] if not self.df[col].mode().empty else None
                    self.df[col] = self.df[col].fillna(mode_value)
            logger.info(f"Filled missing values with mode")
        
        missing_after = self.df.isnull().sum().sum()
        rows_after = len(self.df)
        
        logger.info(f"Rows before cleaning: {initial_rows}")
        logger.info(f"Rows after cleaning: {rows_after}")
        logger.info(f"Rows removed: {initial_rows - rows_after}")
        logger.info(f"Missing values before: {missing_before}")
        logger.info(f"Missing values after: {missing_after}")
        
        return self.df
    
    def transform_data(self, operations=None):
        """
        Transform the data
        
        Args:
            operations (dict): Dictionary of transformation operations
        """
        if self.df is None:
            logger.error("No data loaded. Call load_data() first.")
            return
        
        logger.info("\n" + "="*50)
        logger.info("DATA TRANSFORMATION")
        logger.info("="*50)
        
        if operations is None:
            operations = {}
        
        # Example transformations
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        
        if 'normalize' in operations and operations['normalize']:
            for col in numeric_cols:
                if col in operations.get('normalize_cols', numeric_cols):
                    self.df[f'{col}_normalized'] = (self.df[col] - self.df[col].min()) / (
                        self.df[col].max() - self.df[col].min()
                    )
            logger.info("Normalized numeric columns")
        
        if 'standardize' in operations and operations['standardize']:
            for col in numeric_cols:
                if col in operations.get('standardize_cols', numeric_cols):
                    self.df[f'{col}_standardized'] = (self.df[col] - self.df[col].mean()) / self.df[col].std()
            logger.info("Standardized numeric columns")
        
        return self.df
    
    def analyze_data(self, group_by=None, agg_func='mean'):
        """
        Analyze the data with grouping and aggregation
        
        Args:
            group_by (str or list): Column(s) to group by
            agg_func (str): Aggregation function ('mean', 'sum', 'count', 'min', 'max')
        """
        if self.df is None:
            logger.error("No data loaded. Call load_data() first.")
            return
        
        logger.info("\n" + "="*50)
        logger.info("DATA ANALYSIS")
        logger.info("="*50)
        
        results = {}
        
        # Basic statistics
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            results['statistics'] = self.df[numeric_cols].describe().to_dict()
            logger.info(f"\nNumeric columns statistics calculated")
        
        # Correlation matrix
        if len(numeric_cols) > 1:
            results['correlation'] = self.df[numeric_cols].corr().to_dict()
            logger.info(f"Correlation matrix calculated")
        
        # Group by analysis
        if group_by and group_by in self.df.columns:
            grouped = self.df.groupby(group_by)
            
            if agg_func == 'mean':
                results['grouped'] = grouped.mean(numeric_only=True).to_dict()
            elif agg_func == 'sum':
                results['grouped'] = grouped.sum(numeric_only=True).to_dict()
            elif agg_func == 'count':
                results['grouped'] = grouped.count().to_dict()
            elif agg_func == 'min':
                results['grouped'] = grouped.min(numeric_only=True).to_dict()
            elif agg_func == 'max':
                results['grouped'] = grouped.max(numeric_only=True).to_dict()
            
            logger.info(f"Grouped analysis by '{group_by}' with '{agg_func}' aggregation")
        
        return results
    
    def visualize_data(self):
        """Create visualizations of the data"""
        if self.df is None:
            logger.error("No data loaded. Call load_data() first.")
            return
        
        logger.info("\n" + "="*50)
        logger.info("DATA VISUALIZATION")
        logger.info("="*50)
        
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) == 0:
            logger.warning("No numeric columns found for visualization")
            return
        
        # Set style
        sns.set_style("whitegrid")
        
        # 1. Distribution plots
        n_numeric = min(len(numeric_cols), 4)
        if n_numeric > 0:
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('Data Distribution Analysis', fontsize=16, fontweight='bold')
            
            for idx, col in enumerate(numeric_cols[:4]):
                row, col_idx = idx // 2, idx % 2
                axes[row, col_idx].hist(self.df[col].dropna(), bins=30, edgecolor='black', alpha=0.7)
                axes[row, col_idx].set_title(f'Distribution of {col}')
                axes[row, col_idx].set_xlabel(col)
                axes[row, col_idx].set_ylabel('Frequency')
            
            plt.tight_layout()
            dist_plot_path = self.output_dir / 'distribution_plots.png'
            plt.savefig(dist_plot_path, dpi=300, bbox_inches='tight')
            logger.info(f"Distribution plots saved to: {dist_plot_path}")
            plt.close()
        
        # 2. Correlation heatmap
        if len(numeric_cols) > 1:
            plt.figure(figsize=(12, 8))
            correlation_matrix = self.df[numeric_cols].corr()
            sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0,
                       square=True, linewidths=1, cbar_kws={"shrink": 0.8})
            plt.title('Correlation Heatmap', fontsize=16, fontweight='bold')
            plt.tight_layout()
            heatmap_path = self.output_dir / 'correlation_heatmap.png'
            plt.savefig(heatmap_path, dpi=300, bbox_inches='tight')
            logger.info(f"Correlation heatmap saved to: {heatmap_path}")
            plt.close()
        
        # 3. Box plots
        if len(numeric_cols) > 0:
            fig, axes = plt.subplots(1, min(len(numeric_cols), 3), figsize=(15, 5))
            fig.suptitle('Box Plots - Outlier Detection', fontsize=16, fontweight='bold')
            
            if len(numeric_cols) == 1:
                axes = [axes]
            
            for idx, col in enumerate(numeric_cols[:3]):
                if len(numeric_cols) > 1:
                    ax = axes[idx]
                else:
                    ax = axes[0]
                ax.boxplot(self.df[col].dropna())
                ax.set_title(f'{col}')
                ax.set_ylabel('Value')
            
            plt.tight_layout()
            boxplot_path = self.output_dir / 'boxplots.png'
            plt.savefig(boxplot_path, dpi=300, bbox_inches='tight')
            logger.info(f"Box plots saved to: {boxplot_path}")
            plt.close()
        
        logger.info("Visualization completed successfully")
    
    def export_data(self, format='csv', filename=None):
        """
        Export processed data
        
        Args:
            format (str): Export format ('csv', 'json', 'excel')
            filename (str): Output filename (optional)
        """
        if self.df is None:
            logger.error("No data loaded. Call load_data() first.")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if filename is None:
            filename = f'processed_data_{timestamp}'
        
        try:
            if format == 'csv':
                output_path = self.output_dir / f'{filename}.csv'
                self.df.to_csv(output_path, index=False)
            elif format == 'json':
                output_path = self.output_dir / f'{filename}.json'
                self.df.to_json(output_path, orient='records', indent=2)
            elif format == 'excel':
                output_path = self.output_dir / f'{filename}.xlsx'
                self.df.to_excel(output_path, index=False)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            logger.info(f"Data exported to: {output_path}")
            return output_path
        
        except Exception as e:
            logger.error(f"Error exporting data: {str(e)}")
            raise
    
    def generate_report(self):
        """Generate a comprehensive data processing report"""
        if self.df is None:
            logger.error("No data loaded. Call load_data() first.")
            return
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'input_file': str(self.input_file),
            'original_shape': self.original_shape,
            'final_shape': self.df.shape,
            'columns': list(self.df.columns),
            'data_types': self.df.dtypes.astype(str).to_dict(),
            'missing_values': self.df.isnull().sum().to_dict(),
            'summary_statistics': self.df.describe().to_dict() if len(self.df.select_dtypes(include=[np.number]).columns) > 0 else {}
        }
        
        report_path = self.output_dir / 'processing_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Processing report saved to: {report_path}")
        return report


def create_sample_data():
    """Create sample CSV data for testing"""
    data = {
        'id': range(1, 101),
        'name': [f'Product_{i}' for i in range(1, 101)],
        'category': np.random.choice(['Electronics', 'Clothing', 'Food', 'Books'], 100),
        'price': np.random.uniform(10, 1000, 100).round(2),
        'quantity': np.random.randint(0, 100, 100),
        'rating': np.random.uniform(1, 5, 100).round(1)
    }
    
    df = pd.DataFrame(data)
    
    # Add some missing values
    df.loc[np.random.choice(df.index, 10), 'price'] = np.nan
    df.loc[np.random.choice(df.index, 5), 'rating'] = np.nan
    
    # Add some duplicates
    df = pd.concat([df, df.iloc[:3]], ignore_index=True)
    
    df.to_csv('sample_data.csv', index=False)
    logger.info("Sample data created: sample_data.csv")


def main():
    """Main function to run the data processing pipeline"""
    parser = argparse.ArgumentParser(description='Data Processing Script')
    parser.add_argument('--input', '-i', type=str, help='Input file path (CSV or JSON)')
    parser.add_argument('--output', '-o', type=str, default='output', help='Output directory')
    parser.add_argument('--clean', '-c', type=str, default='drop', 
                       choices=['drop', 'fill', 'mean', 'median', 'mode'],
                       help='Cleaning strategy for missing values')
    parser.add_argument('--visualize', '-v', action='store_true', help='Create visualizations')
    parser.add_argument('--export', '-e', type=str, default='csv',
                       choices=['csv', 'json', 'excel'], help='Export format')
    parser.add_argument('--create-sample', action='store_true', help='Create sample data file')
    
    args = parser.parse_args()
    
    try:
        # Create sample data if requested
        if args.create_sample:
            create_sample_data()
            return
        
        # Check if input file is provided
        if not args.input:
            logger.error("No input file specified. Use --input or --create-sample")
            parser.print_help()
            return
        
        # Initialize processor
        processor = DataProcessor(args.input, args.output)
        
        # Load data
        processor.load_data()
        
        # Explore data
        processor.explore_data()
        
        # Clean data
        processor.clean_data(strategy=args.clean)
        
        # Analyze data
        processor.analyze_data()
        
        # Visualize data
        if args.visualize:
            processor.visualize_data()
        
        # Export processed data
        processor.export_data(format=args.export)
        
        # Generate report
        processor.generate_report()
        
        logger.info("\n" + "="*50)
        logger.info("DATA PROCESSING COMPLETED SUCCESSFULLY!")
        logger.info("="*50)
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise


if __name__ == "__main__":
    main()
