"""
SPADE 2.0 - Spatial Analysis for Display Evaluation
Setup script for installation
"""
from setuptools import setup, find_packages
import os

# Read the long description from README
def read_long_description():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "SPADE - Spatial Analysis for Display Evaluation"

setup(
    name='spade-analysis',
    version='2.0.0',
    author='SPADE Team',
    author_email='',
    description='Modular framework for OLED display quality analysis',
    long_description=read_long_description(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourorg/spade',
    packages=find_packages(exclude=['examples', 'tests']),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: Image Processing',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    python_requires='>=3.7',
    install_requires=[
        'numpy>=1.19.0',
        'pillow>=8.0.0',
        'matplotlib>=3.3.0',
    ],
    extras_require={
        'dev': [
            'pytest>=6.0',
            'pytest-cov>=2.10',
        ],
    },
    entry_points={
        'console_scripts': [
            'spade-report=spade.report_generator:main',
        ],
    },
    package_data={
        'spade': ['*.json'],
    },
    include_package_data=True,
    zip_safe=False,
)
