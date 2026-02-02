"""
HTML Report Generator for SPADE Analysis Results.

Generates comprehensive, professional HTML reports with visualizations and statistics.
"""
import os
import base64
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path


class SPADEReportGenerator:
    """Generate HTML reports for SPADE analysis results."""
    
    def __init__(self, output_dir: str, results: Dict[str, Any]):
        """
        Initialize report generator.
        
        Args:
            output_dir: Directory containing analysis outputs
            results: Analysis results dictionary
        """
        self.output_dir = output_dir
        self.results = results
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _encode_image(self, image_path: str) -> Optional[str]:
        """Encode image to base64 for embedding in HTML."""
        if not os.path.exists(image_path):
            return None
        
        with open(image_path, "rb") as f:
            image_data = f.read()
            base64_data = base64.b64encode(image_data).decode('utf-8')
            
            # Determine mime type
            ext = os.path.splitext(image_path)[1].lower()
            mime_map = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif'
            }
            mime_type = mime_map.get(ext, 'image/png')
            
            return f"data:{mime_type};base64,{base64_data}"
    
    def _get_css(self) -> str:
        """Get CSS styling for the report."""
        return """
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                background: #f5f5f5;
                padding: 20px;
            }
            
            .container {
                max-width: 1400px;
                margin: 0 auto;
                background: white;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                border-radius: 8px;
                overflow: hidden;
            }
            
            /* Header */
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px;
                text-align: center;
            }
            
            .header h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
                font-weight: 700;
            }
            
            .header p {
                font-size: 1.1em;
                opacity: 0.9;
            }
            
            .timestamp {
                margin-top: 15px;
                font-size: 0.9em;
                opacity: 0.8;
            }
            
            /* Navigation */
            .nav {
                background: #2d3748;
                padding: 0;
                position: sticky;
                top: 0;
                z-index: 100;
            }
            
            .nav ul {
                list-style: none;
                display: flex;
                flex-wrap: wrap;
            }
            
            .nav li {
                flex: 1;
                min-width: 150px;
            }
            
            .nav a {
                display: block;
                padding: 15px 20px;
                color: white;
                text-decoration: none;
                text-align: center;
                transition: background 0.3s;
                border-right: 1px solid #4a5568;
            }
            
            .nav a:hover {
                background: #4a5568;
            }
            
            .nav li:last-child a {
                border-right: none;
            }
            
            /* Content */
            .content {
                padding: 40px;
            }
            
            /* Sections */
            .section {
                margin-bottom: 60px;
                scroll-margin-top: 60px;
            }
            
            .section h2 {
                font-size: 2em;
                color: #2d3748;
                margin-bottom: 25px;
                padding-bottom: 15px;
                border-bottom: 3px solid #667eea;
            }
            
            .section h3 {
                font-size: 1.5em;
                color: #4a5568;
                margin: 25px 0 15px 0;
            }
            
            /* Statistics Cards */
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin: 25px 0;
            }
            
            .stat-card {
                background: linear-gradient(135deg, #f6f8fb 0%, #ffffff 100%);
                padding: 25px;
                border-radius: 8px;
                border-left: 4px solid #667eea;
                box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            }
            
            .stat-card .label {
                font-size: 0.9em;
                color: #718096;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 8px;
            }
            
            .stat-card .value {
                font-size: 2em;
                font-weight: 700;
                color: #2d3748;
            }
            
            .stat-card.good { border-left-color: #48bb78; }
            .stat-card.warning { border-left-color: #ed8936; }
            .stat-card.error { border-left-color: #f56565; }
            
            /* Quality Badge */
            .quality-badge {
                display: inline-block;
                padding: 10px 20px;
                border-radius: 50px;
                font-weight: 700;
                font-size: 1.1em;
                margin: 20px 0;
            }
            
            .quality-badge.excellent { background: #48bb78; color: white; }
            .quality-badge.good { background: #38b2ac; color: white; }
            .quality-badge.acceptable { background: #ed8936; color: white; }
            .quality-badge.poor { background: #f56565; color: white; }
            
            /* Tables */
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                background: white;
                box-shadow: 0 2px 5px rgba(0,0,0,0.05);
                border-radius: 8px;
                overflow: hidden;
            }
            
            th {
                background: #2d3748;
                color: white;
                padding: 15px;
                text-align: left;
                font-weight: 600;
            }
            
            td {
                padding: 12px 15px;
                border-bottom: 1px solid #e2e8f0;
            }
            
            tr:hover {
                background: #f7fafc;
            }
            
            tr:last-child td {
                border-bottom: none;
            }
            
            /* Images */
            .image-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
                gap: 30px;
                margin: 25px 0;
            }
            
            .image-card {
                background: white;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            
            .image-card img {
                width: 100%;
                height: auto;
                display: block;
            }
            
            .image-card .caption {
                padding: 15px;
                background: #f7fafc;
                font-weight: 600;
                color: #2d3748;
                text-align: center;
            }
            
            .image-full {
                margin: 25px 0;
            }
            
            .image-full img {
                width: 100%;
                height: auto;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            
            /* Progress Bar */
            .progress-bar {
                width: 100%;
                height: 30px;
                background: #e2e8f0;
                border-radius: 15px;
                overflow: hidden;
                margin: 10px 0;
            }
            
            .progress-fill {
                height: 100%;
                background: linear-gradient(90deg, #48bb78 0%, #38b2ac 100%);
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: 600;
                transition: width 0.3s;
            }
            
            .progress-fill.warning {
                background: linear-gradient(90deg, #ed8936 0%, #dd6b20 100%);
            }
            
            .progress-fill.error {
                background: linear-gradient(90deg, #f56565 0%, #e53e3e 100%);
            }
            
            /* Footer */
            .footer {
                background: #2d3748;
                color: white;
                padding: 30px;
                text-align: center;
                margin-top: 40px;
            }
            
            .footer p {
                margin: 5px 0;
                opacity: 0.8;
            }
            
            /* Utility Classes */
            .text-center { text-align: center; }
            .mt-20 { margin-top: 20px; }
            .mb-20 { margin-bottom: 20px; }
            
            /* Responsive */
            @media (max-width: 768px) {
                .stats-grid {
                    grid-template-columns: 1fr;
                }
                
                .image-grid {
                    grid-template-columns: 1fr;
                }
                
                .nav ul {
                    flex-direction: column;
                }
                
                .nav li {
                    min-width: 100%;
                }
                
                .nav a {
                    border-right: none;
                    border-bottom: 1px solid #4a5568;
                }
            }
            
            @media print {
                .nav {
                    display: none;
                }
                
                .section {
                    page-break-inside: avoid;
                }
            }
        </style>
        """
    
    def _get_quality_grade(self, mean_distance: float) -> tuple:
        """Get quality grade and badge class."""
        if mean_distance < 0.005:
            return "Excellent (A+)", "excellent"
        elif mean_distance < 0.01:
            return "Very Good (A)", "good"
        elif mean_distance < 0.02:
            return "Good (B)", "good"
        elif mean_distance < 0.05:
            return "Acceptable (C)", "acceptable"
        else:
            return "Issues Detected (F)", "poor"
    
    def _generate_header(self) -> str:
        """Generate header section."""
        mean_dist = self.results.get('mean_distance', 0)
        quality, badge_class = self._get_quality_grade(mean_dist)
        
        return f"""
        <div class="header">
            <h1>🔬 SPADE Analysis Report</h1>
            <p>Spatial Analysis for Display Evaluation</p>
            <div class="timestamp">Generated: {self.timestamp}</div>
            <div class="quality-badge {badge_class}">{quality}</div>
        </div>
        """
    
    def _generate_nav(self) -> str:
        """Generate navigation menu."""
        return """
        <nav class="nav">
            <ul>
                <li><a href="#overview">📊 Overview</a></li>
                <li><a href="#statistics">📈 Statistics</a></li>
                <li><a href="#visualizations">🎨 Visualizations</a></li>
                <li><a href="#spatial-maps">🗺️ Spatial Maps</a></li>
                <li><a href="#worst-patches">⚠️ Problem Areas</a></li>
                <li><a href="#metadata">ℹ️ Metadata</a></li>
            </ul>
        </nav>
        """
    
    def _generate_overview(self) -> str:
        """Generate overview section."""
        mean_dist = self.results.get('mean_distance', 0)
        std_dist = self.results.get('std_distance', 0)
        min_dist = self.results.get('min_distance', 0)
        max_dist = self.results.get('max_distance', 0)
        median_dist = self.results.get('median_distance', 0)
        num_patches = self.results.get('num_patches', 0)
        
        quality, _ = self._get_quality_grade(mean_dist)
        
        return f"""
        <section id="overview" class="section">
            <h2>📊 Analysis Overview</h2>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="label">Mean Distance</div>
                    <div class="value">{mean_dist:.6f}</div>
                </div>
                <div class="stat-card">
                    <div class="label">Std Deviation</div>
                    <div class="value">{std_dist:.6f}</div>
                </div>
                <div class="stat-card">
                    <div class="label">Median Distance</div>
                    <div class="value">{median_dist:.6f}</div>
                </div>
                <div class="stat-card good">
                    <div class="label">Min Distance</div>
                    <div class="value">{min_dist:.6f}</div>
                </div>
                <div class="stat-card error">
                    <div class="label">Max Distance</div>
                    <div class="value">{max_dist:.6f}</div>
                </div>
                <div class="stat-card">
                    <div class="label">Total Patches</div>
                    <div class="value">{num_patches:,}</div>
                </div>
            </div>
            
            <h3>Quality Assessment</h3>
            <p style="font-size: 1.2em; margin: 15px 0;">
                Overall Quality: <strong>{quality}</strong>
            </p>
            <p style="color: #4a5568; margin: 10px 0;">
                This assessment is based on the mean perceptual distance between reference and capture patches.
                Lower values indicate better quality and uniformity.
            </p>
        </section>
        """
    
    def _generate_statistics(self) -> str:
        """Generate detailed statistics section."""
        # Threshold statistics
        threshold_html = ""
        for key, value in self.results.items():
            if key.endswith('_threshold') and isinstance(value, dict):
                threshold_name = key.replace('_threshold', '').replace('_', ' ').title()
                count = value.get('count', 0)
                pct = value.get('percentage', 0)
                threshold_val = value.get('value', 0)
                
                # Determine progress bar class
                if pct < 5:
                    bar_class = ""
                elif pct < 20:
                    bar_class = "warning"
                else:
                    bar_class = "error"
                
                threshold_html += f"""
                <div style="margin: 20px 0;">
                    <h4 style="color: #2d3748; margin-bottom: 10px;">{threshold_name} (threshold: {threshold_val})</h4>
                    <div class="progress-bar">
                        <div class="progress-fill {bar_class}" style="width: {min(pct, 100):.1f}%">
                            {pct:.1f}% ({count:,} patches)
                        </div>
                    </div>
                </div>
                """
        
        return f"""
        <section id="statistics" class="section">
            <h2>📈 Detailed Statistics</h2>
            
            <h3>Distribution Analysis</h3>
            <table>
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                        <th>Description</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Mean Distance</td>
                        <td><strong>{self.results.get('mean_distance', 0):.6f}</strong></td>
                        <td>Average perceptual distance across all patches</td>
                    </tr>
                    <tr>
                        <td>Standard Deviation</td>
                        <td><strong>{self.results.get('std_distance', 0):.6f}</strong></td>
                        <td>Variation in patch distances</td>
                    </tr>
                    <tr>
                        <td>Median Distance</td>
                        <td><strong>{self.results.get('median_distance', 0):.6f}</strong></td>
                        <td>Middle value of distance distribution</td>
                    </tr>
                    <tr>
                        <td>Min Distance</td>
                        <td><strong>{self.results.get('min_distance', 0):.6f}</strong></td>
                        <td>Best matching patch</td>
                    </tr>
                    <tr>
                        <td>Max Distance</td>
                        <td><strong>{self.results.get('max_distance', 0):.6f}</strong></td>
                        <td>Worst matching patch (highest error)</td>
                    </tr>
                </tbody>
            </table>
            
            <h3>Threshold Analysis</h3>
            <p style="color: #4a5568; margin: 15px 0;">
                Percentage of patches exceeding quality thresholds:
            </p>
            {threshold_html}
        </section>
        """
    
    def _generate_visualizations(self) -> str:
        """Generate visualizations section."""
        heatmap_path = os.path.join(self.output_dir, 'heatmap.png')
        contour_path = os.path.join(self.output_dir, 'contour_map_scores.png')
        
        heatmap_html = ""
        if os.path.exists(heatmap_path):
            heatmap_b64 = self._encode_image(heatmap_path)
            if heatmap_b64:
                heatmap_html = f"""
                <div class="image-full">
                    <h3>Spatial Heatmap</h3>
                    <p style="color: #4a5568; margin: 10px 0 20px 0;">
                        Color-coded visualization showing patch-level perceptual distances. 
                        Warmer colors (red/yellow) indicate higher error.
                    </p>
                    <img src="{heatmap_b64}" alt="Spatial Heatmap">
                </div>
                """
        
        contour_html = ""
        if os.path.exists(contour_path):
            contour_b64 = self._encode_image(contour_path)
            if contour_b64:
                contour_html = f"""
                <div class="image-full">
                    <h3>Contour Map</h3>
                    <p style="color: #4a5568; margin: 10px 0 20px 0;">
                        Contour visualization showing spatial distribution of quality scores.
                        Contour lines connect regions of similar perceptual distance.
                    </p>
                    <img src="{contour_b64}" alt="Contour Map">
                </div>
                """
        
        return f"""
        <section id="visualizations" class="section">
            <h2>🎨 Visual Analysis</h2>
            {heatmap_html}
            {contour_html}
        </section>
        """
    
    def _generate_spatial_maps(self) -> str:
        """Generate spatial/luma maps section."""
        luma_ref_path = os.path.join(self.output_dir, 'luma_ref.png')
        luma_cap_path = os.path.join(self.output_dir, 'luma_cap.png')
        log_ref_path = os.path.join(self.output_dir, 'log_radiance_ref.png')
        log_cap_path = os.path.join(self.output_dir, 'log_radiance_cap.png')
        
        images = []
        
        # Luma maps
        if os.path.exists(luma_ref_path):
            images.append({
                'src': self._encode_image(luma_ref_path),
                'caption': 'Reference Luma Map',
                'desc': 'Linear luminance of reference image'
            })
        
        if os.path.exists(luma_cap_path):
            images.append({
                'src': self._encode_image(luma_cap_path),
                'caption': 'Capture Luma Map',
                'desc': 'Linear luminance of captured image'
            })
        
        # Log radiance maps
        if os.path.exists(log_ref_path):
            images.append({
                'src': self._encode_image(log_ref_path),
                'caption': 'Reference Log Radiance',
                'desc': 'Logarithmic radiance visualization'
            })
        
        if os.path.exists(log_cap_path):
            images.append({
                'src': self._encode_image(log_cap_path),
                'caption': 'Capture Log Radiance',
                'desc': 'Logarithmic radiance visualization'
            })
        
        # Generate HTML
        images_html = ""
        for img in images:
            if img['src']:
                images_html += f"""
                <div class="image-card">
                    <img src="{img['src']}" alt="{img['caption']}">
                    <div class="caption">
                        <div>{img['caption']}</div>
                        <div style="font-size: 0.85em; font-weight: normal; opacity: 0.8; margin-top: 5px;">
                            {img['desc']}
                        </div>
                    </div>
                </div>
                """
        
        return f"""
        <section id="spatial-maps" class="section">
            <h2>🗺️ Spatial & Luminance Maps</h2>
            <p style="color: #4a5568; margin: 15px 0 25px 0;">
                These maps show luminance and radiance distributions across the display,
                helping identify brightness uniformity issues.
            </p>
            <div class="image-grid">
                {images_html}
            </div>
        </section>
        """
    
    def _generate_worst_patches(self) -> str:
        """Generate worst patches section."""
        worst = self.results.get('worst_patches', {})
        if not worst:
            return ""
        
        indices = worst.get('indices', [])
        coordinates = worst.get('coordinates', [])
        distances = worst.get('distances', [])
        
        if not indices:
            return ""
        
        # Generate table rows
        rows_html = ""
        for i, (idx, coord, dist) in enumerate(zip(indices[:20], coordinates[:20], distances[:20]), 1):
            rows_html += f"""
            <tr>
                <td>{i}</td>
                <td>{idx}</td>
                <td>({coord[0]}, {coord[1]})</td>
                <td><strong>{dist:.6f}</strong></td>
            </tr>
            """
        
        return f"""
        <section id="worst-patches" class="section">
            <h2>⚠️ Problem Areas (Top 20 Worst Patches)</h2>
            <p style="color: #4a5568; margin: 15px 0;">
                These patches show the highest perceptual distance from the reference,
                indicating potential quality issues that may require attention.
            </p>
            
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Patch Index</th>
                        <th>Coordinates (Y, X)</th>
                        <th>Distance</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </section>
        """
    
    def _generate_metadata(self) -> str:
        """Generate metadata section."""
        metric = self.results.get('metric', 'N/A')
        panel = self.results.get('panel', 'N/A')
        num_patches = self.results.get('num_patches', 0)
        
        return f"""
        <section id="metadata" class="section">
            <h2>ℹ️ Analysis Metadata</h2>
            
            <table>
                <thead>
                    <tr>
                        <th>Parameter</th>
                        <th>Value</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Analysis Date</td>
                        <td>{self.timestamp}</td>
                    </tr>
                    <tr>
                        <td>Metric Used</td>
                        <td><strong>{metric}</strong></td>
                    </tr>
                    <tr>
                        <td>Panel Color Space</td>
                        <td><strong>{panel}</strong></td>
                    </tr>
                    <tr>
                        <td>Total Patches Analyzed</td>
                        <td><strong>{num_patches:,}</strong></td>
                    </tr>
                    <tr>
                        <td>Output Directory</td>
                        <td><code>{self.output_dir}</code></td>
                    </tr>
                    <tr>
                        <td>Framework Version</td>
                        <td><strong>SPADE 2.0</strong></td>
                    </tr>
                </tbody>
            </table>
            
            <h3>Configuration Summary</h3>
            <p style="color: #4a5568; margin: 15px 0;">
                Full configuration details are available in <code>analysis_summary.json</code>
            </p>
        </section>
        """
    
    def _generate_footer(self) -> str:
        """Generate footer section."""
        return """
        <div class="footer">
            <p><strong>SPADE 2.0</strong> - Spatial Analysis for Display Evaluation</p>
            <p>Generated automatically by SPADE Report Generator</p>
            <p style="margin-top: 15px; font-size: 0.9em;">
                © 2024 SPADE Framework | For internal use only
            </p>
        </div>
        """
    
    def generate(self, output_filename: str = "analysis_report.html") -> str:
        """
        Generate complete HTML report.
        
        Args:
            output_filename: Name of output HTML file
        
        Returns:
            Path to generated HTML file
        """
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>SPADE Analysis Report - {self.timestamp}</title>
            {self._get_css()}
        </head>
        <body>
            <div class="container">
                {self._generate_header()}
                {self._generate_nav()}
                <div class="content">
                    {self._generate_overview()}
                    {self._generate_statistics()}
                    {self._generate_visualizations()}
                    {self._generate_spatial_maps()}
                    {self._generate_worst_patches()}
                    {self._generate_metadata()}
                </div>
                {self._generate_footer()}
            </div>
            
            <script>
                // Smooth scrolling for navigation
                document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
                    anchor.addEventListener('click', function (e) {{
                        e.preventDefault();
                        const target = document.querySelector(this.getAttribute('href'));
                        if (target) {{
                            target.scrollIntoView({{
                                behavior: 'smooth',
                                block: 'start'
                            }});
                        }}
                    }});
                }});
            </script>
        </body>
        </html>
        """
        
        # Save HTML file
        output_path = os.path.join(self.output_dir, output_filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_path


def generate_report(output_dir: str, 
                   results: Optional[Dict[str, Any]] = None,
                   output_filename: str = "analysis_report.html") -> str:
    """
    Convenience function to generate HTML report.
    
    Args:
        output_dir: Directory containing analysis outputs
        results: Analysis results dict (if None, loads from analysis_summary.json)
        output_filename: Name of output HTML file
    
    Returns:
        Path to generated HTML file
    
    Example:
        >>> from spade.report_generator import generate_report
        >>> report_path = generate_report("output_dir")
        >>> print(f"Report saved to: {report_path}")
    """
    # Load results if not provided
    if results is None:
        summary_path = os.path.join(output_dir, 'analysis_summary.json')
        if os.path.exists(summary_path):
            with open(summary_path, 'r') as f:
                results = json.load(f)
        else:
            raise FileNotFoundError(
                f"No results provided and analysis_summary.json not found in {output_dir}"
            )
    
    # Generate report
    generator = SPADEReportGenerator(output_dir, results)
    return generator.generate(output_filename)
