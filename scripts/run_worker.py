#!/usr/bin/env python3
"""
Script to start Celery worker

Usage:
    python scripts/run_worker.py [--queue queue_name] [--concurrency N]

Examples:
    python scripts/run_worker.py
    python scripts/run_worker.py --queue emails
    python scripts/run_worker.py --concurrency 4
"""

import os
import sys
import argparse
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.tasks.celery_app import celery_app


def main():
    parser = argparse.ArgumentParser(description='Start Celery worker')
    parser.add_argument(
        '--queue', '-Q',
        default='celery',
        help='Queue name to consume from (default: celery)'
    )
    parser.add_argument(
        '--concurrency', '-c',
        type=int,
        default=4,
        help='Number of concurrent worker processes (default: 4)'
    )
    parser.add_argument(
        '--loglevel', '-l',
        default='info',
        choices=['debug', 'info', 'warning', 'error', 'critical'],
        help='Logging level (default: info)'
    )
    
    args = parser.parse_args()
    
    # Start Celery worker
    celery_app.worker_main([
        'worker',
        '--loglevel=' + args.loglevel,
        '--concurrency=' + str(args.concurrency),
        '--queues=' + args.queue
    ])


if __name__ == '__main__':
    main()