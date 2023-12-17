#!/usr/bin/env python3

import json
import subprocess
import sys

if __name__ == "__main__":
    # Hook configuration
    if len(sys.argv) > 1 and sys.argv[1] == "--config":
        config = {
            "configVersion": "v1",
            "kubernetes": [
                {
                    "apiVersion": "stable.veverse.com/v1",
                    "kind": "GameServer",
                    "executeHookOnEvent": ["Deleted"]
                }
            ]
        }
        # Print configuration to the stdout
        print(json.dumps(config))
    else:
        try:
            subprocess.call("../main/delete-game-server-resource.py", shell=True)
        except Exception as e:
            print(str(e))
