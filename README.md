### Notes

1. Start the server-controller deployment:

```shell
kubectl apply -n veverse -f yaml/deployment-server-controller.yaml
```

2. Start the api deployment:

```shell
kubectl apply -n veverse -f yaml/deployment-api.yaml
```

3. CURL request the API to list servers:

```shell
curl -X GET http://veverse-api.local/admin/servers?key=
```

```json
{
  "data": {
    "ok": true,
    "response": {
      "apiVersion": "stable.veverse.com/v1",
      "items": [],
      "kind": "GameServerList",
      "metadata": {
        "continue": "",
        "resourceVersion": "85431"
      }
    }
  }
}
```

4. CURL request the API to create a new server:

```shell
curl -X POST http://veverse-api.local/admin/servers/{space_id}?key=
```

```json
{
  "data": {
    "ok": true,
    "response": {
      "apiVersion": "stable.veverse.com/v1",
      "kind": "GameServer",
      "metadata": {
        "creationTimestamp": "2022-06-02T14:15:39Z",
        "generation": 1,
        "labels": {
          "app": "game-server-ddc9656c6121473b8043eb93dae41176"
        },
        "managedFields": [
          {
            "apiVersion": "stable.veverse.com/v1",
            "fieldsType": "FieldsV1",
            "fieldsV1": {
              "f:metadata": {
                "f:labels": {
                  ".": {},
                  "f:app": {}
                }
              },
              "f:spec": {
                ".": {},
                "f:env": {},
                "f:image": {},
                "f:imagePullSecrets": {},
                "f:settings": {
                  ".": {},
                  "f:host": {},
                  "f:maxPlayers": {},
                  "f:serverId": {},
                  "f:serverName": {},
                  "f:apiEmail": {},
                  "f:apiPassword": {},
                  "f:spaceId": {}
                }
              }
            },
            "manager": "OpenAPI-Generator",
            "operation": "Update",
            "time": "2022-06-02T14:15:39Z"
          }
        ],
        "name": "game-server-xxxxxx",
        "namespace": "veverse",
        "resourceVersion": "89386",
        "uid": "xxxxx-xxxxx-xxxxx-xxxxx-xxxxx"
      },
      "spec": {
        "env": [],
        "image": "registry.example.com/artheon/shell-operator:veverse-server",
        "imagePullSecrets": [
          {
            "name": "dev-hackerman-me"
          }
        ],
        "settings": {
          "host": "game-server.example.com",
          "maxPlayers": 100,
          "serverId": "xxxxx-xxxxx-xxxxx-xxxxx-xxxxx",
          "serverName": "game-server-xxxxxxxx",
          "apiEmail": "gs@example.com",
          "apiPassword": "xxxxxxxx",
          "spaceId": "xxxxx-xxxxx-xxxxx-xxxxx-xxxxx"
        }
      }
    }
  }
}
```

5. CURL request the API to delete an existing server:

```shell
curl -X DELETE http://veverse-api.local/admin/servers/{server_id}?key=
```

### Logic

Create a server:

1. Public API creates a new GameServer resource.
2. ShellOperator listens to the Create GameServer resource events.
3. When such resource is created, ShellOperator deploys a service, ingress and deployment for the game server.

Delete a server:

1. Public API deletes a GameServer resource.
2. ShellOperator listens to the Delete GameServer resource events.
3. When such resource is deleted, ShellOperator deletes a service, ingress and deployment for the game server.

###                 

Start a server by a user request.

1. User approaches the portal or clicks the "Visit Server" button.
2. Portal checks for an available server by sending a match GET request.
    - If server is available, API responds with server metadata having its status "online".
    - If the server is about to start, API responds with server metadata having status "starting".
3. If portal gets "launch" status, then it must poll the API each 5 seconds to check if server status changed to "online".

Server statuses:

- starting - API starts a server, a gs resource created
- online - server is online and can accept new connections
- stopping - API stops a server, a gs resource deleted
- offline - server is offline, its cluster resources has been deleted

### YAML

yaml directory contains development and test deployment configs, should be removed with release

### dos2unix

note that py scripts must be processed with dos2unix otherwise inside the container we get errors related to invalid end line symbols even if they are converted to UNIX before build
