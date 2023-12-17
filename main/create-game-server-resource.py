#!/usr/bin/env python3

import json
import os

from game_server_controller import instance

if __name__ == "__main__":
    binding_context_path = os.environ.get('BINDING_CONTEXT_PATH')
    with open(binding_context_path) as f:
        data = json.load(f)
        instance.process_create_game_server_event(data)
