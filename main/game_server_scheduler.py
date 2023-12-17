import typing

from kubernetes import client, config
from database import Database, instance as db

class ServerScheduleMetadata(object):
    def __init__(self, columns: typing.List[str], row: typing.Tuple):
        self.id = row[columns.index('id')]
        self.schedule_start = row[columns.index('schedule_start')]
        self.schedule_end = row[columns.index('schedule_end')]
        self.space_id = row[columns.index('space_id')]
        self.user_id = row[columns.index('user_id')]


class ServerMetadata(object):
    def __init__(self, columns: typing.List[str], row: typing.Tuple):
        self.id = row[columns.index('id')]
        self.created_at = row[columns.index('created_at')]
        self.updated_at = row[columns.index('updated_at')]
        self.public = row[columns.index('public')]
        self.host = row[columns.index('host')]
        self.port = row[columns.index('port')]
        self.space_id = row[columns.index('space_id')]
        self.max_players = row[columns.index('max_players')]
        self.game_mode = row[columns.index('game_mode')]
        self.user_id = row[columns.index('user_id')]
        self.build = row[columns.index('build')]
        self.map = row[columns.index('map')]
        self.status = row[columns.index('status')]
        self.name = row[columns.index('name')]
        self.details = row[columns.index('details')]
        self.image = row[columns.index('image')]

    def __str__(self):
        return f"id: {self.id}, url: {self.host}:{self.port}, map: {self.map}, space: {self.space_id}, name: {self.name}, status: {self.status}"


class GameServerConfig(object):
    def __init__(self, o):
        if not o:
            raise ValueError("event object is none")

        self._object = o

        if "kind" not in self._object or self._object["kind"] != "GameServer":
            print(self._object)
            raise ValueError("event object has invalid kind field")

        if "spec" not in self._object or "metadata" not in self._object:
            print(self._object)
            raise ValueError("event has no metadata or spec field")

        metadata = self._object["metadata"]
        if "name" not in metadata:
            print(self._object)
            raise ValueError("event object metadata has no name field")
        self.name = metadata["name"]


class GameServerDeploymentConfig(GameServerConfig):
    def __init__(self, o):
        super().__init__(o)

        spec = self._object["spec"]
        if "image" not in spec:
            print(self._object)
            raise ValueError("event object spec has no image field")
        self.image = spec["image"]

        if "imagePullSecrets" not in spec:
            print(self._object)
            raise ValueError("event object spec has no imagePullSecrets field")
        self.image_pull_secrets = spec["imagePullSecrets"]

        if "env" not in spec:
            print(self._object)
            raise ValueError("event object spec has no env field")

        if not isinstance(spec["env"], list):
            print(self._object)
            raise ValueError("event object spec env is not an array")

        self.env = spec["env"]


class ServerManager(object):
    def __init__(self, in_db: Database, in_acc: str, in_host: str, in_pull_secrets: typing.List[typing.Dict[str, str]]):
        self.database = in_db
        # Service account
        self.acc = in_acc
        # Server host
        self.host = in_host
        # Image pull secrets
        self.pull_secrets = in_pull_secrets

        service_account_base_dir = "/var/run/secrets/kubernetes.io/serviceaccount/"

        # Load namespace
        namespace_path = service_account_base_dir + "namespace"
        with open(namespace_path, "r") as namespace_file:
            self.__namespace = namespace_file.read()

        self.api_core = client.CoreV1Api()
        self.api_apps = client.AppsV1Api()

    def create_game_server_deployment(self, in_config: GameServerDeploymentConfig):
        print("image_pull_secrets", in_config.image_pull_secrets)
        cfg = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": in_config.name,
                "labels": {
                    "app": in_config.name
                }
            },
            "spec": {
                "replicas": 1,
                "imagePullSecrets": in_config.image_pull_secrets,
                "serviceAccountName": "veverse-acc",
                "selector": {
                    "matchLabels": {
                        "app": in_config.name
                    }
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": in_config.name
                        }
                    },
                    "spec": {
                        "imagePullSecrets": in_config.image_pull_secrets,
                        "containers": [
                            {
                                "name": in_config.name,
                                "env": in_config.env,
                                "image": in_config.image,
                                "imagePullPolicy": "Always",
                                "ports": [
                                    {
                                        "name": "unreal",
                                        "containerPort": 7777
                                    }
                                ]
                            }
                        ]
                    }
                }
            }
        }
        self.api_apps.create_namespaced_deployment(namespace=self.__namespace, body=cfg)

    def create_game_server_service(self, in_config: GameServerConfig):
        cfg = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": in_config.name
            },
            "spec": {
                "selector": {
                    "app": in_config.name
                },
                "ports": [
                    {
                        "name": "unreal",
                        "port": 7777,
                        "protocol": "UDP"
                    }
                ],
                "type": "NodePort"
            }
        }
        self.api_core.create_namespaced_service(namespace=self.__namespace, body=cfg)

    def delete_game_server_deployment(self, name: str):
        self.api_apps.delete_namespaced_deployment(namespace=self.__namespace, name=name)

    def delete_game_server_service(self, name: str):
        self.api_core.delete_namespaced_service(namespace=self.__namespace, name=name)

    def create_game_server_resources(self, o):
        cfg = GameServerDeploymentConfig(o)
        self.create_game_server_deployment(cfg)
        self.create_game_server_service(cfg)

    def delete_game_server_resources(self, o):
        cfg = GameServerDeploymentConfig(o)
        self.delete_game_server_deployment(cfg.name)
        self.delete_game_server_service(cfg.name)

    def process_create_game_server_event(self, event):
        if isinstance(event, list):
            for e in event:
                if "objects" in e:
                    for o in e["objects"]:
                        self.create_game_server_resources(o)
                elif "object" in e:
                    self.create_game_server_resources(e["object"])
        elif isinstance(event, dict):
            if "objects" in event:
                for o in event["objects"]:
                    self.create_game_server_resources(o)
            elif "object" in event:
                self.create_game_server_resources(event["object"])

    def process_delete_game_server_event(self, event):
        if isinstance(event, list):
            for e in event:
                if "objects" in e:
                    for o in e["objects"]:
                        self.delete_game_server_resources(o)
                elif "object" in e:
                    self.delete_game_server_resources(e["object"])
        elif isinstance(event, dict):
            if "objects" in event:
                for o in event["objects"]:
                    self.delete_game_server_resources(o)
            elif "object" in event:
                self.delete_game_server_resources(event["object"])


# region Vars
config.load_incluster_config()
manager = ServerManager(in_db=db, in_acc='veverse-acc', in_host='192.168.111.111', in_pull_secrets=[{"name": "veverse-secret"}])
# endregion
