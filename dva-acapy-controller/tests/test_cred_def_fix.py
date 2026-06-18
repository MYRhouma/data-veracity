import json
import os
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
from fastapi.testclient import TestClient

from dva_acapy_controller.controller import app


client = TestClient(app)


def test_cred_def_filename_is_json_not_txt():
    source = Path("src/dva_acapy_controller/controller.py").read_text()
    assert 'open("cred_def.txt"' not in source, "cred_def.txt should have been replaced"
    assert 'open("cred_def.json"' in source, "cred_def.json should be used instead"


def test_cred_def_write_and_read_use_same_filename():
    source = Path("src/dva_acapy_controller/controller.py").read_text()
    write_filenames = []
    read_filenames = []
    for line in source.splitlines():
        if 'open("cred_def' in line and '"w"' in line:
            write_filenames.append(line.strip())
        if 'open("cred_def' in line and '"r"' in line:
            read_filenames.append(line.strip())
    assert len(write_filenames) > 0, "Should find a write to cred_def"
    assert len(read_filenames) > 0, "Should find a read from cred_def"
    assert all("cred_def.json" in line for line in write_filenames), "All writes should use cred_def.json"
    assert all("cred_def.json" in line for line in read_filenames), "All reads should use cred_def.json"