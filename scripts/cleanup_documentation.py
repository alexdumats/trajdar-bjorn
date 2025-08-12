#!/usr/bin/env python3
"""
Documentation Cleanup Script
Identifies and consolidates outdated documentation files
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
import json

class DocumentationCleaner:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.project_root = Path(__file__).parent.parent
        self.actions = []
        
    def log_action(self, action, file_path, reason=""):
        entry = {
            "action": action,
            "file": str(file_path),
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
        self.actions.append(entry)
        print(f"{'[DRY RUN] ' if self.dry_run else ''}✅ {action}: {file_path} - {reason}")
    
    def identify_outdated_docs(self):
        """Identify documentation files that are outdated or redundant"""
        
        # Files that are outdated or have been superseded
        outdated_files = [
            "codebase_index.md",  # Superseded by docs/README.md and architecture diagrams
            "configuration_index.md",  # Superseded by schema files
            "mcp_components.md",  # Information now in system_map.yaml
            "system_status_report.md",  # Replaced by health monitoring scripts
            "debuggai_setup_findings.md",  # Temporary debugging notes
            "CUSTOMIZATION_SUMMARY.md",  # Outdated customization info
            "README_REDIS_FALLBACK.md",  # Specific implementation detail, not needed
            "README_MCP_DEPLOYMENT.md",  # Consolidated into main deployment guide
            "README_REFACTORED.md"  # Temporary refactor documentation
        ]
        
        # Files to archive (move to docs/archive)
        archive_files = [
            "TEST_REPORT.md",  # Keep for historical reference
            "SYSTEM_IMPROVEMENTS_SUMMARY.md",  # Historical improvements
            "ai_trading_system_summary.md"  # Historical summary
        ]
        
        return outdated_files, archive_files
    
    def create_archive_directory(self):
        """Create archive directory for historical documentation"""
        archive_dir = self.project_root / "docs" / "archive"
        if not self.dry_run:
            archive_dir.mkdir(parents=True, exist_ok=True)
        return archive_dir
    
    def cleanup_outdated_documentation(self):
        """Remove or archive outdated documentation files"""
        outdated_files, archive_files = self.identify_outdated_docs()
        archive_dir = self.create_archive_directory()
        
        # Remove outdated files
        for filename in outdated_files:
            file_path = self.project_root / filename
            if file_path.exists():
                if not self.dry_run:
                    file_path.unlink()
                self.log_action(
                    "REMOVED", 
                    file_path.relative_to(self.project_root),
                    "Outdated/superseded by new documentation"
                )
        
        # Archive historical files
        for filename in archive_files:
            file_path = self.project_root / filename
            if file_path.exists():
                archive_path = archive_dir / filename
                if not self.dry_run:
                    shutil.move(str(file_path), str(archive_path))
                self.log_action(
                    "ARCHIVED",
                    file_path.relative_to(self.project_root),
                    f"Moved to docs/archive/ for historical reference"
                )
    
    def update_main_readme(self):
        """Update the main README to reference the new documentation structure"""
        readme_path = self.project_root / "README.md"
        
        if not readme_path.exists():
            self.log_action("SKIP", "README.md", "File not found")
            return
        
        # Read current content
        with open(readme_path, 'r') as f:
            content = f.read()
        
        # Add documentation reference if not already present
        doc_section = """
## 📚 Documentation

For comprehensive system documentation, see:
- **[docs/README.md](docs/README.md)** - Complete documentation index
- **[docs/architecture/](docs/architecture/)** - System architecture diagrams
- **[docs/schemas/](docs/schemas/)** - API specifications and configuration schemas

"""
        
        if "docs/README.md" not in content and not self.dry_run:
            # Find a good place to insert the documentation section
            lines = content.split('\n')
            insert_index = -1
            
            # Look for existing documentation section or insert after overview
            for i, line in enumerate(lines):
                if line.startswith('## Documentation') or line.startswith('## 📚 Documentation'):
                    # Replace existing documentation section
                    # Find the next section
                    next_section = i + 1
                    while next_section < len(lines) and not lines[next_section].startswith('## '):
                        next_section += 1
                    lines = lines[:i] + doc_section.strip().split('\n') + lines[next_section:]
                    insert_index = i
                    break
                elif line.startswith('## ') and 'install' not in line.lower() and 'setup' not in line.lower():
                    # Insert before this section
                    lines = lines[:i] + doc_section.strip().split('\n') + [''] + lines[i:]
                    insert_index = i
                    break
            
            if insert_index == -1:
                # Add at the end
                lines.extend([''] + doc_section.strip().split('\n'))
            
            # Write updated content
            with open(readme_path, 'w') as f:
                f.write('\n'.join(lines))
            
            self.log_action(
                "UPDATED",
                "README.md",
                "Added documentation section reference"
            )
        elif "docs/README.md" in content:
            self.log_action(
                "SKIP",
                "README.md", 
                "Documentation reference already present"
            )
        else:
            self.log_action(
                "WOULD UPDATE",
                "README.md",
                "Would add documentation section reference"
            )
    
    def create_cleanup_report(self):
        """Create a report of documentation cleanup actions"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "dry_run": self.dry_run,
            "actions": self.actions,
            "summary": {
                "total_actions": len(self.actions),
                "files_removed": len([a for a in self.actions if a["action"] == "REMOVED"]),
                "files_archived": len([a for a in self.actions if a["action"] == "ARCHIVED"]),
                "files_updated": len([a for a in self.actions if a["action"] == "UPDATED"])
            }
        }
        
        report_file = self.project_root / "logs" / f"documentation_cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        if not self.dry_run:
            report_file.parent.mkdir(exist_ok=True)
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\n📄 Cleanup report saved: {report_file}")
        
        return report
    
    def run_cleanup(self):
        """Run the complete documentation cleanup process"""
        print(f"🧹 Starting documentation cleanup")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'EXECUTION'}")
        print(f"Project root: {self.project_root}")
        
        self.cleanup_outdated_documentation()
        self.update_main_readme()
        
        report = self.create_cleanup_report()
        
        print(f"\n📊 Cleanup Summary:")
        print(f"Total actions: {report['summary']['total_actions']}")
        print(f"Files removed: {report['summary']['files_removed']}")
        print(f"Files archived: {report['summary']['files_archived']}")
        print(f"Files updated: {report['summary']['files_updated']}")
        
        return report

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Documentation cleanup script")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show what would be done without making changes")
    
    args = parser.parse_args()
    
    cleaner = DocumentationCleaner(dry_run=args.dry_run)
    
    try:
        cleaner.run_cleanup()
        print("\n✅ Documentation cleanup completed successfully!")
    except Exception as e:
        print(f"\n❌ Documentation cleanup failed: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()