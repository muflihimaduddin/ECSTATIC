#  ECSTATIC: Extensible, Customizable STatic Analysis Tester Informed by Configuration
#
#  Copyright (c) 2022.
#
#  This program is free software: you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#
#      You should have received a copy of the GNU General Public License
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.


import importlib
import json
import logging
import os.path
from pathlib import Path

from jsonschema.validators import RefResolver, Draft7Validator

from src.ecstatic.util.ApplicationCodeFilter import ApplicationCodeFilter
from src.ecstatic.util.JavaApplicationCodeFilter import JavaApplicationCodeFilter
from src.ecstatic.util.UtilClasses import Benchmark, BenchmarkRecord

logger = logging.getLogger(__name__)


def try_resolve_path(path: str, root: str = "/") -> str:
    if path is None:
        return None
    logging.info(f'Trying to resolve {path} in {root}')
    if path.startswith("/"):
        path = path[1:]
    if os.path.exists(joined_path := os.path.join(root, path)):
        return os.path.abspath(joined_path)
    results = set()
    benchmarks_dir = os.path.join(root, "benchmarks")
    if os.path.exists(benchmarks_dir):
        # Extract filename and path components for flexible matching
        path_parts = path.split('/')
        filename = path_parts[-1] if path_parts else None
        path_prefix_parts = path_parts[:-1] if len(path_parts) > 1 else []
        
        # Search recursively in benchmarks directory
        for rootdir, dirs, files in os.walk(benchmarks_dir):
            # Try exact path match first
            test_path = os.path.join(rootdir, path)
            if os.path.exists(test_path):
                results.add(os.path.abspath(test_path))
            
            # Try flexible matching for files
            if filename and filename in files:
                file_path = os.path.abspath(os.path.join(rootdir, filename))
                # Get relative path from benchmarks directory
                rel_path = os.path.relpath(file_path, benchmarks_dir)
                rel_path_parts = rel_path.replace('\\', '/').split('/')
                
                # Check if path structure matches (allowing for extra intermediate directories)
                if path_prefix_parts:
                    rel_idx = 0
                    match = True
                    for idx, prefix_part in enumerate(path_prefix_parts):
                        found = False
                        is_last_component = (idx == len(path_prefix_parts) - 1)
                        while rel_idx < len(rel_path_parts) - 1:  # -1 to exclude filename
                            current_part = rel_path_parts[rel_idx].lower()
                            prefix_lower = prefix_part.lower()
                            # For the last component before filename, require exact match to avoid ambiguity
                            if is_last_component:
                                if current_part == prefix_lower:
                                    found = True
                                    rel_idx += 1
                                    break
                            else:
                                # Earlier components: allow substring matching
                                if current_part == prefix_lower or prefix_lower in current_part:
                                    found = True
                                    rel_idx += 1
                                    break
                            rel_idx += 1
                        if not found:
                            match = False
                            break
                    if match:
                        results.add(file_path)
                else:
                    results.add(file_path)
            
            # Also try matching directories (for source paths) - only if path doesn't look like a file
            # Check if path is likely a directory (no file extension, or ends with common dir names like 'src')
            is_likely_directory = (not filename or 
                                  filename in ['src', 'target', 'build', 'lib', 'bin'] or
                                  '.' not in filename or
                                  not any(filename.endswith(ext) for ext in ['.jar', '.apk', '.js', '.class', '.java', '.xml', '.sh', '.txt', '.log']))
            
            if is_likely_directory:
                # For directory paths, we need to match the full path structure
                # The last component is the directory name we're looking for
                target_dir_name = path_parts[-1] if path_parts else None
                path_prefix_parts_for_dir = path_parts[:-1] if len(path_parts) > 1 else []
                
                if target_dir_name:
        for d in dirs:
                        if d.lower() == target_dir_name.lower():
                            # Found a directory with matching name, check if path structure matches
                            dir_path = os.path.abspath(os.path.join(rootdir, d))
                            if not os.path.isdir(dir_path):
                                continue
                            
                            # Get relative path from benchmarks directory
                            rel_path = os.path.relpath(dir_path, benchmarks_dir)
                            rel_path_parts = rel_path.replace('\\', '/').split('/')
                            
                            # Prefer exact path matches - check if path ends with the exact requested structure
                            # The rel_path_parts will have extra components (like "Dacapo-2006/benchmarks")
                            # but should end with the requested path_parts
                            if len(rel_path_parts) >= len(path_parts):
                                # Check if the last N components match exactly
                                match_parts = rel_path_parts[-(len(path_parts)):]
                                if all(match_parts[i].lower() == path_parts[i].lower() for i in range(len(path_parts))):
                                    # This is an exact match - add it and continue (prefer exact matches)
                                    results.add(dir_path)
                                    continue
                            
                            # Check if path structure matches (allowing for extra intermediate directories)
                            # But only if we haven't found an exact match yet
                            if path_prefix_parts_for_dir:
                                rel_idx = 0
                                match = True
                                for idx, prefix_part in enumerate(path_prefix_parts_for_dir):
                                    found = False
                                    is_last_component = (idx == len(path_prefix_parts_for_dir) - 1)
                                    while rel_idx < len(rel_path_parts) - 1:  # -1 to exclude the target directory name
                                        current_part = rel_path_parts[rel_idx].lower()
                                        prefix_lower = prefix_part.lower()
                                        # For the last component before target dir, require exact match
                                        if is_last_component:
                                            if current_part == prefix_lower:
                                                found = True
                                                rel_idx += 1
                                                break
                                        else:
                                            # Earlier components: allow substring matching
                                            if current_part == prefix_lower or prefix_lower in current_part:
                                                found = True
                                                rel_idx += 1
                                                break
                                        rel_idx += 1
                                    if not found:
                                        match = False
                                        break
                                if match:
                                    results.add(dir_path)
                            else:
                                # No path prefix, just directory name match
                                results.add(dir_path)
    # If we have multiple results, prefer exact path matches
    if len(results) > 1:
        exact_matches = set()
        path_parts = path.split('/')
        for result_path in results:
            # Get relative path from benchmarks directory
            rel_path = os.path.relpath(result_path, benchmarks_dir) if benchmarks_dir in str(result_path) else os.path.relpath(result_path, root)
            rel_path_parts = rel_path.replace('\\', '/').split('/')
            # Check if this is an exact match (ends with the requested path structure)
            if len(rel_path_parts) >= len(path_parts):
                match_parts = rel_path_parts[-(len(path_parts)):]
                if all(match_parts[i].lower() == path_parts[i].lower() for i in range(len(path_parts))):
                    exact_matches.add(result_path)
        # If we found exact matches, use only those
        if exact_matches:
            results = exact_matches
    
    match len(results):
        case 0: raise FileNotFoundError(f"Could not resolve path {path} from root {root}")
        case 1: return results.pop()
        case _: raise RuntimeError(f"Path {path} in root {root} is ambiguous. Found the following potential results: "
                                   f"{results}. Try adding more context information to the index.json file, "
                                   f"so that the path is unique.")


def validate(benchmark: BenchmarkRecord, root: str = "/") -> BenchmarkRecord:
    """
    Validates a benchmark, resolving each of its paths to an absolute path.
    Searches in the supplied root directory.
    Parameters
    ----------
    benchmark : The benchmark to validate.
    root : Where to look for the benchmark files

    Returns
    -------
    A resolved benchmark
    """
    logger.info(f'Original benchmark record is {benchmark}')
    benchmark.name = try_resolve_path(benchmark.name, root)
    benchmark.depends_on = [try_resolve_path(d, root) for d in benchmark.depends_on]
    benchmark.sources = [try_resolve_path(s, root) for s in benchmark.sources]
    benchmark.build_script = try_resolve_path(benchmark.build_script, root)
    logger.info(f'Resolved benchmark record to {benchmark}')
    return benchmark


class BenchmarkReader:
    def __init__(self,
                 schema: str = importlib.resources.path('src.resources.schema', 'benchmark.schema.json'),
                 application_code_filter: ApplicationCodeFilter = JavaApplicationCodeFilter()):
        self.schema = schema
        with open(schema, 'r') as f:
            self.schema = json.load(f)
        self.resolver = RefResolver.from_schema(self.schema)
        self.validator = Draft7Validator(self.schema, self.resolver)
        self.application_code_filter = application_code_filter

    def read_benchmark(self, file: Path) -> Benchmark:
        with open(file, 'r') as f:
            index = json.load(f)
        self.validator.validate(index)
        benchmark = Benchmark([validate(BenchmarkRecord(**b)) for b in index['benchmark']])
        if self.application_code_filter is not None:
            benchmark = Benchmark([self.application_code_filter.find_application_packages(br) for br in benchmark.benchmarks])
        return benchmark


