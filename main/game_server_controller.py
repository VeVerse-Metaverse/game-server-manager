import typing

from kubernetes import client, config
from kubernetes.client import V1Service

from database import instance as db, server_model


# region Config


class GameServerConfig(object):
    def __init__(self, o):
        if not o:
            raise ValueError("event object is none")

        # unwrap the event object
        if "object" in o:
            o = o["object"]

        self._object = o

        if "kind" not in self._object or self._object["kind"] != "GameServer":
            print(self._object)
            raise ValueError("object has invalid kind field")

        if "spec" not in self._object or "metadata" not in self._object:
            print(self._object)
            raise ValueError("event has no metadata or spec field")

        metadata = self._object["metadata"]
        if "name" not in metadata:
            print(self._object)
            raise ValueError("metadata has no name field")
        self.name = metadata["name"]

        if "uid" not in metadata:
            print(self._object)
            raise ValueError("metadata has no uid field")
        self.uid = metadata["uid"]


class GameServerDeploymentConfig(GameServerConfig):
    def __init__(self, o):
        super().__init__(o)

        spec = self._object["spec"]
        if "image" not in spec:
            print(self._object)
            raise ValueError("object spec has no required image field")
        self.image: str = spec["image"]

        if "imagePullSecrets" in spec:
            self.image_pull_secrets: typing.List = spec["imagePullSecrets"]

        if "env" in spec and isinstance(spec["env"], list):
            self.env: typing.List = spec["env"]

        if "settings" in spec and isinstance(spec, dict):
            self.settings: typing.Dict = spec["settings"]

        if "serverId" not in spec["settings"]:
            raise ValueError("settings has no serverId field")

        if "apiEmail" not in spec["settings"]:
            raise ValueError("settings has no apiEmail field")

        if "apiPassword" not in spec["settings"]:
            raise ValueError("settings has no apiPassword field")


# endregion

class GameServerController(object):
    def __init__(self):
        service_account_base_dir = "/var/run/secrets/kubernetes.io/serviceaccount/"

        # Load namespace
        namespace_path = service_account_base_dir + "namespace"
        with open(namespace_path, "r") as namespace_file:
            self.__namespace = namespace_file.read()

        self.api_core = client.CoreV1Api()
        self.api_apps = client.AppsV1Api()

    # region Create

    def create_game_server_deployment(self, in_config: GameServerDeploymentConfig):
        env = in_config.env
        if in_config.settings:
            if "host" in in_config.settings:
                env.append({"name": "VE_SERVER_HOST", "value": str(in_config.settings["host"])})
            if "key" in in_config.settings:
                env.append({"name": "VE_SERVER_API_KEY", "value": str(in_config.settings["apiKey"])})
            if "maxPlayers" in in_config.settings:
                env.append({"name": "VE_SERVER_MAX_PLAYERS", "value": str(in_config.settings["maxPlayers"])})
            if "spaceId" in in_config.settings:
                env.append({"name": "VE_SERVER_SPACE_ID", "value": str(in_config.settings["spaceId"])})
            if "serverId" in in_config.settings:
                env.append({"name": "VE_SERVER_WORLD_ID", "value": str(in_config.settings["spaceId"])})
            if "serverId" in in_config.settings:
                env.append({"name": "VE_SERVER_ID", "value": str(in_config.settings["serverId"])})
            if "serverName" in in_config.settings:
                env.append({"name": "VE_SERVER_NAME", "value": str(in_config.settings["serverName"])})
            if "apiEmail" in in_config.settings:
                env.append({"name": "VE_SERVER_API_EMAIL", "value": str(in_config.settings["apiEmail"])})
            if "apiPassword" in in_config.settings:
                env.append({"name": "VE_SERVER_API_PASSWORD", "value": str(in_config.settings["apiPassword"])})
            if "apiUrl" in in_config.settings:
                env.append({"name": "VE_API_ROOT_URL", "value": str(in_config.settings["apiUrl"])})
            if "api2Url" in in_config.settings:
                env.append({"name": "VE_API2_ROOT_URL", "value": str(in_config.settings["api2Url"])})
            if "blockchainUrl" in in_config.settings:
                env.append({"name": "VE_BLOCKCHAIN_ROOT_URL", "value": str(in_config.settings["blockchainUrl"])})
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
                                "env": env,
                                "image": in_config.image,
                                "imagePullPolicy": "Always",
                                "resources": {
                                },
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
        return self.api_apps.create_namespaced_deployment(namespace=self.__namespace, body=cfg)

    def create_game_server_service(self, in_config: GameServerDeploymentConfig):
        cfg = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": in_config.name,
                "annotations": {
                    "serverId": in_config.settings["serverId"],
                }
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
        service = self.api_core.create_namespaced_service(namespace=self.__namespace, body=cfg)
        if service and isinstance(service, V1Service):
            for p in service.spec.ports:
                if p.name == 'unreal':
                    server_model.update_port(db=db, id=service.metadata.annotations["serverId"], port=p.node_port)
        return service

    def create_game_server_resources(self, o):
        cfg = GameServerDeploymentConfig(o)
        server_model.update_status(db=db, id=str(cfg.settings["serverId"]), status="starting")
        deployment = self.create_game_server_deployment(cfg)
        service = self.create_game_server_service(cfg)
        return {
            "deployment": deployment,
            "service": service
        }

    def process_create_game_server_event(self, event):
        result: typing.Optional[typing.Dict] = None
        if isinstance(event, list):
            for e in event:
                if "objects" in e:
                    for o in e["objects"]:
                        result = self.create_game_server_resources(o)
                elif "object" in e:
                    result = self.create_game_server_resources(e["object"])
        elif isinstance(event, dict):
            if "objects" in event:
                for o in event["objects"]:
                    result = self.create_game_server_resources(o)
            elif "object" in event:
                result = self.create_game_server_resources(event["object"])
        return result

    # endregion

    # region Delete

    def delete_game_server_deployment(self, name: str):
        self.api_apps.delete_namespaced_deployment(namespace=self.__namespace, name=name)

    def delete_game_server_service(self, name: str):
        self.api_core.delete_namespaced_service(namespace=self.__namespace, name=name)

    def delete_game_server_resources(self, o):
        cfg = GameServerDeploymentConfig(o)
        server_model.update_status(db=db, id=str(cfg.settings["serverId"]), status="offline")
        self.delete_game_server_deployment(cfg.name)
        self.delete_game_server_service(cfg.name)

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

    # endregion


config.load_incluster_config()
instance = GameServerController()
