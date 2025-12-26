"""
Metadata Stripping Module
Removes identifying metadata from files, images, and documents.
"""

import os
import shutil
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS
import exifread
from mutagen import File as MutagenFile
import subprocess
import json


class MetadataStripper:
    """Strip metadata from various file types."""
    
    def __init__(self):
        self.supported_image_formats = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.webp'}
        self.supported_audio_formats = {'.mp3', '.flac', '.ogg', '.m4a', '.wav'}
        self.supported_video_formats = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}
    
    def strip_image_metadata(self, file_path, output_path=None):
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return False, "File not found"
            if file_path.suffix.lower() not in self.supported_image_formats:
                return False, f"Unsupported image format: {file_path.suffix}"
            img = Image.open(file_path)
            exif_data = img.getexif()
            metadata_info = {}
            if exif_data:
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    metadata_info[tag] = str(value)
            data = list(img.getdata())
            image_without_exif = Image.new(img.mode, img.size)
            image_without_exif.putdata(data)
            output = output_path if output_path else file_path
            image_without_exif.save(output, quality=95, optimize=True)
            return True, f"Stripped metadata: {len(metadata_info)} fields removed"
        except Exception as e:
            return False, f"Error stripping metadata: {str(e)}"
    
    def strip_audio_metadata(self, file_path, output_path=None):
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return False, "File not found"
            if file_path.suffix.lower() not in self.supported_audio_formats:
                return False, f"Unsupported audio format: {file_path.suffix}"
            audio_file = MutagenFile(file_path)
            if audio_file is None:
                return False, "Could not read audio file"
            metadata_count = len(audio_file.keys())
            audio_file.delete()
            audio_file.save()
            return True, f"Stripped {metadata_count} metadata fields from audio file"
        except Exception as e:
            return False, f"Error stripping audio metadata: {str(e)}"
    
    def strip_video_metadata(self, file_path, output_path=None):
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return False, "File not found"
            if file_path.suffix.lower() not in self.supported_video_formats:
                return False, f"Unsupported video format: {file_path.suffix}"
            if not output_path:
                output_path = file_path.parent / f"{file_path.stem}_stripped{file_path.suffix}"
            cmd = [
                'ffmpeg', '-i', str(file_path),
                '-map_metadata', '-1',
                '-c', 'copy',
                '-y',
                str(output_path)
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                return True, f"Video metadata stripped. Output: {output_path}"
            else:
                return False, f"FFmpeg error: {result.stderr}"
        except FileNotFoundError:
            return False, "FFmpeg not found. Please install ffmpeg to strip video metadata."
        except Exception as e:
            return False, f"Error stripping video metadata: {str(e)}"
    
    def strip_document_metadata(self, file_path, output_path=None):
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return False, "File not found"
            result = subprocess.run(['which', 'mat2'], capture_output=True)
            if result.returncode == 0:
                output = output_path if output_path else file_path
                cmd = ['mat2', '--inplace', str(file_path)]
                subprocess.run(cmd, capture_output=True)
                return True, "Document metadata stripped using mat2"
            else:
                return False, "mat2 not found. Install mat2 for document metadata stripping."
        except Exception as e:
            return False, f"Error stripping document metadata: {str(e)}"
    
    def batch_strip(self, directory, file_types=None, recursive=True):
        directory = Path(directory)
        if not directory.exists():
            return {"error": "Directory not found"}
        results = {
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        pattern = "**/*" if recursive else "*"
        files = list(directory.glob(pattern))
        for file_path in files:
            if not file_path.is_file():
                continue
            ext = file_path.suffix.lower()
            if file_types and ext not in file_types:
                continue
            results["processed"] += 1
            if ext in self.supported_image_formats:
                success, message = self.strip_image_metadata(file_path)
            elif ext in self.supported_audio_formats:
                success, message = self.strip_audio_metadata(file_path)
            elif ext in self.supported_video_formats:
                success, message = self.strip_video_metadata(file_path, 
                    file_path.parent / f"{file_path.stem}_stripped{ext}")
            else:
                continue
            if success:
                results["successful"] += 1
            else:
                results["failed"] += 1
                results["errors"].append(f"{file_path.name}: {message}")
        return results
    
    def inspect_metadata(self, file_path):
        file_path = Path(file_path)
        if not file_path.exists():
            return {"error": "File not found"}
        metadata = {
            "file": str(file_path),
            "size": file_path.stat().st_size,
            "metadata": {}
        }
        ext = file_path.suffix.lower()
        try:
            if ext in self.supported_image_formats:
                img = Image.open(file_path)
                exif_data = img.getexif()
                if exif_data:
                    for tag_id, value in exif_data.items():
                        tag = TAGS.get(tag_id, tag_id)
                        metadata["metadata"][tag] = str(value)
            elif ext in self.supported_audio_formats:
                audio_file = MutagenFile(file_path)
                if audio_file:
                    for key, value in audio_file.items():
                        metadata["metadata"][key] = str(value)
        except Exception as e:
            metadata["error"] = str(e)
        return metadata
