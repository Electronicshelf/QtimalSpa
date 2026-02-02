"""
Example: Generate HTML Reports for SPADE Analysis.

This script demonstrates how to:
1. Run SPADE analysis
2. Generate professional HTML reports
3. Customize report generation
"""
import sys
import os
from pathlib import Path

# Add parent directory to path (for running from examples/ directory)
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from spade import quick_analysis, SPADEConfig, run_analysis
from spade.report_generator import generate_report


def example_1_basic_report():
    """Example 1: Generate report after quick analysis."""
    print("\n" + "="*60)
    print("Example 1: Basic Report Generation")
    print("="*60)
    
    # Run analysis (using fake paths for demo)
    print("\n[Simulating analysis...]")
    print("In real usage:")
    print("  results = quick_analysis('ref.png', 'cap.png', 'output')")
    print("  report_path = generate_report('output')")
    print("\nThis would create 'output/analysis_report.html'")
    
    # If you have real images:
    # results = quick_analysis("ref.png", "cap.png", "output")
    # report_path = generate_report("output")
    # print(f"\nReport generated: {report_path}")


def example_2_custom_report_name():
    """Example 2: Custom report filename."""
    print("\n" + "="*60)
    print("Example 2: Custom Report Filename")
    print("="*60)
    
    print("\nGenerate report with custom filename:")
    print("  report_path = generate_report('output', output_filename='my_report.html')")


def example_3_manual_results():
    """Example 3: Generate report with manual results."""
    print("\n" + "="*60)
    print("Example 3: Manual Results")
    print("="*60)
    
    # You can also manually provide results
    manual_results = {
        'mean_distance': 0.0234,
        'std_distance': 0.0156,
        'min_distance': 0.0001,
        'max_distance': 0.0892,
        'median_distance': 0.0198,
        'num_patches': 4096,
        'metric': 'perceptual',
        'panel': 'P3A',
        'worst_patches': {
            'indices': [1234, 5678, 9012],
            'coordinates': [[100, 200], [300, 400], [500, 600]],
            'distances': [0.0892, 0.0761, 0.0654]
        },
        'good_threshold': {
            'value': 0.01,
            'count': 3072,
            'percentage': 75.0
        },
        'warning_threshold': {
            'value': 0.05,
            'count': 128,
            'percentage': 3.1
        }
    }
    
    print("\nManual results can be provided:")
    print(f"  Results: {manual_results}")
    print("  report_path = generate_report('output', results=manual_results)")


def example_4_batch_reports():
    """Example 4: Generate reports for multiple analyses."""
    print("\n" + "="*60)
    print("Example 4: Batch Report Generation")
    print("="*60)
    
    print("\nProcess multiple test cases and generate reports:")
    
    test_cases = [
        ("ref1.png", "cap1.png", "output_test1"),
        ("ref2.png", "cap2.png", "output_test2"),
        ("ref3.png", "cap3.png", "output_test3"),
    ]
    
    for i, (ref, cap, output) in enumerate(test_cases, 1):
        print(f"\n  Test {i}:")
        print(f"    results = quick_analysis('{ref}', '{cap}', '{output}')")
        print(f"    report = generate_report('{output}')")
        print(f"    → Would create: {output}/analysis_report.html")


def example_5_integrated_workflow():
    """Example 5: Complete integrated workflow."""
    print("\n" + "="*60)
    print("Example 5: Integrated Workflow")
    print("="*60)
    
    print("\nComplete workflow with configuration and reporting:")
    print("""
    from spade import SPADEConfig, run_analysis
    from spade.report_generator import generate_report
    
    # Configure analysis
    config = SPADEConfig()
    config.metric.metric_name = 'perceptual'
    config.panel.panel_name = 'P3A'
    config.visualization.generate_heatmaps = True
    config.visualization.generate_luma_maps = True
    config.visualization.generate_log_radiance = True
    config.visualization.generate_contours = True
    
    # Run analysis
    results = run_analysis('ref.png', 'cap.png', 'output', config)
    
    # Generate report
    report_path = generate_report('output')
    
    print(f"Analysis complete!")
    print(f"Report: {report_path}")
    print(f"Mean distance: {results['mean_distance']:.6f}")
    """)


def example_6_report_features():
    """Example 6: Report features overview."""
    print("\n" + "="*60)
    print("Example 6: Report Features")
    print("="*60)
    
    print("\nThe HTML report includes:")
    print("\n📊 Sections:")
    print("  1. Overview - Summary cards with key metrics")
    print("  2. Statistics - Detailed distribution analysis")
    print("  3. Visualizations - Heatmaps and contour plots")
    print("  4. Spatial Maps - Luma and log radiance maps")
    print("  5. Problem Areas - Top 20 worst patches")
    print("  6. Metadata - Configuration and analysis details")
    
    print("\n🎨 Features:")
    print("  • Professional gradient design")
    print("  • Sticky navigation menu")
    print("  • Quality badge (A+/A/B/C/F grading)")
    print("  • Color-coded statistics cards")
    print("  • Interactive progress bars")
    print("  • Responsive design (mobile-friendly)")
    print("  • Embedded images (self-contained)")
    print("  • Smooth scrolling navigation")
    print("  • Print-friendly styles")
    
    print("\n📈 Statistics Included:")
    print("  • Mean, median, std deviation")
    print("  • Min/max distances")
    print("  • Threshold analysis with progress bars")
    print("  • Worst patch locations and distances")
    
    print("\n🖼️ Visualizations Embedded:")
    print("  • Spatial heatmap")
    print("  • Contour map")
    print("  • Reference & capture luma maps")
    print("  • Reference & capture log radiance maps")
    print("  • All images embedded as base64 (single file)")


def example_7_custom_styling():
    """Example 7: The report is self-contained and customizable."""
    print("\n" + "="*60)
    print("Example 7: Report Characteristics")
    print("="*60)
    
    print("\n✨ Self-Contained:")
    print("  • Single HTML file")
    print("  • All CSS embedded")
    print("  • All images embedded (base64)")
    print("  • No external dependencies")
    print("  • Easy to share via email")
    
    print("\n🎨 Professional Design:")
    print("  • Modern gradient header")
    print("  • Clean card-based layout")
    print("  • High contrast for readability")
    print("  • Consistent color scheme")
    print("  • Professional typography")
    
    print("\n📱 Responsive:")
    print("  • Works on desktop")
    print("  • Works on tablet")
    print("  • Works on mobile")
    print("  • Adapts to screen size")


def example_8_automation():
    """Example 8: Automate report generation."""
    print("\n" + "="*60)
    print("Example 8: Automated Reporting")
    print("="*60)
    
    print("\nAutomate report generation in your pipeline:")
    print("""
    import os
    from pathlib import Path
    from spade import quick_analysis
    from spade.report_generator import generate_report
    
    def process_test_batch(test_dir):
        '''Process all test cases in a directory.'''
        test_dir = Path(test_dir)
        
        for ref_path in test_dir.glob('ref_*.png'):
            # Find matching capture
            test_id = ref_path.stem.replace('ref_', '')
            cap_path = test_dir / f'cap_{test_id}.png'
            
            if cap_path.exists():
                output_dir = test_dir / f'results_{test_id}'
                
                # Run analysis
                print(f"Processing {test_id}...")
                results = quick_analysis(
                    str(ref_path), 
                    str(cap_path), 
                    str(output_dir)
                )
                
                # Generate report
                report = generate_report(str(output_dir))
                
                print(f"  Report: {report}")
                print(f"  Quality: {results['mean_distance']:.6f}")
    
    # Run batch
    process_test_batch('test_data/')
    """)


if __name__ == "__main__":
    print("\nSPADE HTML Report Generator Examples")
    print("=====================================")
    
    example_1_basic_report()
    example_2_custom_report_name()
    example_3_manual_results()
    example_4_batch_reports()
    example_5_integrated_workflow()
    example_6_report_features()
    example_7_custom_styling()
    example_8_automation()
    
    print("\n" + "="*60)
    print("Examples Complete!")
    print("="*60)
    print("\nQuick Start:")
    print("  1. Run your SPADE analysis")
    print("  2. Call generate_report('output_dir')")
    print("  3. Open the HTML file in your browser")
    print("\nThe report includes:")
    print("  ✓ All visualizations")
    print("  ✓ Complete statistics")
    print("  ✓ Quality assessment")
    print("  ✓ Problem area identification")
    print("  ✓ Professional formatting")
    print("\nAll in a single, shareable HTML file!")
