#!/usr/bin/env python3
"""
Operation Notes for git-ops
Records all operations with timestamps and status for audit trail
"""

import json
from datetime import datetime
from pathlib import Path


class OperationNotes:
    """Records and manages operation notes"""

    def __init__(self):
        home = Path.home()
        self.notes_dir = home / '.git-ops' / 'notes'
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        self.get_today_file()

    def get_today_file(self):
        """Get or create today's notes file"""
        today = datetime.now().strftime('%Y-%m-%d')
        return self.notes_dir / f'{today}.md'

    def add_operation_note(self, operation, input_text, status='INFO', exit_code=None, details=None):
        """Add a note about an operation"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        note_file = self.get_today_file()
        
        # Initialize file if it doesn't exist
        if not note_file.exists():
            with open(note_file, 'w', encoding='utf-8') as f:
                f.write(f"# Git-Ops Operations - {datetime.now().strftime('%Y-%m-%d')}\n\n")
        
        # Format status indicator
        status_icon = {
            'SUCCESS': '✅',
            'FAILED': '❌',
            'SKIPPED': '⏭️',
            'WARNING': '⚠️',
            'INFO': 'ℹ️'
        }.get(status, '❓')
        
        # Build note entry
        note_entry = f"## {timestamp} - {operation}\n"
        note_entry += f"- Status: {status_icon} {status}\n"
        note_entry += f"- Input: `{input_text}`\n"
        
        if exit_code is not None:
            note_entry += f"- Exit Code: {exit_code}\n"
        
        if details:
            note_entry += f"- Details: {details}\n"
        
        note_entry += "\n"
        
        # Append to file
        with open(note_file, 'a', encoding='utf-8') as f:
            f.write(note_entry)

    def add_error_note(self, operation, input_text, error_msg, suggestion=None):
        """Add an error note"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        note_file = self.get_today_file()
        
        # Initialize file if it doesn't exist
        if not note_file.exists():
            with open(note_file, 'w', encoding='utf-8') as f:
                f.write(f"# Git-Ops Operations - {datetime.now().strftime('%Y-%m-%d')}\n\n")
        
        note_entry = f"## {timestamp} - {operation}\n"
        note_entry += f"- Status: ❌ FAILED\n"
        note_entry += f"- Input: `{input_text}`\n"
        note_entry += f"- Error: {error_msg}\n"
        
        if suggestion:
            note_entry += f"- Recovery: {suggestion}\n"
        
        note_entry += "\n"
        
        # Append to file
        with open(note_file, 'a', encoding='utf-8') as f:
            f.write(note_entry)

    def list_recent_notes(self, limit=20):
        """List recent operation notes"""
        note_file = self.get_today_file()
        
        if not note_file.exists():
            return "No notes for today"
        
        with open(note_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Return last N lines
        return ''.join(lines[-limit:])

    def summary(self):
        """Generate summary of today's operations"""
        note_file = self.get_today_file()
        
        if not note_file.exists():
            return "No notes for today"
        
        with open(note_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Count statuses
        success_count = content.count('✅ SUCCESS')
        failed_count = content.count('❌ FAILED')
        warning_count = content.count('⚠️ WARNING')
        
        summary_text = f"\n--- Operations Summary ---\n"
        summary_text += f"✅ Success: {success_count}\n"
        summary_text += f"❌ Failed: {failed_count}\n"
        summary_text += f"⚠️ Warnings: {warning_count}\n"
        
        return summary_text


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Git-ops operation notes')
    parser.add_argument('--add-note', metavar='OPERATION', help='Add a note for an operation')
    parser.add_argument('--input', help='Input text for the operation')
    parser.add_argument('--status', default='INFO', help='Status (SUCCESS/FAILED/WARNING/INFO)')
    parser.add_argument('--exit-code', type=int, help='Exit code')
    parser.add_argument('--details', help='Additional details')
    parser.add_argument('--list', action='store_true', help='List recent notes')
    parser.add_argument('--summary', action='store_true', help='Show summary of today\'s operations')
    
    args = parser.parse_args()
    notes = OperationNotes()
    
    if args.add_note:
        notes.add_operation_note(args.add_note, args.input or '', args.status, args.exit_code, args.details)
        print(f"✅ Note added for {args.add_note}")
    elif args.list:
        print(notes.list_recent_notes())
    elif args.summary:
        print(notes.summary())
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
