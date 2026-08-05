from packages.common.paths import (
    DOWNLOADS_DIR,
    PROFILING_REPORT_DIR,
    PROJECT_ROOT,
    create_project_directories,
)

create_project_directories()

print("PROJECT ROOT")
print(PROJECT_ROOT)

print()

print("DOWNLOAD DIRECTORY")
print(DOWNLOADS_DIR)

print()

print("REPORT DIRECTORY")
print(PROFILING_REPORT_DIR)