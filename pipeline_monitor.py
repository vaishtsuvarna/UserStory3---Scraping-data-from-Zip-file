import pandas as pd
from datetime import datetime
import json
from pathlib import Path
from typing import Dict, Any

class DataPipelineMonitor:
    def __init__(self, csv_path: str = 'employees_cleaned.csv'):
        self.csv_path = Path(csv_path)
        self.metrics_file = Path('pipeline_metrics.json')

    def _read_df(self) -> pd.DataFrame:
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV not found: {self.csv_path}")
        df = pd.read_csv(self.csv_path)
        return df

    def generate_daily_metrics(self) -> Dict[str, Any]:
        """Generate a small executive-friendly metrics JSON file."""
        df = self._read_df()

        now = pd.to_datetime(datetime.now())
        metrics: Dict[str, Any] = {
            'run_date': datetime.now().isoformat(),
            'total_employees': len(df),
            'new_hires_last_30d': None,
            'top_5_roles': {},
            'avg_tenure_days': None,
            'email_domains': {}
        }

        # hire date based metrics
        if 'hire date' in df.columns:
            hire_dates = pd.to_datetime(df['hire date'], errors='coerce')
            metrics['new_hires_last_30d'] = int((hire_dates >= (now - pd.Timedelta(days=30))).sum())
            valid_tenures = (now - hire_dates).dt.days.dropna()
            if len(valid_tenures):
                metrics['avg_tenure_days'] = int(valid_tenures.mean())

        # top roles
        if 'job title' in df.columns:
            metrics['top_5_roles'] = df['job title'].value_counts().head(5).to_dict()

        # email domains if present
        if 'email' in df.columns:
            metrics['email_domains'] = df['email'].dropna().astype(str).str.split('@').str[1].value_counts().to_dict()

        # write metrics
        try:
            self.metrics_file.write_text(json.dumps(metrics, indent=2))
        except Exception:
            pass

        print("📊 DAILY METRICS GENERATED:")
        for k, v in metrics.items():
            print(f"  {k}: {v}")

        return metrics

    def data_quality_report(self) -> Dict[str, Any]:
        """Return a simple data quality report with graceful handling if columns are missing."""
        df = self._read_df()

        quality: Dict[str, Any] = {}

        # completeness metrics
        if 'email' in df.columns:
            quality['completeness_email'] = float(df['email'].notna().mean() * 100)
        else:
            quality['completeness_email'] = None

        if 'phone number' in df.columns:
            quality['completeness_phone'] = float(df['phone number'].notna().mean() * 100)
        else:
            quality['completeness_phone'] = None

        # duplicates based on employee id
        if 'eeid' in df.columns:
            quality['duplicate_emps'] = int(df['eeid'].duplicated().sum())
        elif 'emp id' in df.columns:
            quality['duplicate_emps'] = int(df['emp id'].duplicated().sum())
        else:
            quality['duplicate_emps'] = None

        # valid email check
        if 'email' in df.columns:
            quality['valid_emails'] = float(df['email'].str.contains('@', na=False).mean() * 100)
        else:
            quality['valid_emails'] = None

        # a simple fallback quality score
        scores = [v for v in [quality.get('completeness_email'), quality.get('completeness_phone'), quality.get('valid_emails')] if isinstance(v, (int, float))]
        if scores:
            quality['quality_score'] = float(sum(scores) / len(scores))
        else:
            quality['quality_score'] = 100.0

        print("🔍 DATA QUALITY REPORT:")
        for k, v in quality.items():
            if v is None:
                print(f"  {k}: MISSING")
            elif isinstance(v, float):
                print(f"  {k}: {v:.1f}%")
            else:
                print(f"  {k}: {v}")

        return quality


if __name__ == '__main__':
    monitor = DataPipelineMonitor()
    monitor.generate_daily_metrics()
    monitor.data_quality_report()
