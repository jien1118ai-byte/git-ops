#!/usr/bin/env python3
"""
Error Handler for git-ops
Identifies common Git errors and provides recovery suggestions
"""

import re


# Common Git errors mapping
GIT_ERRORS = {
    'GIT_PUSH_REJECTED': {
        'patterns': [
            r'Updates were rejected because the tip of your current branch is behind',
            r'failed to push some refs',
        ],
        'message_zh': '遠端有更新，本地推送被拒',
        'message_en': 'Remote updates conflict with local push',
        'recovery': [
            'git fetch origin',
            'git rebase origin/<branch>',
            'git push origin <branch>',
        ]
    },
    'GIT_MERGE_CONFLICT': {
        'patterns': [
            r'CONFLICT \(content\)',
            r'Automatic merge failed',
            r'fix conflicts and then commit the result',
        ],
        'message_zh': '合併衝突',
        'message_en': 'Merge conflict detected',
        'recovery': [
            'git status',
            '# Fix conflicts in the files listed above',
            'git add .',
            'git commit -m "resolve merge conflict"',
        ]
    },
    'GIT_REBASE_CONFLICT': {
        'patterns': [
            r'CONFLICT \(content\)',
            r'when you have resolved this problem run',
            r'git rebase --continue',
        ],
        'message_zh': 'Rebase 衝突',
        'message_en': 'Rebase conflict detected',
        'recovery': [
            'git status',
            '# Fix conflicts in the files listed above',
            'git add .',
            'git rebase --continue',
        ]
    },
    'GIT_DETACHED_HEAD': {
        'patterns': [
            r'HEAD detached',
            r'you are currently on a branch',
        ],
        'message_zh': '處於分離的 HEAD 狀態',
        'message_en': 'Detached HEAD state',
        'recovery': [
            'git checkout <branch_name>',
        ]
    },
    'GIT_NO_CHANGES': {
        'patterns': [
            r'nothing to commit',
            r'no changes added to commit',
            r'working tree clean',
        ],
        'message_zh': '沒有變更可提交',
        'message_en': 'No changes to commit',
        'recovery': [
            'git status',
            '# Make changes to files',
            'git add .',
            'git commit -m "message"',
        ]
    },
    'GIT_BRANCH_NOT_FOUND': {
        'patterns': [
            r'error: pathspec .* did not match any file',
            r'pathspec .*? is in the index',
            r'fatal: Not a valid object name',
        ],
        'message_zh': '分支或引用不存在',
        'message_en': 'Branch or reference not found',
        'recovery': [
            'git branch -a',
            '# Verify the branch name exists',
            'git checkout <correct_branch>',
        ]
    },
    'GIT_AUTHENTICATION_FAILED': {
        'patterns': [
            r'Permission denied \(publickey\)',
            r'fatal: Authentication failed',
            r'401 Unauthorized',
        ],
        'message_zh': '認證失敗',
        'message_en': 'Authentication failed',
        'recovery': [
            'git config user.name "Your Name"',
            'git config user.email "your@email.com"',
            '# Ensure SSH key is properly configured',
            '# or provide valid credentials when prompted',
        ]
    },
    'GIT_UNTRACKED_FILES_CONFLICT': {
        'patterns': [
            r'error: Your local changes to .* would be overwritten by merge',
            r'The following untracked working tree files would be overwritten',
        ],
        'message_zh': '未追蹤的文件會被覆蓋',
        'message_en': 'Untracked files would be overwritten',
        'recovery': [
            'git stash',
            '# or delete the untracked files',
            'rm <file>',
        ]
    },
    'GIT_NOTHING_TO_REBASE': {
        'patterns': [
            r'No such ref: HEAD~',
            r'fatal: Needed a single revision',
            r'No changes, already up to date',
        ],
        'message_zh': '沒有東西可以 rebase',
        'message_en': 'Nothing to rebase',
        'recovery': [
            'git log --oneline -5',
            '# Check if there are commits to rebase',
        ]
    },
}


class ErrorHandler:
    """Identifies and handles Git errors"""

    @staticmethod
    def identify_error(error_output):
        """
        Identify error type from git output
        Returns: (error_code, error_info) or (None, None)
        """
        if not error_output:
            return None, None

        for error_code, error_info in GIT_ERRORS.items():
            for pattern in error_info.get('patterns', []):
                if re.search(pattern, error_output, re.IGNORECASE | re.MULTILINE):
                    return error_code, error_info

        return None, None

    @staticmethod
    def get_recovery_steps(error_code):
        """Get recovery steps for an error code"""
        if error_code in GIT_ERRORS:
            return GIT_ERRORS[error_code].get('recovery', [])
        return []

    @staticmethod
    def format_error_message(error_code, lang='en'):
        """Format error message for display"""
        if error_code not in GIT_ERRORS:
            return "Unknown error"

        error_info = GIT_ERRORS[error_code]
        key = f'message_{lang}' if lang != 'en' else 'message_en'
        return error_info.get(key, error_info.get('message_en'))

    @staticmethod
    def format_for_ai(error_code, error_output):
        """Format error information for AI to read"""
        if error_code not in GIT_ERRORS:
            return {
                'error_code': 'UNKNOWN',
                'message': 'Unknown error occurred',
                'recovery': []
            }

        error_info = GIT_ERRORS[error_code]
        return {
            'error_code': error_code,
            'message': error_info.get('message_en'),
            'message_zh': error_info.get('message_zh'),
            'recovery': error_info.get('recovery', []),
            'original_output': error_output[:500]  # First 500 chars
        }

    @staticmethod
    def get_bash_recovery_script(error_code):
        """Get a bash script to attempt recovery"""
        steps = ErrorHandler.get_recovery_steps(error_code)
        if not steps:
            return ""

        script_lines = ["# Suggested recovery steps:"]
        for step in steps:
            if step.startswith('#'):
                script_lines.append(step)
            else:
                script_lines.append(f"{step}")

        return '\n'.join(script_lines)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Git-ops error handler')
    parser.add_argument('error_code', nargs='?', help='Error code to get info for')
    parser.add_argument('--list', action='store_true', help='List all known errors')

    args = parser.parse_args()

    if args.list:
        print("Known error codes:\n")
        for code, info in GIT_ERRORS.items():
            msg_en = info.get('message_en', '')
            msg_zh = info.get('message_zh', '')
            print(f"{code:30s} {msg_en:40s} ({msg_zh})")
    elif args.error_code:
        info = ErrorHandler.format_for_ai(args.error_code, "")
        print(f"Error Code: {info['error_code']}")
        print(f"Message: {info['message']}")
        print(f"Message (ZH): {info['message_zh']}")
        print("\nRecovery steps:")
        for step in info['recovery']:
            print(f"  {step}")
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
