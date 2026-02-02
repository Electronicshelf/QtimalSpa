#!/usr/bin/env python3
"""
Standalone Report Generator Script

Generate HTML reports from existing SPADE analysis results.

Usage:
    python generate_report.py <output_dir>
    python generate_report.py <output_dir> --output custom_report.html
    
Example:
    python generate_report.py ./my_analysis_output
    python generate_report.py ./output --output final_report.html
"""
import sys
import os
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from spade.report_generator import generate_report


def main():
    parser = argparse.ArgumentParser(
        description='Generate HTML report from SPADE analysis results',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s ./output
  %(prog)s ./output --output my_report.html
  %(prog)s /path/to/analysis/results
        """
    )
    
    parser.add_argument(
        'output_dir',
        help='Directory containing SPADE analysis results'
    )
    
    parser.add_argument(
        '-o', '--output',
        default='analysis_report.html',
        help='Output filename (default: analysis_report.html)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    # Validate directory
    if not os.path.isdir(args.output_dir):
        print(f"Error: Directory not found: {args.output_dir}", file=sys.stderr)
        sys.exit(1)
    
    # Check for analysis_summary.json
    summary_path = os.path.join(args.output_dir, 'analysis_summary.json')
    if not os.path.exists(summary_path):
        print(f"Error: analysis_summary.json not found in {args.output_dir}", file=sys.stderr)
        print("Make sure you've run SPADE analysis first.", file=sys.stderr)
        sys.exit(1)
    
    # Generate report
    try:
        if args.verbose:
            print(f"Generating report from: {args.output_dir}")
            print(f"Output file: {args.output}")
        
        report_path = generate_report(args.output_dir, output_filename=args.output)
        
        print(f"✓ Report generated successfully!")
        print(f"  Location: {report_path}")
        print(f"\nOpen in browser:")
        print(f"  file://{os.path.abspath(report_path)}")
        
    except Exception as e:
        print(f"Error generating report: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
