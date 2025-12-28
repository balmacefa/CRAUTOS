#!/usr/bin/env python3
"""
Script to generate reports
"""
import sys
from pathlib import Path
from datetime import datetime
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.connection import SessionLocal
from backend.analyzers.report_generator import ReportGenerator
from backend.utils.logger import logger
from backend. config.settings import settings
import argparse


def main(output_format: str = 'json', output_file: str = None):
    """Generate and export report"""
    logger.info("=" * 50)
    logger.info("REPORT GENERATOR")
    logger.info("=" * 50)
    
    db = SessionLocal()
    
    try:
        # Generate report
        logger.info("Generating top selling report...")
        generator = ReportGenerator(db)
        report = generator.generate_top_selling_report()
        
        logger.info("✅ Report generated successfully")
        
        # Print summary
        logger.info("\n" + "=" * 50)
        logger.info("📊 REPORT SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Total Cars:  {report.total_autos}")
        logger.info("\n🏆 Top 5 Brands:")
        for i, marca in enumerate(report.top_marcas[: 5], 1):
            logger.info(f"  {i}. {marca. marca}:  {marca.cantidad} ({marca.porcentaje}%)")
        
        logger. info("\n🔥 Top 10 Models:")
        for i, modelo in enumerate(report.top_modelos[:10], 1):
            logger.info(f"  {i}. {modelo. modelo_completo}: {modelo.cantidad} ({modelo.porcentaje}%)")
        
        logger.info("\n💰 Price Statistics:")
        if report.precios. promedio:
            logger.info(f"  Average:  ₡{report.precios. promedio: ,.2f}")
        if report.precios.mediana:
            logger.info(f"  Median: ₡{report.precios.mediana:,.2f}")
        if report.precios.minimo:
            logger.info(f"  Min: ₡{report.precios.minimo:,.2f}")
        if report.precios.maximo:
            logger. info(f"  Max: ₡{report.precios. maximo:,.2f}")
        
        logger.info("\n📅 Top 5 Years:")
        for año, cantidad in list(report.años_populares.items())[:5]:
            logger.info(f"  {año}: {cantidad} cars")
        
        # Export report
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"{settings.REPORTS_DIR}/report_{timestamp}.{output_format}"
        
        # Create reports directory if it doesn't exist
        Path(settings.REPORTS_DIR).mkdir(parents=True, exist_ok=True)
        
        logger.info(f"\n💾 Exporting report to {output_file}...")
        
        if output_format == 'json': 
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report.model_dump(mode='json'), f, indent=2, ensure_ascii=False, default=str)
        
        elif output_format == 'csv':
            import pandas as pd
            
            # Export top models to CSV
            df = pd.DataFrame([m.model_dump() for m in report.top_modelos])
            df.to_csv(output_file, index=False, encoding='utf-8')
        
        logger.info(f"✅ Report exported to {output_file}")
        logger.info("=" * 50)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error generating report: {e}")
        return False
        
    finally: 
        db.close()


if __name__ == "__main__": 
    parser = argparse.ArgumentParser(description='Generate CRAutos report')
    parser.add_argument('--format', choices=['json', 'csv'], default='json', help='Output format')
    parser.add_argument('--output', type=str, default=None, help='Output file path')
    
    args = parser.parse_args()
    
    success = main(output_format=args.format, output_file=args.output)
    sys.exit(0 if success else 1)