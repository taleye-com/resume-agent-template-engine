import os
import json
import hashlib
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging
import git
from packaging import version
import yaml

logger = logging.getLogger(__name__)


@dataclass
class TemplateVersion:
    """Represents a template version"""

    version: str
    template_id: str
    author: str
    created_at: datetime
    description: str = ""
    changelog: List[str] = field(default_factory=list)
    compatibility: Dict[str, str] = field(default_factory=dict)
    file_hash: str = ""
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "version": self.version,
            "template_id": self.template_id,
            "author": self.author,
            "created_at": self.created_at.isoformat(),
            "description": self.description,
            "changelog": self.changelog,
            "compatibility": self.compatibility,
            "file_hash": self.file_hash,
            "tags": self.tags,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemplateVersion":
        """Create from dictionary"""
        return cls(**data)


class TemplateVersionManager:
    """Manages template versions and changes"""

    def __init__(self, templates_path: str, versions_path: Optional[str] = None):
        """
        Initialize template version manager

        Args:
            templates_path: Path to templates directory
            versions_path: Path to versions storage (defaults to templates_path/.versions)
        """
        self.templates_path = Path(templates_path)
        self.versions_path = (
            Path(versions_path) if versions_path else self.templates_path / ".versions"
        )
        self.versions_path.mkdir(parents=True, exist_ok=True)

        self.version_index = self._load_version_index()
        self._init_git_repo()

    def _init_git_repo(self) -> None:
        """Initialize Git repository for version tracking"""
        git_dir = self.versions_path / ".git"
        if not git_dir.exists():
            try:
                self.repo = git.Repo.init(str(self.versions_path))
                logger.info("Initialized Git repository for template versioning")
            except Exception as e:
                logger.warning(f"Failed to initialize Git repository: {e}")
                self.repo = None
        else:
            try:
                self.repo = git.Repo(str(self.versions_path))
            except Exception as e:
                logger.warning(f"Failed to load Git repository: {e}")
                self.repo = None

    def _load_version_index(self) -> Dict[str, List[TemplateVersion]]:
        """Load version index from storage"""
        index_file = self.versions_path / "index.json"
        if index_file.exists():
            try:
                with open(index_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                index = {}
                for template_id, versions_data in data.items():
                    index[template_id] = [
                        TemplateVersion.from_dict(version_data)
                        for version_data in versions_data
                    ]

                return index

            except Exception as e:
                logger.error(f"Failed to load version index: {e}")

        return {}

    def _save_version_index(self) -> None:
        """Save version index to storage"""
        index_file = self.versions_path / "index.json"

        try:
            data = {}
            for template_id, versions in self.version_index.items():
                data[template_id] = [version.to_dict() for version in versions]

            with open(index_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Commit to Git if available
            if self.repo:
                try:
                    self.repo.index.add([str(index_file)])
                    self.repo.index.commit("Update version index")
                except Exception as e:
                    logger.debug(f"Git commit failed: {e}")

        except Exception as e:
            logger.error(f"Failed to save version index: {e}")

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        hasher = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return ""

    def _get_template_files(self, template_path: Path) -> List[Path]:
        """Get all files in a template directory"""
        if not template_path.exists():
            return []

        files = []
        for file_path in template_path.rglob("*"):
            if file_path.is_file() and not file_path.name.startswith("."):
                files.append(file_path)

        return sorted(files)

    def create_version(
        self,
        template_id: str,
        version_str: str,
        author: str,
        description: str = "",
        changelog: List[str] = None,
        tags: List[str] = None,
    ) -> TemplateVersion:
        """
        Create a new version of a template

        Args:
            template_id: Template identifier (e.g., "resume/classic")
            version_str: Version string (e.g., "1.0.0")
            author: Author name
            description: Version description
            changelog: List of changes
            tags: Version tags

        Returns:
            Created template version
        """
        # Validate template exists
        parts = template_id.split("/")
        if len(parts) != 2:
            raise ValueError(f"Invalid template ID format: {template_id}")

        doc_type, template_name = parts
        template_path = self.templates_path / doc_type / template_name

        if not template_path.exists():
            raise ValueError(f"Template not found: {template_id}")

        # Validate version string
        try:
            parsed_version = version.parse(version_str)
        except Exception:
            raise ValueError(f"Invalid version string: {version_str}")

        # Check if version already exists
        if template_id in self.version_index:
            existing_versions = [v.version for v in self.version_index[template_id]]
            if version_str in existing_versions:
                raise ValueError(
                    f"Version {version_str} already exists for {template_id}"
                )

        # Calculate file hash
        template_files = self._get_template_files(template_path)
        combined_hash = hashlib.sha256()
        for file_path in template_files:
            file_hash = self._calculate_file_hash(file_path)
            combined_hash.update(file_hash.encode())

        file_hash = combined_hash.hexdigest()

        # Create version object
        template_version = TemplateVersion(
            version=version_str,
            template_id=template_id,
            author=author,
            created_at=datetime.now(),
            description=description,
            changelog=changelog or [],
            file_hash=file_hash,
            tags=tags or [],
        )

        # Store template files
        version_dir = self.versions_path / template_id / version_str
        version_dir.mkdir(parents=True, exist_ok=True)

        # Copy template files
        for file_path in template_files:
            relative_path = file_path.relative_to(template_path)
            target_path = version_dir / relative_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, target_path)

        # Save metadata
        metadata_file = version_dir / "version.yaml"
        with open(metadata_file, "w", encoding="utf-8") as f:
            yaml.dump(template_version.to_dict(), f, default_flow_style=False)

        # Update index
        if template_id not in self.version_index:
            self.version_index[template_id] = []

        self.version_index[template_id].append(template_version)
        self.version_index[template_id].sort(key=lambda v: version.parse(v.version))

        # Save changes
        self._save_version_index()

        # Git commit if available
        if self.repo:
            try:
                self.repo.index.add_items([str(version_dir)])
                self.repo.index.commit(f"Add version {version_str} of {template_id}")
            except Exception as e:
                logger.debug(f"Git commit failed: {e}")

        logger.info(f"Created version {version_str} for template {template_id}")
        return template_version

    def get_versions(self, template_id: str) -> List[TemplateVersion]:
        """Get all versions of a template"""
        return self.version_index.get(template_id, [])

    def get_latest_version(self, template_id: str) -> Optional[TemplateVersion]:
        """Get the latest version of a template"""
        versions = self.get_versions(template_id)
        if not versions:
            return None

        return max(versions, key=lambda v: version.parse(v.version))

    def get_version(
        self, template_id: str, version_str: str
    ) -> Optional[TemplateVersion]:
        """Get a specific version of a template"""
        versions = self.get_versions(template_id)
        for v in versions:
            if v.version == version_str:
                return v
        return None

    def restore_version(self, template_id: str, version_str: str) -> bool:
        """
        Restore a specific version as the current template

        Args:
            template_id: Template identifier
            version_str: Version to restore

        Returns:
            True if successful, False otherwise
        """
        template_version = self.get_version(template_id, version_str)
        if not template_version:
            logger.error(f"Version {version_str} not found for {template_id}")
            return False

        # Get paths
        parts = template_id.split("/")
        doc_type, template_name = parts
        current_template_path = self.templates_path / doc_type / template_name
        version_path = self.versions_path / template_id / version_str

        if not version_path.exists():
            logger.error(f"Version files not found: {version_path}")
            return False

        try:
            # Backup current version if it exists
            if current_template_path.exists():
                backup_path = current_template_path.with_suffix(".backup")
                if backup_path.exists():
                    shutil.rmtree(backup_path)
                shutil.move(str(current_template_path), str(backup_path))

            # Copy version files to current location
            current_template_path.mkdir(parents=True, exist_ok=True)

            for item in version_path.iterdir():
                if item.name == "version.yaml":
                    continue  # Skip metadata file

                target = current_template_path / item.name
                if item.is_dir():
                    shutil.copytree(item, target)
                else:
                    shutil.copy2(item, target)

            logger.info(f"Restored template {template_id} to version {version_str}")
            return True

        except Exception as e:
            logger.error(f"Failed to restore version: {e}")
            return False

    def compare_versions(
        self, template_id: str, version1: str, version2: str
    ) -> Dict[str, Any]:
        """
        Compare two versions of a template

        Args:
            template_id: Template identifier
            version1: First version
            version2: Second version

        Returns:
            Comparison results
        """
        v1 = self.get_version(template_id, version1)
        v2 = self.get_version(template_id, version2)

        if not v1 or not v2:
            return {"error": "One or both versions not found"}

        # Compare metadata
        changes = {
            "metadata_changes": {
                "author": v1.author != v2.author,
                "description_changed": v1.description != v2.description,
                "file_hash_changed": v1.file_hash != v2.file_hash,
                "tags_changed": set(v1.tags) != set(v2.tags),
            },
            "version_info": {
                "v1": {
                    "version": v1.version,
                    "created_at": v1.created_at.isoformat(),
                    "author": v1.author,
                },
                "v2": {
                    "version": v2.version,
                    "created_at": v2.created_at.isoformat(),
                    "author": v2.author,
                },
            },
            "changelog_diff": {
                "added_in_v2": [
                    item for item in v2.changelog if item not in v1.changelog
                ],
                "removed_in_v2": [
                    item for item in v1.changelog if item not in v2.changelog
                ],
            },
        }

        return changes

    def get_template_history(self, template_id: str) -> Dict[str, Any]:
        """Get complete history of a template"""
        versions = self.get_versions(template_id)

        if not versions:
            return {"template_id": template_id, "versions": []}

        history = {
            "template_id": template_id,
            "total_versions": len(versions),
            "first_version": min(
                versions, key=lambda v: version.parse(v.version)
            ).version,
            "latest_version": max(
                versions, key=lambda v: version.parse(v.version)
            ).version,
            "versions": [],
        }

        for v in sorted(versions, key=lambda x: version.parse(x.version), reverse=True):
            history["versions"].append(
                {
                    "version": v.version,
                    "author": v.author,
                    "created_at": v.created_at.isoformat(),
                    "description": v.description,
                    "tags": v.tags,
                    "changelog_count": len(v.changelog),
                }
            )

        return history

    def cleanup_old_versions(self, template_id: str, keep_latest: int = 5) -> int:
        """
        Clean up old versions, keeping only the latest N versions

        Args:
            template_id: Template identifier
            keep_latest: Number of latest versions to keep

        Returns:
            Number of versions removed
        """
        versions = self.get_versions(template_id)
        if len(versions) <= keep_latest:
            return 0

        # Sort by version and keep only the latest ones
        sorted_versions = sorted(
            versions, key=lambda v: version.parse(v.version), reverse=True
        )
        versions_to_remove = sorted_versions[keep_latest:]

        removed_count = 0
        for v in versions_to_remove:
            version_dir = self.versions_path / template_id / v.version
            if version_dir.exists():
                try:
                    shutil.rmtree(version_dir)
                    removed_count += 1
                except Exception as e:
                    logger.error(
                        f"Failed to remove version directory {version_dir}: {e}"
                    )

            # Remove from index
            self.version_index[template_id] = [
                ver
                for ver in self.version_index[template_id]
                if ver.version != v.version
            ]

        if removed_count > 0:
            self._save_version_index()
            logger.info(f"Cleaned up {removed_count} old versions of {template_id}")

        return removed_count

    def export_version(
        self, template_id: str, version_str: str, export_path: str
    ) -> bool:
        """
        Export a specific version to a directory

        Args:
            template_id: Template identifier
            version_str: Version to export
            export_path: Target export directory

        Returns:
            True if successful
        """
        template_version = self.get_version(template_id, version_str)
        if not template_version:
            return False

        version_path = self.versions_path / template_id / version_str
        if not version_path.exists():
            return False

        try:
            export_dir = Path(export_path)
            export_dir.mkdir(parents=True, exist_ok=True)

            # Copy all files except metadata
            for item in version_path.iterdir():
                if item.name == "version.yaml":
                    continue

                target = export_dir / item.name
                if item.is_dir():
                    shutil.copytree(item, target, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, target)

            # Add version info file
            info_file = export_dir / "VERSION_INFO.yaml"
            with open(info_file, "w", encoding="utf-8") as f:
                yaml.dump(template_version.to_dict(), f, default_flow_style=False)

            logger.info(f"Exported {template_id} v{version_str} to {export_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export version: {e}")
            return False

    def get_all_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get summary of all templates and their versions"""
        summary = {}

        for template_id, versions in self.version_index.items():
            if versions:
                latest = max(versions, key=lambda v: version.parse(v.version))
                summary[template_id] = {
                    "version_count": len(versions),
                    "latest_version": latest.version,
                    "latest_author": latest.author,
                    "latest_date": latest.created_at.isoformat(),
                    "all_tags": list(set(tag for v in versions for tag in v.tags)),
                }

        return summary
